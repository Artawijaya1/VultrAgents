"""Offline fake-LLM tests using REAL LangGraph + MCP; no paid API calls."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from agent_core.intelligent_graph import run_chat


class FakeCompletions:
    def __init__(self, tool_name, po_id='PO-001', wrong_po=False):
        self.tool_name = tool_name
        self.po_id = 'PO-999' if wrong_po else po_id
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) % 2:
            tool_call = SimpleNamespace(
                id='call-1',
                function=SimpleNamespace(name=self.tool_name,
                                         arguments='{"po_id":"' + self.po_id + '"}'),
            )
            msg = SimpleNamespace(
                tool_calls=[tool_call], content=None,
                model_dump=lambda exclude_none=True: {
                    'role': 'assistant',
                    'tool_calls': [{'id': 'call-1', 'type': 'function', 'function': {
                        'name': self.tool_name,
                        'arguments': '{"po_id":"' + self.po_id + '"}'}}],
                },
            )
        else:
            msg = SimpleNamespace(
                tool_calls=[],
                content='The initial recommendation requires human approval.',
            )
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


class FakeLLM:
    def __init__(self, tool_name, wrong_po=False):
        self.completions = SimpleNamespace(create=FakeCompletions(tool_name, wrong_po=wrong_po).create)
        self.spy = self.completions.create.__self__
        self.chat = SimpleNamespace(completions=self.completions)


class EnhancedChatRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_negotiation_model_tool_plus_mandatory_po_precheck(self):
        fake = FakeLLM('recommend_price_negotiation')
        with patch.dict(os.environ, {'LLM_API_KEY': 'fake-test-key', 'LLM_MODEL': 'test-model'}), \
             patch('agent_core.intelligent_graph.build_llm_client', return_value=fake):
            result = await run_chat('negotiation', 'PO-001', 'Mohon draf penawaran', str(uuid4()))
        self.assertEqual(result['status'], 'draft')
        self.assertEqual(result['verified_result']['opening_offer_unit'], 130000)
        self.assertEqual(result['precheck']['scope'], 'purchase_order')
        self.assertTrue(result['requires_approval'])
        self.assertEqual(
            result['answer'],
            'The initial recommendation requires human approval.',
        )
        self.assertIn('Human approval is required.', result['notice'])
        self.assertIn(
            'Always respond in English',
            fake.spy.calls[0]['messages'][0]['content'],
        )
        self.assertIn('scan_purchase_order_anomalies', [x['tool'] for x in result['tool_trace']])
        self.assertIn('recommend_price_negotiation', [x['tool'] for x in result['tool_trace']])

    async def test_fraud_scans_po_directly(self):
        fake = FakeLLM('scan_purchase_order_anomalies')
        with patch.dict(os.environ, {'LLM_API_KEY': 'fake-test-key', 'LLM_MODEL': 'test-model'}), \
             patch('agent_core.intelligent_graph.build_llm_client', return_value=fake):
            result = await run_chat('fraud', 'PO-001', 'Periksa invoice PO ini', str(uuid4()))
        self.assertEqual(result['status'], 'review_required')
        self.assertEqual(result['verified_result']['po_id'], 'PO-001')
        self.assertFalse(result['verified_result']['is_fraud_confirmed'])

    async def test_reject_cross_po_tool_call(self):
        fake = FakeLLM('scan_purchase_order_anomalies', wrong_po=True)
        with patch.dict(os.environ, {'LLM_API_KEY': 'fake-test-key', 'LLM_MODEL': 'test-model'}), \
             patch('agent_core.intelligent_graph.build_llm_client', return_value=fake):
            result = await run_chat('fraud', 'PO-001', 'Periksa invoice PO ini', str(uuid4()))
        self.assertEqual(result['status'], 'needs_tool_use')
        self.assertIsNone(result['verified_result'])
        self.assertFalse(result['tool_trace'][-1]['ok'])

    async def test_memory_is_scoped_and_bounded(self):
        fake = FakeLLM('recommend_price_negotiation')
        session = str(uuid4())
        with patch.dict(os.environ, {'LLM_API_KEY': 'fake-test-key', 'LLM_MODEL': 'test-model'}), \
             patch('agent_core.intelligent_graph.build_llm_client', return_value=fake):
            one = await run_chat('negotiation', 'PO-001', 'Permintaan pertama', session)
            two = await run_chat('negotiation', 'PO-001', 'Permintaan kedua', session)
        self.assertEqual(one['turn_index'], 1)
        self.assertEqual(two['turn_index'], 2)
        # Requests 3 and 4 are the second turn's two LLM interactions.
        self.assertTrue(any('Permintaan pertama' in str(x) for x in fake.spy.calls[2]['messages']))

    async def test_missing_credentials_is_safe(self):
        env = dict(os.environ)
        env.pop('LLM_API_KEY', None)
        env.pop('LLM_MODEL', None)
        with patch.dict(os.environ, env, clear=True):
            result = await run_chat('negotiation', 'PO-001', 'Coba tanpa kunci', str(uuid4()))
        self.assertEqual(result['status'], 'not_configured')
        self.assertEqual(
            result['error'],
            'LLM_API_KEY and LLM_MODEL are not configured.',
        )
        self.assertIsNone(result['verified_result'])


if __name__ == '__main__':
    unittest.main()
