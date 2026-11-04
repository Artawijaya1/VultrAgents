# ProcureGuard AI — Serah-terima kontrak Backend ↔ Agents (Stage 7)

Status: implementasi Agent menggunakan MOCK data dan layanan Agent FastAPI mandiri.
Backend asli, frontend, persistent session dan otorisasi per pengguna BELUM diuji.

## Arah arsitektur

`Frontend (login user)` → `Backend (auth + RBAC + ownership PO/session)` →
`Agent (Bearer service)` → `MCP tools (read-only)` → `Provider (mock/http)`.
Jangan letakkan `AGENT_API_KEY`, `LLM_API_KEY`, atau `PROCUREMENT_SERVICE_TOKEN`
di aplikasi browser.

## Jalankan Agent (PowerShell, root Agents)

```powershell
$env:AGENT_DATA_MODE='mock'
$env:AGENT_API_KEY='TOKEN_SERVICE_YANG_DIPILIH_TIM'
$env:LLM_MODEL='gemini-3.5-flash-lite'
$env:LLM_BASE_URL='https://generativelanguage.googleapis.com/v1beta/openai/'
$env:LLM_TIMEOUT_SECONDS='90'
$secure=Read-Host 'Masukkan Gemini API Key' -AsSecureString
$env:LLM_API_KEY=[System.Net.NetworkCredential]::new('', $secure).Password
Remove-Variable secure
.\.venv\Scripts\python.exe -m uvicorn agent_core.graph_api:app --host 127.0.0.1 --port 8001
```

Layanan tersedia di `GET /health`, `POST /api/v1/agents/run` dan
`POST /api/v1/agents/chat`. Kedua POST memerlukan header
`Authorization: Bearer <AGENT_API_KEY>`. `GET /openapi.json` menyediakan schema
runtime. Jangan mengizinkan browser berkomunikasi langsung dengan Agent.

## Request ke Agent

Negosiasi deterministik:

```json
{"task":"negotiation","reference_id":"PO-001","instruction":"Susun strategi harga"}
```

Fraud berdasarkan satu PO:

```json
{"task":"fraud","reference_id":"PO-001","reference_type":"po","instruction":"Periksa anomali"}
```

Chat dua arah dengan sesi:

```json
{"task":"negotiation","reference_id":"PO-001","session_id":"demo-session-001","question":"Beri alternatif negosiasi"}
```

Jaga agar `session_id` unik, terikat ke pengguna dan PO pada Backend; jangan
anggap string ini rahasia atau bukti autentikasi. `turn_index` adalah indikator
kelanjutan sesi, bukan jaminan memori permanen.

## Response dan penanganan status

`/run`: `request_id`, `task`, `reference_id`, `status`, `summary`, `result`,
`precheck`, `tool_trace`, `requires_approval`, `error`.

`/chat`: `session_id`, `turn_index`, `status`, `answer`, `verified_result`,
`precheck`, `tool_trace`, `requires_approval`, `error`.

- `answer` adalah teks generatif yang bisa keliru. Gunakan `result` atau
  `verified_result` sebagai sumber fakta terverifikasi.
- `status=draft` bukan persetujuan PO; `review_required` bukan putusan fraud.
- Tangani `not_configured`, `model_unavailable`, `needs_tool_use`, 401, 422,
  timeout, dan 502/503/504 tanpa auto-approve.
- Semua tindakan bisnis (kirim supplier email, perubahan PO, pembayaran,
  persetujuan) harus dilakukan sistem terpisah setelah human approval.

## Data Backend yang diperlukan Agent dalam mode http

`AGENT_DATA_MODE=http`, `PROCUREMENT_BACKEND_URL` dan
`PROCUREMENT_SERVICE_TOKEN` hanya server-side. Gunakan HTTPS di luar localhost.

| Metode | Path backend | Bentuk minimum |
|---|---|---|
| GET | `/api/v1/procurement/pos/{po_id}` | object PO |
| GET | `/api/v1/procurement/suppliers/{supplier_id}` | object supplier |
| GET | `/api/v1/procurement/suppliers/{supplier_id}/invoices` | array atau `{"items": [...]}` |

PO: `po_id`, `supplier_id`, `product_id`, `quantity`, `offered_unit_price`,
`budget_ceiling_unit`, `previous_unit_price`, `currency`, `required_delivery_date`.
Supplier: `supplier_id`, `name`, `bank_last_changed_at` (nullable).
Invoice: `record_id`, `invoice_number`, `supplier_id`, `po_id`, `product_id`,
`amount`, `unit_price`, `invoice_date`.
Lakukan validasi nilai uang/tanggal; contoh sekarang hanya IDR dan mock data.

## Wajib dicek oleh Backend sebelum produksi (P0)

1. Autentikasi pengguna + RBAC pengadaan + hak baca PO dan invoice.
2. `session_id` harus terikat ke user dan PO; tolak cross-user/cross-tenant.
3. Audit log non-sensitif, request limits, rate limits, secret rotation.
4. Approval workflow berbasis identitas dan log kejadian.
5. Integrasi dengan endpoint backend asli harus diuji di staging, termasuk
   401/403, tidak ada data, timeout, dan anomali data.

Session Agent saat ini `InMemorySaver` untuk demo satu worker; restart menghapus
memori, bukan penyimpanan permanen. Jangan klaim production-ready.
