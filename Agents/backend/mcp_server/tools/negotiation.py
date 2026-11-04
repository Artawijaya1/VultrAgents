from backend.agents.negotiation_agent import propose_for_po

def draft_negotiation(po_number: str) -> dict:
    return propose_for_po(po_number)
