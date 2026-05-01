"""Generate a real PDF invoice using reportlab.

reportlab works in Lambda (pure Python, no native deps). We build the PDF
into an in-memory buffer and return the bytes.
"""
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _money(cents: int, currency: str) -> str:
    return f"{currency} {cents / 100:,.2f}"


def render_invoice_pdf(event: dict) -> bytes:
    """Build an invoice PDF from an InvoiceEvent dict."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=f"ShopCloud invoice {event['order_id'][:8]}",
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body = styles["BodyText"]
    h2 = styles["Heading2"]

    story = []

    # Header
    story.append(Paragraph("ShopCloud", title_style))
    story.append(Paragraph("Order Invoice", h2))
    story.append(Spacer(1, 12))

    # Order metadata table
    created = event.get("created_at", "")
    if created:
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            created = dt.strftime("%Y-%m-%d %H:%M UTC")
        except ValueError:
            pass

    meta = [
        ["Order ID", event["order_id"]],
        ["Customer", event["customer_email"]],
        ["Date", created],
        ["Currency", event.get("currency", "USD")],
    ]
    meta_table = Table(meta, colWidths=[1.5 * inch, 4.5 * inch])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 18))

    # Items table
    currency = event.get("currency", "USD")
    items_data = [["Product", "Qty", "Unit price", "Line total"]]
    for item in event["items"]:
        items_data.append(
            [
                item["product_name"],
                str(item["quantity"]),
                _money(item["unit_price_cents"], currency),
                _money(item["line_total_cents"], currency),
            ]
        )
    items_data.append(
        [
            "",
            "",
            "Total",
            _money(event["total_cents"], currency),
        ]
    )

    items_table = Table(
        items_data, colWidths=[3.5 * inch, 0.6 * inch, 1.2 * inch, 1.2 * inch]
    )
    items_table.setStyle(
        TableStyle(
            [
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                # Body grid
                ("GRID", (0, 0), (-1, -2), 0.25, colors.lightgrey),
                # Total row
                ("LINEABOVE", (-2, -1), (-1, -1), 1, colors.black),
                ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
                # Padding
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(items_table)
    story.append(Spacer(1, 24))

    story.append(
        Paragraph(
            "Thank you for shopping with ShopCloud. "
            "Questions? Reply to this email and our team will help.",
            body,
        )
    )

    doc.build(story)
    return buffer.getvalue()
