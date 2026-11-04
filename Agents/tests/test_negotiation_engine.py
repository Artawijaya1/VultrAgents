import unittest
from backend.services.negotiation_engine import plan_negotiation
from backend.database.repositories.procurement_repository import get_po

class NegotiationTests(unittest.TestCase):
    def test_draft_requires_approval(self):
        out = plan_negotiation(get_po("PO-001"))
        self.assertTrue(out["approval_required"])
        self.assertEqual(out["status"], "DRAFT_ONLY")
        self.assertEqual(out["estimated_savings_if_accepted"], "1000000")

    def test_reject_missing_order(self):
        with self.assertRaises(ValueError):
            plan_negotiation(None)
