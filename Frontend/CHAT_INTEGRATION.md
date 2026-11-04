# Chat Integration Contract

Frontend ↔ Backend assumed shapes for the Agent Chat feature.
All endpoints return HTTP 501 as of 2026-11-04. This document lists the
shapes the frontend expects so the backend teammate can implement them.

## Architecture

```
Browser (Supabase access token) → Backend /api/v1 → Agent service (port 8001)
```

The browser NEVER contacts the Agent service directly.
AGENT_API_KEY, INTERNAL_API_KEY and X-API-Key MUST NOT appear in frontend
code, environment variables, or build output.

## Endpoints the frontend calls

### POST /api/v1/conversations

Create a new conversation bound to one task + one reference_id.

**Request:**
```json
{ "task": "negotiation" | "fraud", "reference_id": "PO-001" }
```

**Response (assumed):**
```json
{
  "id": "conv-uuid",
  "task": "negotiation",
  "reference_id": "PO-001",
  "session_id": "backend-generated-session-id",
  "created_at": "2026-11-04T10:00:00Z"
}
```

- `session_id` is generated and owned by the Backend. The frontend never
  invents session IDs.
- A conversation is bound to exactly one task + one reference_id. Changing
  either requires creating a new conversation.

### GET /api/v1/conversations

List conversations for the authenticated user.

**Response (assumed):**
```json
[
  { "id": "conv-uuid", "task": "negotiation", "reference_id": "PO-001", "created_at": "..." }
]
```

### GET /api/v1/conversations/{id}/messages

List messages in a conversation.

**Response (assumed):**
```json
{
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user" | "assistant",
      "content": "question text or answer text",
      "status": "draft" | "review_required" | "no_flags" | null,
      "verified_result": { ... } | null,
      "precheck": { "flag_count": 2, "findings": [...] } | null,
      "tool_trace": [{ "tool": "get_purchase_order", "reference_id": "PO-001", "ok": true }],
      "requires_approval": true,
      "approval_id": "approval-uuid" | null,
      "error": null,
      "notice": null,
      "created_at": "2026-11-04T10:01:00Z"
    }
  ]
}
```

### POST /api/v1/conversations/{id}/messages

Send a user question and receive the agent response.

**Request:**
```json
{ "question": "string, 1-1000 chars" }
```

**Response (assumed):**
The assistant message object (same shape as above), which MUST include `id`.

The Backend proxies this to Agent `POST /api/v1/agents/chat` with:
```json
{
  "task": "<from conversation>",
  "reference_id": "<from conversation>",
  "session_id": "<backend-owned>",
  "question": "<from request>"
}
```

Agent response fields that map to the message object:
- `answer` → message `content` (role: assistant)
- `verified_result` → `verified_result`
- `precheck` → `precheck`
- `tool_trace` → `tool_trace`
- `requires_approval` → `requires_approval`
- `status` → `status`
- `error` → `error`
- `notice` → `notice`

### POST /api/v1/messages/{id}/feedback

Submit feedback on an assistant message.

**Request:**
```json
{ "rating": "up" | "down" }
```

**Response (assumed):**
```json
{ "id": "msg-uuid", "rating": "up" }
```

### GET /api/v1/approvals

List pending approvals for the authenticated user.

### POST /api/v1/approvals/{id}/approve

Approve an approval request.

**Request:** `{}`
**Response (assumed):** `{ "id": "approval-uuid", "status": "approved" }`

### POST /api/v1/approvals/{id}/reject

Reject an approval request.

**Request:** `{}`
**Response (assumed):** `{ "id": "approval-uuid", "status": "rejected" }`

## Status values the frontend handles

| Status | Meaning |
|---|---|
| `draft` | AI generated a draft recommendation |
| `review_required` | Findings need human review |
| `no_flags` | No risk indicators found |
| `no_invoices` | No invoice data available for analysis |
| `not_found` | Reference ID not found |
| `invalid_request` | Validation failed |
| `data_unavailable` | Backend data source is down |
| `model_unavailable` | AI model is temporarily unavailable |
| `needs_tool_use` | Agent needs to run tools but couldn't |
| `not_configured` | LLM not configured on the agent |
| `step_limit` | Agent reached its analysis step limit |

## HTTP error handling

| Status | Frontend behavior |
|---|---|
| 401 | Refresh token once, then redirect to /login |
| 501 | Show "Not available yet" banner, offer switch to mock mode |
| 502/504 | Show retry button |
| Network error | Inline error message |

## Gaps for the backend teammate

1. **All endpoints return 501.** No Pydantic schemas, no proxy logic to Agent.

2. **Message ID in response.** POST /conversations/{id}/messages MUST return
   the assistant message `id` so the frontend can call POST /messages/{id}/feedback.

3. **approval_id in message payload.** The Agent response has no `approval_id`.
   The Backend needs to generate or map approval IDs when `requires_approval: true`.
   If `approval_id` is null, the frontend disables Approve/Reject buttons with
   tooltip "No approval request yet".

4. **session_id ownership.** The Backend generates `session_id`, binds it to the
   authenticated user + conversation, and passes it to the Agent. The frontend
   never sees or sends `session_id` — only `conversation_id`.

5. **Conversation ↔ task+reference_id binding.** The Backend must enforce that a
   conversation cannot change its task or reference_id after creation.

6. **User authorization.** The Backend must verify the user has access to the
   referenced PO before proxying to the Agent.

7. **Approval workflow.** POST /approvals/{id}/approve and /reject need a real
   implementation. Currently 501.

8. **Fraud findings shape.** Each finding must include: `rule_id`, `severity`,
   `description`, `evidence_record_ids` (array of strings), `next_action`.

9. **reference_id validation.** Pattern: `^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$`.
   Validated client-side; Backend should also validate.

10. **question length.** 1-1000 characters. Validated client-side; Backend should
    also validate.
