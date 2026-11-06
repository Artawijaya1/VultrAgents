from datetime import date
from unittest.mock import AsyncMock

from sqlalchemy import select

from app.core.config import Settings
from app.models.procurement import (
    AgentRun,
    AgentSession,
    ApprovalRequest,
    ChangeRequest,
    Invoice,
    Negotiation,
    PurchaseOrder,
    PurchaseOrderFollowUp,
    Supplier,
)
from app.models.user import User
from app.schemas.token import SupabaseIdentity


def _seed_procurement(factory, *, owner_user_id=None):
    with factory() as db:
        user = User(
            auth_user_id=SupabaseIdentity(
                id="4c9727a8-9194-4c93-a94c-2ca3fd2e0243",
                email="admin@example.com",
                app_metadata={"role": "admin"},
            ).id,
            email="admin@example.com",
        )
        db.add(user)
        db.flush()
        owner_id = owner_user_id if owner_user_id is not None else user.id

        supplier = Supplier(supplier_id="SUP-1", name="Supplier One")
        db.add(supplier)
        po = PurchaseOrder(
            po_id="PO-1",
            supplier_id=supplier.supplier_id,
            owner_user_id=owner_id,
            product_id="PRODUCT-1",
            quantity=10,
            offered_unit_price=1000,
            budget_ceiling_unit=1200,
            previous_unit_price=900,
            currency="IDR",
            required_delivery_date=date(2026, 12, 1),
        )
        db.add(po)
        db.add(
            Invoice(
                record_id="INV-ROW-1",
                invoice_number="INV-1",
                supplier_id=supplier.supplier_id,
                po_id=po.po_id,
                product_id=po.product_id,
                amount=10000,
                unit_price=1000,
                invoice_date=date(2026, 11, 1),
            )
        )
        db.commit()
        return user.id, po.po_id


def test_internal_procurement_routes_match_agent_provider_contract(
    client, test_session_factory
):
    _seed_procurement(test_session_factory)
    headers = {"X-API-Key": "test-internal-api-key"}

    po_response = client.get("/api/v1/internal/procurement/pos/PO-1", headers=headers)
    supplier_response = client.get(
        "/api/v1/internal/procurement/suppliers/SUP-1", headers=headers
    )
    invoice_response = client.get(
        "/api/v1/internal/procurement/suppliers/SUP-1/invoices", headers=headers
    )

    assert po_response.status_code == 200
    assert po_response.json()["po_id"] == "PO-1"
    assert po_response.json()["required_delivery_date"] == "2026-12-01"
    assert supplier_response.status_code == 200
    assert supplier_response.json() == {
        "supplier_id": "SUP-1",
        "name": "Supplier One",
        "bank_last_changed_at": None,
    }
    assert invoice_response.status_code == 200
    assert invoice_response.json()["items"][0]["record_id"] == "INV-ROW-1"


def test_negotiation_analysis_persists_target_and_uses_database_order_values(
    client, test_session_factory
):
    _seed_procurement(test_session_factory)

    response = client.post(
        "/api/v1/negotiations",
        headers={"Authorization": "Bearer test-token"},
        json={
            "po_id": "PO-1",
            "context": {
                "target_unit_price": 850,
                "offered_unit_price": 1,
                "quantity": 1,
                "currency": "USD",
            },
        },
    )

    assert response.status_code == 201
    result = response.json()
    assert result["context"] == {
        "target_unit_price": 850,
        "offered_unit_price": 1000,
        "quantity": 10.0,
        "currency": "IDR",
        "budget_ceiling_unit": 1200,
        "previous_unit_price": 900,
    }

    listed = client.get(
        "/api/v1/negotiations",
        headers={"Authorization": "Bearer test-token"},
    )
    assert listed.status_code == 200
    assert listed.json()[0]["negotiation_id"] == result["negotiation_id"]
    assert listed.json()[0]["context"] == result["context"]

    with test_session_factory() as db:
        saved = db.get(Negotiation, result["negotiation_id"])
        assert saved is not None
        assert saved.context == result["context"]


def test_negotiation_analysis_rejects_nonpositive_target_price(
    client, test_session_factory
):
    _seed_procurement(test_session_factory)

    response = client.post(
        "/api/v1/negotiations",
        headers={"Authorization": "Bearer test-token"},
        json={"po_id": "PO-1", "context": {"target_unit_price": 0}},
    )

    assert response.status_code == 422
    with test_session_factory() as db:
        assert db.scalar(select(Negotiation)) is None


def test_agent_run_persists_approval_and_audit(client, test_session_factory, monkeypatch):
    _seed_procurement(test_session_factory)
    async def fake_agent_call(endpoint, payload, timeout):
        return {
            "request_id": payload["request_id"],
            "task": "negotiation",
            "reference_id": "PO-1",
            "status": "draft",
            "summary": "Draft prepared.",
            "result": {"requires_approval": True},
            "precheck": None,
            "tool_trace": [],
            "requires_approval": True,
            "error": None,
        }

    mocked_call = AsyncMock(
        side_effect=fake_agent_call
    )
    monkeypatch.setattr("app.api.v1.endpoints.agents.call_agent", mocked_call)

    response = client.post(
        "/api/v1/agents/run",
        headers={"Authorization": "Bearer user-token"},
        json={
            "task": "negotiation",
            "reference_id": "PO-1",
            "reference_type": "po",
            "instruction": "Prepare options",
        },
    )

    assert response.status_code == 200
    approval_id = response.json()["approval_id"]
    mocked_call.assert_awaited_once()
    with test_session_factory() as db:
        run = db.scalar(select(AgentRun))
        approval = db.get(ApprovalRequest, approval_id)
        assert run is not None
        assert approval is not None
        assert approval.status == "pending"

    decision = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={"Authorization": "Bearer user-token"},
        json={"notes": "Reviewed by admin"},
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "approved"


def test_agent_chat_rejects_another_users_session(
    client, test_session_factory, monkeypatch
):
    current_user_id, po_id = _seed_procurement(test_session_factory)
    with test_session_factory() as db:
        other_user = User(email="other@example.com")
        db.add(other_user)
        db.flush()
        db.add(
            AgentSession(
                session_id="owned-by-other",
                user_id=other_user.id,
                po_id=po_id,
                task="negotiation",
            )
        )
        db.commit()

    mocked_call = AsyncMock()
    monkeypatch.setattr("app.api.v1.endpoints.agents.call_agent", mocked_call)
    response = client.post(
        "/api/v1/agents/chat",
        headers={"Authorization": "Bearer user-token"},
        json={
            "task": "negotiation",
            "reference_id": po_id,
            "session_id": "owned-by-other",
            "question": "Continue",
        },
    )

    assert current_user_id != 0
    assert response.status_code == 403
    mocked_call.assert_not_awaited()


def test_internal_rejection_creates_approval_without_rejecting_request(
    client, test_session_factory
):
    _, po_id = _seed_procurement(test_session_factory)
    with test_session_factory() as db:
        db.add(
            ChangeRequest(
                change_request_id="CR-1",
                po_id=po_id,
                status="pending",
                requested_changes={"quantity": 12},
            )
        )
        db.commit()

    response = client.post(
        "/api/v1/internal/change-requests/CR-1/reject",
        headers={"X-API-Key": "test-internal-api-key"},
        json={"reason": "Needs human review"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    with test_session_factory() as db:
        change_request = db.get(ChangeRequest, "CR-1")
        approval = db.scalar(
            select(ApprovalRequest).where(
                ApprovalRequest.action_type == "reject_change_request"
            )
        )
        assert change_request.status == "pending"
        assert approval is not None


def test_internal_follow_up_is_stored_for_approval_not_sent(
    client, test_session_factory
):
    _seed_procurement(test_session_factory)

    response = client.post(
        "/api/v1/internal/purchase-orders/PO-1/follow-ups",
        headers={"X-API-Key": "test-internal-api-key"},
        json={"message": "Follow up with the supplier"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    with test_session_factory() as db:
        follow_up = db.scalar(select(PurchaseOrderFollowUp))
        assert follow_up is not None
        assert follow_up.status == "pending_approval"
        assert follow_up.approval_id == response.json()["id"]


def test_agent_chat_persists_user_scoped_session(
    client, test_session_factory, monkeypatch
):
    _, po_id = _seed_procurement(test_session_factory)
    async def fake_agent_call(endpoint, payload, timeout):
        return {
            "session_id": payload["session_id"],
            "task": "negotiation",
            "reference_id": po_id,
            "status": "draft",
            "summary": "Draft prepared.",
            "answer": "Here is a draft.",
            "verified_result": {},
            "precheck": None,
            "tool_trace": [],
            "turn_index": 1,
            "requires_approval": True,
            "error": None,
            "notice": "Review required.",
        }

    mocked_call = AsyncMock(
        side_effect=fake_agent_call
    )
    monkeypatch.setattr("app.api.v1.endpoints.agents.call_agent", mocked_call)

    response = client.post(
        "/api/v1/agents/chat",
        headers={"Authorization": "Bearer user-token"},
        json={
            "task": "negotiation",
            "reference_id": po_id,
            "question": "Prepare a draft",
        },
    )

    assert response.status_code == 200
    assert response.json()["session_id"]
    assert response.json()["approval_id"]
    with test_session_factory() as db:
        session = db.get(AgentSession, response.json()["session_id"])
        approval = db.get(ApprovalRequest, response.json()["approval_id"])
        assert session is not None
        assert session.po_id == po_id
        assert approval is not None
        assert approval.status == "pending"


def test_agent_proxy_reports_missing_agent_configuration(
    client, test_session_factory, monkeypatch
):
    _seed_procurement(test_session_factory)
    monkeypatch.setattr(
        "app.services.agent_client.get_settings",
        lambda: Settings(agent_api_url=None, agent_api_key=None),
    )

    response = client.post(
        "/api/v1/agents/run",
        headers={"Authorization": "Bearer user-token"},
        json={
            "task": "fraud",
            "reference_id": "PO-1",
            "reference_type": "po",
            "instruction": "Review this PO",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Agent service is not configured."}


def test_negotiation_requires_explicit_purchase_order_reference(client):
    response = client.post(
        "/api/v1/agents/run",
        headers={"Authorization": "Bearer user-token"},
        json={
            "task": "negotiation",
            "reference_id": "PO-1",
            "instruction": "Prepare options",
        },
    )

    assert response.status_code == 422
