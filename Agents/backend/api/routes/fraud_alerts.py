from fastapi import APIRouter
from backend.agents.fraud_agent import analyze_demo_invoices
router = APIRouter(prefix="/demo/fraud", tags=["demo-fraud"])

@router.get("/scan")
def scan_demo():
    return analyze_demo_invoices()
