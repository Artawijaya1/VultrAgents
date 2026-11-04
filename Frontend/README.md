# PROCUREMIND AI Frontend

AI-powered procurement intelligence interface built with React, Vite, React Router, Recharts, Framer Motion, and Lucide. Plain JavaScript (JSX) — no TypeScript configuration.

## Getting started

```bash
npm install
npm run dev
```

Start the FastAPI backend separately from `../Backend`:

```powershell
uvicorn app.main:app --reload
```

Copy `.env.example` to `.env` if the backend uses a different local address. The Vite development server proxies `/api`, `/health`, and `/ready` to `http://127.0.0.1:8000`. Set `VITE_BACKEND_PROXY_TARGET` if needed. For a deployed frontend, set `VITE_API_BASE_URL` to the backend API base URL (for example `https://api.example.com/api/v1`) and configure the backend CORS origins.

The landing page is at `/`; sign in at `/login` with an account provisioned in Supabase Auth. Authenticated API data management is at `/dashboard/data`, and the backend connection page is at `/dashboard/api`.

The data page uses the v1 auth/profile endpoints, owner-scoped item CRUD, and admin-only user listing/updates. User creation and deletion are not exposed by the backend; provision accounts in Supabase Auth. The access and rotating refresh tokens are held in `sessionStorage` for the current browser tab. This avoids persistent browser storage, but JavaScript running on the page can access the tokens; use HTTPS and protect the frontend against script injection. Never put the internal agent `X-API-Key` in frontend environment variables or browser code.

Negotiation and most procurement workflows are still previews because their backend routes currently return HTTP 501. The data page requires valid Supabase configuration and an applied backend database migration.

Other module previews are available at `/dashboard`, `/negotiation`, and `/fraud-detection`.

## Build

```bash
npm run build
```
