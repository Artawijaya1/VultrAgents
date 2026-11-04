"""Explainable flags; requires auditor/finance review for any action."""
from backend.database.repositories.procurement_repository import get_invoices, get_price_history
from backend.services.fraud_rules import scan_invoices
from backend.services.risk_scoring import summarize_findings

def analyze_demo_invoices() -> dict:
    findings = scan_invoices(get_invoices(), get_price_history())
    return {"findings": findings, "summary": summarize_findings(findings)}
