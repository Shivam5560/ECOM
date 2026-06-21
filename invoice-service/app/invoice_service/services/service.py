from __future__ import annotations

from io import BytesIO

from invoice_service.schemas import Invoice
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class InvoiceService:
    def generate(self, *, order_id: str, user_id: str, total: int) -> Invoice:
        return Invoice(
            order_id=order_id,
            user_id=user_id,
            total=total,
            created_by=user_id,
            receipt_html=f"<h1>Receipt</h1><p>Order {order_id}</p><strong>{total}</strong>",
        )

    def generate_pdf(self, invoice: Invoice) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setTitle(f"Invoice {invoice.id}")
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(72, 780, "ECOM Invoice")
        pdf.setFont("Helvetica", 11)
        pdf.drawString(72, 740, f"Invoice ID: {invoice.id}")
        pdf.drawString(72, 720, f"Order ID: {invoice.order_id}")
        pdf.drawString(72, 700, f"Customer: {invoice.user_id}")
        pdf.drawString(72, 680, f"Total: {invoice.total}")
        pdf.showPage()
        pdf.save()
        return buffer.getvalue()
