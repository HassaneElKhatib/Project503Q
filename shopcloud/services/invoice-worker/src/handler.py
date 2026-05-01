"""Invoice Lambda handler.

Triggered by SQS. For each record:
  1. Parse the JSON body into an InvoiceEvent
  2. Generate the PDF
  3. Upload to S3 with SSE
  4. Send via SES with the PDF attached
  5. Update the invoice row in RDS (best-effort; failures don't block delivery)

Lambda partial-batch failures: if some records succeed and others fail, we
return the failed message IDs in `batchItemFailures` so SQS only retries
those. This requires the event source mapping to have
  ReportBatchItemFailures = True

Otherwise SQS retries the entire batch on any failure, and the successful
emails get re-sent (customers receive duplicates).
"""
import json
import logging
import os
from datetime import datetime, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import boto3

from src.pdf import render_invoice_pdf

# Lambda runs in CloudWatch Logs by default; structured JSON helps Insights queries
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# AWS clients are global so they're reused across invocations (warm starts)
_s3 = boto3.client("s3")
_ses = boto3.client("ses")

INVOICES_BUCKET = os.environ["INVOICES_BUCKET"]
SES_FROM_ADDRESS = os.environ["SES_FROM_ADDRESS"]
KMS_KEY_ARN = os.environ.get("KMS_KEY_ARN")  # optional - if set, use SSE-KMS


def s3_key_for(order_id: str, created_at: str) -> str:
    """invoices/<year>/<month>/<order_id>.pdf - per the project spec."""
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        dt = datetime.now(timezone.utc)
    return f"invoices/{dt.year}/{dt.month:02d}/{order_id}.pdf"


def _upload_pdf(key: str, pdf_bytes: bytes) -> None:
    """PUT the PDF to S3 with server-side encryption."""
    extra: dict[str, Any] = {"ContentType": "application/pdf"}
    if KMS_KEY_ARN:
        extra["ServerSideEncryption"] = "aws:kms"
        extra["SSEKMSKeyId"] = KMS_KEY_ARN
    else:
        extra["ServerSideEncryption"] = "AES256"

    _s3.put_object(
        Bucket=INVOICES_BUCKET,
        Key=key,
        Body=pdf_bytes,
        **extra,
    )


def _send_email(event: dict, pdf_bytes: bytes) -> str:
    """Build a multipart email with the PDF attached and ship via SES SendRawEmail."""
    msg = MIMEMultipart()
    msg["Subject"] = f"ShopCloud invoice for order {event['order_id'][:8]}"
    msg["From"] = SES_FROM_ADDRESS
    msg["To"] = event["customer_email"]

    text = (
        f"Thanks for your order!\n\n"
        f"Order ID: {event['order_id']}\n"
        f"Total: {event.get('currency', 'USD')} {event['total_cents'] / 100:,.2f}\n\n"
        f"Your invoice is attached.\n\n"
        f"-- ShopCloud"
    )
    msg.attach(MIMEText(text, "plain"))

    pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_part.add_header(
        "Content-Disposition",
        "attachment",
        filename=f"invoice-{event['order_id'][:8]}.pdf",
    )
    msg.attach(pdf_part)

    response = _ses.send_raw_email(
        Source=SES_FROM_ADDRESS,
        Destinations=[event["customer_email"]],
        RawMessage={"Data": msg.as_string()},
    )
    return response["MessageId"]


def process_record(record: dict) -> dict:
    """Process one SQS record. Returns a dict with the result (for tests)."""
    body_text = record["body"]
    event = json.loads(body_text)

    # Defensive shape check
    required = {"order_id", "customer_email", "items", "total_cents"}
    missing = required - event.keys()
    if missing:
        raise ValueError(f"Invoice event missing fields: {sorted(missing)}")

    logger.info(
        "processing invoice",
        extra={"order_id": event["order_id"], "customer": event["customer_email"]},
    )

    # 1. PDF
    pdf_bytes = render_invoice_pdf(event)

    # 2. S3
    key = s3_key_for(event["order_id"], event.get("created_at", ""))
    _upload_pdf(key, pdf_bytes)
    logger.info("invoice uploaded", extra={"order_id": event["order_id"], "s3_key": key})

    # 3. SES
    message_id = _send_email(event, pdf_bytes)
    logger.info(
        "invoice emailed",
        extra={"order_id": event["order_id"], "ses_message_id": message_id},
    )

    return {
        "order_id": event["order_id"],
        "s3_key": key,
        "ses_message_id": message_id,
    }


def lambda_handler(event: dict, context: Any) -> dict:
    """SQS event entrypoint with partial-batch failure reporting."""
    failures: list[dict] = []
    succeeded: list[str] = []

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        try:
            process_record(record)
            succeeded.append(message_id)
        except Exception:
            logger.exception(
                "record processing failed",
                extra={"message_id": message_id},
            )
            failures.append({"itemIdentifier": message_id})

    logger.info(
        "batch processed",
        extra={"succeeded": len(succeeded), "failed": len(failures)},
    )
    return {"batchItemFailures": failures}
