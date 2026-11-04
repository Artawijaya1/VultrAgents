import unittest
from backend.mcp_server.tools.procurement import get_purchase_order
from backend.mcp_server.tools.negotiation import draft_negotiation
from backend.mcp_server.resources.policies import procurement_policy

class ToolLogicTests(unittest.TestCase):
    def test_pure_tool_logic(self):
        self.assertEqual(get_purchase_order("PO-001")["supplier_id"], 1)
        self.assertTrue(draft_negotiation("PO-001")["approval_required"])
        self.assertIn("persetujuan manusia", procurement_policy())
