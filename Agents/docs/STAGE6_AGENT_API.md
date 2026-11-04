# ProcureGuard AI — Tahap 6: LLM, LangGraph memory, dan PO-scoped fraud

## Ruang lingkup

Hanya folder `VultrAgents/Agents/`; **tidak mengubah** `Backend/`, `Frontend/`, atau skema database. `graph_api.py` adalah API *layanan Agent*, bukan backend aplikasi milik anggota tim.

## Endpoint lama (kompatibel)

`POST /api/v1/agents/run` dengan `Authorization: Bearer <AGENT_API_KEY>`.

- Negotiation berdasarkan PO tetap seperti sebelumnya: `{"task":"negotiation","reference_id":"PO-001"}`.
- Fraud berdasarkan supplier masih didukung: `{"task":"fraud","reference_id":"SUP-001"}`.
- **Baru:** Fraud berdasarkan PO: `{"task":"fraud","reference_id":"PO-001","reference_type":"po"}`.
- Precheck pada Negotiation sekarang **terbatas ke PO yang sama**, bukan seluruh supplier.

## Endpoint baru: percakapan berbasis LLM

`POST /api/v1/agents/chat`, wajib header `Authorization: Bearer <AGENT_API_KEY>`:

```json
{
  "task": "negotiation",
  "reference_id": "PO-001",
  "session_id": "demo-session-001",
  "question": "Susun langkah negosiasi berikutnya. Berapa batas anggarannya?"
}
```

Untuk Fraud ubah `task` menjadi `fraud` dan tetap gunakan `reference_id: "PO-001"`.

Respons berisi `session_id`, `turn_index`, `summary`, `answer` (teks LLM, **tidak terverifikasi secara numerik**), `verified_result` (hasil MCP sebenarnya), `precheck`, `tool_trace`, dan `requires_approval: true`.

- **Jangan tampilkan `answer` sebagai harga atau bukti final** tanpa memeriksa `verified_result`.
- Selalu gunakan `session_id` yang **unik untuk setiap pengguna dan alur**. Backend milik anggota tim harus mengautentikasi pengguna dan memeriksa kepemilikan sesi. Shared bearer token ini hanya autentikasi *service*, bukan autentikasi per pengguna.
- Memori sesi memakai `InMemorySaver` (demo). Restart server menghapus memori; jangan deploy dalam banyak worker atau menyimpan data sensitif. Gunakan persistent checkpoint terisolasi + TTL + otorisasi per pengguna sebelum produksi.
- Semua tools read-only; LLM tidak bisa mengubah PO, mengirim email, atau menyetujui pembayaran. Output adalah draf dan indikasi untuk ditinjau manusia.
- Tool model dibatasi ke PO yang diminta (cross-PO call ditolak). Pembatasan ini tidak menggantikan pengecekan akses PO oleh backend.
- Jika model tidak mengakses tool analisis yang diwajibkan, respons `needs_tool_use`, **bukan** jawaban yang seolah terverifikasi.
- Tanpa `LLM_API_KEY` dan `LLM_MODEL`, endpoint `/chat` mengembalikan `not_configured`; `/run` tetap berfungsi tanpa biaya model.

## Contoh menjalankan dari PowerShell

Terminal pertama, root `VultrAgents\Agents`:

```powershell
$env:AGENT_DATA_MODE="mock"
$env:AGENT_API_KEY="ganti-ke-secret-lokal-baru"
$secure=Read-Host 'Masukkan Gemini API Key' -AsSecureString
$env:LLM_API_KEY=[System.Net.NetworkCredential]::new('', $secure).Password
Remove-Variable secure
$env:LLM_MODEL="nama-model-yang-mendukung-tool-calling"
# Opsional bila provider OpenAI-compatible lain:
# $env:LLM_BASE_URL="https://alamat-provider/v1"
.\.venv\Scripts\python.exe -m uvicorn agent_core.graph_api:app --host 127.0.0.1 --port 8001
```

Terminal kedua:

```powershell
$headers=@{ Authorization = "Bearer ganti-ke-secret-lokal-baru" }
$body=@{ task="negotiation"; reference_id="PO-001"; session_id="demo-001"; question="Buat opsi penawaran baru" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/agents/chat" -Headers $headers -ContentType "application/json" -Method POST -Body $body | ConvertTo-Json -Depth 12
```

Ganti `question` tetapi gunakan `session_id` yang sama untuk menguji putaran kedua dan melihat `turn_index` bertambah. Tes offline otomatis memakai fake LLM (tidak butuh API key sungguhan).

## Kebutuhan backend teman

Sesuai `docs/INTEGRATION_CONTRACT.md`, backend harus menyediakan data PO, supplier, invoice. API Agent tidak mengakses database langsung. Beri tahu rekan backend bahwa `/run` sekarang mendukung fraud PO (`reference_type=po`) dan `/chat` memakai `session_id` + `question`.

## Batasan & keamanan

- Teks `answer` dari LLM berpotensi salah meski ditambatkan ke tools; referensi ke `verified_result` untuk angka/bukti.
- Simpan API key di environment, bukan source code/Swagger/JavaScript frontend.
- `localhost` hanya dapat diakses pada komputer yang sama. Untuk integrasi antar komputer, gunakan HTTPS dan otorisasi service-to-service serta atur firewall, tanpa mengekspos server secara publik sekarang.
- Gemini 3.5 Flash-Lite telah diuji berhasil pada laptop pengembang (mock data, tool calling, dan dua putaran memori); pengujian endpoint/cloud produksi belum dilakukan.
- Sebelum GitHub: pastikan `.gitignore` melarang `.venv/`, `.env`, file key/token, serta backup/hasil ekstraksi.

## Catatan pengujian lokal Stage 7 (2026-11-04)

Konfigurasi yang berhasil pada mock data: `LLM_MODEL=gemini-3.5-flash-lite`,
`LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`,
dan `LLM_TIMEOUT_SECONDS=90` (opsional, dibaca dari kode Agent).
Pengujian mencakup 41 unit test, pemanggilan MCP, peninjauan fraud PO,
dua turn percakapan, dan mengingat dua prioritas non-MCP pada satu sesi.
Hal ini **tidak** memvalidasi integrasi Backend tim atau keamanan produksi.
`InMemorySaver` hilang saat restart dan belum mendukung multi-worker produksi.
HTTP 400 dari direct probe pada audit berikutnya harus didiagnosis menggunakan
body error Google, bukan langsung dianggap sebagai perubahan kode Agent.
