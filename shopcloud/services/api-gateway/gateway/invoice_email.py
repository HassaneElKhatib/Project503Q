from __future__ import annotations

import smtplib
from email.message import EmailMessage
from html import escape

from fpdf import FPDF

from .settings import settings


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _smtp_ready() -> bool:
    return bool(
        settings.smtp_enabled
        and settings.smtp_host
        and settings.smtp_from_email
        and settings.smtp_user
        and settings.smtp_password
    )


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
    if not _smtp_ready() or not to_email:
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
    pdf.cell(0, 8, f"Invoice ID: {invoice.get('invoiceId', '')}", ln=True)
    pdf.cell(0, 8, f"Order ID: {order.get('_id', '')}", ln=True)
    pdf.cell(0, 8, f"Generated At: {invoice.get('generatedAt', '')}", ln=True)
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
            pdf.cell(0, 7, line, ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Items", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for item in order.get("items", []):
        name = item.get("name") or item.get("productId") or "Item"
        qty = int(item.get("quantity", 1))
        price = float(item.get("price", 0))
        line_total = qty * price
        pdf.multi_cell(0, 7, f"- {name} x{qty}  @ {_money(price)}  = {_money(line_total)}")

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
    if not _smtp_ready() or not to_email:
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
