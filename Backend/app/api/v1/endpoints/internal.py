from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.procurement import (
    ApprovalRequest,
    AuditLog,
    ChangeRequest,
    Communication,
    FraudAlert,
    FraudRule,
    FraudScan,
    Invoice,
    Negotiation,
    NegotiationDraft,
    ProcurementPolicy,
    PurchaseOrder,
    PurchaseOrderFollowUp,
    PurchaseOrderVersion,
    Supplier,
    VendorPerformance,
)
router = APIRouter()


class ChangeRejection(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)

    model_config = ConfigDict(extra="forbid")


class FollowUpRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    due_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class CommunicationClassification(BaseModel):
    classification: Literal["confirmed", "change_requested", "other"]
    confidence: float | None = Field(default=None, ge=0, le=1)
    rationale: str | None = Field(default=None, max_length=2000)

    model_config = ConfigDict(extra="forbid")


class NegotiationDraftUpdate(BaseModel):
    content: dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class FraudAlertCreate(BaseModel):
    alert_id: str | None = Field(default=None, min_length=1, max_length=100)
    scan_id: str | None = Field(default=None, min_length=1, max_length=100)
    po_id: str | None = Field(default=None, min_length=1, max_length=100)
    supplier_id: str | None = Field(default=None, min_length=1, max_length=100)
    severity: Literal["low", "medium", "high", "critical"]
    title: str = Field(min_length=1, max_length=200)
    explanation: str = Field(default="", max_length=8000)
    evidence: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


def _approval_response(approval: ApprovalRequest) -> dict[str, Any]:
    return {
        "id": approval.id,
        "action_type": approval.action_type,
        "reference_type": approval.reference_type,
        "reference_id": approval.reference_id,
        "status": approval.status,
        "payload": approval.payload,
        "created_at": approval.created_at,
    }


def _create_internal_approval(
    db: Session,
    *,
    action_type: str,
    reference_type: str,
    reference_id: str,
    payload: dict[str, Any],
) -> ApprovalRequest:
    approval = ApprovalRequest(
        action_type=action_type,
        reference_type=reference_type,
        reference_id=reference_id,
        status="pending",
        payload=payload,
    )
    db.add(approval)
    db.flush()
    db.add(
        AuditLog(
            action="approval.created_by_agent",
            entity_type="approval",
            entity_id=str(approval.id),
            details={"action_type": action_type, "reference_type": reference_type},
        )
    )
    db.commit()
    db.refresh(approval)
    return approval


@router.get("/procurement/pos/{po_id}", operation_id="internal_procurement_purchase_order")
def read_procurement_purchase_order(
    po_id: str,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found.")
    return {
        "po_id": po.po_id,
        "supplier_id": po.supplier_id,
        "product_id": po.product_id,
        "quantity": po.quantity,
        "offered_unit_price": po.offered_unit_price,
        "budget_ceiling_unit": po.budget_ceiling_unit,
        "previous_unit_price": po.previous_unit_price,
        "currency": po.currency,
        "required_delivery_date": po.required_delivery_date.isoformat(),
    }


@router.get(
    "/procurement/suppliers/{supplier_id}",
    operation_id="internal_procurement_supplier",
)
def read_procurement_supplier(
    supplier_id: str,
    db: Session = Depends(get_db),
) -> dict[str, object | None]:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return {
        "supplier_id": supplier.supplier_id,
        "name": supplier.name,
        "bank_last_changed_at": (
            supplier.bank_last_changed_at.date().isoformat()
            if supplier.bank_last_changed_at is not None
            else None
        ),
    }


@router.get(
    "/procurement/suppliers/{supplier_id}/invoices",
    operation_id="internal_procurement_supplier_invoices",
)
def list_procurement_supplier_invoices(
    supplier_id: str,
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, object]]]:
    if db.get(Supplier, supplier_id) is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    invoices = db.scalars(
        select(Invoice)
        .where(Invoice.supplier_id == supplier_id)
        .order_by(Invoice.invoice_date.desc(), Invoice.record_id)
    )
    return {
        "items": [
            {
                "record_id": invoice.record_id,
                "invoice_number": invoice.invoice_number,
                "supplier_id": invoice.supplier_id,
                "po_id": invoice.po_id,
                "product_id": invoice.product_id,
                "amount": invoice.amount,
                "unit_price": invoice.unit_price,
                "invoice_date": invoice.invoice_date.isoformat(),
            }
            for invoice in invoices
        ]
    }


@router.get("/purchase-orders/{po_id}/versions", operation_id="internal_purchase_order_versions")
def list_purchase_order_versions(
    po_id: str,
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    if db.get(PurchaseOrder, po_id) is None:
        raise HTTPException(status_code=404, detail="Purchase order not found.")
    versions = db.scalars(
        select(PurchaseOrderVersion)
        .where(PurchaseOrderVersion.po_id == po_id)
        .order_by(PurchaseOrderVersion.version_number)
    )
    return {
        "items": [
            {
                "version_number": version.version_number,
                "snapshot": version.snapshot,
                "created_at": version.created_at,
            }
            for version in versions
        ]
    }


@router.get("/vendors/{supplier_id}/performance", operation_id="internal_vendor_performance")
def read_vendor_performance(
    supplier_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if db.get(Supplier, supplier_id) is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    performance = db.get(VendorPerformance, supplier_id)
    if performance is None:
        return {
            "supplier_id": supplier_id,
            "on_time_rate": None,
            "defect_rate": None,
            "rating": None,
            "metrics": {},
        }
    return {
        "supplier_id": performance.supplier_id,
        "on_time_rate": performance.on_time_rate,
        "defect_rate": performance.defect_rate,
        "rating": performance.rating,
        "metrics": performance.metrics,
    }


@router.get("/policies", operation_id="internal_policies")
def list_procurement_policies(
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    policies = db.scalars(
        select(ProcurementPolicy)
        .where(ProcurementPolicy.enabled.is_(True))
        .order_by(ProcurementPolicy.policy_key)
    )
    return {
        "items": [
            {
                "policy_key": policy.policy_key,
                "description": policy.description,
                "value": policy.value,
            }
            for policy in policies
        ]
    }


@router.get("/invoices", operation_id="internal_invoices")
def list_invoices(
    supplier_id: str | None = None,
    po_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    statement = select(Invoice)
    if supplier_id is not None:
        statement = statement.where(Invoice.supplier_id == supplier_id)
    if po_id is not None:
        statement = statement.where(Invoice.po_id == po_id)
    invoices = db.scalars(
        statement.order_by(Invoice.invoice_date.desc(), Invoice.record_id).limit(limit)
    )
    return {"items": [_invoice_payload(invoice) for invoice in invoices]}


def _invoice_payload(invoice: Invoice) -> dict[str, Any]:
    return {
        "record_id": invoice.record_id,
        "invoice_number": invoice.invoice_number,
        "supplier_id": invoice.supplier_id,
        "po_id": invoice.po_id,
        "product_id": invoice.product_id,
        "amount": invoice.amount,
        "unit_price": invoice.unit_price,
        "invoice_date": invoice.invoice_date.isoformat(),
    }


@router.get("/invoices/{invoice_id}", operation_id="internal_invoice")
def read_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return _invoice_payload(invoice)


@router.get("/change-requests/{request_id}", operation_id="internal_change_request")
def read_change_request(
    request_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    change_request = db.get(ChangeRequest, request_id)
    if change_request is None:
        raise HTTPException(status_code=404, detail="Change request not found.")
    return {
        "change_request_id": change_request.change_request_id,
        "po_id": change_request.po_id,
        "status": change_request.status,
        "requested_changes": change_request.requested_changes,
        "outcome_reason": change_request.outcome_reason,
        "created_at": change_request.created_at,
    }


@router.post("/change-requests/{request_id}/reject", operation_id="internal_reject_change_request")
def request_change_rejection(
    request_id: str,
    payload: ChangeRejection,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    change_request = db.get(ChangeRequest, request_id)
    if change_request is None:
        raise HTTPException(status_code=404, detail="Change request not found.")
    if change_request.status != "pending":
        raise HTTPException(status_code=409, detail="Change request is not pending.")
    approval = _create_internal_approval(
        db,
        action_type="reject_change_request",
        reference_type="change_request",
        reference_id=request_id,
        payload=payload.model_dump(mode="json"),
    )
    return _approval_response(approval)


@router.post(
    "/purchase-orders/{po_id}/follow-ups",
    operation_id="internal_create_purchase_order_follow_up",
)
def request_purchase_order_follow_up(
    po_id: str,
    payload: FollowUpRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if db.get(PurchaseOrder, po_id) is None:
        raise HTTPException(status_code=404, detail="Purchase order not found.")
    approval = _create_internal_approval(
        db,
        action_type="purchase_order_follow_up",
        reference_type="po",
        reference_id=po_id,
        payload=payload.model_dump(mode="json"),
    )
    follow_up = PurchaseOrderFollowUp(
        po_id=po_id,
        message=payload.message,
        due_at=payload.due_at,
        status="pending_approval",
        approval_id=approval.id,
    )
    db.add(follow_up)
    db.commit()
    return _approval_response(approval)


@router.get("/communications/{communication_id}", operation_id="internal_communication")
def read_communication(
    communication_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    communication = db.get(Communication, communication_id)
    if communication is None:
        raise HTTPException(status_code=404, detail="Communication not found.")
    return {
        "communication_id": communication.communication_id,
        "po_id": communication.po_id,
        "direction": communication.direction,
        "subject": communication.subject,
        "body": communication.body,
        "classification": communication.classification,
        "classification_confidence": communication.classification_confidence,
        "created_at": communication.created_at,
    }


@router.post(
    "/communications/{communication_id}/classification",
    operation_id="internal_classify_communication",
)
def request_communication_classification(
    communication_id: str,
    payload: CommunicationClassification,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if db.get(Communication, communication_id) is None:
        raise HTTPException(status_code=404, detail="Communication not found.")
    approval = _create_internal_approval(
        db,
        action_type="classify_communication",
        reference_type="communication",
        reference_id=communication_id,
        payload=payload.model_dump(mode="json"),
    )
    return _approval_response(approval)


@router.get("/negotiations/{negotiation_id}", operation_id="internal_negotiation")
def read_negotiation(
    negotiation_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    negotiation = db.get(Negotiation, negotiation_id)
    if negotiation is None:
        raise HTTPException(status_code=404, detail="Negotiation not found.")
    drafts = db.scalars(
        select(NegotiationDraft)
        .where(NegotiationDraft.negotiation_id == negotiation_id)
        .order_by(NegotiationDraft.updated_at.desc())
    )
    return {
        "negotiation_id": negotiation.negotiation_id,
        "po_id": negotiation.po_id,
        "status": negotiation.status,
        "selected_option": negotiation.selected_option,
        "context": negotiation.context,
        "drafts": [
            {
                "draft_id": draft.draft_id,
                "content": draft.content,
                "status": draft.status,
                "updated_at": draft.updated_at,
            }
            for draft in drafts
        ],
    }


@router.patch(
    "/negotiations/{negotiation_id}/drafts/{draft_id}",
    operation_id="internal_update_negotiation_draft",
)
def request_negotiation_draft_update(
    negotiation_id: str,
    draft_id: str,
    payload: NegotiationDraftUpdate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    draft = db.get(NegotiationDraft, draft_id)
    if draft is None or draft.negotiation_id != negotiation_id:
        raise HTTPException(status_code=404, detail="Negotiation draft not found.")
    approval = _create_internal_approval(
        db,
        action_type="update_negotiation_draft",
        reference_type="negotiation",
        reference_id=negotiation_id,
        payload={"draft_id": draft_id, "content": payload.content},
    )
    return _approval_response(approval)


@router.get("/fraud/rules", operation_id="internal_fraud_rules")
def list_fraud_rules(
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    rules = db.scalars(
        select(FraudRule).where(FraudRule.enabled.is_(True)).order_by(FraudRule.rule_id)
    )
    return {
        "items": [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "config": rule.config,
            }
            for rule in rules
        ]
    }


@router.post("/fraud/alerts", status_code=201, operation_id="internal_create_fraud_alert")
def create_fraud_alert(
    payload: FraudAlertCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if payload.po_id is None and payload.supplier_id is None:
        raise HTTPException(
            status_code=422,
            detail="A fraud alert must reference a purchase order or supplier.",
        )
    po = db.get(PurchaseOrder, payload.po_id) if payload.po_id is not None else None
    if payload.po_id is not None and po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found.")
    if payload.supplier_id is not None and db.get(Supplier, payload.supplier_id) is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    if po is not None and payload.supplier_id is not None and po.supplier_id != payload.supplier_id:
        raise HTTPException(
            status_code=422,
            detail="Supplier does not match the purchase order.",
        )
    if payload.scan_id is not None and db.get(FraudScan, payload.scan_id) is None:
        raise HTTPException(status_code=404, detail="Fraud scan not found.")

    alert = FraudAlert(
        alert_id=payload.alert_id or str(uuid4()),
        scan_id=payload.scan_id,
        po_id=payload.po_id,
        supplier_id=payload.supplier_id or (po.supplier_id if po is not None else None),
        severity=payload.severity,
        title=payload.title,
        explanation=payload.explanation,
        status="review_required",
        evidence=payload.evidence,
    )
    db.add(alert)
    db.add(
        AuditLog(
            action="fraud.alert_created",
            entity_type="fraud_alert",
            entity_id=alert.alert_id,
            details={"severity": alert.severity, "status": alert.status},
        )
    )
    db.commit()
    return {
        "alert_id": alert.alert_id,
        "status": alert.status,
        "requires_human_review": True,
    }


@router.get("/fraud/scans/{scan_id}", operation_id="internal_fraud_scan")
def read_fraud_scan(
    scan_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    scan = db.get(FraudScan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Fraud scan not found.")
    return {
        "scan_id": scan.scan_id,
        "po_id": scan.po_id,
        "supplier_id": scan.supplier_id,
        "status": scan.status,
        "results": scan.results,
        "created_at": scan.created_at,
        "completed_at": scan.completed_at,
    }
