from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_identity, get_current_user, get_db, require_admin
from app.models.procurement import ApprovalRequest, AuditLog, PurchaseOrder, Supplier
from app.models.user import User
from app.schemas.agent import ApprovalCreate, ApprovalDecision, ApprovalRead
from app.schemas.token import SupabaseIdentity

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _check_reference_access(
    db: Session,
    user: User,
    reference_type: str,
    reference_id: str,
) -> None:
    if reference_type == "po":
        reference = db.get(PurchaseOrder, reference_id)
        if reference is None:
            raise HTTPException(status_code=404, detail="Purchase order not found.")
        if reference.owner_user_id != user.id:
            raise HTTPException(status_code=403, detail="Purchase order access is denied.")
        return

    reference = db.get(Supplier, reference_id)
    if reference is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    owned_po = db.scalar(
        select(PurchaseOrder.po_id).where(
            PurchaseOrder.supplier_id == reference_id,
            PurchaseOrder.owner_user_id == user.id,
        )
    )
    if owned_po is None:
        raise HTTPException(status_code=403, detail="Supplier access is denied.")


def _get_approval_for_user(
    db: Session,
    approval_id: int,
    user: User,
    identity: SupabaseIdentity,
) -> ApprovalRequest:
    approval = db.get(ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    if not identity.is_admin and approval.requested_by_user_id != user.id:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    return approval


@router.get("", response_model=list[ApprovalRead])
def list_approvals(
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    identity: SupabaseIdentity = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> list[ApprovalRequest]:
    statement = select(ApprovalRequest)
    if not identity.is_admin:
        statement = statement.where(ApprovalRequest.requested_by_user_id == user.id)
    statement = statement.order_by(ApprovalRequest.created_at.desc()).limit(limit)
    return list(db.scalars(statement))


@router.post("", response_model=ApprovalRead, status_code=201)
def create_approval(
    request: ApprovalCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApprovalRequest:
    _check_reference_access(db, user, request.reference_type, request.reference_id)
    approval = ApprovalRequest(
        action_type=request.action_type,
        reference_type=request.reference_type,
        reference_id=request.reference_id,
        requested_by_user_id=user.id,
        status="pending",
        payload=request.payload,
    )
    db.add(approval)
    db.flush()
    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="approval.created",
            entity_type="approval",
            entity_id=str(approval.id),
            details={"action_type": request.action_type},
        )
    )
    db.commit()
    db.refresh(approval)
    return approval


@router.get("/{approval_id}", response_model=ApprovalRead)
def read_approval(
    approval_id: int,
    user: User = Depends(get_current_user),
    identity: SupabaseIdentity = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> ApprovalRequest:
    return _get_approval_for_user(db, approval_id, user, identity)


def _decide(
    approval_id: int,
    status_value: str,
    request: ApprovalDecision,
    user: User,
    db: Session,
) -> ApprovalRequest:
    approval = db.scalar(
        select(ApprovalRequest)
        .where(ApprovalRequest.id == approval_id)
        .with_for_update()
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail="Approval request is already decided.")

    approval.status = status_value
    approval.decision_by_user_id = user.id
    approval.decision_notes = request.notes
    approval.decided_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            actor_user_id=user.id,
            action=f"approval.{status_value}",
            entity_type="approval",
            entity_id=str(approval.id),
            details={"reference_type": approval.reference_type, "reference_id": approval.reference_id},
        )
    )
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalRead)
def approve_approval(
    approval_id: int,
    request: ApprovalDecision,
    _: SupabaseIdentity = Depends(require_admin),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApprovalRequest:
    return _decide(approval_id, "approved", request, user, db)


@router.post("/{approval_id}/reject", response_model=ApprovalRead)
def reject_approval(
    approval_id: int,
    request: ApprovalDecision,
    _: SupabaseIdentity = Depends(require_admin),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApprovalRequest:
    return _decide(approval_id, "rejected", request, user, db)
