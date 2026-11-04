from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.models.procurement import Invoice, PurchaseOrder
from app.models.user import User
from scripts.seed_agent_demo import INVOICE_NUMBER, PO_ID, SUPPLIER_ID, seed


def test_agent_demo_seed_is_idempotent(test_session_factory):
    first = seed(session_factory=test_session_factory)
    second = seed(session_factory=test_session_factory)

    assert first["supplier_created"] is True
    assert first["purchase_order_created"] is True
    assert first["invoices_created"] == 2
    assert second["supplier_created"] is False
    assert second["purchase_order_created"] is False
    assert second["invoices_created"] == 0

    with test_session_factory() as db:
        po = db.get(PurchaseOrder, PO_ID)
        assert po is not None
        assert po.owner_user_id is None
        assert po.supplier_id == SUPPLIER_ID
        assert po.quantity == Decimal("10.0000")
        assert db.scalar(select(func.count()).select_from(Invoice)) == 2
        assert db.scalar(
            select(func.count()).select_from(Invoice).where(
                Invoice.invoice_number == INVOICE_NUMBER
            )
        ) == 2


def test_agent_demo_seed_can_bind_to_existing_user(test_session_factory):
    with test_session_factory() as db:
        db.add(User(email="agent-demo-owner@example.com"))
        db.commit()

    result = seed(
        owner_email="agent-demo-owner@example.com",
        session_factory=test_session_factory,
    )

    assert result["owner_linked"] is True
    with test_session_factory() as db:
        user = db.scalar(
            select(User).where(User.email == "agent-demo-owner@example.com")
        )
        po = db.get(PurchaseOrder, PO_ID)
        assert po.owner_user_id == user.id


def test_agent_demo_seed_rejects_unknown_owner_without_partial_data(
    test_session_factory,
):
    try:
        seed(
            owner_email="missing@example.com",
            session_factory=test_session_factory,
        )
    except ValueError as exc:
        assert "No matching Backend user profile" in str(exc)
    else:
        raise AssertionError("Expected missing owner to be rejected.")

    with test_session_factory() as db:
        assert db.scalar(select(func.count()).select_from(PurchaseOrder)) == 0
