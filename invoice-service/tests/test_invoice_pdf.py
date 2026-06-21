from __future__ import annotations

import unittest

from invoice_service.service import InvoiceService


class InvoicePdfTests(unittest.TestCase):
    def test_generates_pdf_bytes_for_order_invoice(self) -> None:
        service = InvoiceService()

        invoice = service.generate(order_id="order-1", user_id="buyer-1", total=249)
        pdf = service.generate_pdf(invoice)

        self.assertEqual(invoice.order_id, "order-1")
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 500)


if __name__ == "__main__":
    unittest.main()
