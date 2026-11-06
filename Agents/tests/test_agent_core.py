import unittest
from agent_core.data_provider import MockProvider
from agent_core.orchestrator import execute_agent

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.data = MockProvider()

    def test_negotiation_within_budget(self):
        r = execute_agent('negotiation','PO-001',self.data)
        self.assertEqual(r['status'],'draft')
        self.assertLessEqual(r['opening_offer_unit'],r['budget_ceiling_unit'])
        self.assertTrue(r['requires_approval'])
        self.assertIn('Please consider an offer', r['draft_message'])
        self.assertIn('not been sent to the supplier', r['disclaimer'])
        self.assertTrue(all(option['reason'].isascii() for option in r['options']))

    def test_negotiation_no_po(self):
        self.assertEqual(execute_agent('negotiation','NONE',self.data)['status'],'not_found')

    def test_fraud_duplicate_flag(self):
        r = execute_agent('fraud','SUP-001',self.data)
        self.assertIn('DUPLICATE_INVOICE',[x['rule_id'] for x in r['findings']])
        self.assertFalse(r['is_fraud_confirmed'])
        self.assertIn('not proof', r['disclaimer'])
        self.assertTrue(all(
            finding['description'].isascii()
            and finding['next_action'].isascii()
            for finding in r['findings']
        ))

    def test_fraud_recent_bank_change(self):
        r = execute_agent('fraud','SUP-001',self.data)
        self.assertIn('RECENT_BANK_CHANGE',[x['rule_id'] for x in r['findings']])

    def test_unknown_supplier(self):
        self.assertEqual(execute_agent('fraud','UNKNOWN',self.data)['status'],'not_found')

    def test_clean_supplier(self):
        self.data.invoices=[]
        self.data.suppliers['SUP-001']['bank_last_changed_at']=None
        self.assertEqual(execute_agent('fraud','SUP-001',self.data)['status'],'no_flags')

    def test_unknown_task(self):
        self.assertEqual(execute_agent('delete','PO-001',self.data)['status'],'invalid_task')

if __name__=='__main__':
    unittest.main()
