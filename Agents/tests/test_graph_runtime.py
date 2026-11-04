"""Requires installed MCP v2 and LangGraph; skipped when unavailable."""
import importlib.util
import unittest

HAS_GRAPH_RUNTIME = (importlib.util.find_spec('langgraph') is not None
                     and importlib.util.find_spec('mcp') is not None)


@unittest.skipUnless(HAS_GRAPH_RUNTIME, 'Install graph_requirements.txt and agent_requirements.txt')
class LangGraphMCPIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_negotiation_with_fraud_precheck(self):
        from agent_core.graph_workflow import run_workflow
        response = await run_workflow('negotiation', 'PO-001', request_id='itest-001')
        self.assertEqual(response['status'], 'draft')
        self.assertTrue(response['requires_approval'])
        self.assertEqual(len(response['tool_trace']), 3)
        self.assertIsNotNone(response['precheck'])

    async def test_fraud_workflow(self):
        from agent_core.graph_workflow import run_workflow
        response = await run_workflow('fraud', 'SUP-001', request_id='itest-002')
        self.assertEqual(response['status'], 'review_required')
        self.assertTrue(response['result']['findings'])
        self.assertEqual(len(response['tool_trace']), 2)


if __name__ == '__main__':
    unittest.main()
