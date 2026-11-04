"""Demo-only read endpoints. Do not put this API on the public internet."""
from fastapi import FastAPI
from backend.api.routes import negotiations, fraud_alerts, approvals

app = FastAPI(title="ProcureGuard AI — Local Demo", version="0.1.0")
app.include_router(negotiations.router)
app.include_router(fraud_alerts.router)
app.include_router(approvals.router)

@app.get("/health")
def health():
    return {"ok": True, "mode": "synthetic-demo", "writes_enabled": False}
