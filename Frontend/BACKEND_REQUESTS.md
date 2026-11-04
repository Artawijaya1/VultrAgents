# Backend Requests — Frontend Integration Gaps & API Contract Needs

This document lists all backend endpoints the frontend requires, their current implementation
status, assumed request/response contracts, and priority for the demo.
Prepared for the backend teammate.

Generated: 2026-11-04 (Updated Phase C)

---

## Executive Summary: Priority for Demo

1. **P0 (Demo Blockers — Core Read & Chat Execution)**
   - Chat: `POST /conversations` (session owner), `POST /conversations/{id}/messages` (with assistant message `id`).
   - Negotiation Copilot: `POST /negotiations/{id}/options` (AI strategy analysis), `POST /negotiations/{id}/drafts` (draft generation), `GET /negotiations` (history).
   - Fraud Detection: `GET /fraud/alerts`, `GET /fraud/alerts/{id}`, `PATCH /fraud/alerts/{id}` (status review), `GET /fraud/dashboard` (overview metrics).
   - Procurement Registers: `GET /purchase-orders`, `GET /vendors`, `GET /invoices`, `GET /contracts`.

2. **P1 (Workflow Actions & Human Approvals)**
   - Approval Workflow: `POST /approvals/{id}/approve`, `POST /approvals/{id}/reject`, `GET /approvals` (with approval ID mapped in agent responses).
   - Message Feedback: `POST /messages/{id}/feedback`.
   - Fraud Audit & Mitigation: `POST /fraud/alerts/{id}/explain`, `POST /fraud/alerts/{id}/hold-payment`.
   - Historical Context: `GET /price-history`, `GET /purchase-history`, `GET /vendors/{id}/performance`.

3. **P2 (Platform Operations & Scaffolding)**
   - Background Runs: `GET /runs/{id}`, `GET /runs/{id}/events`, `POST /runs/{id}/cancel`, `GET /runs/{id}/tool-calls`.
   - Fraud Rules: `GET/POST/PATCH /fraud/rules`, `POST /fraud/scans`.
   - PO Lifecycle: `POST /purchase-orders/{id}/send`, `/confirmations`, `/follow-ups`, `/cancel`.
   - Analytics aggregates: `GET /procurement/summary` (if KPI metrics are server-computed).

---

## 1. Chat Feature (`src/pages/ChatPage.jsx`, `src/services/chatService.js`)

**Status in Frontend:** Live adapter and mock adapter implemented. Switchable via `VITE_CHAT_MODE=live|mock` (default: `mock`).

### Critical Chat Gaps (P0 / P1)

1. **`session_id` Ownership (P0):**
   - *Current Workaround:* The frontend generates `session_id` via `crypto.randomUUID()` because `POST /conversations` returns 501.
   - *Required Fix:* The Backend must generate and own `session_id`, bind it securely to the authenticated Supabase user ID, the Purchase Order ID, and task. The frontend must never invent or supply `session_id`.
2. **Message ID in Message Response (P0):**
   - The response from `POST /conversations/{id}/messages` MUST include the generated assistant message `id` (`string`). Without this, the frontend cannot submit feedback (`POST /messages/{id}/feedback`).
3. **Approval ID Mapping (P1):**
   - When the Agent response has `requires_approval: true`, the Agent currently does not return an `approval_id`. The Backend must create a record in the approvals table and return `approval_id` (`string`) in the message payload. If null, the frontend approval buttons remain disabled.
4. **Conversation Scope Enforcement (P0):**
   - A conversation is strictly bound to `(task, reference_id)`. The Backend must reject messages if the reference ID or task does not match the conversation record.

### Chat Endpoints Specification

| Priority | Method | Path | Status | Assumed Request | Assumed Response |
|---|---|---|---|---|---|
| P0 | POST | `/conversations` | 501 | `{"task": "negotiation" \| "fraud", "reference_id": "PO-001"}` | `{"id": "conv-uuid", "task": "negotiation", "reference_id": "PO-001", "session_id": "backend-sess-uuid", "created_at": "ISO"}` |
| P0 | GET | `/conversations/{id}/messages` | 501 | (none) | `{"messages": [{"id": "msg-uuid", "role": "assistant", "content": "...", "status": "draft", "verified_result": {}, "precheck": {}, "tool_trace": [], "requires_approval": true, "approval_id": "appr-uuid", "created_at": "ISO"}]}` |
| P0 | POST | `/conversations/{id}/messages` | 501 | `{"question": "string (1-1000 chars)"}` | Assistant message object including `id`, `content`, `status`, `verified_result`, `precheck`, `tool_trace`, `requires_approval`, `approval_id`. |
| P0 | POST | `/agents/chat` | IMPLEMENTED | `{"task": "...", "reference_id": "...", "session_id": "...", "question": "..."}` | Direct Agent proxy response shape. |
| P1 | POST | `/messages/{id}/feedback` | 501 | `{"rating": "up" \| "down"}` | `{"id": "msg-uuid", "rating": "up"}` |
| P1 | POST | `/approvals/{id}/approve` | 501 | `{}` | `{"id": "appr-uuid", "status": "approved"}` |
| P1 | POST | `/approvals/{id}/reject` | 501 | `{}` | `{"id": "appr-uuid", "status": "rejected"}` |

---

## 2. Negotiation Copilot (`src/pages/NegotiationPage.jsx`, `src/services/negotiationService.js`)

**Status in Frontend:** Live adapter and mock adapter implemented. Switchable via `VITE_NEGOTIATION_MODE=mock|live` (default: `mock`).

| Priority | Method | Path | Status | Assumed Request | Assumed Response |
|---|---|---|---|---|---|
| P0 | GET | `/negotiations` | 501 | (none) | `[{"id": "NEG-...", "supplier_name": "...", "purchase_order_id": "PO-...", "strategy": "...", "target_price": 12.5, "status": "Pending Review", "created_at": "ISO"}]` |
| P0 | POST | `/negotiations/{id}/options` | 501 | `{"offered_price": 14.2, "target_price": 13.2, "requested_quantity": 2400, "proposed_delivery_date": "YYYY-MM-DD", "preferred_delivery_date": "YYYY-MM-DD", "supplier_id": "SUP-..."}` | `{"historical_average": 12.8, "offer_difference": 1.4, "offer_difference_percent": 10.9, "potential_savings": 2400, "recommendation": "...", "approach": "...", "confidence": 85, "reasons": ["..."]}` |
| P0 | POST | `/negotiations/{id}/drafts` | 501 | `{"strategy": "price", "tone": "Collaborative", "language": "en", "offered_price": 14.2, "target_price": 13.2, "requested_quantity": 2400, "supplier_id": "SUP-...", "notes": "..."}` | `{"draft_text": "Dear Supplier team..."}` |
| P1 | POST | `/negotiations` | 501 | `{"purchase_order_id": "PO-...", "supplier_id": "SUP-...", "strategy": "...", "target_price": 13.2}` | `{"id": "NEG-...", "status": "draft"}` |
| P1 | GET | `/price-history` | 501 | `?po_id=...` or `?product_id=...` | `[{"date": "2026-01-15", "unit_price": 12.5}]` |
| P1 | GET | `/purchase-history` | 501 | `?supplier_id=...` | `[{"po_id": "...", "date": "...", "amount": 1000, "status": "Completed"}]` |
| P1 | GET | `/vendors/{id}/performance` | 501 | (none) | `{"supplier_id": "...", "on_time_rate": 94, "average_delivery_days": 14, "rating": 4.7, "previous_orders": 28}` |

---

## 3. Fraud Detection (`src/pages/FraudDetectionPage.jsx`, `src/services/fraudDetectionService.js`)

**Status in Frontend:** Live adapter and mock adapter implemented. Switchable via `VITE_FRAUD_MODE=mock|live` (default: `mock`).

| Priority | Method | Path | Status | Assumed Request | Assumed Response |
|---|---|---|---|---|---|
| P0 | GET | `/fraud/alerts` | 501 | (none) | `[{"id": "ALT-...", "transaction_id": "INV-...", "invoice_id": "INV-...", "supplier_name": "...", "anomaly_type": "Duplicate Invoice", "amount": 148500000, "risk_score": 96, "severity": "Critical", "detected_at": "ISO", "status": "New", "explanation": ["..."], "evidence": [{"label": "...", "value": "...", "comparison": "...", "emphasis": "alert"}], "risk_factors": [{"label": "...", "score": 40, "explanation": "..."}], "recommended_actions": ["..."], "audit_trail": [{"id": "...", "timestamp": "...", "actor": "...", "action": "..."}]}]` |
| P0 | GET | `/fraud/alerts/{id}` | 501 | (none) | Detailed alert object (same shape as array element above). |
| P0 | PATCH | `/fraud/alerts/{id}` | 501 | `{"status": "Under Review" \| "Documents Requested" \| "Escalated" \| "False Positive" \| "Confirmed Anomaly"}` | `{"id": "ALT-...", "status": "..."}` |
| P0 | GET | `/fraud/dashboard` | 501 | (none) | `{"transactions_analyzed": 12845, "suspicious_transactions": 128, "high_risk_suppliers": 14, "potential_exposure": 842500000, "trend": [{"date": "Nov 1", "alerts": 14}], "distribution": [{"type": "Duplicate Invoice", "count": 42, "color": "#ed747b"}]}` |
| P1 | POST | `/fraud/alerts/{id}/explain` | 501 | `{"action": "...", "notes": "...", "previous_status": "...", "new_status": "..."}` | `{"id": "EV-...", "timestamp": "ISO", "actor": "...", "action": "...", "notes": "..."}` |
| P1 | POST | `/fraud/alerts/{id}/hold-payment` | 501 | `{"reason": "Potential duplicate invoice under investigation"}` | `{"id": "ALT-...", "payment_held": true}` |
| P2 | POST | `/fraud/scans` | 501 | `{"reference_id": "PO-001", "reference_type": "po"}` | `{"scan_id": "...", "status": "completed", "flags_found": 2}` |
| P2 | GET | `/fraud/rules` | 501 | (none) | `[{"rule_id": "DUP-INV-001", "name": "Duplicate Invoice", "threshold": 0.95, "enabled": true}]` |
| — | `/fraud/trend` | NO-ENDPOINT | (none) | If not provided in `/fraud/dashboard`, needs a separate endpoint: `[{"date": "Nov 1", "alerts": 14}]`. |
| — | `/fraud/distribution` | NO-ENDPOINT | (none) | If not provided in `/fraud/dashboard`, needs a separate endpoint: `[{"type": "Duplicate Invoice", "count": 42, "color": "..."}]`. |

---

## 4. Procurement Registers (`src/pages/ProcurementPages.jsx`, `src/services/procurementService.js`)

**Status in Frontend:** Live adapter and mock adapter implemented. Switchable via `VITE_PROCUREMENT_MODE=mock|live` (default: `mock`).

| Priority | Method | Path | Status | Assumed Request | Assumed Response |
|---|---|---|---|---|---|
| P0 | GET | `/purchase-orders` | 501 | `?skip=0&limit=50` | `[{"id": "PO-...", "supplier_id": "SUP-...", "product_name": "...", "category": "...", "quantity": 100, "unit": "units", "current_offer": 85000, "budget_ceiling_unit": 80000, "created_at": "ISO", "status": "Pending Approval", "requester": "..."}]` |
| P0 | GET | `/vendors` | 501 | `?skip=0&limit=50` | `[{"id": "SUP-...", "name": "...", "category": "...", "location": "...", "rating": 4.7, "spend_ytd": 186400, "risk": "Low", "status": "Active", "email": "...", "phone": "..."}]` |
| P0 | GET | `/invoices` | 501 | `?skip=0&limit=50` | `[{"id": "INV-...", "supplier_id": "SUP-...", "purchase_order_id": "PO-...", "contract_id": "CTR-...", "issue_date": "ISO", "due_date": "ISO", "amount": 148500, "currency": "USD", "status": "Under Review", "description": "..."}]` |
| P0 | GET | `/contracts` | 501 | `?skip=0&limit=50` | `[{"id": "CTR-...", "supplier_id": "SUP-...", "title": "...", "category": "...", "start_date": "ISO", "end_date": "ISO", "value": 500000, "currency": "USD", "status": "Active", "owner": "...", "purchase_order_ids": ["PO-..."]}]` |
| P1 | GET | `/purchase-orders/{id}` | 501 | (none) | Single PO detail object |
| P1 | GET | `/vendors/{id}` | 501 | (none) | Single supplier/vendor detail |
| P1 | GET | `/invoices/{id}` | 501 | (none) | Single invoice detail |
| P1 | GET | `/contracts/{id}` | 501 | (none) | Single contract detail |
| P1 | POST | `/purchase-orders` | 501 | `{"supplier_id": "...", "product_name": "...", "quantity": 100, "current_offer": 85000}` | Created PO object |
| P1 | POST | `/invoices` | 501 | `{"supplier_id": "...", "purchase_order_id": "...", "amount": 148500}` | Created invoice object |
| — | `/procurement/summary` | NO-ENDPOINT | (none) | Needed if KPI numbers on overview page (`open_orders`, `pending_approval_count`, `open_order_value`) should be backend-computed rather than client-calculated. |




