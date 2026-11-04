from backend.agents.fraud_agent import analyze_demo_invoices

def scan_procurement_anomalies() -> dict:
    return analyze_demo_invoices()
