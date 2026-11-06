import json
import unittest
from types import SimpleNamespace
from agent_core.graph_helpers import validate_reference, normalize_mcp_result, build_summary


class HelpersTest(unittest.TestCase):
    def test_valid_reference(self):
        self.assertIsNone(validate_reference('negotiation', 'PO-001'))
    def test_task_rejected(self):
        self.assertIsNotNone(validate_reference('other', 'PO-001'))
    def test_unsafe_reference_rejected(self):
        self.assertIsNotNone(validate_reference('fraud', '../etc/passwd'))
    def test_structured_mcp_response(self):
        r = SimpleNamespace(is_error=False, structured_content={'result': {'status': 'draft'}}, content=[])
        self.assertEqual(normalize_mcp_result(r)['status'], 'draft')
    def test_text_mcp_response(self):
        r = SimpleNamespace(is_error=False, structured_content=None,
                            content=[SimpleNamespace(text=json.dumps({'flag_count': 2}))])
        self.assertEqual(normalize_mcp_result(r)['flag_count'], 2)
    def test_error_mcp_response(self):
        r = SimpleNamespace(is_error=True, structured_content=None, content=[])
        self.assertIn('error', normalize_mcp_result(r))
    def test_summary_warns_on_precheck(self):
        s = build_summary('negotiation', {'opening_offer_unit': 100, 'currency': 'IDR'}, {'flag_count': 1})
        self.assertIn('risk indicators', s)


if __name__ == '__main__':
    unittest.main()
