"""Negotiation reasoning entry point; currently deterministic, LLM integration is TODO."""
from backend.services.negotiation_engine import plan_negotiation
from backend.database.repositories.procurement_repository import get_po

def propose_for_po(po_number: str) -> dict:
    return plan_negotiation(get_po(po_number))
