"""Dedicated, read-only MCP v2 tool host for LangGraph workflow."""
from functools import lru_cache
from mcp.server import MCPServer
from .provider_http import build_provider
from .negotiation import recommend_negotiation
from .fraud import analyze_supplier

mcp = MCPServer('ProcureGuard-LangGraph-MCP')


@lru_cache(maxsize=1)
def provider():
    return build_provider()


@mcp.tool()
def get_purchase_order(po_id: str) -> dict:
    """Read one purchase order; immutable, authorized provider data only."""
    return provider().get_po(po_id) or {'error': 'Purchase order not found.', 'status': 'not_found'}


@mcp.tool()
def get_supplier_profile(supplier_id: str) -> dict:
    """Read supplier profile for context and risk precheck."""
    return provider().get_supplier(supplier_id) or {'error': 'Supplier not found.', 'status': 'not_found'}


@mcp.tool()
def recommend_price_negotiation(po_id: str) -> dict:
    """Return negotiation options; only a draft; never sends messages."""
    return recommend_negotiation(provider(), po_id)


@mcp.tool()
def scan_supplier_anomalies(supplier_id: str) -> dict:
    """Return transparent anomaly flags; never labels supplier fraudulent."""
    return analyze_supplier(provider(), supplier_id)


# PROCUREGUARD_STAGE6_PO_SCOPE
from .po_fraud import analyze_purchase_order

@mcp.tool()
def scan_purchase_order_anomalies(po_id: str) -> dict:
    """Read-only anomaly check bounded to a single Purchase Order."""
    return analyze_purchase_order(provider(), po_id)


if __name__ == '__main__':
    mcp.run()
