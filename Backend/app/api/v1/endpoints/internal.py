from fastapi import APIRouter

from app.api.v1.endpoints._placeholders import EndpointContract, register_contracts

router = register_contracts(
    APIRouter(),
    (
        EndpointContract(
            "GET",
            "/purchase-orders/{id}/versions",
            "internal_purchase_order_versions",
            "List purchase order versions",
        ),
        EndpointContract(
            "GET",
            "/vendors/{id}/performance",
            "internal_vendor_performance",
            "Get vendor performance",
        ),
        EndpointContract(
            "GET",
            "/policies",
            "internal_policies",
            "List policies",
        ),
        EndpointContract(
            "GET",
            "/invoices",
            "internal_invoices",
            "List invoices",
        ),
        EndpointContract(
            "GET",
            "/invoices/{id}",
            "internal_invoice",
            "Get an invoice",
        ),
        EndpointContract(
            "GET",
            "/change-requests/{id}",
            "internal_change_request",
            "Get a change request",
        ),
        EndpointContract(
            "POST",
            "/change-requests/{id}/reject",
            "internal_reject_change_request",
            "Reject a change request",
            has_body=True,
        ),
        EndpointContract(
            "POST",
            "/purchase-orders/{id}/follow-ups",
            "internal_create_purchase_order_follow_up",
            "Create a purchase order follow-up",
            has_body=True,
        ),
        EndpointContract(
            "GET",
            "/communications/{id}",
            "internal_communication",
            "Get a communication",
        ),
        EndpointContract(
            "POST",
            "/communications/{id}/classification",
            "internal_classify_communication",
            "Classify a communication",
            has_body=True,
        ),
        EndpointContract(
            "GET",
            "/negotiations/{id}",
            "internal_negotiation",
            "Get a negotiation",
        ),
        EndpointContract(
            "PATCH",
            "/negotiations/{id}/drafts/{draft_id}",
            "internal_update_negotiation_draft",
            "Update a negotiation draft",
            has_body=True,
        ),
        EndpointContract(
            "GET",
            "/fraud/rules",
            "internal_fraud_rules",
            "List fraud rules",
        ),
        EndpointContract(
            "POST",
            "/fraud/alerts",
            "internal_create_fraud_alert",
            "Create a fraud alert",
            has_body=True,
        ),
        EndpointContract(
            "GET",
            "/fraud/scans/{id}",
            "internal_fraud_scan",
            "Get a fraud scan",
        ),
    ),
)
