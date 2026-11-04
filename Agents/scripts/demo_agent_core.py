"""Run: python -m scripts.demo_agent_core from Agents directory."""
import json
from agent_core.orchestrator import execute_agent

for task, reference in [('negotiation','PO-001'),('fraud','SUP-001')]:
    print(f'\n=== {task.upper()} ===')
    print(json.dumps(execute_agent(task, reference), indent=2, ensure_ascii=False))
