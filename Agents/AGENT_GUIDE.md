# ProcureGuard Agents — MVP Tim

MVP ini hanya menambahkan modul `Agents/` dan tidak mengubah folder `Backend/` atau `Frontend/` milik tim.

## Persyaratan
Python 3.11+, Git; Node.js jika ingin menggunakan MCP Inspector.

## Instalasi (PowerShell, dari folder Agents)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r agent_requirements.txt
```

## Demo lokal (tanpa database atau LLM)

```powershell
python -m unittest discover -s tests -v
python -m scripts.demo_agent_core
```

## Jalankan server MCP (SDK v2)

```powershell
mcp dev agent_core/mcp_server.py
```

Alternatif host MCP lokal adalah `python -m agent_core.mcp_server` (stdio, diam menunggu request).

## Jalankan API untuk frontend

```powershell
uvicorn agent_core.graph_api:app --reload --port 8001
```

Buka http://127.0.0.1:8001/docs ; endpoint POST `/api/v1/agents/run` menerima:

```json
{"task":"negotiation","reference_id":"PO-001"}
```

atau

```json
{"task":"fraud","reference_id":"SUP-001"}
```

## Jalankan LLM Agent (opsional)

Gunakan model yang mendukung OpenAI-compatible chat tool calling. Atur env dalam PowerShell (jangan tempel API key di chat atau commit):

```powershell
$env:LLM_API_KEY="<YOUR_API_KEY>"
$env:LLM_MODEL="<YOUR_TOOL_CALLING_MODEL>"
# $env:LLM_BASE_URL="<PROVIDER_API_BASE_URL>"
python -m agent_core.llm_agent "Tolong susun strategi negosiasi untuk PO-001"
```

LLM Agent menggunakan MCP Client in-memory untuk memanggil tiga tools MCP; tidak memerlukan server HTTP atau stdio terpisah.

## Kontrak integrasi tim

- DB teammate: implementasikan `ProcurementProvider` (get_po/get_supplier/get_invoices) yang sesuai. Data sensitif tidak diberikan penuh ke LLM.
- Frontend teammate: kirim permintaan ke Backend tim; Backend memverifikasi pengguna/hak akses PO/sesi lalu meneruskan ke Agent API melalui Bearer service. Tampilkan evidence dan permintaan human approval, bukan keputusan otomatis.
- Agent teammate: jaga nama tools, bentuk output JSON, tests, dan approval gate.

## Batasan saat ini

- Mock data; belum membaca MySQL.
- Agent LLM hanya berfungsi setelah API key dan model dipasang.
- Fraud scanner adalah aturan pemeriksaan, bukan klasifikasi hukum/putusan fraud.
- Tidak ada fungsi mengirim email, mengubah PO, atau mengeksekusi pembayaran.
- Autentikasi Bearer service-to-service tersedia di API Stage 6; otorisasi pengguna/PO/sesi end-to-end, rate limiting, persistent audit log, serta pengujian cloud belum terverifikasi.
- Untuk integrasi produksi, wajib tambah identitas pengguna, RBAC, persistence, audit, approval workflow, dan prompt-injection safeguards.

## Referensi
- https://py.sdk.modelcontextprotocol.io/

## Status API saat ini (Stage 7)

Jalankan dari folder `Agents/` (bukan API lama `agent_core.api`). Pastikan environment
`AGENT_API_KEY` ada; untuk chat nyata tambahkan `LLM_API_KEY`, `LLM_MODEL`,
`LLM_BASE_URL`, dan `LLM_TIMEOUT_SECONDS`. Jangan tulis API key dalam kode atau history.

```powershell
$env:AGENT_DATA_MODE='mock'
$env:AGENT_API_KEY='TOKEN_SERVICE_LOKAL_GANTI_SENDIRI'
$env:LLM_MODEL='gemini-3.5-flash-lite'
$env:LLM_BASE_URL='https://generativelanguage.googleapis.com/v1beta/openai/'
$env:LLM_TIMEOUT_SECONDS='90'
$secure=Read-Host 'Masukkan Gemini API Key' -AsSecureString
$env:LLM_API_KEY=[System.Net.NetworkCredential]::new('', $secure).Password
Remove-Variable secure
.\.venv\Scripts\python.exe -m uvicorn agent_core.graph_api:app --host 127.0.0.1 --port 8001
```

Endpoint yang digunakan Backend: `GET /health`, `POST /api/v1/agents/run`,
`POST /api/v1/agents/chat`. Keduanya mewajibkan `Authorization: Bearer <AGENT_API_KEY>`.
`/run` untuk negosiasi atau fraud deterministik, `/chat` untuk LLM dengan `session_id`.
Jangan memanggil Agent langsung dari browser; Backend wajib memverifikasi pengguna,
hak atas PO, dan kepemilikan session sebelum proxy. Agent tidak menyetujui PO,
mengirim email, mengeksekusi pembayaran, atau mengubah transaksi. Hasil masih mock.

Lihat `docs/INTEGRATION_CONTRACT.md`, `docs/STAGE6_AGENT_API.md`, dan
`docs/STAGE7_BACKEND_HANDOFF.md`.
