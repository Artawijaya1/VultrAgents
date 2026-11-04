"""Official MCP Python SDK v2 server. Run from Agents/ directory."""
from mcp.server import MCPServer
from agent_core.data_provider import MockProvider
from agent_core.negotiation import recommend_negotiation
from agent_core.fraud import analyze_supplier

mcp = MCPServer('ProcureGuard Agents MCP')
provider = MockProvider()  # Replace with team's adapter after agreeing schema

@mcp.tool()
def get_purchase_order(po_id: str) -> dict:
    """Get a purchase order from the demo procurement data (read only)."""
    return provider.get_po(po_id) or {'error': 'PO tidak ditemukan'}

@mcp.tool()
def recommend_price_negotiation(po_id: str) -> dict:
    """Recommend negotiation options based on PO prices and budget; no sending."""
    return recommend_negotiation(provider, po_id)

@mcp.tool()
def scan_supplier_anomalies(supplier_id: str) -> dict:
    """Flag potentially unusual invoice/bank activity for human review."""
    return analyze_supplier(provider, supplier_id)


from agent_core.po_fraud import analyze_purchase_order

@mcp.tool()
def scan_purchase_order_anomalies(po_id: str) -> dict:
    """Check invoice and bank-change anomalies related to a specific PO ID (read-only)."""
    return analyze_purchase_order(provider, po_id)

if __name__ == '__main__':
    mcp.run()  # stdio: no server port, intended for local MCP clients
