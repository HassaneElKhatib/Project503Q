"""Async SQS publisher for the invoice pipeline.

Checkout uses this to publish invoice events. It's deliberately thin: one
method, retries on transient errors, structured logging, no batching.

Why aioboto3 and not boto3? boto3 is sync. Calling sync code from an async
FastAPI handler blocks the event loop. aioboto3 is the async wrapper.
"""
import json
from typing import Any, Protocol

from libs.logger import get_logger

logger = get_logger(__name__)


class SqsPublisher(Protocol):
    """Protocol so tests can substitute an in-memory fake."""

    async def publish(self, payload: dict[str, Any]) -> str: ...


class AwsSqsPublisher:
    """Real SQS publisher using aioboto3."""

    def __init__(
        self,
        queue_url: str,
        *,
        region: str = "us-east-1",
        max_attempts: int = 3,
    ) -> None:
        self._queue_url = queue_url
        self._region = region
        self._max_attempts = max_attempts
        # Lazy: the session is created on first call so test imports don't
        # need AWS creds.
        self._session = None

    def _get_session(self):
        if self._session is None:
            import aioboto3
            self._session = aioboto3.Session()
        return self._session

    async def publish(self, payload: dict[str, Any]) -> str:
        """Send one message. Returns the SQS MessageId."""
        body = json.dumps(payload, default=str)
        last_exc: Exception | None = None

        session = self._get_session()
        for attempt in range(1, self._max_attempts + 1):
            try:
                async with session.client("sqs", region_name=self._region) as sqs:
                    response = await sqs.send_message(
                        QueueUrl=self._queue_url,
                        MessageBody=body,
                    )
                logger.info(
                    "sqs message sent",
                    extra={
                        "message_id": response["MessageId"],
                        "queue": self._queue_url,
                        "attempt": attempt,
                    },
                )
                return response["MessageId"]
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "sqs send failed",
                    extra={
                        "attempt": attempt,
                        "max_attempts": self._max_attempts,
                        "error": str(exc),
                    },
                )

        # Out of retries
        assert last_exc is not None
        raise last_exc


class InMemorySqsPublisher:
    """Test double. Records every published message."""

    def __init__(self) -> None:
        self.published: list[dict[str, Any]] = []
        self._next_id = 1
        self.fail_next: int = 0  # set to N to make next N publishes raise

    async def publish(self, payload: dict[str, Any]) -> str:
        if self.fail_next > 0:
            self.fail_next -= 1
            raise RuntimeError("fake sqs failure")

        self.published.append(payload)
        msg_id = f"in-mem-{self._next_id}"
        self._next_id += 1
        return msg_id
