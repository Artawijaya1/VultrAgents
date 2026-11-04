# ProcureGuard AI

**AI Negotiation Copilot + Procurement Fraud Detection Agent (MCP prototype).**

Ini adalah **starter project / proof of concept**, bukan sistem ERP atau sistem fraud produksi. MCP Tools sudah terdaftar dalam `backend/mcp_server/server.py`, dan engine aturan berbasis data sintetis dapat diuji tanpa API key. Integrasi LLM, akses database MySQL aktual, frontend, autentikasi, audit permanen, investigasi, dan email outbound **belum diimplementasikan**. Jangan deploy endpoint demo ke internet.

## Prasyarat
- Python 3.11+ dan pip/uv
- Node.js + npm/npx untuk MCP Inspector
- MySQL 8.x (opsional, skema disediakan; demo tidak mengakses MySQL)

Dokumentasi MCP Python SDK v2: https://py.sdk.modelcontextprotocol.io/v2/

## Jalankan dari root proyek

Windows PowerShell:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m scripts.demo
mcp dev backend/mcp_server/server.py
```

Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m unittest discover -s tests -v
python -m scripts.demo
mcp dev backend/mcp_server/server.py
```

Di MCP Inspector, panggil:
- `get_purchase_order(po_number="PO-001")`
- `draft_negotiation(po_number="PO-001")`
- `scan_procurement_anomalies()`
- `list_suppliers()`
- `get_approval_status(approval_id="APR-001")`

Contoh Resource: `procurement://policies/default`; Prompt: `prepare_negotiation`.

API demo tanpa autentikasi (**localhost saja**):
```bash
uvicorn backend.api.main:app --host 127.0.0.1 --port 8001
```
- http://127.0.0.1:8001/health
- http://127.0.0.1:8001/demo/negotiations/PO-001
- http://127.0.0.1:8001/demo/fraud/scan

## Skema MySQL untuk tahap integrasi

Salin `.env.example` menjadi `.env` lalu **ganti semua password placeholder**. Untuk database lokal kosong, gunakan `docker compose up -d mysql`. Saat volume MySQL pertama kali dibuat, `schema.sql` dan `seed.sql` akan dijalankan otomatis. Database saat ini **tidak dihubungkan dengan tools demo**: ubah repository setelah akses pengguna, audit, dan validasi disiapkan.

## Aturan desain yang tidak boleh dilanggar
- Draf negosiasi tidak sama dengan persetujuan atau pengiriman email.
- Anomali harga/invoice tidak membuktikan fraud: perlu investigasi oleh manusia.
- Semua tindakan berdampak harus diautentikasi, diotorisasi, dicatat, dan disetujui.
- Jangan izinkan LLM membuat SQL mentah, mengeksekusi pembayaran, atau mengubah rekening supplier.
- Verifikasi perubahan rekening melalui kanal independen, bukan hanya email perubahan tersebut.
- Simpan fingerprint/reference rekening dengan kebijakan retensi dan enkripsi; jangan expose nomor rekening mentah ke AI.

## Roadmap implementasi nyata
1. Database & repository queries hanya-baca dengan scope pengguna.
2. Autentikasi JWT/OAuth, RBAC per tool, audit trail permanen.
3. LLM agent orchestrator dengan batas panggilan tools & prompt injection guard.
4. Negotiation sessions bertahap + draft email + human approval.
5. Fraud alert persistence, case review, human resolution + false-positive tracking.
6. Frontend React + uji integrasi/security + deployment.

Lihat `docs/` untuk kontrak tools, arsitektur, aturan bisnis, dan ancaman keamanan.
