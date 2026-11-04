from backend.database.repositories.procurement_repository import get_approvals

def get_approval_status(approval_id: str) -> dict:
    return next((a for a in get_approvals() if a["id"] == approval_id), {"error": "Approval not found"})
