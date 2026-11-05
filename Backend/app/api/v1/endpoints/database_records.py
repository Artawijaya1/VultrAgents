from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.procurement import (
    AuditLog,
    FraudAlert,
    FraudScan,
    Invoice,
    Negotiation,
    PurchaseOrder,
    Supplier,
    VendorPerformance,
)
from app.models.user import User

router = APIRouter()


def _owned_orders(db: Session, user: User):
    return select(PurchaseOrder).where(PurchaseOrder.owner_user_id == user.id)


def _order_payload(order: PurchaseOrder, supplier: Supplier | None = None) -> dict[str, Any]:
    return {
        "po_id": order.po_id,
        "supplier_id": order.supplier_id,
        "supplier_name": supplier.name if supplier else None,
        "product_id": order.product_id,
        "product_name": order.product_id,
        "quantity": float(order.quantity),
        "offered_unit_price": order.offered_unit_price,
        "budget_ceiling_unit": order.budget_ceiling_unit,
        "previous_unit_price": order.previous_unit_price,
        "currency": order.currency,
        "required_delivery_date": order.required_delivery_date.isoformat(),
        "status": order.status,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }


@router.get("/purchase-orders")
def list_purchase_orders(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    rows = db.execute(
        select(PurchaseOrder, Supplier)
        .join(Supplier, Supplier.supplier_id == PurchaseOrder.supplier_id)
        .where(PurchaseOrder.owner_user_id == user.id)
        .order_by(PurchaseOrder.created_at.desc())
    ).all()
    return [_order_payload(order, supplier) for order, supplier in rows]


@router.get("/purchase-orders/{id}")
def read_purchase_order(
    id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict[str, Any] | None:
    row = db.execute(
        select(PurchaseOrder, Supplier)
        .join(Supplier, Supplier.supplier_id == PurchaseOrder.supplier_id)
        .where(PurchaseOrder.po_id == id, PurchaseOrder.owner_user_id == user.id)
    ).first()
    return _order_payload(*row) if row else None


@router.get("/vendors")
def list_vendors(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    owned_ids = _owned_orders(db, user).with_only_columns(PurchaseOrder.supplier_id).distinct()
    vendors = db.scalars(select(Supplier).where(Supplier.supplier_id.in_(owned_ids)).order_by(Supplier.name)).all()
    counts = dict(db.execute(
        select(PurchaseOrder.supplier_id, func.count(PurchaseOrder.po_id))
        .where(PurchaseOrder.owner_user_id == user.id).group_by(PurchaseOrder.supplier_id)
    ).all())
    perf = {row.supplier_id: row for row in db.scalars(
        select(VendorPerformance).where(VendorPerformance.supplier_id.in_(owned_ids))
    ).all()}
    return [{
        "supplier_id": item.supplier_id,
        "name": item.name,
        "bank_last_changed_at": item.bank_last_changed_at.isoformat() if item.bank_last_changed_at else None,
        "purchase_order_count": counts.get(item.supplier_id, 0),
        "rating": perf[item.supplier_id].rating if item.supplier_id in perf else None,
        "on_time_rate": perf[item.supplier_id].on_time_rate if item.supplier_id in perf else None,
        "defect_rate": perf[item.supplier_id].defect_rate if item.supplier_id in perf else None,
        "metrics": perf[item.supplier_id].metrics if item.supplier_id in perf else {},
    } for item in vendors]


@router.get("/invoices")
def list_invoices(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    rows = db.execute(
        select(Invoice, PurchaseOrder, Supplier)
        .join(PurchaseOrder, Invoice.po_id == PurchaseOrder.po_id)
        .join(Supplier, Supplier.supplier_id == Invoice.supplier_id)
        .where(PurchaseOrder.owner_user_id == user.id)
        .order_by(Invoice.invoice_date.desc())
    ).all()
    return [{
        "record_id": invoice.record_id,
        "invoice_number": invoice.invoice_number,
        "supplier_id": invoice.supplier_id,
        "supplier_name": supplier.name,
        "po_id": invoice.po_id,
        "product_id": invoice.product_id,
        "amount": invoice.amount,
        "unit_price": invoice.unit_price,
        "invoice_date": invoice.invoice_date.isoformat(),
        "status": None,
        "currency": order.currency,
    } for invoice, order, supplier in rows]


@router.get("/contracts")
def list_contracts() -> list[dict[str, Any]]:
    # There is no contract table in this database schema. Return no records instead of fabricating them.
    return []


@router.get("/negotiations")
def list_negotiations(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    rows = db.execute(
        select(Negotiation, PurchaseOrder, Supplier)
        .join(PurchaseOrder, PurchaseOrder.po_id == Negotiation.po_id)
        .join(Supplier, Supplier.supplier_id == PurchaseOrder.supplier_id)
        .where(PurchaseOrder.owner_user_id == user.id)
        .order_by(Negotiation.created_at.desc())
    ).all()
    return [{
        "negotiation_id": negotiation.negotiation_id,
        "po_id": order.po_id,
        "purchase_order_id": order.po_id,
        "supplier_id": supplier.supplier_id,
        "supplier_name": supplier.name,
        "status": negotiation.status,
        "selected_option": negotiation.selected_option,
        "context": negotiation.context,
        "created_at": negotiation.created_at.isoformat(),
    } for negotiation, order, supplier in rows]


@router.post("/negotiations", status_code=201)
def create_negotiation(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    po_id = payload.get("po_id") or payload.get("purchase_order_id")
    order = db.scalar(select(PurchaseOrder).where(PurchaseOrder.po_id == po_id, PurchaseOrder.owner_user_id == user.id))
    if order is None:
        raise HTTPException(status_code=404, detail="Purchase order not found for this account.")
    negotiation = Negotiation(
        negotiation_id=f"NEG-{uuid4().hex}",
        po_id=order.po_id,
        status="draft",
        context=payload.get("context") if isinstance(payload.get("context"), dict) else {},
    )
    db.add(negotiation)
    db.add(AuditLog(
        actor_user_id=user.id,
        action="Negotiation analysis created",
        entity_type="Negotiation",
        entity_id=negotiation.negotiation_id,
        details={"purchase_order_id": order.po_id},
    ))
    db.commit()
    db.refresh(negotiation)
    supplier = db.get(Supplier, order.supplier_id)
    return {
        "negotiation_id": negotiation.negotiation_id,
        "po_id": order.po_id,
        "purchase_order_id": order.po_id,
        "supplier_id": supplier.supplier_id if supplier else None,
        "supplier_name": supplier.name if supplier else None,
        "status": negotiation.status,
        "context": negotiation.context,
        "created_at": negotiation.created_at.isoformat(),
    }


def _alert_payload(alert: FraudAlert, order: PurchaseOrder | None, supplier: Supplier | None) -> dict[str, Any]:
    return {
        "id": alert.alert_id,
        "alert_id": alert.alert_id,
        "scan_id": alert.scan_id,
        "purchaseOrderId": alert.po_id,
        "po_id": alert.po_id,
        "supplierId": alert.supplier_id,
        "supplier": supplier.name if supplier else (alert.supplier_id or "Unknown supplier"),
        "invoiceId": None,
        "amount": (int(order.quantity) * order.offered_unit_price) if order else 0,
        "currency": order.currency if order else "IDR",
        "severity": alert.severity,
        "title": alert.title,
        "explanation": [alert.explanation] if alert.explanation else [],
        "status": alert.status,
        "evidence": alert.evidence or {},
        "riskFactors": [],
        "recommendedActions": [],
        "auditTrail": [],
        "created_at": alert.created_at.isoformat(),
    }


@router.get("/fraud/alerts")
def list_fraud_alerts(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    rows = db.execute(
        select(FraudAlert, PurchaseOrder, Supplier)
        .join(PurchaseOrder, PurchaseOrder.po_id == FraudAlert.po_id)
        .join(Supplier, Supplier.supplier_id == PurchaseOrder.supplier_id)
        .where(PurchaseOrder.owner_user_id == user.id)
        .order_by(FraudAlert.created_at.desc())
    ).all()
    return [_alert_payload(alert, order, supplier) for alert, order, supplier in rows]


@router.get("/fraud/alerts/{id}")
def read_fraud_alert(
    id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict[str, Any] | None:
    row = db.execute(
        select(FraudAlert, PurchaseOrder, Supplier)
        .join(PurchaseOrder, PurchaseOrder.po_id == FraudAlert.po_id)
        .join(Supplier, Supplier.supplier_id == PurchaseOrder.supplier_id)
        .where(FraudAlert.alert_id == id, PurchaseOrder.owner_user_id == user.id)
    ).first()
    return _alert_payload(*row) if row else None


@router.get("/fraud/dashboard")
def fraud_dashboard(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict[str, Any]:
    alerts = list_fraud_alerts(db, user)
    active = [item for item in alerts if item["status"].lower() not in {"resolved", "false positive", "dismissed"}]
    severity = defaultdict(int)
    for item in active:
        severity[item["severity"].lower()] += 1
    scans = db.scalar(
        select(func.count(FraudScan.scan_id)).where(
            FraudScan.po_id.in_(_owned_orders(db, user).with_only_columns(PurchaseOrder.po_id))
        )
    ) or 0
    distribution = [{"type": key.title(), "count": value, "color": color} for (key, value), color in zip(
        sorted(((key, count) for key, count in severity.items()), key=lambda item: item[0]),
        ["#20b9f2", "#f0b648", "#f06a79", "#8a79fa"],
    )]
    return {
        "totalAlerts": len(alerts),
        "transactionsAnalyzed": scans,
        "suspiciousTransactions": len(active),
        "highRiskSuppliers": len({item["supplierId"] for item in active if item["severity"].lower() == "high"}),
        "potentialExposure": sum(item["amount"] for item in active),
        "totalScans": scans,
        "distribution": distribution,
        "trend": [],
    }


@router.patch("/fraud/alerts/{id}")
def update_fraud_alert(
    id: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    row = db.execute(
        select(FraudAlert, PurchaseOrder, Supplier)
        .join(PurchaseOrder, PurchaseOrder.po_id == FraudAlert.po_id)
        .join(Supplier, Supplier.supplier_id == PurchaseOrder.supplier_id)
        .where(FraudAlert.alert_id == id, PurchaseOrder.owner_user_id == user.id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Fraud alert not found.")
    alert, order, supplier = row
    new_status = payload.get("status")
    if not isinstance(new_status, str) or not new_status.strip():
        raise HTTPException(status_code=422, detail="A non-empty status is required.")
    previous_status = alert.status
    alert.status = new_status.strip()
    db.add(AuditLog(
        actor_user_id=user.id,
        action="Fraud alert status updated",
        entity_type="Fraud",
        entity_id=alert.alert_id,
        details={"previous_status": previous_status, "new_status": alert.status, "notes": payload.get("notes")},
    ))
    db.commit()
    db.refresh(alert)
    return _alert_payload(alert, order, supplier)


@router.post("/fraud/alerts/{id}/explain")
def explain_fraud_alert(
    id: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    row = db.execute(
        select(FraudAlert, PurchaseOrder, Supplier)
        .join(PurchaseOrder, PurchaseOrder.po_id == FraudAlert.po_id)
        .join(Supplier, Supplier.supplier_id == PurchaseOrder.supplier_id)
        .where(FraudAlert.alert_id == id, PurchaseOrder.owner_user_id == user.id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Fraud alert not found.")
    alert, order, supplier = row
    db.add(AuditLog(
        actor_user_id=user.id,
        action=str(payload.get("action") or "Fraud alert reviewed"),
        entity_type="Fraud",
        entity_id=alert.alert_id,
        details={"notes": payload.get("notes"), "status": alert.status},
    ))
    db.commit()
    return _alert_payload(alert, order, supplier)


@router.get("/audit-logs")
def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    rows = db.execute(
        select(AuditLog, User.email)
        .outerjoin(User, User.id == AuditLog.actor_user_id)
        .where(AuditLog.actor_user_id == user.id)
        .order_by(AuditLog.created_at.desc())
        .offset(max(skip, 0)).limit(min(max(limit, 1), 500))
    ).all()
    return [{
        "id": row.id,
        "timestamp": row.created_at.isoformat(),
        "category": (
            "Fraud" if row.entity_type.lower() == "fraud" else
            "Negotiation" if row.entity_type.lower() == "negotiation" else
            "Agent" if row.entity_type.lower() == "agent" else
            "Procurement" if row.entity_type.lower() in {"purchase order", "supplier", "invoice", "procurement"} else
            "System"
        ),
        "action": row.action,
        "entityType": row.entity_type,
        "entityId": row.entity_id,
        "actor": email or "System",
        "outcome": row.details.get("outcome", "Recorded") if row.details else "Recorded",
        "summary": row.details.get("summary", row.action) if row.details else row.action,
        "details": row.details or {},
    } for row, email in rows]

