import unittest
from backend.services.fraud_rules import scan_invoices
from backend.database.repositories.procurement_repository import get_invoices, get_price_history

class FraudRulesTests(unittest.TestCase):
    def test_detects_duplicates_price_spike_and_bank_change(self):
        findings = scan_invoices(get_invoices(), get_price_history())
        codes = {f["code"] for f in findings}
        self.assertIn("DUPLICATE_INVOICE_NUMBER", codes)
        self.assertIn("PRICE_SPIKE", codes)
        self.assertIn("BANK_CHANGE_REVIEW", codes)

    def test_possible_split_invoices_flagged(self):
        rows = [
            {"id": 51, "supplier_id": 9, "invoice_number": "A", "product_id": 10,
             "unit_price": "1000", "total_amount": "2800000", "invoice_date": "2026-11-01"},
            {"id": 52, "supplier_id": 9, "invoice_number": "B", "product_id": 10,
             "unit_price": "1000", "total_amount": "2700000", "invoice_date": "2026-11-03"},
        ]
        codes = {x["code"] for x in scan_invoices(rows, [])}
        self.assertIn("POSSIBLE_SPLIT_PURCHASE", codes)

    def test_no_false_alert_on_empty_dataset(self):
        self.assertEqual(scan_invoices([], []), [])
