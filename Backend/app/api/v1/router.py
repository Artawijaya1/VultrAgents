from fastapi import APIRouter
from fastapi import Depends

from app.api.deps import require_internal_api_key
from app.api.v1.endpoints import approvals, agents, auth, contracts, database_records, internal, items, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(agents.router)
api_router.include_router(approvals.router)
api_router.include_router(database_records.router)
api_router.include_router(contracts.router)
api_router.include_router(
    internal.router,
    prefix="/internal",
    tags=["internal-agent"],
    dependencies=[Depends(require_internal_api_key)],
)
