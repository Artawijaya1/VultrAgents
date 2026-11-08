# ProcureMind / ProcureGuard

This repository contains a procurement intelligence application composed of a **React frontend**, a **FastAPI backend**, and a **LangGraph-based Agent service**. The application provides an interface for procurement data, risk and fraud analysis, negotiation, and Agent chat. Actions that require approval remain subject to human review; the Agent does not execute payments or modify purchase orders.

## Repository structure

| Folder/file | Purpose |
|---|---|
| [`Frontend/`](./Frontend/) | React + Vite interface for the landing page and dashboard. |
| [`Backend/`](./Backend/) | FastAPI REST API, Supabase Auth, PostgreSQL, Alembic migrations, and a secure proxy to the Agent. |
| [`Agents/`](./Agents/) | LangGraph Agent API, fraud and negotiation workflows, MCP tools, and procurement data integration. |
| [`deploy/`](./deploy/) | Docker Compose and Nginx templates for deploying to a single Linux VPS. |
| [`procureguard_stage9.py`](./procureguard_stage9.py) | Stage 9 integration and verification script. |

## Architecture

```text
Browser ── HTTPS ──> Nginx ──> Frontend (static files)
                              └── /api/* ──> Backend :8000
                                               └── Agent :8001
                                                    └── Backend internal procurement API
```

- The browser communicates only with the Backend. The Agent is never called directly by the browser.
- The Backend validates user authentication and purchase order access before forwarding requests to the Agent.
- The Backend and Agent use server-to-server shared secrets. Never expose these secrets to the Frontend.
- The Agent can use sample data (`mock`) or read from the Backend procurement API (`http`).
- For Vultr deployments, the Backend and Agent bind only to `127.0.0.1`; Nginx terminates public TLS.

## Requirements

- Python 3.11 or later
- Node.js and npm
- PostgreSQL through a Supabase project to run the Backend
- Docker Engine, the Docker Compose plugin, and Nginx for a Linux VPS deployment
- An LLM provider API key only if LLM chat is needed

## Local development

Run each component in a separate terminal.

### 1. Backend

```powershell
cd Backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Add your database and Supabase credentials to `Backend/.env`. Important variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` or `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | Supabase PostgreSQL connection. |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` | Supabase authentication. Use a publishable/anon key, not a service-role key. |
| `INTERNAL_API_KEY` | Secret for internal procurement endpoints and Agent data access. |
| `AGENT_API_URL`, `AGENT_API_KEY` | Agent URL and secret, which must match the values in `Agents/.env`. |
| `CORS_ORIGINS` | Allowed browser origins, for example `["http://localhost:5173"]`. |

Generate a secret with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set `INTERNAL_API_KEY` and `AGENT_API_KEY` to two strong, distinct secrets. Do not commit `.env` files.

Then, from the `Backend` folder:

```powershell
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Migrations modify the database schema; verify the target database before running them. Optionally, create synthetic data for Agent testing with `python .\scripts\seed_agent_demo.py`.

### 2. Agents

In a new terminal:

```powershell
cd Agents
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.graph.example .env
```

Configure `Agents/.env`:

```dotenv
AGENT_DATA_MODE=http
AGENT_API_KEY=<match the Backend AGENT_API_KEY>
PROCUREMENT_BACKEND_URL=http://127.0.0.1:8000
PROCUREMENT_SERVICE_TOKEN=<match the Backend INTERNAL_API_KEY>
LLM_API_KEY=<provider API key, if using LLM chat>
LLM_MODEL=<tool-calling model name>
LLM_BASE_URL=<optional OpenAI-compatible provider URL>
```

Start the Agent API:

```powershell
uvicorn agent_core.graph_api:app --reload --host 127.0.0.1 --port 8001
```

Use `AGENT_DATA_MODE=mock` for sample data without reading from the Backend database. The `http` data mode requires the Backend to be running and the internal token to match. The Agent endpoint is protected by `Authorization: Bearer <AGENT_API_KEY>` and must not be exposed directly to the internet.

### 3. Frontend

In a new terminal:

```powershell
cd Frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

The Frontend is available at the URL displayed by Vite (default: `http://localhost:5173`). The local configuration in `Frontend/.env.example` uses the Vite proxy to reach the Backend at `http://127.0.0.1:8000`. For deployment, `VITE_API_BASE_URL` must point to a Backend API accessible to the browser; never put server secrets in `VITE_*` variables.

## API and authentication

- Backend: `http://127.0.0.1:8000/docs`
- Agent: `http://127.0.0.1:8001/docs`
- Backend health: `GET /health`; database readiness: `GET /ready`
- Supabase auth: `/api/v1/auth/*`
- Agent run/chat and approvals: `/api/v1/agents/*`, `/api/v1/approvals/*`
- Server-only internal procurement reads: `/api/v1/internal/procurement/*`

Create user accounts through Supabase Auth. User administration endpoints require an admin role in `app_metadata`; set this role only from a trusted environment. See [`Backend/README.md`](./Backend/README.md) for details about database connections, admin roles, endpoints, and API limitations.

Some procurement workflows are still previews, and related endpoints may return HTTP 501. Chat uses an LLM when provider credentials are configured. For details about integration behavior and approvals, see [`Frontend/CHAT_INTEGRATION.md`](./Frontend/CHAT_INTEGRATION.md) and [`Agents/docs/INTEGRATION_CONTRACT.md`](./Agents/docs/INTEGRATION_CONTRACT.md).

## Testing and build

Backend, from the `Backend` folder:

```powershell
pytest
```

Agents, from the `Agents` folder:

```powershell
python -m unittest discover -s tests -v
```

Build the Frontend, from the `Frontend` folder:

```powershell
npm run build
```

## Deploying to Vultr

The full deployment guide is available in [`deploy/STAGE9_DEPLOYMENT.md`](./deploy/STAGE9_DEPLOYMENT.md). In summary:

1. Prepare a Linux VPS, domain/DNS, Docker Engine with the Compose plugin, and a TLS certificate.
2. Create `Backend/.env` and `Agents/.env` on the server; provide Supabase credentials and matching server-to-server secrets. Do not commit secrets or send them through the Frontend.
3. Review the changes and configuration, then run this command from the repository root on the VPS:

   ```bash
   docker compose -f deploy/compose.vultr.yml up -d --build
   ```

4. Compose does **not** run database migrations automatically. After backing up the database, verifying the target, and approving maintenance, run migrations deliberately:

   ```bash
   docker compose -f deploy/compose.vultr.yml exec backend alembic upgrade head
   ```

5. Build the Frontend by running `npm ci` and then `npm run build` from `Frontend/`. Copy the contents of `Frontend/dist` to `/var/www/procureguard/frontend`.
6. Configure [`deploy/nginx.https.template.conf`](./deploy/nginx.https.template.conf) for your domain and certificate, validate it with `nginx -t`, then test login, PO access, chat, approvals, and denial of cross-user access.

This Compose deployment is for Linux VPS environments because it uses `network_mode: host`; both services bind to loopback. A public Agent subdomain is not required. Do not expose ports 8000 or 8001 to the internet.

## Security and limitations

- Do not commit `.env` files, Supabase tokens, LLM API keys, or internal secrets.
- Do not put `INTERNAL_API_KEY`, `AGENT_API_KEY`, or `PROCUREMENT_SERVICE_TOKEN` in browser code or configuration.
- Use HTTPS for the Frontend and public API. Frontend session tokens are stored in `sessionStorage`; protect the application against script injection/XSS.
- Mock mode and detection results are analytical aids, not proof or a legal determination that fraud occurred.
- Approvals record decisions by authorized users; the Agent does not send emails, approve transactions, make payments, or modify procurement data.
- For component-specific setup information, see [`Backend/README.md`](./Backend/README.md), [`Frontend/README.md`](./Frontend/README.md), and [`Agents/AGENT_GUIDE.md`](./Agents/AGENT_GUIDE.md).
