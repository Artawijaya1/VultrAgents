import unittest
from copy import deepcopy
from agent_core.data_provider import MockProvider
from agent_core.po_fraud import analyze_purchase_order


class POFraudTests(unittest.TestCase):
    def setUp(self):
        self.provider = MockProvider()

    def test_po_001_has_three_flags(self):
        result = analyze_purchase_order(self.provider, 'PO-001')
        self.assertEqual(result['po_id'], 'PO-001')
        self.assertEqual(result['supplier_id'], 'SUP-001')
        self.assertEqual(result['invoice_count'], 2)
        self.assertEqual(result['flag_count'], 3)
        self.assertEqual(result['status'], 'review_required')
        self.assertFalse(result['is_fraud_confirmed'])
        self.assertEqual(
            [f['rule_id'] for f in result['findings']].count('RECENT_BANK_CHANGE'), 2
        )

    def test_unknown_po(self):
        result = analyze_purchase_order(self.provider, 'PO-999')
        self.assertEqual(result['status'], 'not_found')

    def test_po_without_invoices_is_not_claimed_clean(self):
        po = deepcopy(self.provider.pos['PO-001'])
        po['po_id'] = 'PO-002'
        self.provider.pos['PO-002'] = po
        result = analyze_purchase_order(self.provider, 'PO-002')
        self.assertEqual(result['status'], 'no_invoices')
        self.assertEqual(result['invoice_count'], 0)
        self.assertEqual(result['flag_count'], 0)

    def test_cross_po_duplicate_appears_on_both_related_pos(self):
        po = deepcopy(self.provider.pos['PO-001'])
        po['po_id'] = 'PO-002'
        self.provider.pos['PO-002'] = po
        self.provider.invoices[1]['po_id'] = 'PO-002'
        result = analyze_purchase_order(self.provider, 'PO-001')
        dup = next(x for x in result['findings'] if x['rule_id'] == 'DUPLICATE_INVOICE')
        self.assertEqual(set(dup['evidence_record_ids']), {'REC-01', 'REC-02'})
        self.assertEqual(result['invoice_count'], 1)
        self.assertEqual(result['flag_count'], 2)

    def test_other_po_bank_change_not_included(self):
        po = deepcopy(self.provider.pos['PO-001'])
        po['po_id'] = 'PO-002'
        self.provider.pos['PO-002'] = po
        self.provider.invoices[1]['po_id'] = 'PO-002'
        result = analyze_purchase_order(self.provider, 'PO-001')
        bank_flags = [x for x in result['findings'] if x['rule_id'] == 'RECENT_BANK_CHANGE']
        self.assertEqual(len(bank_flags), 1)
        self.assertEqual(bank_flags[0]['evidence_record_ids'], ['REC-01'])


if __name__ == '__main__':
    unittest.main()
