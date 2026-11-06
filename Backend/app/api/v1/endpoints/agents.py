from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.procurement import (
    AgentRun,
    AgentSession,
    ApprovalRequest,
    AuditLog,
    PurchaseOrder,
    Supplier,
)
from app.models.user import User
from app.schemas.agent import AgentChatRequest, AgentRunRequest
from app.services.agent_client import (
    AgentServiceError,
    AgentServiceNotConfigured,
    AgentServiceTimeout,
    call_agent,
)

router = APIRouter(prefix="/agents", tags=["agents"])


def _require_reference_access(
    db: Session,
    user: User,
    reference_type: str,
    reference_id: str,
) -> PurchaseOrder | None:
    if reference_type == "po":
        po = db.get(PurchaseOrder, reference_id)
        if po is None:
            raise HTTPException(status_code=404, detail="Purchase order not found.")
        if po.owner_user_id != user.id:
            raise HTTPException(status_code=403, detail="Purchase order access is denied.")
        return po

    supplier = db.get(Supplier, reference_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    owned_po = db.scalar(
        select(PurchaseOrder).where(
            PurchaseOrder.supplier_id == reference_id,
            PurchaseOrder.owner_user_id == user.id,
        )
    )
    if owned_po is None:
        raise HTTPException(status_code=403, detail="Supplier access is denied.")
    return None


def _store_result(
    db: Session,
    *,
    user: User,
    task: str,
    reference_type: str,
    reference_id: str,
    request_payload: dict[str, Any],
    response_payload: dict[str, Any],
) -> int | None:
    approval_id = None
    if response_payload.get("requires_approval") is True:
        approval = ApprovalRequest(
            action_type="agent_review",
            reference_type=reference_type,
            reference_id=reference_id,
            requested_by_user_id=user.id,
            status="pending",
            payload={"request": request_payload, "response": response_payload},
        )
        db.add(approval)
        db.flush()
        approval_id = approval.id

    db.add(
        AgentRun(
            request_id=str(response_payload.get("request_id") or uuid4()),
            user_id=user.id,
            reference_type=reference_type,
            reference_id=reference_id,
            task=task,
            request_payload=request_payload,
            response_payload=response_payload,
            approval_id=approval_id,
        )
    )
    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="agent.run",
            entity_type=reference_type,
            entity_id=reference_id,
            details={"task": task, "approval_id": approval_id},
        )
    )
    db.commit()
    return approval_id


@router.post("/run")
async def run_agent(
    request: AgentRunRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_reference_access(db, user, request.reference_type, request.reference_id)
    # Release the read connection before the potentially long Agent request.
    db.commit()
    request_id = str(uuid4())
    payload = request.model_dump()
    payload["request_id"] = request_id

    try:
        response = await call_agent("run", payload, timeout=32.0)
    except AgentServiceTimeout as exc:
        raise HTTPException(status_code=504, detail="Agent request timed out.") from exc
    except AgentServiceNotConfigured as exc:
        raise HTTPException(status_code=503, detail="Agent service is not configured.") from exc
    except AgentServiceError as exc:
        raise HTTPException(status_code=502, detail="Agent service is unavailable.") from exc

    if (
        response.get("request_id") != request_id
        or response.get("task") != request.task
        or response.get("reference_id") != request.reference_id
    ):
        raise HTTPException(status_code=502, detail="Agent response does not match the request.")

    approval_id = _store_result(
        db,
        user=user,
        task=request.task,
        reference_type=request.reference_type,
        reference_id=request.reference_id,
        request_payload=payload,
        response_payload=response,
    )
    if approval_id is not None:
        response["approval_id"] = approval_id
    return response


@router.post("/chat")
async def chat_agent(
    request: AgentChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    po = db.get(PurchaseOrder, request.reference_id)
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found.")
    if po.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Purchase order access is denied.")

    session_id = request.session_id or str(uuid4())
    agent_session = db.get(AgentSession, session_id)
    if agent_session is not None:
        if (
            agent_session.user_id != user.id
            or agent_session.po_id != po.po_id
            or agent_session.task != request.task
        ):
            raise HTTPException(status_code=403, detail="Agent session access is denied.")

    # Keep database connections available while waiting on the Agent service.
    db.commit()
    payload = request.model_dump()
    payload["session_id"] = session_id
    try:
        response = await call_agent("chat", payload, timeout=160.0)
    except AgentServiceTimeout as exc:
        raise HTTPException(status_code=504, detail="Agent conversation timed out.") from exc
    except AgentServiceNotConfigured as exc:
        raise HTTPException(status_code=503, detail="Agent service is not configured.") from exc
    except AgentServiceError as exc:
        raise HTTPException(status_code=502, detail="Agent service is unavailable.") from exc

    if (
        response.get("session_id") != session_id
        or response.get("task") != request.task
        or response.get("reference_id") != request.reference_id
    ):
        raise HTTPException(status_code=502, detail="Agent response does not match the request.")

    if agent_session is None:
        agent_session = AgentSession(
            session_id=session_id,
            user_id=user.id,
            po_id=po.po_id,
            task=request.task,
        )
        db.add(agent_session)
    else:
        agent_session.updated_at = datetime.now(timezone.utc)

    approval_id = _store_result(
        db,
        user=user,
        task=request.task,
        reference_type="po",
        reference_id=po.po_id,
        request_payload=payload,
        response_payload=response,
    )
    if approval_id is not None:
        response["approval_id"] = approval_id
    response["session_id"] = session_id
    return response
