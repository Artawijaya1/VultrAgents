from fastapi import APIRouter
from backend.mcp_server.tools.approvals import get_approval_status
router = APIRouter(prefix="/demo/approvals", tags=["demo-approvals"])

@router.get("/{approval_id}")
def get_status(approval_id: str):
    return get_approval_status(approval_id)
