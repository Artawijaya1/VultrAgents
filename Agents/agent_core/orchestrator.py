"""Simple deterministic router (baseline). Actual LLM tool-calling is in llm_agent.py."""
from .data_provider import MockProvider, ProcurementProvider
from .negotiation import recommend_negotiation
from .fraud import analyze_supplier


def execute_agent(task: str, reference_id: str, provider: ProcurementProvider | None = None) -> dict:
    provider = provider or MockProvider()
    if task == 'negotiation':
        return recommend_negotiation(provider, reference_id)
    if task == 'fraud':
        return analyze_supplier(provider, reference_id)
    return {'status': 'invalid_task', 'error': 'Use negotiation or fraud as the task.'}
