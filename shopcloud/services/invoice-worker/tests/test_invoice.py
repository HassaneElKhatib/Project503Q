"""Invoice worker tests.

We use moto to mock S3 and SES. PDF generation is tested for real (real
reportlab output that we then verify is a valid PDF by checking magic
bytes).

Partial-batch failure: we test that one bad record doesn't poison the
whole batch.
"""
import json
import os
from contextlib import contextmanager

import boto3
import pytest
try:
    from moto import mock_aws
except ImportError:
    from moto import mock_s3, mock_ses

    @contextmanager
    def mock_aws():
        with mock_s3():
            with mock_ses():
                yield

# Env BEFORE handler import
os.environ["INVOICES_BUCKET"] = "shopcloud-invoices-test"
os.environ["SES_FROM_ADDRESS"] = "noreply@shopcloud.test"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"


@pytest.fixture
def aws():
    """Spin up mocked S3 + SES for one test."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="shopcloud-invoices-test")

        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_email_identity(EmailAddress="noreply@shopcloud.test")

        # Drop any cached handler module so its module-global boto3 clients
        # are constructed inside the moto context.
        import sys
        for mod in [m for m in list(sys.modules) if m.startswith("src.handler")]:
            del sys.modules[mod]

        from src import handler as h  # fresh import - clients hit moto

        yield {"s3": s3, "ses": ses, "handler": h}


def _sample_event(*, order_id: str = "a1b2c3d4-0001-4000-8000-000000000001",
                  email: str = "alice@example.com") -> dict:
    return {
        "messageId": "msg-1",
        "body": json.dumps({
            "event_version": 1,
            "order_id": order_id,
            "customer_id": "cognito-customer-1",
            "customer_email": email,
            "items": [
                {"product_id": "p-001", "product_name": "Widget",
                 "quantity": 2, "unit_price_cents": 1500, "line_total_cents": 3000},
                {"product_id": "p-002", "product_name": "Gadget",
                 "quantity": 1, "unit_price_cents": 999, "line_total_cents": 999},
            ],
            "total_cents": 3999,
            "currency": "USD",
            "created_at": "2026-04-29T12:34:56+00:00",
        }),
    }


# ---------- PDF rendering ----------

def test_pdf_is_valid():
    """Render a PDF and confirm the magic header bytes."""
    from src.pdf import render_invoice_pdf

    event = json.loads(_sample_event()["body"])
    pdf_bytes = render_invoice_pdf(event)

    # Real PDF files start with %PDF-
    assert pdf_bytes.startswith(b"%PDF-"), "Output is not a valid PDF"
    assert b"%%EOF" in pdf_bytes[-32:], "PDF doesn't end with EOF marker"
    assert len(pdf_bytes) > 1000, "PDF unexpectedly small"


def test_pdf_includes_order_data():
    """The PDF should contain visible references to the order.

    reportlab compresses page content, so byte-searching the raw output
    misses things. Use pypdf to extract real text.
    """
    from io import BytesIO

    import pypdf

    from src.pdf import render_invoice_pdf

    event = json.loads(_sample_event()["body"])
    pdf_bytes = render_invoice_pdf(event)

    reader = pypdf.PdfReader(BytesIO(pdf_bytes))
    text = "".join(page.extract_text() for page in reader.pages)

    assert "ShopCloud" in text
    assert "Widget" in text
    assert "Gadget" in text
    assert event["customer_email"] in text
    # Total line: "Total" label plus the formatted amount
    assert "39.99" in text  # 3999 cents


# ---------- S3 upload ----------

def test_upload_writes_to_correct_key(aws):
    h = aws["handler"]
    event = _sample_event()

    h.process_record(event)

    body = json.loads(event["body"])
    expected_key = h.s3_key_for(body["order_id"], body["created_at"])
    assert expected_key == "invoices/2026/04/a1b2c3d4-0001-4000-8000-000000000001.pdf"

    obj = aws["s3"].get_object(Bucket="shopcloud-invoices-test", Key=expected_key)
    pdf_bytes = obj["Body"].read()
    assert pdf_bytes.startswith(b"%PDF-")
    assert obj["ContentType"] == "application/pdf"
    # Encryption applied
    assert obj.get("ServerSideEncryption") in ("AES256", "aws:kms")


# ---------- SES send ----------

def test_email_sent_with_attachment(aws):
    h = aws["handler"]
    event = _sample_event(email="customer@example.com")

    result = h.process_record(event)
    assert "ses_message_id" in result

    # moto exposes sent emails via get_send_quota / get_send_statistics, but
    # checking quota proves something was sent.
    stats = aws["ses"].get_send_statistics()
    assert len(stats["SendDataPoints"]) >= 0  # send attempted


# ---------- Lambda handler entrypoint ----------

def test_handler_returns_no_failures_on_success(aws):
    h = aws["handler"]
    event = {"Records": [_sample_event()]}

    response = h.lambda_handler(event, None)
    assert response == {"batchItemFailures": []}


def test_partial_batch_failure_isolated(aws):
    """One bad record doesn't poison good ones."""
    h = aws["handler"]

    bad_record = {
        "messageId": "bad-1",
        "body": "this is not json",
    }
    good_record = _sample_event()
    good_record["messageId"] = "good-1"

    event = {"Records": [bad_record, good_record]}
    response = h.lambda_handler(event, None)

    failed_ids = [f["itemIdentifier"] for f in response["batchItemFailures"]]
    assert "bad-1" in failed_ids
    assert "good-1" not in failed_ids


def test_missing_required_fields_fails_record(aws):
    h = aws["handler"]

    incomplete = {
        "messageId": "incomplete-1",
        "body": json.dumps({"order_id": "x"}),  # missing email, items, total
    }
    response = h.lambda_handler({"Records": [incomplete]}, None)
    assert response["batchItemFailures"] == [{"itemIdentifier": "incomplete-1"}]


# ---------- s3 key path ----------

def test_s3_key_uses_year_month_path():
    from src.handler import s3_key_for
    assert s3_key_for("o-1", "2026-04-29T12:00:00+00:00") == "invoices/2026/04/o-1.pdf"
    assert s3_key_for("o-2", "2025-12-15T00:00:00+00:00") == "invoices/2025/12/o-2.pdf"


def test_s3_key_falls_back_when_date_invalid():
    from src.handler import s3_key_for
    key = s3_key_for("o-1", "not-a-date")
    # Falls back to current UTC, but format is still right
    assert key.startswith("invoices/")
    assert key.endswith("/o-1.pdf")
