"""Unit tests for tool routing and anti-cross-PO access."""
import json
import unittest

from agent_core.intelligent_graph import (
    available_tools, required_specialist, validate_model_call,
    verify_input, safe_model_content,
)


class Stage6PolicyTests(unittest.TestCase):
    def test_required_specialist(self):
        self.assertEqual(required_specialist('negotiation'), 'recommend_price_negotiation')
        self.assertEqual(required_specialist('fraud'), 'scan_purchase_order_anomalies')

    def test_tools_are_read_only_and_po_scoped(self):
        names = [x['function']['name'] for x in available_tools('negotiation')]
        self.assertIn('scan_purchase_order_anomalies', names)
        self.assertNotIn('send_email', names)
        self.assertNotIn('approve_purchase_order', names)

    def test_valid_tool_call(self):
        self.assertEqual(validate_model_call('scan_purchase_order_anomalies',
                                             '{"po_id":"PO-001"}', 'fraud', 'PO-001'),
                         {'po_id': 'PO-001'})

    def test_cross_po_access_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_model_call('scan_purchase_order_anomalies',
                                '{"po_id":"PO-002"}', 'fraud', 'PO-001')

    def test_supplier_tool_or_mutation_rejected(self):
        for name in ('scan_supplier_anomalies', 'send_email', 'delete_invoice'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_model_call(name, '{"po_id":"PO-001"}', 'negotiation', 'PO-001')

    def test_extra_args_rejected(self):
        with self.assertRaises(ValueError):
            validate_model_call('get_purchase_order',
                                json.dumps({'po_id': 'PO-001', 'sql': 'DROP TABLE invoices'}),
                                'negotiation', 'PO-001')

    def test_invalid_input_rejected(self):
        result = verify_input({'task': 'negotiation', 'reference_id': 'PO-001',
                               'session_id': '../unsafe', 'question': 'Test'})
        self.assertEqual(result['status'], 'invalid_request')

    def test_model_answer_truncation(self):
        self.assertEqual(len(safe_model_content('a' * 5000)), 1800)


if __name__ == '__main__':
    unittest.main()
