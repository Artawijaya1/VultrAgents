from fastapi import APIRouter

from app.api.v1.endpoints._placeholders import EndpointContract, register_contracts

router = register_contracts(
    APIRouter(),
    (
        EndpointContract(
            "GET", "/conversations", "list_conversations", "List conversations"
        ),
        EndpointContract(
            "POST", "/conversations", "create_conversation", "Create a conversation", True
        ),
        EndpointContract(
            "GET",
            "/conversations/{id}/messages",
            "list_conversation_messages",
            "List conversation messages",
        ),
        EndpointContract(
            "POST",
            "/conversations/{id}/messages",
            "create_conversation_message",
            "Create a conversation message",
            True,
        ),
        EndpointContract(
            "POST",
            "/messages/{id}/feedback",
            "create_message_feedback",
            "Submit message feedback",
            True,
        ),
        EndpointContract("GET", "/runs/{id}", "read_run", "Get a run"),
        EndpointContract("GET", "/runs/{id}/events", "list_run_events", "List run events"),
        EndpointContract(
            "POST", "/runs/{id}/cancel", "cancel_run", "Cancel a run", True
        ),
        EndpointContract(
            "GET", "/runs/{id}/tool-calls", "list_run_tool_calls", "List run tool calls"
        ),
        EndpointContract(
            "GET", "/purchase-orders", "list_purchase_orders", "List purchase orders"
        ),
        EndpointContract(
            "POST",
            "/purchase-orders",
            "create_purchase_order",
            "Create a purchase order",
            True,
        ),
        EndpointContract(
            "GET", "/purchase-orders/{id}", "read_purchase_order", "Get a purchase order"
        ),
        EndpointContract(
            "GET",
            "/purchase-orders/{id}/versions",
            "list_purchase_order_versions",
            "List purchase order versions",
        ),
        EndpointContract(
            "POST",
            "/purchase-orders/{id}/send",
            "send_purchase_order",
            "Send a purchase order",
            True,
        ),
        EndpointContract(
            "POST",
            "/purchase-orders/{id}/confirmations",
            "create_purchase_order_confirmation",
            "Record a purchase order confirmation",
            True,
        ),
        EndpointContract(
            "POST",
            "/purchase-orders/{id}/follow-ups",
            "create_purchase_order_follow_up",
            "Create a purchase order follow-up",
            True,
        ),
        EndpointContract(
            "POST",
            "/purchase-orders/{id}/cancel",
            "cancel_purchase_order",
            "Cancel a purchase order",
            True,
        ),
        EndpointContract(
            "POST",
            "/purchase-orders/{id}/notify-stakeholders",
            "notify_purchase_order_stakeholders",
            "Notify purchase order stakeholders",
            True,
        ),
        EndpointContract(
            "GET", "/change-requests", "list_change_requests", "List change requests"
        ),
        EndpointContract(
            "POST",
            "/change-requests",
            "create_change_request",
            "Create a change request",
            True,
        ),
        EndpointContract(
            "GET", "/change-requests/{id}", "read_change_request", "Get a change request"
        ),
        EndpointContract(
            "POST",
            "/change-requests/{id}/accept",
            "accept_change_request",
            "Accept a change request",
            True,
        ),
        EndpointContract(
            "POST",
            "/change-requests/{id}/analyze",
            "analyze_change_request",
            "Analyze a change request",
            True,
        ),
        EndpointContract(
            "POST",
            "/change-requests/{id}/reject",
            "reject_change_request",
            "Reject a change request",
            True,
        ),
        EndpointContract(
            "GET",
            "/purchase-orders/{id}/communications",
            "list_purchase_order_communications",
            "List purchase order communications",
        ),
        EndpointContract(
            "POST",
            "/communications/draft",
            "draft_communication",
            "Draft a communication",
            True,
        ),
        EndpointContract(
            "POST",
            "/communications/{id}/send",
            "send_communication",
            "Send a communication",
            True,
        ),
        EndpointContract(
            "PATCH",
            "/communications/{id}",
            "update_communication",
            "Edit a communication draft",
            True,
        ),
        EndpointContract("GET", "/vendors", "list_vendors", "List vendors"),
        EndpointContract("POST", "/vendors", "create_vendor", "Create a vendor", True),
        EndpointContract("GET", "/vendors/{id}", "read_vendor", "Get a vendor"),
        EndpointContract(
            "GET", "/vendors/{id}/contacts", "list_vendor_contacts", "List vendor contacts"
        ),
        EndpointContract(
            "GET",
            "/vendors/{id}/performance",
            "read_vendor_performance",
            "Get vendor performance",
        ),
        EndpointContract(
            "GET",
            "/vendors/{id}/bank-accounts",
            "list_vendor_bank_accounts",
            "List vendor bank accounts",
        ),
        EndpointContract(
            "POST",
            "/vendors/{id}/bank-accounts/change-requests",
            "create_bank_account_change_request",
            "Request a bank account change",
            True,
        ),
        EndpointContract(
            "POST",
            "/vendors/{id}/bank-accounts/change-requests/{request_id}/verify",
            "verify_bank_account_change_request",
            "Verify a bank account change request",
            True,
        ),
        EndpointContract(
            "GET", "/contracts", "list_contracts", "List contracts"
        ),
        EndpointContract(
            "GET", "/contracts/search", "search_contracts", "Search contracts"
        ),
        EndpointContract("GET", "/contracts/{id}", "read_contract", "Get a contract"),
        EndpointContract(
            "GET", "/purchase-history", "read_purchase_history", "Get purchase history"
        ),
        EndpointContract("GET", "/price-history", "read_price_history", "Get price history"),
        EndpointContract(
            "POST", "/negotiations", "create_negotiation", "Create a negotiation", True
        ),
        EndpointContract(
            "GET", "/negotiations/{id}", "read_negotiation", "Get a negotiation"
        ),
        EndpointContract(
            "GET",
            "/negotiations/{id}/context",
            "read_negotiation_context",
            "Get negotiation context",
        ),
        EndpointContract(
            "GET",
            "/negotiations/{id}/options",
            "list_negotiation_options",
            "List negotiation options",
        ),
        EndpointContract(
            "POST",
            "/negotiations/{id}/options",
            "create_negotiation_options",
            "Create negotiation options",
            True,
        ),
        EndpointContract(
            "POST",
            "/negotiations/{id}/options/{opt_id}/select",
            "select_negotiation_option",
            "Select a negotiation option",
            True,
        ),
        EndpointContract(
            "POST",
            "/negotiations/{id}/drafts",
            "create_negotiation_draft",
            "Create a negotiation draft",
            True,
        ),
        EndpointContract(
            "GET",
            "/negotiations/{id}/drafts",
            "list_negotiation_drafts",
            "List negotiation drafts",
        ),
        EndpointContract(
            "PATCH",
            "/negotiations/{id}/drafts/{draft_id}",
            "update_negotiation_draft",
            "Update a negotiation draft",
            True,
        ),
        EndpointContract(
            "POST",
            "/negotiations/{id}/drafts/{draft_id}/send",
            "send_negotiation_draft",
            "Send a negotiation draft",
            True,
        ),
        EndpointContract(
            "POST",
            "/negotiations/{id}/outcome",
            "create_negotiation_outcome",
            "Record a negotiation outcome",
            True,
        ),
        EndpointContract(
            "POST", "/fraud/scans", "create_fraud_scan", "Start a fraud scan", True
        ),
        EndpointContract("GET", "/fraud/alerts", "list_fraud_alerts", "List fraud alerts"),
        EndpointContract(
            "GET", "/fraud/alerts/{id}", "read_fraud_alert", "Get a fraud alert"
        ),
        EndpointContract(
            "PATCH",
            "/fraud/alerts/{id}",
            "update_fraud_alert",
            "Update a fraud alert",
            True,
        ),
        EndpointContract(
            "POST",
            "/fraud/alerts/{id}/explain",
            "explain_fraud_alert",
            "Explain a fraud alert",
            True,
        ),
        EndpointContract(
            "POST",
            "/fraud/alerts/{id}/hold-payment",
            "hold_fraudulent_payment",
            "Hold a payment",
            True,
        ),
        EndpointContract("GET", "/fraud/rules", "list_fraud_rules", "List fraud rules"),
        EndpointContract(
            "POST", "/fraud/rules", "create_fraud_rule", "Create a fraud rule", True
        ),
        EndpointContract(
            "PATCH", "/fraud/rules", "update_fraud_rules", "Update fraud rules", True
        ),
        EndpointContract(
            "GET", "/fraud/dashboard", "read_fraud_dashboard", "Get fraud dashboard"
        ),
        EndpointContract("GET", "/invoices", "list_invoices", "List invoices"),
        EndpointContract("POST", "/invoices", "create_invoice", "Create an invoice", True),
        EndpointContract("GET", "/invoices/{id}", "read_invoice", "Get an invoice"),
        EndpointContract("GET", "/audit-logs", "list_audit_logs", "List audit logs"),
        EndpointContract("GET", "/notifications", "list_notifications", "List notifications"),
        EndpointContract(
            "POST", "/notifications", "create_notification", "Create a notification", True
        ),
        EndpointContract(
            "GET", "/settings/policies", "read_policies", "Get policy settings"
        ),
        EndpointContract(
            "PATCH",
            "/settings/policies",
            "update_policies",
            "Update policy settings",
            True,
        ),
        EndpointContract("GET", "/usage", "read_usage", "Get usage"),
        EndpointContract(
            "POST",
            "/webhooks/inbound-email",
            "receive_inbound_email",
            "Receive an inbound email webhook",
            True,
        ),
    ),
)
