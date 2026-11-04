"""Smoke-check pure Python engines without MCP server running."""
from backend.agents.negotiation_agent import propose_for_po
from backend.agents.fraud_agent import analyze_demo_invoices

def main():
    assert propose_for_po("PO-001")["approval_required"] is True
    assert analyze_demo_invoices()["summary"]["human_review_required"] is True
    print("Demo logic smoke test: PASS")

if __name__ == "__main__":
    main()
