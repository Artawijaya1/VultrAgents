from backend.database.repositories.procurement_repository import get_po, get_suppliers

def get_purchase_order(po_number: str) -> dict:
    return get_po(po_number) or {"error": "PO not found"}

def list_suppliers() -> list[dict]:
    return get_suppliers()
