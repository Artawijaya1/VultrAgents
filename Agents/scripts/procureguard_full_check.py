r"""One-command local smoke/E2E checker for ProcureGuard AI Stage 6.

Copy to VultrAgents/Agents/scripts/procureguard_full_check.py and run from Agents:
  .\.venv\Scripts\python.exe .\scripts\procureguard_full_check.py

Options:
  --offline   Run unit tests and local authenticated Fraud API, without a Gemini call.
  --quick     Run one Gemini chat turn instead of two.

No files in the repository are modified. The local FastAPI server is started on an
available loopback port and stopped automatically. Temporary logs are placed under
Windows' TEMP directory. No API keys are written to reports or printed.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = "gemini-3.8-flash"
results = []


def record(label, state, detail=""):
    results.append({"check": label, "status": state, "detail": detail})
    tag = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}.get(state, state)
    print(f"{tag} {label}: {detail}", flush=True)


def redacted(message, keys):
    msg = str(message)
    for key in keys:
        if key:
            msg = msg.replace(key, "[REDACTED]")
    # Do not put exception request headers or raw tokenized URLs in reports.
    msg = re.sub(r"(?i)(Bearer\s+)\S+", r"\1[REDACTED]", msg)
    return msg[:600]


def request_json(base, route, token=None, payload=None, timeout=120):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        base + route, data=data, method="POST" if payload is not None else "GET", headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            return response.status, json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            body = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeError):
            body = {"detail": "non-JSON HTTP error"}
        return error.code, body


def free_local_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_units(keys):
    print("\n=== 1. UNIT TEST ===")
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT, capture_output=True, text=True, errors="replace", timeout=180,
    )
    combined = proc.stdout + "\n" + proc.stderr
    match = re.search(r"Ran\s+(\d+)\s+tests?", combined)
    count = int(match.group(1)) if match else 0
    skipped = re.search(r"skipped\s*=\s*(\d+)", combined)
    if proc.returncode == 0 and count >= 41 and not (skipped and int(skipped.group(1)) > 0):
        record("Unit test", "PASS", f"{count} tes; tanpa error atau skip")
    elif proc.returncode == 0 and count:
        record("Unit test", "WARN", f"{count} tes, cek apakah ada tes yang kurang atau skipped")
    else:
        record("Unit test", "FAIL", "Unit test gagal. Bagian akhir log:")
        print(redacted("\n".join(combined.splitlines()[-17:]), keys))


def test_gemini(env, keys):
    print("\n=== 2. GEMINI API (LIVE) ===")
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=env["LLM_API_KEY"],
            base_url=env["LLM_BASE_URL"],
            timeout=60.0,
            max_retries=0,
        )
        resp = client.chat.completions.create(
            model=env["LLM_MODEL"],
            messages=[{"role": "user", "content": "Balas tepat satu kata: SIAP"}],
        )
        msg = resp.choices[0].message.content or ""
        if msg.strip():
            record("Koneksi Gemini", "PASS", f"Model merespons: {msg.strip()[:80]}")
        else:
            record("Koneksi Gemini", "WARN", "Request diterima, tetapi jawaban teks kosong")
    except Exception as exc:
        record("Koneksi Gemini", "FAIL", redacted(exc, keys))


def spawn_server(env, folder, keys):
    print("\n=== 3. FASTAPI LOKAL ===")
    port = free_local_port()
    base = f"http://127.0.0.1:{port}"
    log_path = folder / "uvicorn.log"
    log_file = log_path.open("w", encoding="utf-8")
    args = [sys.executable, "-m", "uvicorn", "agent_core.graph_api:app",
            "--host", "127.0.0.1", "--port", str(port), "--no-access-log"]
    try:
        proc = subprocess.Popen(args, cwd=ROOT, env=env, stdout=log_file,
                                stderr=subprocess.STDOUT)
    except Exception:
        log_file.close()
        raise
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        try:
            code, info = request_json(base, "/health", timeout=2)
            if code == 200:
                record("FastAPI /health", "PASS", f"HTTP 200 di port sementara {port}")
                return proc, log_file, log_path, base
        except (OSError, ValueError):
            time.sleep(0.4)
    log_file.flush()
    text = log_path.read_text(encoding="utf-8", errors="replace")[-1200:]
    record("FastAPI /health", "FAIL", "Uvicorn gagal memulai. Cek log lokal.")
    if text:
        print(redacted(text, keys))
    return proc, log_file, log_path, None


def test_api(base, env, folder, quick, offline, keys):
    token = env["AGENT_API_KEY"]
    po = "PO-001"
    fraud_payload = {
        "task": "fraud", "reference_id": po, "reference_type": "po",
        "instruction": "Analisis risiko pengadaan pada PO-001",
    }
    try:
        code, _ = request_json(base, "/api/v1/agents/run", token="sengaja-salah", payload=fraud_payload)
        record("Penolakan token salah", "PASS" if code == 401 else "FAIL", f"HTTP {code}")
    except Exception as exc:
        record("Penolakan token salah", "FAIL", redacted(exc, keys))
    try:
        code, res = request_json(base, "/api/v1/agents/run", token=token, payload=fraud_payload)
        (folder / "fraud_po001.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
        data = res.get("result") or {}
        trace = [x.get("tool") for x in (res.get("tool_trace") or []) if isinstance(x, dict)]
        valid = (code == 200 and data.get("scope") == "purchase_order" and
                 data.get("po_id") == po and data.get("is_fraud_confirmed") is False and
                 data.get("requires_human_review") is True and
                 "scan_purchase_order_anomalies" in trace)
        record("Fraud berbasis PO", "PASS" if valid else "FAIL",
               f"HTTP {code}; status={res.get('status')}; flags={data.get('flag_count')}; tools={','.join(trace)}")
    except Exception as exc:
        record("Fraud berbasis PO", "FAIL", redacted(exc, keys))

    if offline:
        record("Gemini Agent & Memory", "SKIP", "Mode --offline: tidak ada panggilan Gemini")
        return

    session = "auto-check-" + uuid.uuid4().hex[:12]
    first = {
        "task": "negotiation", "reference_id": po, "session_id": session,
        "question": "Analisis PO-001. Panggil tool MCP negosiasi yang tersedia, lalu susun strategi harga dan risikonya.",
    }
    second = {
        "task": "negotiation", "reference_id": po, "session_id": session,
        "question": "Jika supplier menolak penawaran awal yang tadi kamu berikan, jelaskan opsi alternatifnya dengan merujuk strategi sebelumnya.",
    }
    answers = []
    for index, data in enumerate([first] if quick else [first, second], start=1):
        print(f"\n=== {3+index}. CHAT GEMINI PUTARAN {index} ===", flush=True)
        try:
            code, res = request_json(base, "/api/v1/agents/chat", token=token, payload=data, timeout=150)
            (folder / f"chat_turn_{index}.json").write_text(
                json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
            trace = [x.get("tool") for x in (res.get("tool_trace") or []) if isinstance(x, dict)]
            status = str(res.get("status"))
            has_verified = bool(res.get("verified_result"))
            has_precheck = bool(res.get("precheck"))
            answer = str(res.get("answer") or "")
            approval = res.get("requires_approval") is True
            negotiation_tool_used = "recommend_price_negotiation" in trace
            if code != 200 or status in {"not_configured", "model_unavailable", "step_limit", "error"}:
                state = "FAIL"
            elif not approval:
                state = "FAIL"
            elif (status == "needs_tool_use" or not has_verified or not has_precheck
                  or not answer.strip() or (index == 1 and not negotiation_tool_used)):
                state = "WARN"
            else:
                state = "PASS"
            record(f"Chat putaran {index}", state,
                   f"HTTP {code}, status={status}, turn_index={res.get('turn_index')}, "
                   f"verified={has_verified}, precheck={has_precheck}, "
                   f"approval={approval}, negotiation_tool={negotiation_tool_used}, tools={','.join(trace)}")
            if res.get("error"):
                print("  Error:", redacted(res.get("error"), keys))
            if answer:
                print("  Cuplikan jawaban:", " ".join(answer.split())[:300])
            answers.append(res)
        except Exception as exc:
            record(f"Chat putaran {index}", "FAIL", redacted(exc, keys))
            break
    if quick:
        record("Memori 2 putaran", "SKIP", "Mode --quick")
    elif len(answers) == 2:
        a, b = answers
        ok = (a.get("session_id") == b.get("session_id") == session and
              isinstance(a.get("turn_index"), int) and
              isinstance(b.get("turn_index"), int) and
              b["turn_index"] == a["turn_index"] + 1)
        record("Memori 2 putaran", "PASS" if ok else "FAIL",
               f"turn_index {a.get('turn_index')} -> {b.get('turn_index')}, session sama={a.get('session_id') == b.get('session_id')}")
        if ok:
            record("Kualitas ingatan isi jawaban", "WARN", "Perlu cek manual apakah jawaban kedua benar-benar merujuk strategi pertama")
    else:
        record("Memori 2 putaran", "FAIL", "Dua respons tidak berhasil diperoleh")


def main():
    parser = argparse.ArgumentParser(description="ProcureGuard AI end-to-end checker")
    parser.add_argument("--offline", action="store_true", help="Tidak memanggil Gemini")
    parser.add_argument("--quick", action="store_true", help="Hanya satu putaran chat Gemini")
    args = parser.parse_args()
    if not (ROOT / "agent_core" / "graph_api.py").exists():
        print("ERROR: Simpan script ini di Agents/scripts/, lalu jalankan dari folder Agents.")
        return 2
    env = os.environ.copy()
    env["AGENT_DATA_MODE"] = "mock"
    env["AGENT_API_KEY"] = secrets.token_urlsafe(36)
    env["LLM_MODEL"] = env.get("LLM_MODEL") or DEFAULT_MODEL
    env["LLM_BASE_URL"] = env.get("LLM_BASE_URL") or DEFAULT_BASE_URL
    keys = [env["AGENT_API_KEY"]]
    if not args.offline:
        key = env.get("LLM_API_KEY", "").strip()
        if not key:
            print("Gemini key hanya diminta di terminal ini; tidak akan dicetak atau disimpan.")
            key = getpass.getpass("Tempel GEMINI API KEY (input tersembunyi): ").strip()
        if not key:
            print("Tidak ada key. Jalankan dengan --offline jika ingin tes lokal saja.")
            return 2
        env["LLM_API_KEY"] = key
        keys.append(key)
    else:
        env.pop("LLM_API_KEY", None)
        env.pop("LLM_MODEL", None)
    folder = Path(tempfile.mkdtemp(prefix="procureguard_check_"))
    print("\nProcureGuard Stage 6 - Pengujian otomatis")
    print("Root:", ROOT)
    print("Model:", env.get("LLM_MODEL", "(offline)"))
    print("Laporan lokal:", folder)
    process = None
    log_handle = None
    try:
        test_units(keys)
        if not args.offline:
            test_gemini(env, keys)
        else:
            record("Koneksi Gemini", "SKIP", "Mode offline")
        process, log_handle, log_path, base = spawn_server(env, folder, keys)
        if base:
            test_api(base, env, folder, args.quick, args.offline, keys)
    except KeyboardInterrupt:
        record("Proses", "WARN", "Dihentikan oleh pengguna")
    except Exception as exc:
        record("Proses", "FAIL", redacted(exc, keys))
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=6)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if log_handle:
            log_handle.close()
        (folder / "ringkasan.json").write_text(
            json.dumps({"model": env.get("LLM_MODEL", "offline"), "checks": results},
                       indent=2, ensure_ascii=False), encoding="utf-8")
    passed = sum(r["status"] == "PASS" for r in results)
    failed = sum(r["status"] == "FAIL" for r in results)
    warned = sum(r["status"] == "WARN" for r in results)
    skipped = sum(r["status"] == "SKIP" for r in results)
    print(f"\nHASIL: PASS={passed} WARN={warned} FAIL={failed} SKIP={skipped}")
    print("Detail:", folder / "ringkasan.json")
    print("Jawaban lengkap, jika ada: chat_turn_1.json / chat_turn_2.json di folder laporan")
    print("Tidak ada commit, push, atau perubahan file repository.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
