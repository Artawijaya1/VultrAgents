import unittest
from backend.security.permissions import may

class PermissionTests(unittest.TestCase):
    def test_auditor_cannot_approve(self):
        self.assertTrue(may("auditor", "fraud.read"))
        self.assertFalse(may("auditor", "approval.decide"))

    def test_buyer_cannot_send_money(self):
        self.assertFalse(may("buyer", "payment.send"))
