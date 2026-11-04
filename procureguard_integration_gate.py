#!/usr/bin/env python3
"""ProcureGuard Stage 9 integration gate (Windows/Linux, Python 3.11+).

Checks actual running Frontend->Backend->Agent wiring, with no automatic changes to
Backend, Frontend, Agent, database, or Git. An optional one-line correction only
repairs the previous Stage9 *auditor*'s truncated OpenAPI response reader.

Real authenticated E2E tests are opt-in because they create AgentRun/AgentSession/
ApprovalRequest records in the actual backend database. No passwords or tokens
are written to reports, printed, or included in exception details.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib import error, parse, request
from uuid import uuid4

MAX_RESPONSE = 6_000_000
PO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")

@dataclass
class Finding:
    level: str
    name: str
    detail: str

class Gate:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.root = Path(args.repo).resolve()
        self.run_dir = Path(tempfile.mkdtemp(prefix="procureguard_integration_gate_"))
        self.findings: list[Finding] = []
        self.b = self.env_file(self.root / "Backend/.env")
        self.a = self.env_file(self.root / "Agents/.env")
        self.backend_schema: dict[str, Any] | None = None
        self.agent_schema: dict[str, Any] | None = None
        self.backend_ready = False
        self.agent_ready = False
        self.frontend_ready = False
        self.po_exists = False
        self.local_gate = "NOT_READY"
        self.real_gate = "NOT_TESTED"

    @staticmethod
    def env_file(path: Path) -> dict[str, str]:
        if not path.is_file():
            return {}
        out: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip().strip('"').strip("'")
        return out

    def add(self, level: str, name: str, detail: str) -> None:
        self.findings.append(Finding(level, name, detail))
        print(f"[{level}] {name}: {detail}", flush=True)

    def check(self, name: str, good: bool, ok: str, bad: str, bad_level: str = "FAIL") -> bool:
        self.add("PASS" if good else bad_level, name, ok if good else bad)
        return good

    @staticmethod
    def fetch(url: str, *, method: str = "GET", headers: dict[str, str] | None = None,
              payload: dict[str, Any] | None = None, timeout: int = 12) -> tuple[int, Any, int, str]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        h = {"Accept": "application/json", **(headers or {})}
        if data is not None:
            h["Content-Type"] = "application/json"
        req = request.Request(url, data=data, headers=h, method=method)
        try:
            with request.urlopen(req, timeout=timeout) as res:
                body = res.read(MAX_RESPONSE + 1)
                code = res.status
        except error.HTTPError as exc:
            code = exc.code
            body = exc.read(16384)  # Never include body in report; it may contain sensitive data.
        except (error.URLError, ConnectionError, TimeoutError, OSError) as exc:
            return 0, None, 0, type(exc).__name__
        if len(body) > MAX_RESPONSE:
            return code, None, len(body), "response_too_large"
        try:
            obj = json.loads(body) if body else None
        except (ValueError, UnicodeError):
            obj = None
        return code, obj, len(body), ""

    def git_ignore(self, relative: str) -> bool | None:
        if not (self.root / ".git").exists() or not shutil.which("git"):
            return None
        p = subprocess.run(["git", "check-ignore", "-q", "--", relative],
                           cwd=self.root, capture_output=True)
        return p.returncode == 0

    def preflight(self):
        print("\n===== A. KONFIGURASI DAN KEAMANAN =====")
        expected = ["Backend/app/main.py", "Agents/agent_core/graph_api.py",
                    "Frontend/vite.config.js", "procureguard_stage9.py"]
        missing = [p for p in expected if not (self.root / p).is_file()]
        self.check("Struktur repository", not missing, "Folder utama sesuai", "Tidak ditemukan: " + ", ".join(missing))
        for rel in ("Backend/.env", "Agents/.env"):
            self.check(rel, (self.root / rel).is_file(), "File tersedia", "File belum tersedia")
            ignored = self.git_ignore(rel)
            if ignored is not None:
                self.check(rel + " dilindungi Git", ignored, "Di-ignore", "BERBAHAYA: berpotensi masuk commit")
        old_env = self.root / "Backend/env"
        if old_env.is_file():
            ignored = self.git_ignore("Backend/env")
            if ignored is False:
                self.add("WARN", "File Backend/env tanpa titik", "Berisi kemungkinan rahasia dan tidak di-ignore; pindahkan dari repo setelah konfigurasi selesai")
        b_agent = self.b.get("AGENT_API_KEY", "")
        a_agent = self.a.get("AGENT_API_KEY", "")
        b_internal = self.b.get("INTERNAL_API_KEY", "")
        a_internal = self.a.get("PROCUREMENT_SERVICE_TOKEN", "")
        self.check("Token Backend->Agent", bool(b_agent) and b_agent == a_agent,
                   "Kedua layanan memakai token yang sama", "Token belum ada atau tidak cocok")
        self.check("Token Agent->Backend", bool(b_internal) and b_internal == a_internal,
                   "Kedua layanan memakai token yang sama", "INTERNAL_API_KEY dan PROCUREMENT_SERVICE_TOKEN tidak cocok")
        expected_agent_url = self.args.agent_url.rstrip("/")
        expected_backend_url = self.args.backend_url.rstrip("/")
        self.check("Backend AGENT_API_URL", self.b.get("AGENT_API_URL", "").rstrip("/") == expected_agent_url,
                   "Mengarah ke Agent lokal", "Tidak menunjuk ke Agent URL yang diuji")
        self.check("Agent PROCUREMENT_BACKEND_URL", self.a.get("PROCUREMENT_BACKEND_URL", "").rstrip("/") == expected_backend_url,
                   "Mengarah ke Backend lokal", "Tidak menunjuk ke Backend URL yang diuji")
        self.check("Konfigurasi Agent HTTP", self.a.get("AGENT_DATA_MODE", "").lower() == "http",
                   "Mode http", "Agent/.env masih bukan mode http")
        self.check("Gemini tersedia", bool(self.a.get("LLM_API_KEY") or os.getenv("LLM_API_KEY")),
                   "Key tersedia (tidak divalidasi/ditampilkan)", "Key belum ada; live chat belum dapat divalidasi", "WARN")
        self.check("Supabase tersedia", bool(self.b.get("SUPABASE_URL") and self.b.get("SUPABASE_ANON_KEY")),
                   "Konfigurasi tersedia", "Konfigurasi Supabase belum lengkap", "WARN")
        if self.args.po_id and not PO_RE.fullmatch(self.args.po_id):
            self.add("FAIL", "Format PO ID", "Gunakan huruf, angka, _, -, atau . (maksimal 100 karakter)")

    def services(self):
        print("\n===== B. LAYANAN DAN OPENAPI NYATA =====")
        b, _, _, _ = self.fetch(self.args.backend_url + "/health")
        a, health, _, _ = self.fetch(self.args.agent_url + "/health")
        f, _, _, _ = self.fetch(self.args.frontend_url + "/", headers={"Accept": "text/html"})
        self.backend_ready = self.check("Backend :8000 health", b == 200, "HTTP 200", f"HTTP {b}; periksa backend_runtime.log")
        self.agent_ready = self.check("Agent :8001 health", a == 200, "HTTP 200", f"HTTP {a}; periksa agent_runtime.log")
        self.frontend_ready = self.check("Frontend :5173", f == 200, "HTTP 200", f"HTTP {f}; server Vite belum tersedia")
        if self.agent_ready:
            mode = (health or {}).get("mode") if isinstance(health, dict) else None
            self.check("Agent mode runtime", mode == "http", "Runtime http; bukan mock", f"Runtime={mode!r}, restart Agent dengan konfigurasi terbaru")
        if self.backend_ready:
            code, _, _, _ = self.fetch(self.args.backend_url + "/ready")
            self.check("Supabase readiness", code == 200, "HTTP 200; DB dapat dihubungi", f"HTTP {code}; periksa DB/schema")
        schemas = [
            ("Backend", self.args.backend_url, ("/api/v1/agents/chat", "/api/v1/agents/run")),
            ("Agent", self.args.agent_url, ("/api/v1/agents/chat", "/api/v1/agents/run")),
        ]
        for label, root, routes in schemas:
            code, schema, size, problem = self.fetch(root + "/openapi.json", timeout=20)
            good = code == 200 and isinstance(schema, dict)
            self.check(label + " OpenAPI parse lengkap", good,
                       f"HTTP 200; {size} byte; {len(schema.get('paths',{}))} path",
                       f"HTTP {code}; ukuran {size}; problem={problem or 'JSON tidak lengkap'}")
            if not good:
                continue
            paths = schema.get("paths", {})
            for route in routes:
                found = isinstance(paths.get(route), dict) and "post" in paths[route]
                self.check(label + " POST " + route, found, "Ada di OpenAPI", "Rute tidak ada di schema runtime")
            if label == "Backend":
                self.backend_schema = schema
                internal_path = "/api/v1/internal/procurement/pos/{po_id}"
                self.check("Backend internal procurement schema", internal_path in paths,
                           "Rute internal tersedia", "Rute procurement provider tidak ditemukan")
            else:
                self.agent_schema = schema
        if self.frontend_ready:
            code, _, _, _ = self.fetch(self.args.frontend_url + "/api/v1/agents/chat", method="POST", payload={})
            self.check("Vite /api proxy ke Backend", code == 401,
                       "HTTP 401; permintaan berhasil diteruskan ke Backend dan autentikasi dipertahankan",
                       f"HTTP {code}; proxy tidak sesuai atau Backend tidak tersedia")

    def auth(self):
        print("\n===== C. OTORISASI DAN SERVICE LINK =====")
        endpoints = [
            ("Backend chat tanpa user", self.args.backend_url + "/api/v1/agents/chat", "POST", {}),
            ("Backend run tanpa user", self.args.backend_url + "/api/v1/agents/run", "POST", {}),
            ("Agent chat tanpa token", self.args.agent_url + "/api/v1/agents/chat", "POST", {}),
            ("Agent run tanpa token", self.args.agent_url + "/api/v1/agents/run", "POST", {}),
        ]
        for label, url, method, body in endpoints:
            code, _, _, _ = self.fetch(url, method=method, payload=body)
            self.check(label, code == 401, "HTTP 401 (akses ditolak)", f"HTTP {code}; ekspektasi 401")
        code, _, _, _ = self.fetch(self.args.backend_url + "/api/v1/internal/procurement/pos/PO-TEST", headers={"X-API-Key": "invalid"})
        self.check("Backend internal token salah", code == 401, "HTTP 401", f"HTTP {code}")
        if not self.args.po_id:
            self.add("BLOCKED", "Read data PO nyata", "Tambahkan --po-id PO_MILIK_USER untuk memeriksa data Backend asli")
            return
        key = self.b.get("INTERNAL_API_KEY", "")
        if not key:
            self.add("BLOCKED", "Read data PO nyata", "INTERNAL_API_KEY tidak tersedia di Backend/.env")
            return
        code, body, _, _ = self.fetch(
            self.args.backend_url + "/api/v1/internal/procurement/pos/" + parse.quote(self.args.po_id, safe=""),
            headers={"X-API-Key": key}, timeout=20)
        good = code == 200 and isinstance(body, dict) and str(body.get("po_id")) == self.args.po_id
        if good:
            self.po_exists = True
            self.add("PASS", "Read PO asli via Backend", "HTTP 200; PO ID sesuai; data tidak dicetak")
        elif code == 404:
            self.add("BLOCKED", "Read PO asli via Backend", "HTTP 404: PO belum tersedia di database; gunakan ID PO yang benar")
        else:
            self.add("FAIL", "Read PO asli via Backend", f"HTTP {code}; periksa konfigurasi HTTP provider dan schema database")
        if self.po_exists and self.agent_ready:
            agentkey = self.a.get("AGENT_API_KEY", "")
            if not agentkey:
                self.add("BLOCKED", "Agent run PO asli", "Service Agent token belum tersedia")
                return
            code, result, _, _ = self.fetch(self.args.agent_url + "/api/v1/agents/run", method="POST",
                headers={"Authorization": "Bearer " + agentkey}, timeout=80,
                payload={"task": "fraud", "reference_type": "po", "reference_id": self.args.po_id,
                         "instruction": "Periksa anomali secara read-only dan wajib human review."})
            good = code == 200 and isinstance(result, dict) and result.get("requires_approval") is True
            self.check("Agent -> Backend -> PO nyata", good,
                       "HTTP 200; hasil fraud memerlukan human review", f"HTTP {code}; tool/data provider gagal")

    def fix_false_openapi(self):
        print("\n===== D. PERBAIKAN FALSE NEGATIVE AUDITOR (OPSIONAL) =====")
        if self.args.no_repair_auditor:
            self.add("INFO", "Perbaikan skrip Stage9", "Dinonaktifkan oleh --no-repair-auditor")
            return
        if not (isinstance(self.backend_schema, dict) and
                "/api/v1/agents/chat" in self.backend_schema.get("paths", {})):
            self.add("INFO", "Perbaikan skrip Stage9", "Tidak diterapkan: rute OpenAPI Backend belum diverifikasi")
            return
        path = self.root / "procureguard_stage9.py"
        if not path.exists():
            self.add("WARN", "Perbaikan skrip Stage9", "File utama Stage9 tidak ditemukan")
            return
        source = path.read_text(encoding="utf-8-sig")
        old = "raw = response.read(65536)"
        if old not in source:
            self.add("PASS", "Perbaikan skrip Stage9", "Pemeriksa sudah tidak memakai pembatas 64 KB")
            return
        if source.count(old) != 1:
            self.add("FAIL", "Perbaikan skrip Stage9", "Marker tidak unik; tidak mengubah file")
            return
        replacement = ("raw = response.read(5_000_001)\n"
                       "                if len(raw) > 5_000_000:\n"
                       "                    return response.status, None")
        patched = source.replace(old, replacement, 1)
        try:
            compile(patched, str(path), "exec")
            backup = self.run_dir / "procureguard_stage9.py.before_openapi_fix.bak"
            shutil.copy2(path, backup)
            path.write_text(patched, encoding="utf-8", newline="\n")
        except (OSError, SyntaxError) as exc:
            self.add("FAIL", "Perbaikan skrip Stage9", f"Tidak berhasil: {type(exc).__name__}")
            return
        self.add("PASS", "Perbaikan false negative Stage9", "Baca OpenAPI hingga 5 MB; backup dibuat; Backend/Frontend/Agent tidak berubah")

    def run_regression(self):
        if self.args.skip_regression:
            self.add("INFO", "Regression tests", "Dilewati dengan --skip-regression")
            return
        print("\n===== E. REGRESSION TESTS =====")
        jobs = [
            ("Agents unit tests", self.root / "Agents", ["Agents", ".venv", "Scripts", "python.exe"],
             ["-m", "unittest", "discover", "-s", "tests", "-q"], 240),
            ("Backend pytest", self.root / "Backend", ["Backend", ".venv", "Scripts", "python.exe"],
             ["-m", "pytest", "-q"], 300),
        ]
        for label, cwd, path_bits, args, timeout in jobs:
            interpreter = self.root.joinpath(*path_bits)
            if os.name != "nt":
                interpreter = self.root / path_bits[0] / ".venv" / "bin" / "python"
            if not interpreter.exists():
                self.add("WARN", label, "Virtual environment belum ditemukan; tes tidak dijalankan")
                continue
            log = self.run_dir / ("agents_tests.log" if label.startswith("Agents") else "backend_tests.log")
            try:
                with log.open("w", encoding="utf-8", errors="replace") as out:
                    cp = subprocess.run([str(interpreter), *args], cwd=cwd, stdout=out,
                                        stderr=subprocess.STDOUT, timeout=timeout)
                self.check(label, cp.returncode == 0, "Exit 0; detail log lokal", "Gagal; periksa log lokal")
            except (OSError, subprocess.TimeoutExpired) as exc:
                self.add("FAIL", label, f"Error menjalankan tes: {type(exc).__name__}")
        frontend = self.root / "Frontend"
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        if npm and (frontend / "node_modules").is_dir():
            log = self.run_dir / "frontend_build.log"
            try:
                with log.open("w", encoding="utf-8", errors="replace") as out:
                    cp = subprocess.run([npm, "run", "build"], cwd=frontend, stdout=out,
                                        stderr=subprocess.STDOUT, timeout=240)
                self.check("Frontend production build", cp.returncode == 0, "Build berhasil", "Build gagal; periksa frontend_build.log")
            except (OSError, subprocess.TimeoutExpired) as exc:
                self.add("FAIL", "Frontend production build", f"Error: {type(exc).__name__}")
        else:
            self.add("WARN", "Frontend production build", "npm/node_modules belum tersedia")

    def get_user_token(self) -> str:
        token = os.getenv(self.args.user_token_env, "").strip()
        if token:
            return token
        if not self.args.login_email:
            return ""
        if not sys.stdin.isatty():
            self.add("BLOCKED", "Supabase login", "Memerlukan terminal interaktif untuk membaca password tersembunyi")
            return ""
        password = getpass.getpass("Password akun pengguna Supabase (tersembunyi): ")
        if not password:
            return ""
        code, obj, _, _ = self.fetch(self.args.backend_url + "/api/v1/auth/login", method="POST", timeout=40,
                                    payload={"email": self.args.login_email, "password": password})
        password = ""  # best effort; Python cannot guarantee memory scrubbing.
        if code != 200 or not isinstance(obj, dict) or not obj.get("access_token"):
            self.add("BLOCKED", "Supabase login", f"HTTP {code}; akun/password atau layanan Supabase belum siap")
            return ""
        self.add("PASS", "Supabase login", "HTTP 200; token hanya digunakan di memori proses ini")
        return obj["access_token"]

    def real_e2e(self):
        print("\n===== F. INTEGRASI NYATA USER -> BACKEND -> AGENT -> DATA =====")
        if not self.args.live_e2e:
            self.add("BLOCKED", "Real E2E", "Tidak dijalankan; aktifkan dengan --live-e2e --po-id PO_SAH --allow-db-write")
            return
        if not self.args.allow_db_write:
            self.add("BLOCKED", "Real E2E", "Dibatalkan: --allow-db-write diperlukan; chat membuat session/run/approval pada DB nyata")
            return
        if not self.args.po_id or not self.po_exists:
            self.add("BLOCKED", "Real E2E", "PO belum diverifikasi; gunakan PO yang ada dan milik akun login")
            return
        token = self.get_user_token()
        if not token:
            self.add("BLOCKED", "Real E2E", "Butuh --login-email (password tersembunyi) atau environment variable user token")
            return
        code, _, _, _ = self.fetch(self.args.backend_url + "/api/v1/auth/me",
                                  headers={"Authorization": "Bearer " + token})
        if not self.check("Supabase user identity", code == 200,
                          "HTTP 200; pengguna berhasil diautentikasi", f"HTTP {code}; akses pengguna tidak valid"):
            return
        session = "integration-gate-" + str(uuid4())
        headers = {"Authorization": "Bearer " + token}
        prompts = [
            "Untuk PO ini, ingat dua prioritas khusus: jangan menaikkan jumlah pembelian dan utamakan ketepatan pengiriman dibanding diskon. Buat strategi negosiasi tanpa tindakan otomatis.",
            "Sebutkan dua prioritas khusus saya sebelumnya dan sesuaikan strategi jika supplier menolak.",
        ]
        ok_all = True
        for n, question in enumerate(prompts, 1):
            code, obj, _, _ = self.fetch(self.args.backend_url + "/api/v1/agents/chat", method="POST", headers=headers,
                payload={"task": "negotiation", "reference_id": self.args.po_id,
                         "session_id": session, "question": question}, timeout=190)
            valid = (code == 200 and isinstance(obj, dict) and obj.get("session_id") == session
                     and obj.get("requires_approval") is True
                     and obj.get("precheck") is not None
                     and obj.get("verified_result") is not None
                     and obj.get("turn_index") == n)
            if valid:
                self.add("PASS", f"Real E2E chat putaran {n}",
                         f"HTTP 200, session cocok, turn={n}, verified, precheck, human approval")
            else:
                self.add("FAIL", f"Real E2E chat putaran {n}",
                         f"HTTP {code}; response tidak memenuhi kontrak atau user tidak memiliki hak PO; cek Backend logs")
                ok_all = False
                break
            if n == 2:
                answer = str(obj.get("answer", "")).lower()
                memory_ok = ("jumlah" in answer or "kuantitas" in answer) and "pengiriman" in answer
                self.check("Memori preferensi lintas turn", memory_ok,
                           "Kedua prioritas terdeteksi; tidak cukup sebagai bukti persistensi restart",
                           "Dua prioritas tidak lengkap pada jawaban; perlu pemeriksaan manual", "WARN")
        self.real_gate = "PASS" if ok_all else "FAIL"

    def save(self):
        failures = [f for f in self.findings if f.level == "FAIL"]
        block = [f for f in self.findings if f.level == "BLOCKED"]
        if failures:
            self.local_gate = "FAIL"
        elif block:
            self.local_gate = "PASS_WITH_BLOCKERS"
        else:
            self.local_gate = "PASS"
        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "local_gate": self.local_gate,
            "real_e2e_gate": self.real_gate,
            "counts": {x: sum(f.level == x for f in self.findings) for x in ("PASS", "WARN", "FAIL", "BLOCKED", "INFO")},
            "findings": [asdict(f) for f in self.findings],
        }
        (self.run_dir / "ringkasan.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        md = ["# ProcureGuard Stage 9 – Integration Gate", "",
              "Tidak menyimpan token, password, detail data PO, atau respons Gemini.", "",
              f"**Gate pemeriksaan:** {self.local_gate}", f"**Gate E2E pengguna nyata:** {self.real_gate}", "",
              "## Temuan", ""]
        for f in self.findings:
            md.append(f"- **{f.level}** — {f.name}: {f.detail}")
        md += ["", "## Prinsip keamanan", "", "- Tidak ada git add/commit/push atau migrasi DB.",
               "- Tidak mengubah Backend/Frontend/Agent. Hanya patch auditor Stage9 jika terbukti ada false-negative.",
               "- Live E2E membuat catatan AgentSession/AgentRun/ApprovalRequest; hanya dengan --allow-db-write.",
               "- URL publik HTTPS/Vultr dan otorisasi lintas pengguna membutuhkan pengujian server asli.", ""]
        (self.run_dir / "LAPORAN_INTEGRASI.md").write_text("\n".join(md), encoding="utf-8")
        print("\n====== HASIL AKHIR ======")
        for k, v in report["counts"].items(): print(f"{k}={v}", end=" ")
        print("\nGATE_LOKAL:", self.local_gate)
        print("GATE_E2E_NYATA:", self.real_gate)
        print("LAPORAN:", self.run_dir / "LAPORAN_INTEGRASI.md")
        print("JSON:", self.run_dir / "ringkasan.json")
        print("Tidak ada Git push atau migrasi database.")
        return 1 if failures else (2 if self.args.live_e2e and self.real_gate != "PASS" else 0)

    def run(self):
        print("ProcureGuard Stage 9 - Integration Gate: pemeriksaan nyata, tidak mengklaim nol bug")
        print("Repository:", self.root)
        print("Laporan lokal:", self.run_dir)
        try:
            self.preflight()
            self.services()
            self.auth()
            self.fix_false_openapi()
            self.run_regression()
            self.real_e2e()
        except Exception as exc:
            # Never print raw exception (could include URL, authorization, DB values).
            self.add("FAIL", "Kesalahan penguji", f"{type(exc).__name__}; periksa kondisi service dan source")
        return self.save()

def main() -> int:
    parser = argparse.ArgumentParser(description="ProcureGuard Stage 9, trusted full-OpenAPI + genuine user E2E gate")
    parser.add_argument("--repo", default=".", help="Root repository VultrAgents")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--agent-url", default="http://127.0.0.1:8001")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:5173")
    parser.add_argument("--po-id", default="", help="Purchase order yang benar-benar ada pada Backend")
    parser.add_argument("--live-e2e", action="store_true", help="Jalankan dua turn chat lewat Backend dengan akun Supabase nyata")
    parser.add_argument("--allow-db-write", action="store_true", help="Setuju membuat record AgentSession/Run/Approval selama E2E")
    parser.add_argument("--login-email", default="", help="Email pengguna Supabase; password diminta tersembunyi")
    parser.add_argument("--user-token-env", default="PROCUREGUARD_USER_TOKEN", help="Nama env var bearer pengguna")
    parser.add_argument("--skip-regression", action="store_true")
    parser.add_argument("--no-repair-auditor", action="store_true")
    return Gate(parser.parse_args()).run()

if __name__ == "__main__":
    raise SystemExit(main())
