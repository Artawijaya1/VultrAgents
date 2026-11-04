# Kontrak integrasi Backend ↔ Procurement Agent

## A. API Agent (milik pengembang Agent)

`POST http://127.0.0.1:8001/api/v1/agents/run` (backend-to-backend, token wajib).

Headers:

```http
Authorization: Bearer <AGENT_API_KEY>
Content-Type: application/json
```

Input negotiation:

```json
{"task":"negotiation","reference_id":"PO-001","instruction":"Susun opsi negosiasi untuk pemasok"}
```

Input fraud:

```json
{"task":"fraud","reference_id":"SUP-001","instruction":"Periksa kejanggalan invoice"}
```

Output shape:

```json
{
  "request_id": "generated-uuid",
  "task": "negotiation",
  "reference_id": "PO-001",
  "status": "draft",
  "summary": "Draf ...",
  "result": {"status":"draft","options":[],"requires_approval":true},
  "precheck": {"flag_count":2,"findings":[]},
  "tool_trace": [{"tool":"get_purchase_order","reference_id":"PO-001","ok":true}],
  "requires_approval": true,
  "error": null
}
```

`GET /health` does not require authentication; do not expose detailed secrets there.
Swagger: `GET /docs` on agent service. Never expose dev docs publicly without gateway controls.

## B. Backend procurement API (milik teman database/backend)

Used only when `AGENT_DATA_MODE=http` and `PROCUREMENT_BACKEND_URL` is configured.
Backend must require `Authorization: Bearer <PROCUREMENT_SERVICE_TOKEN>`.

| Method | Endpoint | Returns |
|---|---|---|
| GET | `/api/v1/procurement/pos/{po_id}` | JSON PO or HTTP 404 |
| GET | `/api/v1/procurement/suppliers/{supplier_id}` | JSON supplier or HTTP 404 |
| GET | `/api/v1/procurement/suppliers/{supplier_id}/invoices` | JSON array of invoices or `{ "items": [...] }` |

Required PO fields (current calculation): `po_id`, `supplier_id`, `product_id`, `quantity`, `offered_unit_price`, `budget_ceiling_unit`, `previous_unit_price`, `currency`, `required_delivery_date`.

Required supplier fields: `supplier_id`, `name`, `bank_last_changed_at` (nullable ISO date).

Required invoice fields: `record_id` (unique database row), `invoice_number`, `supplier_id`, `po_id`, `product_id`, `amount`, `unit_price`, `invoice_date`.

Amounts are in minor-less integer IDR units in current demo. Update currency rounding before expanding to other currencies. Input and output must match these contracts, or adapt the fields in `provider_http.py`.

## C. Trust and business requirements

- Backend should authenticate & authorize the actual human user BEFORE calling agent service. Shared agent token only authenticates the service, not user-specific permissions.
- Prevent direct browser access to agent API in production; frontend -> backend -> agent.
- All tools are read-only. Negotiation produces drafts, never sends email or updates PO.
- Risk flags require human review, not automated penalties, rejection or fraud verdicts.
- Protect bank-account identifiers and personal data; return only metadata needed by the rules.
- Do not expose agent to the internet on 0.0.0.0 until authentication, HTTPS, request limits, logging, and access controls are hardened.
- Fraud evidence must be reviewed by a human; duplicate invoice numbers may arise from legitimate data errors.
- Mock data is synthetic. There is no database integration until backend contract implemented.

## D. Integration options

Option 1 (recommended): backend proxies HTTP POST into Agent API. No CORS needed when backend-to-backend.
Option 2: in the existing Agent FastAPI app add `from agent_core.graph_api import app` routes via an APIRouter refactor after testing; don't run two uvicorn servers on the same port.

## E. Penambahan Stage 6/7: PO fraud, chat, dan kepemilikan

### `POST /api/v1/agents/run`

Gunakan `task` bernilai `negotiation` atau `fraud`, dan `reference_id`.
Untuk pemeriksaan fraud khusus PO, **wajib** gunakan `reference_type: "po"`:

```json
{
  "task": "fraud",
  "reference_id": "PO-001",
  "reference_type": "po",
  "instruction": "Periksa invoice duplikat dan perubahan rekening terkait PO ini"
}
```

Untuk fraud supplier, gunakan `reference_type: "supplier"` jika didukung
oleh kontrak runtime; pastikan melalui `/openapi.json` sebelum mengirim.
Periksa `result`, `precheck`, `tool_trace`, `requires_approval`, serta `status`.
`review_required` adalah indikator perlu review, **bukan** vonis kecurangan.

### `POST /api/v1/agents/chat`

```json
{
  "task": "negotiation",
  "reference_id": "PO-001",
  "session_id": "user-scoped-session-001",
  "question": "Susun strategi negosiasi sesuai anggaran"
}
```

Field chat: `task`, `reference_id`, `session_id`, `question`.
Respons chat: `session_id`, `turn_index`, `status`, `answer`,
`verified_result`, `precheck`, `tool_trace`, `requires_approval`, `error`.
Teks `answer` adalah saran LLM, **bukan** evidence final; gunakan `verified_result`
untuk fakta transaksi. Klien wajib menangani `draft`, `review_required`,
`model_unavailable`, `needs_tool_use`, `not_configured`, dan kesalahan HTTP.

### Tanggung jawab otorisasi Backend (P0)

Bearer `AGENT_API_KEY` hanya identitas layanan. **Sebelum meneruskan request**,
Backend harus memvalidasi identitas pengguna, RBAC procurement, kepemilikan
`reference_id`/PO, izin akses supplier/invoice, dan `session_id` milik pengguna.
Kunci `session_id` dengan identitas pengguna di backend; jangan menerima ID
sesi pelanggan lain begitu saja. Jangan mengirim service token ke frontend.
Sementara tidak ada otorisasi pengguna end-to-end, Agent hanya untuk demo
terisolasi pada `127.0.0.1`, bukan endpoint publik.

### Integrasi asli masih menunggu validasi

Pengujian sekarang menggunakan mock provider atau HTTP MockTransport, **bukan**
API Backend asli. Untuk staging, gunakan `AGENT_DATA_MODE=http`,
`PROCUREMENT_BACKEND_URL=https://...`, `PROCUREMENT_SERVICE_TOKEN` yang aman,
lalu uji PO yang diizinkan, PO yang ditolak, respons kosong, timeout, dan data
invoicing yang sesuai schema. Verifikasi model dan source berdasarkan runtime
`GET /openapi.json`, bukan snapshot yang mungkin usang.
