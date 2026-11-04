"""MCP Python SDK v2; synthetic data and read-only tools.
Use 'python -m backend.mcp_server.server' or 'mcp dev backend/mcp_server/server.py'.
"""
from mcp.server import MCPServer
from backend.mcp_server.tools import procurement, negotiation, fraud, approvals
from backend.mcp_server.resources.policies import procurement_policy
from backend.mcp_server.prompts.negotiation import negotiation_prompt

mcp = MCPServer("ProcureGuard AI (Demo)")

@mcp.tool()
def get_purchase_order(po_number: str) -> dict:
    """Read synthetic purchase-order data by number. Does not modify a PO."""
    return procurement.get_purchase_order(po_number)

@mcp.tool()
def list_suppliers() -> list[dict]:
    """List synthetic suppliers. Financial credentials are never returned."""
    return procurement.list_suppliers()

@mcp.tool()
def draft_negotiation(po_number: str) -> dict:
    """Propose a negotiation strategy and supplier email draft; never send it."""
    return negotiation.draft_negotiation(po_number)

@mcp.tool()
def scan_procurement_anomalies() -> dict:
    """Identify explainable invoice anomaly indicators; not findings of fraud."""
    return fraud.scan_procurement_anomalies()

@mcp.tool()
def get_approval_status(approval_id: str) -> dict:
    """Read synthetic approval status, without granting or changing approvals."""
    return approvals.get_approval_status(approval_id)

@mcp.resource("procurement://policies/default")
def default_policy() -> str:
    """Non-sensitive demo procurement policy."""
    return procurement_policy()

@mcp.prompt()
def prepare_negotiation(po_number: str) -> str:
    """Request a policy-aware negotiation plan for a purchase order."""
    return negotiation_prompt(po_number)

if __name__ == "__main__":
    mcp.run()
