from fastapi import APIRouter, HTTPException
from backend.agents.negotiation_agent import propose_for_po
router = APIRouter(prefix="/demo/negotiations", tags=["demo-negotiations"])

@router.get("/{po_number}")
def show_negotiation(po_number: str):
    try:
        return propose_for_po(po_number)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
