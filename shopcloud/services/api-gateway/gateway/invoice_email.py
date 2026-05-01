from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from html import escape

from fpdf import FPDF

from .settings import settings

logger = logging.getLogger(__name__)


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _pdf_safe_text(value: object) -> str:
    """Coerce text to a charset compatible with FPDF core fonts."""
    text = str(value or "")
    # Normalize common punctuation first for readability.
    text = text.replace("—", "-").replace("–", "-").replace("’", "'").replace("“", '"').replace("”", '"')
    # FPDF core fonts support latin-1; replace unsupported codepoints safely.
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _smtp_ready() -> bool:
    return bool(
        settings.smtp_enabled
        and settings.smtp_host
        and settings.smtp_from_email
        and settings.smtp_user
        and settings.smtp_password
    )


def _ses_region() -> str:
    return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "eu-central-1"


def _send_via_ses(*, to_email: str, subject: str, text_body: str, html_body: str | None) -> bool:
    """Send simple mail via SES API (works with EKS IRSA; no SMTP password)."""
    if not settings.smtp_from_email:
        return False
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        return False

    src = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    body: dict = {"Text": {"Data": text_body, "Charset": "UTF-8"}}
    if html_body:
        body["Html"] = {"Data": html_body, "Charset": "UTF-8"}
    try:
        boto3.client("ses", region_name=_ses_region()).send_email(
            Source=src,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": body,
            },
        )
        return True
    except (BotoCoreError, ClientError) as exc:
        logger.warning("SES send failed (%s); falling back to SMTP if configured", exc)
        return False


def _deliver_message(msg: EmailMessage) -> bool:
    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return True

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    return True


def send_email(*, to_email: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    if not to_email:
        return False
    if _send_via_ses(to_email=to_email, subject=subject, text_body=text_body, html_body=html_body):
        return True
    if not _smtp_ready():
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    return _deliver_message(msg)


def build_invoice_pdf(order: dict, invoice: dict) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "The Glow Lab - Invoice", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, _pdf_safe_text(f"Invoice ID: {invoice.get('invoiceId', '')}"), ln=True)
    pdf.cell(0, 8, _pdf_safe_text(f"Order ID: {order.get('_id', '')}"), ln=True)
    pdf.cell(0, 8, _pdf_safe_text(f"Generated At: {invoice.get('generatedAt', '')}"), ln=True)
    pdf.ln(4)

    address = order.get("address") or {}
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Billing Details", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for line in [
        address.get("name", ""),
        address.get("line1", ""),
        address.get("line2", ""),
        f"{address.get('city', '')} {address.get('postalCode', '')}".strip(),
        address.get("country", ""),
        f"Phone: {address.get('phone', '')}" if address.get("phone") else "",
    ]:
        if line:
            pdf.cell(0, 7, _pdf_safe_text(line), ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Items", ln=True)
    pdf.set_font("Helvetica", "", 11)
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin
    for item in order.get("items", []):
        name = item.get("name") or item.get("productId") or "Item"
        qty = int(item.get("quantity", 1))
        price = float(item.get("price", 0))
        line_total = qty * price
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(
            usable_width,
            7,
            _pdf_safe_text(f"- {name} x{qty}  @ {_money(price)}  = {_money(line_total)}"),
        )

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Total: {_money(float(order.get('total', 0)))}", ln=True)

    out = pdf.output(dest="S")
    if isinstance(out, bytearray):
        return bytes(out)
    if isinstance(out, bytes):
        return out
    return out.encode("latin-1")


def send_invoice_email(*, to_email: str, customer_name: str, order: dict, invoice: dict) -> bool:
    if not to_email:
        return False

    total = float(order.get("total", 0))
    order_id = order.get("_id", "")
    invoice_id = invoice.get("invoiceId", "")

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.5;">
        <h2 style="margin-bottom: 8px;">Thank you for your order, {customer_name or 'Valued Customer'}.</h2>
        <p>Your purchase with <strong>The Glow Lab</strong> has been confirmed.</p>
        <table style="border-collapse: collapse; margin: 16px 0;">
          <tr><td style="padding: 6px 12px; border: 1px solid #e5e7eb;"><strong>Invoice</strong></td><td style="padding: 6px 12px; border: 1px solid #e5e7eb;">{invoice_id}</td></tr>
          <tr><td style="padding: 6px 12px; border: 1px solid #e5e7eb;"><strong>Order ID</strong></td><td style="padding: 6px 12px; border: 1px solid #e5e7eb;">{order_id}</td></tr>
          <tr><td style="padding: 6px 12px; border: 1px solid #e5e7eb;"><strong>Total</strong></td><td style="padding: 6px 12px; border: 1px solid #e5e7eb;">{_money(total)}</td></tr>
        </table>
        <p>Please find your PDF invoice attached to this email.</p>
        <p style="margin-top: 22px;">Warm regards,<br /><strong>The Glow Lab Billing Team</strong></p>
      </body>
    </html>
    """

    msg = EmailMessage()
    msg["Subject"] = f"Invoice {invoice_id} - The Glow Lab"
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email
    msg.set_content(
        f"Hello {customer_name or 'Customer'},\n\n"
        f"Thank you for your order. Invoice {invoice_id} for order {order_id} totals {_money(total)}.\n"
        "Your PDF invoice is attached.\n\n"
        "The Glow Lab Billing Team"
    )
    msg.add_alternative(html, subtype="html")
    msg.add_attachment(
        build_invoice_pdf(order, invoice),
        maintype="application",
        subtype="pdf",
        filename=f"{invoice_id}.pdf",
    )

    # Primary path in EKS: SES API with IRSA and raw MIME (supports attachments).
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        boto3.client("ses", region_name=_ses_region()).send_raw_email(
            Source=msg["From"],
            Destinations=[to_email],
            RawMessage={"Data": msg.as_bytes()},
        )
        return True
    except Exception as exc:
        logger.warning("SES raw invoice send failed (%s); trying SMTP fallback", exc)

    if not _smtp_ready():
        return False
    return _deliver_message(msg)


def send_order_status_update_email(
    *,
    to_email: str,
    customer_name: str,
    order_id: str,
    old_status: str,
    new_status: str,
) -> bool:
    safe_name = escape(customer_name or "Customer")
    safe_order_id = escape(order_id)
    safe_old = escape(old_status or "unknown")
    safe_new = escape(new_status)
    subject = f"Order {order_id} status updated to {new_status.title()}"
    text_body = (
        f"Hello {customer_name or 'Customer'},\n\n"
        f"Your order {order_id} status was updated from {old_status} to {new_status}.\n"
        "Thank you for shopping with The Glow Lab.\n\n"
        "The Glow Lab Team"
    )
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.5;">
        <h2>Order status updated</h2>
        <p>Hello <strong>{safe_name}</strong>,</p>
        <p>Your order <strong>{safe_order_id}</strong> has moved from <strong>{safe_old}</strong> to <strong>{safe_new}</strong>.</p>
        <p>Thank you for shopping with The Glow Lab.</p>
      </body>
    </html>
    """
    return send_email(to_email=to_email, subject=subject, text_body=text_body, html_body=html_body)


def send_password_reset_code_email(*, to_email: str, customer_name: str, code: str) -> bool:
    safe_name = escape(customer_name or "Customer")
    safe_code = escape(code)
    subject = "Your password reset code - The Glow Lab"
    text_body = (
        f"Hello {customer_name or 'Customer'},\n\n"
        f"Use this code to reset your password: {code}\n"
        "This code expires soon. If you didn't request this, ignore this email.\n\n"
        "The Glow Lab Security Team"
    )
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.5;">
        <h2>Password reset request</h2>
        <p>Hello <strong>{safe_name}</strong>,</p>
        <p>Use this one-time code to reset your password:</p>
        <p style="font-size: 24px; font-weight: bold; letter-spacing: 2px;">{safe_code}</p>
        <p>If you didn't request this, you can ignore this email.</p>
      </body>
    </html>
    """
    return send_email(to_email=to_email, subject=subject, text_body=text_body, html_body=html_body)


def send_login_otp_email(*, to_email: str, customer_name: str, code: str) -> bool:
    safe_name = escape(customer_name or "Customer")
    safe_code = escape(code)
    subject = "Your login verification code - The Glow Lab"
    text_body = (
        f"Hello {customer_name or 'Customer'},\n\n"
        f"Your one-time login code is: {code}\n"
        "If this wasn't you, please reset your password.\n\n"
        "The Glow Lab Security Team"
    )
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.5;">
        <h2>Login verification</h2>
        <p>Hello <strong>{safe_name}</strong>,</p>
        <p>Use this code to complete sign-in:</p>
        <p style="font-size: 24px; font-weight: bold; letter-spacing: 2px;">{safe_code}</p>
      </body>
    </html>
    """
    return send_email(to_email=to_email, subject=subject, text_body=text_body, html_body=html_body)
