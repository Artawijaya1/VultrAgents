#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ProcureGuard - safe Stage 7 batch remediation (Agents only).

Usage from VultrAgents/Agents:
  .\\.venv\\Scripts\\python.exe .\\scripts\\procureguard_stage7_batch_repair.py --apply --quick
  .\\.venv\\Scripts\\python.exe .\\scripts\\procureguard_stage7_batch_repair.py --apply --offline
  .\\.venv\\Scripts\\python.exe .\\scripts\\procureguard_stage7_batch_repair.py

No edits without --apply. No Git staging/commit/push, no Backend/Frontend edits,
no external purchasing actions. A full local backup is created before modifying.
The script does NOT claim to fix external backend authorization or persistence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import uuid

ROOT = Path(__file__).resolve().parent.parent
PREPARED: dict[str, bytes] = {}
NOTES: list[str] = []


def note(message: str) -> None:
    NOTES.append(message)
    print(message, flush=True)


def read_text(relative: str) -> str | None:
    file = ROOT / relative
    if not file.exists():
        note(f'[SKIP] File tidak ada: {relative}')
        return None
    return file.read_text(encoding='utf-8-sig')


def queue_text(relative: str, content: str) -> None:
    file = ROOT / relative
    if file.exists():
        before = file.read_bytes()
        after = content.encode('utf-8')
        if before == after:
            note(f'[OK] Tanpa perubahan: {relative}')
            return
    PREPARED[relative] = content.encode('utf-8')
    note(f'[RENCANA] Perbarui {relative}')


def set_doc_once(relative: str, content: str) -> None:
    if (ROOT / relative).exists():
        note(f'[OK] Dokumen handoff sudah ada, tidak ditimpa: {relative}')
        return
    queue_text(relative, content)


def patch_guide() -> None:
    relative = 'AGENT_GUIDE.md'
    old = read_text(relative)
    if old is None:
        return
    content = old
    replacements = [
        ('uvicorn agent_core.api:app', 'uvicorn agent_core.graph_api:app'),
        ('`/api/agents/execute`', '`/api/v1/agents/run`'),
        ('`/api/agents/chat`', '`/api/v1/agents/chat`'),
        ('POST `/api/agents/execute`', 'POST `/api/v1/agents/run`'),
        ('Frontend teammate: POST `/api/v1/agents/run` atau `/api/v1/agents/chat` lalu tampilkan hasil dan bukti, tidak langsung menyetujui atau mengirim.',
         'Frontend teammate: kirim permintaan ke Backend tim; Backend memverifikasi pengguna/hak akses PO/sesi lalu meneruskan ke Agent API melalui Bearer service. Tampilkan evidence dan permintaan human approval, bukan keputusan otomatis.'),
        ('Belum ada autentikasi API, rate limiting, persistent audit log, atau pengujian MCP end-to-end ke cloud.',
         'Autentikasi Bearer service-to-service tersedia di API Stage 6; otorisasi pengguna/PO/sesi end-to-end, rate limiting, persistent audit log, serta pengujian cloud belum terverifikasi.'),
        ('belum ada autentikasi API', 'belum ada otorisasi pengguna/PO/sesi end-to-end'),
    ]
    for source, target in replacements:
        content = content.replace(source, target)
    if '## Status API saat ini (Stage 7)' not in content:
        stage7 = """\n## Status API saat ini (Stage 7)\n\nJalankan dari folder `Agents/` (bukan API lama `agent_core.api`). Pastikan environment\n`AGENT_API_KEY` ada; untuk chat nyata tambahkan `LLM_API_KEY`, `LLM_MODEL`,\n`LLM_BASE_URL`, dan `LLM_TIMEOUT_SECONDS`. Jangan tulis API key dalam kode atau history.\n\n```powershell\n$env:AGENT_DATA_MODE='mock'\n$env:AGENT_API_KEY='TOKEN_SERVICE_LOKAL_GANTI_SENDIRI'\n$env:LLM_MODEL='gemini-3.5-flash-lite'\n$env:LLM_BASE_URL='https://generativelanguage.googleapis.com/v1beta/openai/'\n$env:LLM_TIMEOUT_SECONDS='90'\n$secure=Read-Host 'Masukkan Gemini API Key' -AsSecureString\n$env:LLM_API_KEY=[System.Net.NetworkCredential]::new('', $secure).Password\nRemove-Variable secure\n.\\.venv\\Scripts\\python.exe -m uvicorn agent_core.graph_api:app --host 127.0.0.1 --port 8001\n```\n\nEndpoint yang digunakan Backend: `GET /health`, `POST /api/v1/agents/run`,\n`POST /api/v1/agents/chat`. Keduanya mewajibkan `Authorization: Bearer <AGENT_API_KEY>`.\n`/run` untuk negosiasi atau fraud deterministik, `/chat` untuk LLM dengan `session_id`.\nJangan memanggil Agent langsung dari browser; Backend wajib memverifikasi pengguna,\nhak atas PO, dan kepemilikan session sebelum proxy. Agent tidak menyetujui PO,\nmengirim email, mengeksekusi pembayaran, atau mengubah transaksi. Hasil masih mock.\n\nLihat `docs/INTEGRATION_CONTRACT.md`, `docs/STAGE6_AGENT_API.md`, dan\n`docs/STAGE7_BACKEND_HANDOFF.md`.\n"""
        content = content.rstrip() + '\n' + stage7
    if content != old:
        queue_text(relative, content)
    else:
        note('[OK] Panduan utama telah sinkron')


def patch_contract() -> None:
    relative = 'docs/INTEGRATION_CONTRACT.md'
    old = read_text(relative)
    if old is None:
        return
    appendix = """\n## E. Penambahan Stage 6/7: PO fraud, chat, dan kepemilikan\n\n### `POST /api/v1/agents/run`\n\nGunakan `task` bernilai `negotiation` atau `fraud`, dan `reference_id`.\nUntuk pemeriksaan fraud khusus PO, **wajib** gunakan `reference_type: \"po\"`:\n\n```json\n{\n  "task": "fraud",\n  "reference_id": "PO-001",\n  "reference_type": "po",\n  "instruction": "Periksa invoice duplikat dan perubahan rekening terkait PO ini"\n}\n```\n\nUntuk fraud supplier, gunakan `reference_type: \"supplier\"` jika didukung\noleh kontrak runtime; pastikan melalui `/openapi.json` sebelum mengirim.\nPeriksa `result`, `precheck`, `tool_trace`, `requires_approval`, serta `status`.\n`review_required` adalah indikator perlu review, **bukan** vonis kecurangan.\n\n### `POST /api/v1/agents/chat`\n\n```json\n{\n  "task": "negotiation",\n  "reference_id": "PO-001",\n  "session_id": "user-scoped-session-001",\n  "question": "Susun strategi negosiasi sesuai anggaran"\n}\n```\n\nField chat: `task`, `reference_id`, `session_id`, `question`.\nRespons chat: `session_id`, `turn_index`, `status`, `answer`,\n`verified_result`, `precheck`, `tool_trace`, `requires_approval`, `error`.\nTeks `answer` adalah saran LLM, **bukan** evidence final; gunakan `verified_result`\nuntuk fakta transaksi. Klien wajib menangani `draft`, `review_required`,\n`model_unavailable`, `needs_tool_use`, `not_configured`, dan kesalahan HTTP.\n\n### Tanggung jawab otorisasi Backend (P0)\n\nBearer `AGENT_API_KEY` hanya identitas layanan. **Sebelum meneruskan request**,\nBackend harus memvalidasi identitas pengguna, RBAC procurement, kepemilikan\n`reference_id`/PO, izin akses supplier/invoice, dan `session_id` milik pengguna.\nKunci `session_id` dengan identitas pengguna di backend; jangan menerima ID\nsesi pelanggan lain begitu saja. Jangan mengirim service token ke frontend.\nSementara tidak ada otorisasi pengguna end-to-end, Agent hanya untuk demo\nterisolasi pada `127.0.0.1`, bukan endpoint publik.\n\n### Integrasi asli masih menunggu validasi\n\nPengujian sekarang menggunakan mock provider atau HTTP MockTransport, **bukan**\nAPI Backend asli. Untuk staging, gunakan `AGENT_DATA_MODE=http`,\n`PROCUREMENT_BACKEND_URL=https://...`, `PROCUREMENT_SERVICE_TOKEN` yang aman,\nlalu uji PO yang diizinkan, PO yang ditolak, respons kosong, timeout, dan data\ninvoicing yang sesuai schema. Verifikasi model dan source berdasarkan runtime\n`GET /openapi.json`, bukan snapshot yang mungkin usang.\n"""
    if '## E. Penambahan Stage 6/7:' not in old:
        queue_text(relative, old.rstrip() + '\n' + appendix)
    else:
        note('[OK] Kontrak Stage 6/7 sudah tercatat')


def patch_stage6_doc() -> None:
    relative = 'docs/STAGE6_AGENT_API.md'
    old = read_text(relative)
    if old is None:
        return
    content = old
    content = content.replace('Contoh model belum diuji terhadap penyedia LLM nyata; pengujian offline memakai fake model.',
        'Gemini 3.5 Flash-Lite telah diuji berhasil pada laptop pengembang (mock data, tool calling, dan dua putaran memori); pengujian endpoint/cloud produksi belum dilakukan.')
    content = content.replace('Contoh model belum diuji terhadap penyedia LLM nyata',
        'Gemini 3.5 Flash-Lite telah diuji lokal dengan penyedia nyata')
    content = content.replace('$env:LLM_API_KEY="kunci-model-kamu"  # JANGAN bagikan atau commit',
        "$secure=Read-Host 'Masukkan Gemini API Key' -AsSecureString\n$env:LLM_API_KEY=[System.Net.NetworkCredential]::new('', $secure).Password\nRemove-Variable secure")
    if 'LLM_TIMEOUT_SECONDS' not in content:
        content += """\n## Catatan pengujian lokal Stage 7 (2026-11-04)\n\nKonfigurasi yang berhasil pada mock data: `LLM_MODEL=gemini-3.5-flash-lite`,\n`LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`,\ndan `LLM_TIMEOUT_SECONDS=90` (opsional, dibaca dari kode Agent).\nPengujian mencakup 41 unit test, pemanggilan MCP, peninjauan fraud PO,\ndua turn percakapan, dan mengingat dua prioritas non-MCP pada satu sesi.\nHal ini **tidak** memvalidasi integrasi Backend tim atau keamanan produksi.\n`InMemorySaver` hilang saat restart dan belum mendukung multi-worker produksi.\nHTTP 400 dari direct probe pada audit berikutnya harus didiagnosis menggunakan\nbody error Google, bukan langsung dianggap sebagai perubahan kode Agent.\n"""
    if content != old:
        queue_text(relative, content)
    else:
        note('[OK] Dokumentasi Stage 6 sudah relevan')


def refresh_openapi() -> None:
    relative = 'docs/agent-openapi.json'
    # Prefer runtime spec to ensure all current fields and endpoints are correct.
    try:
        sys.path.insert(0, str(ROOT))
        sys.dont_write_bytecode = True
        from agent_core.graph_api import app
        spec = app.openapi()
        required = {'/health', '/api/v1/agents/run', '/api/v1/agents/chat'}
        if not required.issubset(set(spec.get('paths', {}))):
            note('[WARN] Runtime OpenAPI tidak memuat semua path; tidak menimpa snapshot')
            return
        queue_text(relative, json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
        note('[OK] OpenAPI diperbarui dari FastAPI runtime tanpa UTF-8 BOM')
    except Exception as exc:
        note(f'[WARN] Tidak dapat import FastAPI runtime: {type(exc).__name__} (fallback normalisasi JSON)')
        old = read_text(relative)
        if old is None:
            return
        try:
            spec = json.loads(old)
        except json.JSONDecodeError as error:
            note(f'[WARN] JSON snapshot tidak valid: {error}')
            return
        queue_text(relative, json.dumps(spec, ensure_ascii=False, indent=2) + '\n')


def patch_auditor() -> None:
    relative = 'scripts/procureguard_stage7_audit.py'
    old = read_text(relative)
    if old is None:
        return
    content = old
    # Previously tested standalone probe used one-word SIAP. Low effort is
    # supported by Google's OpenAI-compatible endpoint and can reduce latency.
    original = "model=env['LLM_MODEL'], messages=[{'role': 'user', 'content': 'Balas tepat: SIAP'}])"
    replacement = "model=env['LLM_MODEL'],\n            messages=[{'role': 'user', 'content': 'Balas tepat satu kata: SIAP'}],\n            reasoning_effort='low')"
    if original in content:
        content = content.replace(original, replacement, 1)
    elif "reasoning_effort='low'" not in content:
        note('[WARN] Bentuk probe Gemini berbeda; tidak diubah secara spekulatif')
    original_except = """    except Exception as exc:
        check('7D', 'Gemini API live', 'FAIL', f'{type(exc).__name__}: {redact(exc)}',
              'P0', 'Pisahkan masalah jaringan, akses model, dan token sebelum mengubah LangGraph.')
        return False
"""
    improved_except = """    except Exception as exc:
        # Record the provider's diagnostic message, without printing any secret.
        # 400 could mean model/parameter issue; do not report as Agent logic bug.
        raw = getattr(exc, 'body', None)
        if not raw:
            response = getattr(exc, 'response', None)
            try:
                raw = response.text if response is not None else None
            except Exception:
                raw = None
        detail = redact(str(raw) if raw else str(exc), 900)
        check('7D', 'Gemini API live', 'FAIL', f'{type(exc).__name__}: {detail}',
              'P0', 'Periksa error.status/error.message Google, kuota, model, dan parameter; '
                    'model dan tool Agent sebelumnya telah lulus tes lokal.')
        return False
"""
    if original_except in content:
        content = content.replace(original_except, improved_except, 1)
    elif 'Record the provider\'s diagnostic message' not in content:
        note('[WARN] Blok exception Gemini tidak cocok; tidak diubah secara spekulatif')
    if content != old:
        try:
            compile(content, relative, 'exec')
        except SyntaxError as exc:
            note(f'[FAIL] Auditor hasil patch tidak valid: {exc}; file auditor tidak ditimpa')
            return
        queue_text(relative, content)
    else:
        note('[OK] Auditor Stage 7 sudah sinkron')


HANDOFF = """# ProcureGuard AI — Serah-terima kontrak Backend ↔ Agents (Stage 7)

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
.\\.venv\\Scripts\\python.exe -m uvicorn agent_core.graph_api:app --host 127.0.0.1 --port 8001
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
| GET | `/api/v1/procurement/suppliers/{supplier_id}/invoices` | array atau `{\"items\": [...]}` |

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
"""


REMAINING = """# ProcureGuard Stage 7 — Pekerjaan terbuka setelah batch perbaikan

DOKUMEN INI ADALAH DAFTAR RISIKO DAN DEPENDENSI, BUKAN DAFTAR YANG SUDAH FIX.

| Prioritas | Temuan | Owner / syarat penutupan |
|---|---|---|
| P0 | Akses PO/sesi per pengguna belum ditegakkan oleh Agent service Bearer | Backend: login, RBAC, hak akses PO/session di proxy; tes negatif cross-user |
| P0 | Gemini direct probe menerima HTTP 400 dalam satu audit | Diagnostik body error provider dan uji ulang live setelah pembaruan probe; jangan berasumsi root cause |
| P1 | Backend asli belum diuji | Tim Backend + Agent: test mode http dengan data staging |
| P1 | Memori `InMemorySaver` tidak persisten | Pakai persistent checkpoint, session binding, TTL hanya bila deployment memerlukannya |
| P1 | Secret scan hanya mendeteksi pola standar | Audit histori Git, file lain, dan rotasi Google key lama secara manual |
| P2 | Contoh LAPTOP-01 Rp150.000 tidak realistis | Beri label DATA SIMULASI; buat contoh realistis setelah validasi test fixtures |

Pengujian lokal sebelumnya telah menghasilkan 41 unit test PASS dan memori
2 putaran yang mengingat 2 preferensi user. Hasil ini tidak membuktikan
keamanan pengguna, integrasi data asli, atau keandalan model di produksi.

Tindakan batch ini sengaja TIDAK mengubah `agent_core/` atau test fixture.
Hindari auto-fix pada security/auth dan provider schema tanpa kontrak tim.
"""


def prepare_changes() -> None:
    patch_guide()
    patch_contract()
    patch_stage6_doc()
    refresh_openapi()
    patch_auditor()
    set_doc_once('docs/STAGE7_BACKEND_HANDOFF.md', HANDOFF)
    set_doc_once('docs/STAGE7_REMAINING_RISKS.md', REMAINING)


def check_root() -> None:
    required = [ROOT / 'agent_core' / 'graph_api.py', ROOT / 'agent_core' / 'intelligent_graph.py']
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise SystemExit('Folder tidak tepat / Stage 6 belum terpasang. Missing: ' + str(missing))


def commit_changes(folder: Path) -> None:
    backups = folder / 'backup_original'
    backups.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    for relative in PREPARED:
        file = ROOT / relative
        if file.exists():
            dest = backups / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, dest)
            manifest.append({'file': relative, 'existed_before': True})
        else:
            manifest.append({'file': relative, 'existed_before': False})
    (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    changed: list[tuple[Path, bool, Path]] = []
    try:
        for data in manifest:
            relative = data['file']
            target = ROOT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='wb', prefix='.stage7-', suffix='.tmp',
                                             dir=target.parent, delete=False) as temp:
                temp.write(PREPARED[relative])
                temp_path = Path(temp.name)
            try:
                os.replace(temp_path, target)
                changed.append((target, data['existed_before'], backups / relative))
                note(f'[DITERAPKAN] {relative}')
            finally:
                if temp_path.exists():
                    temp_path.unlink()
    except Exception:
        for target, existed, backup in reversed(changed):
            if existed:
                shutil.copy2(backup, target)
            elif target.exists():
                target.unlink()
        raise


def run_audit(offline: bool, quick: bool, folder: Path) -> int:
    auditor = ROOT / 'scripts' / 'procureguard_stage7_audit.py'
    if not auditor.is_file():
        note('[WARN] Auditor asli tidak ditemukan; verifikasi otomatis dilewati')
        return 0
    cmd = [sys.executable, str(auditor)]
    if offline:
        cmd.append('--offline')
    elif quick:
        cmd.append('--quick')
    note('\n=== PENGUJIAN ULANG STAGE 7 ===')
    note('Perhatian: audit live akan meminta API key tersembunyi jika belum tersedia di sesi ini.')
    try:
        proc = subprocess.run(cmd, cwd=ROOT, env=os.environ.copy(), check=False)
        return proc.returncode
    except KeyboardInterrupt:
        note('[WARN] Audit dibatalkan pengguna; perubahan dokumentasi tetap disimpan dengan backup')
        return 130


def main() -> int:
    parser = argparse.ArgumentParser(description='Stage 7 batch patch - safe Agents-only docs/contract/audit')
    parser.add_argument('--apply', action='store_true', help='Terapkan semua perubahan aman dalam satu batch')
    parser.add_argument('--offline', action='store_true', help='Audit tanpa Gemini')
    parser.add_argument('--quick', action='store_true', help='Audit Gemini satu putaran saja')
    parser.add_argument('--no-audit', action='store_true', help='Hanya terapkan batch tanpa menjalankan auditor')
    args = parser.parse_args()
    check_root()
    folder = Path(tempfile.mkdtemp(prefix='procureguard_stage7_batch_'))
    note('ProcureGuard Stage 7 — Batch Remediation (tanpa commit/push)')
    note(f'Root: {ROOT}')
    note(f'Laporan/backup lokal: {folder}')
    prepare_changes()
    if not PREPARED:
        note('[PASS] Tidak ada perubahan baru; patch sudah terpasang')
    elif args.apply:
        commit_changes(folder)
        note(f'[PASS] {len(PREPARED)} file diterapkan; backup tersedia')
    else:
        note('[DRY RUN] Belum mengubah file. Tambahkan --apply untuk menerapkan sekaligus.')
        return 0
    (folder / 'perubahan.txt').write_text('\n'.join(NOTES) + '\n', encoding='utf-8')
    if args.no_audit:
        note('[INFO] Audit tidak dijalankan karena --no-audit')
        return 0
    rc = run_audit(args.offline, args.quick, folder)
    note(f'\n[SELESAI] Exit code auditor: {rc}. Backup batch: {folder / "backup_original"}')
    note('Temuan backend/produksi yang belum terselesaikan ada di docs/STAGE7_REMAINING_RISKS.md')
    note('Tidak ada git add, commit, push, atau perubahan Backend/Frontend.')
    return rc


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'[FATAL] {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(2)
