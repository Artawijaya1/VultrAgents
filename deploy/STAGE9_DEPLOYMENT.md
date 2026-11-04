# ProcureGuard Stage 9: Satu VPS, Backend 8000, Agent 8001

- Frontend: `https://DOMAIN_NAME/`, requests same-origin `/api/v1`.
- Backend: private `http://127.0.0.1:8000`, proxied by HTTPS Nginx.
- Agent URL: **`http://127.0.0.1:8001`** (internal, configured in Backend `.env` as `AGENT_API_URL`).
- Agent reads procurement Backend `http://127.0.0.1:8000` with `PROCUREMENT_SERVICE_TOKEN` = Backend `INTERNAL_API_KEY`.
- Backend calls Agent with `AGENT_API_KEY` matching Agent `AGENT_API_KEY`.
- Frontend NEVER gets those secrets. `VITE_CHAT_MODE=live` is required for real chat.

## Local Windows

Run `python procureguard_stage9.py --repo "D:\Kuliah Semester 3\VultrAgents" --mode all`.
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
