"""FastAPI contract tests that never call an external LLM."""
import os
import unittest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from agent_core.graph_api import app


class Stage6APITests(unittest.IsolatedAsyncioTestCase):
    async def test_chat_auth_required(self):
        with patch.dict(os.environ, {'AGENT_API_KEY': 'testing-secret'}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
                resp = await c.post('/api/v1/agents/chat', json={
                    'task': 'negotiation', 'reference_id': 'PO-001', 'question': 'Harga?'
                })
        self.assertEqual(resp.status_code, 401)

    async def test_chat_request_contract(self):
        response_data = {
            'session_id': 'S-001', 'task': 'negotiation', 'reference_id': 'PO-001',
            'status': 'draft', 'summary': 'Human approval is required.', 'answer': 'Draft',
            'verified_result': {'opening_offer_unit': 130000}, 'precheck': None,
            'tool_trace': [], 'turn_index': 1, 'requires_approval': True,
            'error': None, 'notice': 'The model-generated text is a draft.',
        }
        async def fake_run_chat(**kwargs):
            return response_data
        with patch.dict(os.environ, {'AGENT_API_KEY': 'testing-secret'}), \
             patch('agent_core.graph_api.run_chat', side_effect=fake_run_chat):
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
                resp = await c.post('/api/v1/agents/chat',
                    headers={'Authorization': 'Bearer testing-secret'},
                    json={'task': 'negotiation', 'reference_id': 'PO-001',
                          'session_id': 'S-001', 'question': 'Buat draf'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['session_id'], 'S-001')
        self.assertEqual(resp.json()['answer'], 'Draft')
        self.assertEqual(resp.json()['summary'], 'Human approval is required.')
        self.assertTrue(resp.json()['requires_approval'])

    async def test_old_run_fraud_accepts_po_id(self):
        with patch.dict(os.environ, {'AGENT_API_KEY': 'testing-secret', 'AGENT_DATA_MODE': 'mock'}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
                resp = await c.post('/api/v1/agents/run',
                    headers={'Authorization': 'Bearer testing-secret'},
                    json={'task': 'fraud', 'reference_id': 'PO-001',
                          'reference_type': 'po', 'instruction': 'Pemeriksaan PO'})
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()['result']['scope'], 'purchase_order')
        self.assertEqual(resp.json()['result']['po_id'], 'PO-001')
        result = resp.json()['result']
        self.assertEqual(
            result['disclaimer'],
            'Anomaly indicators are not proof or a determination of fraud.',
        )
        self.assertIn('anomaly indicator(s)', resp.json()['summary'])
        descriptions = {finding['description'] for finding in result['findings']}
        actions = {finding['next_action'] for finding in result['findings']}
        self.assertIn('Invoice number TAG-100 is recorded more than once.', descriptions)
        self.assertIn('Manually verify the documents and payment status.', actions)


if __name__ == '__main__':
    unittest.main()
