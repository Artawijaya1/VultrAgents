"""Constrained routing demo; later replace with an LLM tool-using orchestrator.
Never route to money movement or external mail actions automatically.
"""
from backend.agents.negotiation_agent import propose_for_po
from backend.agents.fraud_agent import analyze_demo_invoices

def run_demo(intent: str, po_number: str = "PO-001") -> dict:
    if intent == "negotiate":
        return {"agent": "negotiation", "result": propose_for_po(po_number)}
    if intent == "fraud_check":
        return {"agent": "fraud", "result": analyze_demo_invoices()}
    raise ValueError("Supported intents: negotiate, fraud_check")
