"""Seed deterministic synthetic procurement records for Agent integration tests."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.procurement import (
    FraudRule,
    Invoice,
    ProcurementPolicy,
    PurchaseOrder,
    PurchaseOrderVersion,
    Supplier,
    VendorPerformance,
)
from app.models.user import User

SUPPLIER_ID = "AGENT-DEMO-SUP-001"
PO_ID = "AGENT-DEMO-PO-001"
INVOICE_IDS = ("AGENT-DEMO-INV-001", "AGENT-DEMO-INV-002")
INVOICE_NUMBER = "DEMO-DUPLICATE-2026-001"
SEED_MARKER = "Synthetic Agent integration demo data. Not a real supplier or fraud finding."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--owner-email",
        help=(
            "Attach the demo PO to this existing Backend user profile. "
            "Log in through the Backend once first so the profile is synchronized."
        ),
    )
    return parser.parse_args()


def _insert_if_missing(session, model, key, values) -> bool:
    if session.get(model, key) is not None:
        return False
    session.add(model(**values))
    return True


def seed(owner_email: str | None = None, session_factory=SessionLocal) -> dict[str, int | bool]:
    with session_factory() as session:
        with session.begin():
            owner = None
            if owner_email:
                owner = session.scalar(
                    select(User).where(User.email == owner_email.strip().lower())
                )
                if owner is None:
                    raise ValueError(
                        "No matching Backend user profile. Log in once through the Backend, "
                        "then rerun with --owner-email."
                    )

            supplier_created = _insert_if_missing(
                session,
                Supplier,
                SUPPLIER_ID,
                {
                    "supplier_id": SUPPLIER_ID,
                    "name": "Demo Supplier (Synthetic)",
                    "bank_last_changed_at": datetime(2026, 10, 25, tzinfo=timezone.utc),
                },
            )
            session.flush()

            existing_po = session.get(PurchaseOrder, PO_ID)
            po_created = existing_po is None
            if existing_po is None:
                session.add(
                    PurchaseOrder(
                        po_id=PO_ID,
                        supplier_id=SUPPLIER_ID,
                        owner_user_id=owner.id if owner else None,
                        product_id="AGENT-DEMO-PRODUCT-001",
                        quantity=Decimal("10"),
                        offered_unit_price=150000,
                        budget_ceiling_unit=135000,
                        previous_unit_price=140000,
                        currency="IDR",
                        required_delivery_date=date(2026, 12, 4),
                        status="open",
                    )
                )
            elif (
                existing_po.supplier_id != SUPPLIER_ID
                or existing_po.product_id != "AGENT-DEMO-PRODUCT-001"
            ):
                raise ValueError(
                    "The demo PO ID is already used by a different purchase order."
                )
            elif owner is not None:
                if existing_po.owner_user_id not in (None, owner.id):
                    raise ValueError(
                        "The demo PO is already owned by a different user; "
                        "refusing to change its owner."
                    )
                existing_po.owner_user_id = owner.id
            session.flush()

            invoices_created = 0
            for record_id, invoice_date in zip(
                INVOICE_IDS,
                (date(2026, 11, 1), date(2026, 11, 3)),
                strict=True,
            ):
                if _insert_if_missing(
                    session,
                    Invoice,
                    record_id,
                    {
                        "record_id": record_id,
                        "invoice_number": INVOICE_NUMBER,
                        "supplier_id": SUPPLIER_ID,
                        "po_id": PO_ID,
                        "product_id": "AGENT-DEMO-PRODUCT-001",
                        "amount": 1500000,
                        "unit_price": 150000,
                        "invoice_date": invoice_date,
                    },
                ):
                    invoices_created += 1

            performance_created = _insert_if_missing(
                session,
                VendorPerformance,
                SUPPLIER_ID,
                {
                    "supplier_id": SUPPLIER_ID,
                    "on_time_rate": 0.92,
                    "defect_rate": 0.02,
                    "rating": 4.2,
                    "metrics": {"sample_size": 12, "source": "synthetic demo"},
                },
            )
            policy_created = _insert_if_missing(
                session,
                ProcurementPolicy,
                "agent_demo_review_thresholds",
                {
                    "policy_key": "agent_demo_review_thresholds",
                    "description": SEED_MARKER,
                    "value": {
                        "currency": "IDR",
                        "price_variance_review_percent": 5,
                        "duplicate_invoice_action": "human_review_only",
                    },
                    "enabled": True,
                },
            )
            rule_created = _insert_if_missing(
                session,
                FraudRule,
                "agent_demo_duplicate_invoice",
                {
                    "rule_id": "agent_demo_duplicate_invoice",
                    "name": "Demo duplicate invoice indicator",
                    "description": SEED_MARKER,
                    "enabled": True,
                    "config": {"same_invoice_number": "review_required"},
                },
            )
            existing_version = session.scalar(
                select(PurchaseOrderVersion).where(
                    PurchaseOrderVersion.po_id == PO_ID,
                    PurchaseOrderVersion.version_number == 1,
                )
            )
            version_created = existing_version is None
            if version_created:
                session.add(
                    PurchaseOrderVersion(
                        po_id=PO_ID,
                        version_number=1,
                        snapshot={
                            "po_id": PO_ID,
                            "supplier_id": SUPPLIER_ID,
                            "product_id": "AGENT-DEMO-PRODUCT-001",
                            "quantity": 10,
                            "offered_unit_price": 150000,
                            "budget_ceiling_unit": 135000,
                            "currency": "IDR",
                            "seed_marker": SEED_MARKER,
                        },
                    )
                )

            return {
                "supplier_created": supplier_created,
                "purchase_order_created": po_created,
                "invoices_created": invoices_created,
                "vendor_performance_created": performance_created,
                "policy_created": policy_created,
                "fraud_rule_created": rule_created,
                "purchase_order_version_created": version_created,
                "owner_linked": owner is not None,
            }


if __name__ == "__main__":
    args = parse_args()
    result = seed(args.owner_email)
    for key, value in result.items():
        print(f"{key}={value}")
    if not result["owner_linked"]:
        print(
            "note=PO currently has no owner; login through Backend once, then rerun "
            "with --owner-email to enable authenticated Agent proxy tests."
        )
