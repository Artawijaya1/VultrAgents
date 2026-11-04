from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    bank_last_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    po_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("suppliers.supplier_id"), index=True, nullable=False
    )
    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    product_id: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    offered_unit_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    budget_ceiling_unit: Mapped[int] = mapped_column(BigInteger, nullable=False)
    previous_unit_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="IDR", nullable=False)
    required_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Invoice(Base):
    __tablename__ = "invoices"

    record_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("suppliers.supplier_id"), index=True, nullable=False
    )
    po_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_orders.po_id"), index=True, nullable=False
    )
    product_id: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    unit_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PurchaseOrderVersion(Base):
    __tablename__ = "purchase_order_versions"
    __table_args__ = (
        UniqueConstraint("po_id", "version_number", name="uq_po_version_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_orders.po_id"), index=True, nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class VendorPerformance(Base):
    __tablename__ = "vendor_performance"

    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("suppliers.supplier_id"), primary_key=True
    )
    on_time_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    defect_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ProcurementPolicy(Base):
    __tablename__ = "procurement_policies"

    policy_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    change_request_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    po_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_orders.po_id"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    requested_changes: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    outcome_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PurchaseOrderFollowUp(Base):
    __tablename__ = "purchase_order_follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_orders.po_id"), index=True, nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="pending_approval", nullable=False)
    approval_id: Mapped[int | None] = mapped_column(
        ForeignKey("approval_requests.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Communication(Base):
    __tablename__ = "communications"

    communication_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    po_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_orders.po_id"), index=True, nullable=False
    )
    direction: Mapped[str] = mapped_column(String(20), default="inbound", nullable=False)
    subject: Mapped[str | None] = mapped_column(String(300), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str | None] = mapped_column(String(80), nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Negotiation(Base):
    __tablename__ = "negotiations"

    negotiation_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    po_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_orders.po_id"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)
    selected_option: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class NegotiationDraft(Base):
    __tablename__ = "negotiation_drafts"

    draft_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    negotiation_id: Mapped[str] = mapped_column(
        ForeignKey("negotiations.negotiation_id"), index=True, nullable=False
    )
    content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class FraudRule(Base):
    __tablename__ = "fraud_rules"

    rule_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FraudScan(Base):
    __tablename__ = "fraud_scans"

    scan_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    po_id: Mapped[str | None] = mapped_column(
        ForeignKey("purchase_orders.po_id"), index=True, nullable=True
    )
    supplier_id: Mapped[str | None] = mapped_column(
        ForeignKey("suppliers.supplier_id"), index=True, nullable=True
    )
    status: Mapped[str] = mapped_column(String(40), default="completed", nullable=False)
    results: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    alert_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    scan_id: Mapped[str | None] = mapped_column(
        ForeignKey("fraud_scans.scan_id"), index=True, nullable=True
    )
    po_id: Mapped[str | None] = mapped_column(
        ForeignKey("purchase_orders.po_id"), index=True, nullable=True
    )
    supplier_id: Mapped[str | None] = mapped_column(
        ForeignKey("suppliers.supplier_id"), index=True, nullable=True
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="review_required", nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    requested_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    decision_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    session_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    po_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_orders.po_id"), index=True, nullable=False
    )
    task: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    request_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    reference_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    task: Mapped[str] = mapped_column(String(30), nullable=False)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    approval_id: Mapped[int | None] = mapped_column(
        ForeignKey("approval_requests.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
