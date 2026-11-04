#!/usr/bin/env python3
"""ProcureGuard Stage 9A-9D: fail-closed synchronizer, environment and deployment kit.

Run on a checked-out VultrAgents repository. Does not git add/commit/push.
Never logs API tokens; writes .env only in gitignored application folders.
"""
from __future__ import annotations

import argparse
import datetime as dt
import getpass
import json
import os
import pathlib
import platform
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict


class StageError(RuntimeError):
    pass


@dataclass
class Finding:
    stage: str
    level: str
    subject: str
    detail: str


class Stage9:
    def __init__(self, args):
        self.args = args
        self.root = pathlib.Path(args.repo).expanduser().resolve()
        self.run_dir = pathlib.Path(tempfile.mkdtemp(prefix="procureguard_stage9_"))
        self.backup_dir = self.run_dir / "backup_original"
        self.findings: list[Finding] = []
        self.changed: list[str] = []
        self.model = args.model
        self.agent_env: dict[str, str] = {}
        self.backend_env: dict[str, str] = {}
        self.processes: list[dict] = []

    def record(self, stage, level, subject, detail):
        result = Finding(stage, level, subject, str(detail))
        self.findings.append(result)
        print(f"[{level}] {stage} {subject}: {detail}", flush=True)

    def execute(self, label, stage, action):
        try:
            action()
        except (StageError, OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
            # Do not render raw exception if it may contain URL query secrets.
            error = type(exc).__name__
            if isinstance(exc, StageError):
                error = str(exc)
            self.record(stage, "FAIL", label, error)

    def check_root(self):
        required = ["Agents/agent_core/graph_api.py", "Backend/app/main.py", "Frontend/src/services/chatService.js", "Frontend/vite.config.js"]
        missing = [x for x in required if not (self.root / x).is_file()]
        if missing:
            raise StageError("Folder repo salah; tidak ditemukan: " + ", ".join(missing))

    def run(self, cmd, cwd=None, env=None, logfile=None, timeout=600, check=True):
        if logfile is not None:
            with open(logfile, "w", encoding="utf-8", errors="replace") as out:
                p = subprocess.run(cmd, cwd=cwd or self.root, env=env, stdout=out,
                                   stderr=subprocess.STDOUT, text=True, timeout=timeout)
        else:
            p = subprocess.run(cmd, cwd=cwd or self.root, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, timeout=timeout)
        if check and p.returncode:
            raise StageError(f"exit={p.returncode} pada {cmd[0]}; periksa {logfile.name if logfile else 'output'}")
        return p

    def is_git(self):
        return (self.root / ".git").exists()

    def stage9a_pull(self):
        if not self.is_git():
            self.record("9A", "WARN", "Git Pull", "Bekerja pada salinan tanpa .git; jalankan di clone asli untuk git pull")
            return
        branch = self.run(["git", "branch", "--show-current"]).stdout.strip()
        if branch != "main":
            raise StageError("Branch aktif bukan main; Git Pull otomatis dibatalkan")
        changes = self.run(["git", "status", "--porcelain"]).stdout.splitlines()
        # Existing untracked launcher is acceptable; no tracked dirty changes allowed.
        tracked = [x for x in changes if x[:2].strip() != "??"]
        if tracked:
            raise StageError("Ada perubahan tracked lokal; simpan dahulu sebelum git pull")
        self.run(["git", "fetch", "origin", "main"], logfile=self.run_dir / "git_fetch.log", timeout=90)
        self.run(["git", "pull", "--ff-only", "origin", "main"], logfile=self.run_dir / "git_pull.log", timeout=90)
        rev = self.run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()
        self.record("9A", "PASS", "Git Pull", "branch main sinkron; HEAD=" + rev)

    def content(self, rel):
        p = self.root / rel
        if not p.is_file():
            raise StageError(f"File yang diperlukan tidak ada: {rel}")
        return p.read_text(encoding="utf-8-sig")

    def put(self, rel, content, stage="9B"):
        p = self.root / rel
        before = p.read_text(encoding="utf-8-sig") if p.exists() else None
        if before == content:
            return False
        if before is not None:
            backup = self.backup_dir / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                shutil.copy2(p, backup)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="\n")
        self.changed.append(rel)
        self.record(stage, "PASS", "Perbarui " + rel, "Backup di folder laporan jika file sebelumnya ada")
        return True

    def replace_one(self, rel, old, new, description):
        content = self.content(rel)
        if old in content:
            if content.count(old) != 1:
                raise StageError(f"Marker tidak unik pada {rel}: {description}; hentikan patch")
            content = content.replace(old, new, 1)
            self.put(rel, content)
        elif new not in content:
            raise StageError(f"Versi {rel} tidak cocok; patch {description} tidak diterapkan")

    def patch(self):
        # Ensure chat calls a REAL endpoint; the /conversations routes are 501 placeholders.
        self.replace_one(
            "Frontend/src/services/api.js",
            "async function request(path, init = {}, authenticated = false) {",
            "async function request(path, init = {}, authenticated = false, timeoutMs = 10000) {",
            "request timeout configurable",
        )
        self.replace_one(
            "Frontend/src/services/api.js",
            "sendRequest(path, init, authenticated ? session?.access_token : undefined);",
            "sendRequest(path, init, authenticated ? session?.access_token : undefined, timeoutMs);",
            "forward timeout to first request",
        )
        self.replace_one(
            "Frontend/src/services/api.js",
            "sendRequest(path, init, refreshed.access_token)",
            "sendRequest(path, init, refreshed.access_token, timeoutMs)",
            "forward timeout on token refresh",
        )
        self.replace_one(
            "Frontend/src/services/api.js",
            "async function sendRequest(path, init, accessToken) {",
            "async function sendRequest(path, init, accessToken, timeoutMs = 10000) {",
            "sendRequest timeout argument",
        )
        self.replace_one(
            "Frontend/src/services/api.js",
            "window.setTimeout(() => controller.abort(), 10000);",
            "window.setTimeout(() => controller.abort(), timeoutMs);",
            "avoid 10-second Gemini abort",
        )
        # Add direct Backend authenticated Agent proxy call; no browser Agent service secret.
        api = self.content("Frontend/src/services/api.js")
        marker = "// --- Chat / Conversation helpers ---"
        addition = (
            "// Live Agent goes through the authenticated Backend proxy, never directly to Agent.\n"
            "export const chatWithAgent = (task, referenceId, sessionId, question) =>\n"
            "    request('/agents/chat', { method: 'POST', body: JSON.stringify({\n"
            "        task, reference_id: referenceId, session_id: sessionId, question\n"
            "    }) }, true, Number(import.meta.env.VITE_AGENT_REQUEST_TIMEOUT_MS || 185000));\n"
        )
        if "export const chatWithAgent" not in api:
            if api.count(marker) != 1:
                raise StageError("Tidak menemukan marker Chat API frontend yang unik")
            self.put("Frontend/src/services/api.js", api.replace(marker, addition + marker))

        chat = self.content("Frontend/src/services/chatService.js")
        importline = "  ApiError,\n"
        if "  chatWithAgent,\n" not in chat:
            if chat.count(importline) != 1:
                raise StageError("Tidak menemukan marker import Chat Service")
            chat = chat.replace(importline, importline + "  chatWithAgent,\n", 1)
        start = chat.find("const liveAdapter = {")
        end = chat.find("// ── Mock adapter", start)
        if start < 0 or end < 0:
            if "const liveAdapter = {" not in chat or "chatWithAgent(task, referenceId" not in chat:
                raise StageError("Format frontend chatService tidak cocok")
        else:
            new_adapter = '''// Backend `/conversations` endpoints are placeholders (501) in this repository.
// Keep conversations in this browser tab during the local demo and send messages
// via the REAL authenticated Backend Agent endpoint. Server-side AgentSession and
// AgentRun still enforce user/PO scope. This is NOT durable message history.
const liveConversations = new Map();
const liveAdapter = {
  async createConversation(task, referenceId) {
    const id = crypto.randomUUID();
    liveConversations.set(id, { task, referenceId, messages: [] });
    return { id, task, referenceId, sessionId: id };
  },
  async getMessages(conversationId) {
    return liveConversations.get(conversationId)?.messages ?? [];
  },
  async sendMessage(conversationId, question, task, referenceId) {
    const c = liveConversations.get(conversationId);
    if (!c || c.task !== task || c.referenceId !== referenceId) {
      throw new ApiError('Agent session context has changed. Start a new chat.', 400);
    }
    const raw = await chatWithAgent(task, referenceId, conversationId, question);
    const userMessage = normalize({ id: crypto.randomUUID(), question }, 'user');
    const assistantMessage = normalize(raw, 'assistant');
    c.messages.push(userMessage, assistantMessage);
    return assistantMessage;
  },
  async sendFeedback(_messageId, _rating) {
    throw new ApiError('Message feedback is not implemented by Backend yet.', 501);
  },
  async approve(approvalId) { return apiApprove(approvalId); },
  async reject(approvalId) { return apiReject(approvalId); },
};

'''
            if "const liveConversations = new Map();" in chat:
                # Idempotence: already patched. Avoid clobbering user edits.
                pass
            else:
                chat = chat[:start] + new_adapter + chat[end:]
        self.put("Frontend/src/services/chatService.js", chat)

        # Timeouts form an ordered chain: Agent 145 < Backend 160 < Browser 185 sec.
        self.replace_one("Agents/agent_core/graph_api.py", "        ), timeout=50)",
                         "        ), timeout=float(os.getenv('AGENT_CHAT_TIMEOUT_SECONDS', '145')))\n", "Agent Chat timeout")
        self.replace_one("Backend/app/api/v1/endpoints/agents.py", "call_agent(\"chat\", payload, timeout=52.0)",
                         "call_agent(\"chat\", payload, timeout=160.0)", "Backend Chat timeout")

        # Document defaults, never insert real keys into examples.
        fenv = self.content("Frontend/.env.example")
        for line in ["VITE_CHAT_MODE=live", "VITE_AGENT_REQUEST_TIMEOUT_MS=185000"]:
            key = line.split("=", 1)[0]
            fenv = re.sub(r"(?m)^" + re.escape(key) + r"=.*$", line, fenv)
            if not re.search(r"(?m)^" + re.escape(key) + r"=", fenv): fenv = fenv.rstrip() + "\n" + line + "\n"
        self.put("Frontend/.env.example", fenv)
        aenv = self.content("Agents/.env.graph.example")
        if "AGENT_CHAT_TIMEOUT_SECONDS=" not in aenv:
            aenv = aenv.rstrip() + "\nAGENT_CHAT_TIMEOUT_SECONDS=145\nLLM_TIMEOUT_SECONDS=90\n"
        self.put("Agents/.env.graph.example", aenv)
        self.deploy_files()
        self.record("9B", "PASS", "Penyelarasan kode", "Frontend live -> Backend 8000 -> Agent 8001, tanpa mengekspos token layanan")

    def deploy_files(self):
        dockerfile = '''FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY agent_requirements.txt graph_requirements.txt ./
RUN pip install --no-cache-dir -r agent_requirements.txt -r graph_requirements.txt
COPY agent_core ./agent_core
EXPOSE 8001
CMD ["uvicorn", "agent_core.graph_api:app", "--host", "127.0.0.1", "--port", "8001"]
'''
        compose = '''# Linux VPS ONLY: host networking permits safe loopback-to-loopback S2S
# Agent/API stay private; terminate PUBLIC TLS in Nginx on the host.
services:
  agent:
    build:
      context: ../Agents
      dockerfile: ../deploy/Agent.Dockerfile
    network_mode: host
    env_file: ../Agents/.env
    environment:
      AGENT_DATA_MODE: http
      PROCUREMENT_BACKEND_URL: http://127.0.0.1:8000
      AGENT_CHAT_TIMEOUT_SECONDS: "145"
    command: ["uvicorn", "agent_core.graph_api:app", "--host", "127.0.0.1", "--port", "8001"]
    restart: unless-stopped
  backend:
    build: ../Backend
    network_mode: host
    env_file: ../Backend/.env
    environment:
      AGENT_API_URL: http://127.0.0.1:8001
    command: ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    restart: unless-stopped
'''
        nginx = '''# Replace DOMAIN_NAME and SSL certificate paths. Do NOT expose HTTP auth publicly.
# The frontend dist files must be copied to /var/www/procureguard/frontend.
server {
    listen 443 ssl http2;
    server_name DOMAIN_NAME;
    ssl_certificate /etc/letsencrypt/live/DOMAIN_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN_NAME/privkey.pem;
    root /var/www/procureguard/frontend;
    index index.html;
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 190s;
    }
    location /health { proxy_pass http://127.0.0.1:8000; }
    location /ready { proxy_pass http://127.0.0.1:8000; }
    location / {
        try_files $uri $uri/ /index.html;
    }
}
'''
        guide = '''# ProcureGuard Stage 9: Satu VPS, Backend 8000, Agent 8001

- Frontend: `https://DOMAIN_NAME/`, requests same-origin `/api/v1`.
- Backend: private `http://127.0.0.1:8000`, proxied by HTTPS Nginx.
- Agent URL: **`http://127.0.0.1:8001`** (internal, configured in Backend `.env` as `AGENT_API_URL`).
- Agent reads procurement Backend `http://127.0.0.1:8000` with `PROCUREMENT_SERVICE_TOKEN` = Backend `INTERNAL_API_KEY`.
- Backend calls Agent with `AGENT_API_KEY` matching Agent `AGENT_API_KEY`.
- Frontend NEVER gets those secrets. `VITE_CHAT_MODE=live` is required for real chat.

## Local Windows

Run `python procureguard_stage9.py --repo "D:\\Kuliah Semester 3\\VultrAgents" --mode all`.
Requires Supabase DB credentials in Backend `.env`; no destructive migrations are run.
`--mode start` launches two FastAPI servers and Vite with separate ports if configured.
`--mode status` checks both endpoints and the frontend; to test authenticated
PO-scoped chat, provide `--po-id` and a Supabase access token via `PROCUREGUARD_USER_TOKEN`
(environment variable; do not paste to chat).

## Vultr Linux (deployment requires server access, domain, DNS, cert)

1. Clone/pull the reviewed version of the repository onto your VPS. Apply the
   Stage9 patch and review Git changes. NEVER deploy an unreviewed tree.
2. Configure ignored `Backend/.env` with Supabase database/auth settings and
   private `INTERNAL_API_KEY`, `AGENT_API_KEY`, `AGENT_API_URL`.
3. Configure ignored `Agents/.env` with Gemini key, `AGENT_API_KEY`,
   `AGENT_DATA_MODE=http`, `PROCUREMENT_SERVICE_TOKEN` and backend URL.
4. Install Docker Engine + compose plugin. On **Linux VPS only**, run:
   `docker compose -f deploy/compose.vultr.yml up -d --build`.
   Both services bind only 127.0.0.1, so there is NO separate public Agent URL.
5. Apply schema migrations only with a DB backup, permission and an explicit
   maintenance decision; this script does NOT run Alembic.
6. Set DNS to VPS, provision TLS certificate, deploy Nginx configuration from
   `deploy/nginx.https.template.conf`, copy `Frontend/dist` to
   `/var/www/procureguard/frontend`, then validate `nginx -t` before reload.
7. Test HTTPS login, owned PO chat, fraud evidence, approval, and refusal of
   another user's PO. Monitor service logs; use a persistent session checkpointer
   for multi-worker/production sessions (current InMemorySaver is demo-only).

Public **Agent** subdomain is NOT necessary. If explicitly required, add it
only behind a private network/service-authenticated HTTPS gateway; never expose
Gemini key, Agent token or bare port 8001 to browsers.
'''
        self.put("deploy/Agent.Dockerfile", dockerfile, "9D")
        self.put("deploy/compose.vultr.yml", compose, "9D")
        self.put("deploy/nginx.https.template.conf", nginx, "9D")
        self.put("deploy/STAGE9_DEPLOYMENT.md", guide, "9D")

    def read_env(self, path):
        data = {}
        if not path.exists(): return data
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
        return data

    @staticmethod
    def real_secret(value):
        if not value or any(p in value.upper() for p in ("REPLACE", "YOUR_", "<", ">", "EXAMPLE", "PLACEHOLDER", "CHANGE_ME")):
            return False
        return len(value) >= 24

    def set_env(self, path, entries):
        if self.is_git():
            relative = path.relative_to(self.root).as_posix()
            tracked = self.run(["git", "ls-files", "--error-unmatch", "--", relative], check=False)
            if tracked.returncode == 0:
                raise StageError(f"RAHASIA: {relative} ternyata tracked; tidak akan diisi")
            ignored = self.run(["git", "check-ignore", "-q", "--", relative], check=False)
            if ignored.returncode != 0:
                raise StageError(f"RAHASIA: {relative} tidak di-ignore; jangan tulis secret")
        original = path.read_text(encoding="utf-8-sig") if path.exists() else "# Local secrets; do not commit.\n"
        lines = original.splitlines()
        index = {}
        for i, line in enumerate(lines):
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
            if m: index[m.group(1)] = i
        changed = False
        for k, v in entries.items():
            if v is None: continue
            value = f"{k}={v}"
            if k in index:
                if lines[index[k]] != value:
                    lines[index[k]] = value; changed = True
            else:
                lines.append(value); changed = True
        if changed:
            # Backup may contain secrets. Kept outside repo and never shared automatically.
            if path.exists():
                b = self.backup_dir / path.relative_to(self.root)
                b.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, b)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
            if os.name != "nt": os.chmod(path, 0o600)
        return changed

    def config(self):
        bfile = self.root / "Backend/.env"
        afile = self.root / "Agents/.env"
        ffile = self.root / "Frontend/.env.local"
        b = self.read_env(bfile)
        a = self.read_env(afile)
        # Existing real secret disagreements MUST be resolved by operator.
        def shared(bkey, akey):
            left, right = b.get(bkey), a.get(akey)
            if self.real_secret(left) and self.real_secret(right) and left != right:
                raise StageError(f"Token {bkey}/{akey} berbeda; hentikan sebelum mengubah secret")
            return left if self.real_secret(left) else (right if self.real_secret(right) else secrets.token_urlsafe(36))
        shared_agent = shared("AGENT_API_KEY", "AGENT_API_KEY")
        shared_internal = shared("INTERNAL_API_KEY", "PROCUREMENT_SERVICE_TOKEN")
        gemini = (a.get("LLM_API_KEY") or os.getenv("LLM_API_KEY", "")).strip()
        if not self.real_secret(gemini) and not self.args.no_prompt and sys.stdin.isatty():
            gemini = getpass.getpass("Gemini API key (input tersembunyi; Enter untuk lewati): ").strip()
        bentries = {
            "AGENT_API_URL": "http://127.0.0.1:8001",
            "AGENT_API_KEY": shared_agent,
            "INTERNAL_API_KEY": shared_internal,
        }
        aentries = {
            "AGENT_DATA_MODE": self.args.data_mode,
            "PROCUREMENT_BACKEND_URL": "http://127.0.0.1:8000",
            "PROCUREMENT_SERVICE_TOKEN": shared_internal,
            "AGENT_API_KEY": shared_agent,
            "LLM_MODEL": self.model,
            "LLM_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "LLM_TIMEOUT_SECONDS": "90",
            "AGENT_CHAT_TIMEOUT_SECONDS": "145",
        }
        if self.real_secret(gemini): aentries["LLM_API_KEY"] = gemini
        fentries = {
            "VITE_API_BASE_URL": "/api/v1",
            "VITE_BACKEND_PROXY_TARGET": "http://127.0.0.1:8000",
            "VITE_CHAT_MODE": "live",
            "VITE_AGENT_REQUEST_TIMEOUT_MS": "185000",
        }
        for f, entries in [(bfile, bentries), (afile, aentries), (ffile, fentries)]:
            self.set_env(f, entries)
        self.backend_env = self.read_env(bfile)
        self.agent_env = self.read_env(afile)
        self.record("9B", "PASS", "Agent URL terkonfigurasi", "Backend AGENT_API_URL=http://127.0.0.1:8001; Frontend /api/v1 -> Backend 8000")
        self.record("9C", "PASS" if self.real_secret(self.agent_env.get("LLM_API_KEY")) else "WARN",
                    "Gemini API Key", "Tersedia tanpa ditampilkan" if self.real_secret(self.agent_env.get("LLM_API_KEY")) else "Belum tersedia; live chat memerlukan key")
        db_good = self.db_credentials_ok()
        self.record("9C", "PASS" if db_good else "WARN", "Supabase database",
                    "Konfigurasi database terdeteksi" if db_good else "DATABASE_URL atau parameter DB_* belum lengkap; Backend startup/real E2E akan terhalang")
        self.record("9C", "WARN", "Migrasi DB", "Tidak dijalankan otomatis (membutuhkan persetujuan dan backup DB)")

    def db_credentials_ok(self):
        e = self.backend_env
        db = e.get("DATABASE_URL", "")
        if db and db.startswith("postgresql") and not any(x in db for x in ("<", "REPLACE_", ">")):
            return True
        return all(e.get(x) and not any(y in e[x] for y in ("<", ">", "REPLACE")) for x in ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"))

    def py_in_venv(self, dirname):
        p = self.root / dirname / ".venv"
        return p / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    def install_dependencies(self):
        for folder, extra in [("Agents", None), ("Backend", "backend")]:
            vpy = self.py_in_venv(folder)
            if not vpy.exists():
                self.run([sys.executable, "-m", "venv", str(vpy.parent.parent)],
                         logfile=self.run_dir / f"venv_{folder}.log", timeout=120)
            if folder == "Agents":
                cmd = [str(vpy), "-m", "pip", "install", "-r", "agent_requirements.txt", "-r", "graph_requirements.txt"]
            else:
                cmd = [str(vpy), "-m", "pip", "install", "-e", ".[dev]"]
            self.run(cmd, cwd=self.root / folder,
                     logfile=self.run_dir / f"install_{folder}.log", timeout=850)
            self.record("9B", "PASS", folder + " dependencies", "pip install selesai pada .venv tersendiri")
        if not shutil.which("npm"):
            self.record("9B", "WARN", "Node/npm", "npm tidak tersedia; frontend build/start belum bisa dilakukan")
        else:
            node_modules = self.root / "Frontend/node_modules"
            if not node_modules.exists():
                self.run(["npm.cmd" if os.name == "nt" else "npm", "ci"], cwd=self.root / "Frontend", logfile=self.run_dir / "npm_ci.log", timeout=650)
            self.record("9B", "PASS", "Frontend dependencies", "npm siap")

    def tests(self):
        for folder, testcmd, log in [
            ("Agents", [str(self.py_in_venv("Agents")), "-m", "unittest", "discover", "-s", "tests", "-v"], "agent_tests.log"),
            ("Backend", [str(self.py_in_venv("Backend")), "-m", "pytest", "-q"], "backend_tests.log"),
        ]:
            if not self.py_in_venv(folder).exists():
                self.record("9C", "WARN", folder + " tests", "Python .venv belum ada; jalankan --mode all tanpa --skip-install")
                continue
            try:
                self.run(testcmd, cwd=self.root / folder, logfile=self.run_dir / log, timeout=250)
                self.record("9C", "PASS", folder + " tests", "Seluruh tes yang dijalankan lulus; log=" + log)
            except (StageError, subprocess.TimeoutExpired) as exc:
                self.record("9C", "FAIL", folder + " tests", f"Periksa {log} ({type(exc).__name__})")
        if shutil.which("npm") and (self.root / "Frontend/node_modules").exists():
            try:
                self.run(["npm.cmd" if os.name == "nt" else "npm", "run", "build"], cwd=self.root / "Frontend", logfile=self.run_dir / "frontend_build.log", timeout=220)
                self.record("9C", "PASS", "Frontend build", "npm run build lulus")
            except (StageError, subprocess.TimeoutExpired):
                self.record("9C", "FAIL", "Frontend build", "Lihat frontend_build.log")
        else:
            self.record("9C", "WARN", "Frontend build", "npm / node_modules belum tersedia")
        self.static_checks()

    def static_checks(self):
        front = self.content("Frontend/src/services/chatService.js")
        api = self.content("Frontend/src/services/api.js")
        agent = self.content("Agents/agent_core/graph_api.py")
        backend = self.content("Backend/app/api/v1/endpoints/agents.py")
        checks = [
            ("Frontend live calls REAL Agent proxy", "chatWithAgent(task, referenceId, conversationId, question)" in front),
            ("Frontend requires user auth for Agent", "request('/agents/chat'" in api and ", true, Number(import.meta.env.VITE_AGENT_REQUEST_TIMEOUT_MS" in api),
            ("Backend validates PO/session scope", '_require_reference_access' in backend and "agent_session.user_id != user.id" in backend),
            ("Agent enforces service Bearer", "secrets.compare_digest" in agent),
            ("Backend proxy path exists", "@router.post(\"/chat\")" in backend),
            ("Agent API route exists", "@app.post('/api/v1/agents/chat'" in agent),
        ]
        for label, passed in checks:
            self.record("9C", "PASS" if passed else "FAIL", label, "Ditemukan" if passed else "Kontrak tidak cocok")

    def _http(self, url, headers=None, data=None, timeout=10):
        req = urllib.request.Request(url, headers=headers or {}, data=data)
        if data is not None: req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read(5_000_001)
                if len(raw) > 5_000_000:
                    return response.status, None
                try:
                    parsed = json.loads(raw) if raw else None
                except (ValueError, UnicodeDecodeError):
                    parsed = None  # Frontend serves HTML, not JSON.
                return response.status, parsed
        except urllib.error.HTTPError as exc:
            return exc.code, None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            return 0, None

    def smoke(self):
        agent, payload = self._http("http://127.0.0.1:8001/health")
        back, _ = self._http("http://127.0.0.1:8000/health")
        front, _ = self._http("http://127.0.0.1:5173/")
        self.record("9C", "PASS" if agent == 200 else "FAIL", "Agent :8001/health", f"HTTP={agent}")
        if agent == 200 and payload and payload.get("mode") != self.args.data_mode:
            self.record("9C", "WARN", "Agent data mode", f"Berjalan dalam mode {payload.get('mode')}, target {self.args.data_mode}")
        self.record("9C", "PASS" if back == 200 else "FAIL", "Backend :8000/health", f"HTTP={back}")
        self.record("9C", "PASS" if front == 200 else "WARN", "Frontend :5173", f"HTTP={front}")
        for endpoint in ("http://127.0.0.1:8000/openapi.json", "http://127.0.0.1:8001/openapi.json"):
            code, body = self._http(endpoint)
            good = code == 200 and isinstance(body, dict) and "/api/v1/agents/chat" in body.get("paths", {})
            self.record("9C", "PASS" if good else "FAIL", "OpenAPI " + endpoint.split(":")[2][:5], f"HTTP={code}, agent chat={good}")
        code, _ = self._http("http://127.0.0.1:8001/api/v1/agents/chat", data=b'{}')
        self.record("9C", "PASS" if code == 401 else "FAIL", "Agent tanpa Bearer ditolak", f"HTTP={code}")
        code, _ = self._http("http://127.0.0.1:8000/api/v1/internal/procurement/pos/PO-001")
        self.record("9C", "PASS" if code == 401 else "FAIL", "Backend internal tanpa token ditolak", f"HTTP={code}")
        if back == 200:
            readiness, _ = self._http("http://127.0.0.1:8000/ready")
            self.record("9C", "PASS" if readiness == 200 else "FAIL", "Backend /ready + Supabase DB",
                        f"HTTP={readiness}; database harus benar-benar terjangkau")
            code, _ = self._http(
                "http://127.0.0.1:8000/api/v1/internal/procurement/pos/" + self.args.po_id,
                headers={"X-API-Key": self.backend_env.get("INTERNAL_API_KEY", "")},
            )
            self.record("9C", "PASS" if code == 200 else "WARN", "Backend Agent read",
                        f"HTTP={code}; 404 artinya PO belum ada, 503 artinya DB belum siap")
        user = os.getenv("PROCUREGUARD_USER_TOKEN", "")
        if user and back == 200:
            body = json.dumps({"task": "negotiation", "reference_id": self.args.po_id,
                               "question": "Analisis PO ini dan lakukan fraud precheck"}).encode()
            req = urllib.request.Request("http://127.0.0.1:8000/api/v1/agents/chat",
                data=body, headers={"Authorization": "Bearer " + user, "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=180) as response:
                    obj = json.load(response)
                    ok = response.status == 200 and obj.get("requires_approval") is True and obj.get("precheck") is not None
                    self.record("9C", "PASS" if ok else "FAIL", "REAL user->Backend->Agent chat", f"HTTP={response.status}; verified={ok}")
            except urllib.error.HTTPError as exc:
                self.record("9C", "FAIL", "REAL user->Backend->Agent chat", f"HTTP={exc.code}; lihat log backend dan pastikan PO dimiliki user")
            except Exception as exc:
                self.record("9C", "FAIL", "REAL user->Backend->Agent chat", type(exc).__name__)
        else:
            self.record("9C", "WARN", "Real user->Backend->Agent E2E", "Belum diuji; set PROCUREGUARD_USER_TOKEN dan --po-id PO milik user")

    def start(self):
        if not self.db_credentials_ok():
            self.record("9B", "FAIL", "Startup Backend", "DATABASE_URL/DB_* belum dikonfigurasi; tidak akan memakai mock secara diam-diam")
            return
        for folder in ("Backend", "Agents"):
            if not self.py_in_venv(folder).exists():
                self.record("9B", "FAIL", "Startup " + folder, ".venv tidak tersedia; install dependencies dulu")
                return
        # Stop rather than occupying an unknown existing process.
        for port in (8000, 8001):
            code, _ = self._http(f"http://127.0.0.1:{port}/health", timeout=1)
            if code:
                self.record("9B", "WARN", "Port " + str(port), "Sudah dipakai oleh HTTP service; skrip tidak menghentikan proses lain")
                return
        service_defs = [
            ("Agent", "Agents", 8001, [str(self.py_in_venv("Agents")), "-m", "uvicorn", "agent_core.graph_api:app", "--host", "127.0.0.1", "--port", "8001"]),
            ("Backend", "Backend", 8000, [str(self.py_in_venv("Backend")), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]),
        ]
        for service, folder, port, cmd in service_defs:
            env = dict(os.environ)
            if folder == "Agents": env.update(self.agent_env)
            # Backend Pydantic Settings loads .env from workdir.
            log = open(self.run_dir / f"{service.lower()}_runtime.log", "w", encoding="utf-8")
            flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            p = subprocess.Popen(cmd, cwd=self.root / folder, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, creationflags=flags,
                                 start_new_session=(os.name != "nt"))
            log.close()
            self.processes.append({"name": service, "pid": p.pid, "port": port})
            status = 0
            for _ in range(30):
                if p.poll() is not None: break
                status, _ = self._http(f"http://127.0.0.1:{port}/health", timeout=1)
                if status == 200: break
                time.sleep(0.4)
            else: status = 0
            self.record("9B", "PASS" if status == 200 else "FAIL", service + " running", f"HTTP={status}; PID={p.pid}")
            if status != 200:
                self.record("9B", "WARN", service + " log", f"Lihat {service.lower()}_runtime.log di laporan")
                return
        if shutil.which("npm") and (self.root / "Frontend/node_modules").exists():
            code, _ = self._http("http://127.0.0.1:5173/", timeout=1)
            if code:
                self.record("9B", "WARN", "Frontend :5173", "Port sudah dipakai, bukan proses skrip")
            else:
                logfile = open(self.run_dir / "frontend_runtime.log", "w", encoding="utf-8")
                p = subprocess.Popen(["npm.cmd" if os.name == "nt" else "npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
                                    cwd=self.root / "Frontend", stdout=logfile,
                                    stderr=subprocess.STDOUT,
                                    creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
                                    start_new_session=(os.name != "nt"))
                logfile.close()
                self.processes.append({"name": "Frontend", "pid": p.pid, "port": 5173})
                for _ in range(30):
                    code, _ = self._http("http://127.0.0.1:5173/", timeout=1)
                    if code == 200: break
                    if p.poll() is not None: break
                    time.sleep(0.4)
                self.record("9B", "PASS" if code == 200 else "FAIL", "Frontend :5173", f"HTTP={code}; PID={p.pid}")
        (self.run_dir / "processes.json").write_text(json.dumps(self.processes, indent=2), encoding="utf-8")
        # Print stop command using PIDs; do not modify another process without a check.
        self.record("9B", "PASS", "Proses startup", "Terminal dapat ditutup; PID dicatat dalam folder laporan")

    def deploy_check(self):
        self.record("9D", "PASS", "Agent URL internal", "http://127.0.0.1:8001 (Backend AGENT_API_URL), bukan URL publik")
        templates = ("deploy/compose.vultr.yml", "deploy/nginx.https.template.conf", "deploy/Agent.Dockerfile")
        ready = all((self.root / name).is_file() for name in templates)
        self.record("9D", "PASS" if ready else "WARN", "Template Docker/Nginx",
                    "Tersedia" if ready else "Belum dibuat (jalankan --mode apply/all)")
        if not self.args.domain:
            self.record("9D", "WARN", "URL publik HTTPS", "Belum bisa dibuat: domain/Vultr VPS/cert belum diberikan")
        else:
            if not re.fullmatch(r"(?=.{1,253}$)[A-Za-z0-9.-]+", self.args.domain):
                self.record("9D", "FAIL", "Domain", "Format domain salah")
            else:
                self.record("9D", "WARN", "Domain target", "https://" + self.args.domain + " (belum terverifikasi online)")
        self.record("9D", "WARN", "Deployment nyata", "Jalankan Docker Compose di VPS Linux berizin, pasang TLS, migrasi DB terkontrol, uji Supabase & PO; skrip lokal tidak memiliki akses VPS")
        self.record("9D", "WARN", "LangGraph memory", "InMemorySaver tidak persisten dan tidak aman untuk multi-worker produksi")

    def deploy(self):
        """Opt-in Stage9D on the VPS itself, NOT a background/remote action."""
        if platform.system() != "Linux":
            raise StageError("Deployment harus dijalankan DI VPS Linux; Windows hanya menyiapkan template")
        if not self.args.domain or not re.fullmatch(r"(?=.{1,253}$)[A-Za-z0-9.-]+", self.args.domain):
            raise StageError("--domain wajib dan harus berupa hostname valid; siapkan DNS + SSL sebelum deploy")
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            raise StageError("Jalankan --mode deploy sebagai root/sudo di VPS yang kamu kelola")
        required = [("docker", "Docker"), ("nginx", "Nginx"), ("systemctl", "systemd"), ("npm", "Node/npm")]
        for cmd, label in required:
            if not shutil.which(cmd):
                raise StageError(f"{label} tidak terpasang di VPS")
        if not self.db_credentials_ok():
            raise StageError("Backend/.env tidak memiliki database Supabase valid; DB tidak akan dimigrasi otomatis")
        if not self.real_secret(self.agent_env.get("LLM_API_KEY")):
            raise StageError("Gemini key belum dikonfigurasi pada Agents/.env")
        for bk, ak in [("AGENT_API_KEY", "AGENT_API_KEY"),
                       ("INTERNAL_API_KEY", "PROCUREMENT_SERVICE_TOKEN")]:
            if not self.real_secret(self.backend_env.get(bk)) or self.backend_env.get(bk) != self.agent_env.get(ak):
                raise StageError("Token Backend/Agent belum sama: " + bk)
        cert = pathlib.Path(f"/etc/letsencrypt/live/{self.args.domain}/fullchain.pem")
        key = pathlib.Path(f"/etc/letsencrypt/live/{self.args.domain}/privkey.pem")
        if not cert.is_file() or not key.is_file():
            raise StageError("TLS certificate belum ada di /etc/letsencrypt/live/DOMAIN; jangan publish HTTP tanpa HTTPS")
        if not (self.root / "Frontend/dist/index.html").is_file():
            raise StageError("Frontend/dist belum ter-build; jalankan --mode test/npm run build")
        self.run(["docker", "compose", "-f", "deploy/compose.vultr.yml", "config", "-q"],
                 logfile=self.run_dir / "compose_check.log", timeout=30)
        self.record("9D", "PASS", "Docker compose config", "Valid untuk Linux host networking")

        # Compose services bind localhost; no direct public Agent port.
        self.run(["docker", "compose", "-f", "deploy/compose.vultr.yml", "up", "-d", "--build"],
                 logfile=self.run_dir / "compose_deploy.log", timeout=900)
        self.record("9D", "PASS", "Service deployment", "Backend+Agent Compose mulai; port 8000/8001 loopback")
        for port in (8000, 8001):
            ready = False
            for _ in range(40):
                code, _ = self._http(f"http://127.0.0.1:{port}/health", timeout=2)
                if code == 200:
                    ready = True; break
                time.sleep(1)
            self.record("9D", "PASS" if ready else "FAIL", f"Service port {port}",
                        "HTTP 200" if ready else "Belum siap; cek docker compose logs")
        if any(f.level == "FAIL" and f.stage == "9D" for f in self.findings):
            return

        config_template = self.content("deploy/nginx.https.template.conf")
        rendered = config_template.replace("DOMAIN_NAME", self.args.domain)
        dest = pathlib.Path("/etc/nginx/sites-available/procureguard.conf")
        link = pathlib.Path("/etc/nginx/sites-enabled/procureguard.conf")
        if dest.exists():
            backup = self.run_dir / "previous_nginx.conf"
            shutil.copy2(dest, backup)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered, encoding="utf-8")
        if not link.exists():
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(dest)
        try:
            self.run(["nginx", "-t"], logfile=self.run_dir / "nginx_check.log", timeout=30)
        except StageError:
            if (self.run_dir / "previous_nginx.conf").is_file():
                shutil.copy2(self.run_dir / "previous_nginx.conf", dest)
            else:
                link.unlink(missing_ok=True)
                dest.unlink(missing_ok=True)
            raise StageError("Nginx config gagal; konfigurasi sebelumnya dikembalikan")

        # Deployment asset copy occurs only after TLS config validation.
        www = pathlib.Path("/var/www/procureguard/frontend")
        www.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.root / "Frontend/dist", www, dirs_exist_ok=True)
        self.run(["systemctl", "reload", "nginx"], logfile=self.run_dir / "nginx_reload.log", timeout=45)
        code, _ = self._http(f"https://{self.args.domain}/health", timeout=15)
        self.record("9D", "PASS" if code == 200 else "FAIL", "HTTPS Backend publik",
                    f"HTTPS /health -> HTTP {code}")
        self.record("9D", "WARN", "Keamanan rilis",
                    "Masih wajib uji Supabase auth, PO milik user, persetujuan admin, migrasi DB, dan InMemorySaver")

    def report(self):
        levels = {x: sum(f.level == x for f in self.findings) for x in ("PASS", "WARN", "FAIL")}
        payload = {
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo": str(self.root),
            "counts": levels,
            "changed_files": self.changed,
            "findings": [asdict(f) for f in self.findings],
            "processes": self.processes,
            "public_agent_url": None,
            "internal_agent_url": "http://127.0.0.1:8001",
        }
        (self.run_dir / "ringkasan.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = ["# ProcureGuard Stage 9 audit / rollout", "", f"Root: `{self.root}`", "",
                 f"**PASS={levels['PASS']} WARN={levels['WARN']} FAIL={levels['FAIL']}**", "",
                 "## Temuan", ""]
        lines.extend(f"- **{f.level} {f.stage}** {f.subject}: {f.detail}" for f in self.findings)
        lines += ["", "## File sumber diperbarui", ""] + [f"- `{p}`" for p in self.changed]
        lines += ["", "**Tidak ada commit, push, Alembic migration, atau pembocoran secret oleh skrip.**"]
        (self.run_dir / "LAPORAN_STAGE9.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n====== HASIL STAGE 9 ======", flush=True)
        print(" ".join(f"{k}={v}" for k, v in levels.items()))
        print("Laporan:", self.run_dir / "LAPORAN_STAGE9.md")
        print("JSON   :", self.run_dir / "ringkasan.json")
        print("Backup:", self.backup_dir)
        print("Agent URL internal: http://127.0.0.1:8001")
        print("Backend URL internal: http://127.0.0.1:8000")
        print("Frontend URL local: http://127.0.0.1:5173")
        if self.args.mode in ("apply", "all"):
            print("Perubahan lokal perlu direview; TIDAK ada git add/commit/push.")
        return 1 if levels["FAIL"] else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Path root VultrAgents (bukan Backend/ atau Agents/)")
    parser.add_argument("--mode", choices=["plan", "apply", "test", "start", "status", "deploy", "all"], default="all")
    parser.add_argument("--skip-pull", action="store_true", help="Skip 9A; untuk patch pada ZIP/snapshot offline")
    parser.add_argument("--skip-install", action="store_true", help="Skip pip install/npm ci (pakai dependencies existing)")
    parser.add_argument("--no-prompt", action="store_true", help="Jangan minta Gemini key secara interaktif")
    parser.add_argument("--data-mode", choices=["http", "mock"], default="http", help="Default HTTP asli, mock hanya demo")
    parser.add_argument("--model", default="gemini-3.5-flash-lite")
    parser.add_argument("--po-id", default="PO-001", help="PO milik user untuk E2E bila PROCUREGUARD_USER_TOKEN tersedia")
    parser.add_argument("--domain", default="", help="Hanya untuk verifikasi rencana deployment, bukan domain aktif")
    args = parser.parse_args()
    ctx = Stage9(args)
    try:
        ctx.check_root()
    except StageError as exc:
        print("[FATAL]", exc)
        return 2
    print("ProcureGuard Stage9 - 9A Git, 9B ports, 9C integration, 9D Vultr", flush=True)
    print("Repository:", ctx.root, "\nLog/backup:", ctx.run_dir, flush=True)
    if args.mode == "plan":
        print("Rencana: pull --ff-only (jika bersih), patch live chat + timeout, konfigurasi gitignored, tests, startup, deploy checks.")
        ctx.record("9A", "PASS", "Snapshot", "Source terdeteksi; tidak ada perubahan pada mode plan")
        ctx.record("9B", "WARN", "Source & secret", "Belum diubah; jalankan --mode all setelah review")
        ctx.deploy_check()
        return ctx.report()
    if args.mode in ("apply", "all"):
        if not args.skip_pull:
            ctx.execute("Git Pull", "9A", ctx.stage9a_pull)
            if any(f.stage == "9A" and f.level == "FAIL" for f in ctx.findings):
                return ctx.report()
        ctx.execute("Satu batch patch Frontend-Backend-Agent", "9B", ctx.patch)
        if any(f.stage == "9B" and f.level == "FAIL" for f in ctx.findings):
            return ctx.report()
        ctx.execute("Konfigurasi URL dan secret antarservice", "9B", ctx.config)
        if not args.skip_install:
            ctx.execute("Install dependencies", "9B", ctx.install_dependencies)
        else:
            ctx.record("9B", "WARN", "Instalasi dependencies", "Dilewati (--skip-install)")
        ctx.tests()
        if args.mode == "all":
            ctx.start()
            ctx.smoke()
        ctx.deploy_check()
    elif args.mode == "test":
        ctx.backend_env = ctx.read_env(ctx.root / "Backend/.env")
        ctx.agent_env = ctx.read_env(ctx.root / "Agents/.env")
        ctx.tests()
        ctx.smoke()
        ctx.deploy_check()
    elif args.mode == "start":
        ctx.backend_env = ctx.read_env(ctx.root / "Backend/.env")
        ctx.agent_env = ctx.read_env(ctx.root / "Agents/.env")
        ctx.start()
        ctx.smoke()
    elif args.mode == "deploy":
        ctx.backend_env = ctx.read_env(ctx.root / "Backend/.env")
        ctx.agent_env = ctx.read_env(ctx.root / "Agents/.env")
        ctx.execute("Deploy Vultr Linux berizin", "9D", ctx.deploy)
    elif args.mode == "status":
        ctx.backend_env = ctx.read_env(ctx.root / "Backend/.env")
        ctx.agent_env = ctx.read_env(ctx.root / "Agents/.env")
        ctx.smoke()
        ctx.deploy_check()
    return ctx.report()


if __name__ == "__main__":
    sys.exit(main())
