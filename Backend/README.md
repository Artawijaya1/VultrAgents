# Life Purpose API

FastAPI backend with PostgreSQL (Supabase), SQLAlchemy 2, Alembic, Supabase Auth, and authenticated users/items APIs.

## Requirements

- Python 3.11+
- A Supabase project with its database credentials

## Local setup

From this directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set these Supabase project values in `.env`. For the database, either provide a complete `DATABASE_URL`:

- `DATABASE_URL`: the Supabase PostgreSQL connection string in `psycopg` SQLAlchemy URL form:

```text
postgresql+psycopg://postgres:<URL-encoded-password>@<host>:5432/postgres?sslmode=require
```

- `SUPABASE_URL`: project URL from **Project Settings → API**.
- `SUPABASE_ANON_KEY`: project publishable (or legacy anon) key from **Project Settings → API Keys**. This is not a service-role key.

Or provide the connection parameters separately; the backend also accepts the lowercase variable names shown here:

```dotenv
user=postgres.<PROJECT_REF>
password=<DATABASE_PASSWORD>
host=<POOLER_HOST>
port=6543
dbname=postgres
```

The backend builds a `postgresql+psycopg` URL and safely encodes the password. A valid `DATABASE_URL` takes precedence; if it is malformed, the separate parameters are used. Use the exact connection details shown in **Project Settings → Database → Connect**, especially the pooler username when using the transaction pooler. Never commit `.env`.

Generate a private API key for agent-only endpoints and store it as `INTERNAL_API_KEY` in `.env` (do not commit or expose it in frontend code):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Send it in the `X-API-Key` header when calling `/api/v1/internal/*`. These endpoints return `503` until a key is configured, `401` for a missing/invalid key, and `501` when the key is valid but the endpoint's business logic has not yet been implemented. All paths and methods listed in `MD.md` are registered and visible in `/docs`. Procurement workflow placeholders return `501`; do not connect them to real business data until their authorization and business logic are implemented.

Apply the schema migrations and start the development server:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`; health and database readiness checks are at `/health` and `/ready`.

## Supabase Auth

Create and manage accounts through Supabase Auth (Dashboard or a trusted Supabase Auth client). The backend proxies:

- `POST /api/v1/auth/login` with `{ "email": "...", "password": "..." }`
- `POST /api/v1/auth/refresh` with `{ "refresh_token": "..." }`
- `POST /api/v1/auth/logout` with `Authorization: Bearer <access_token>`
- `GET /api/v1/auth/me` and `PATCH /api/v1/auth/me` with a bearer access token

Supabase issues and rotates access/refresh tokens. The backend validates every bearer token against Supabase Auth's `/auth/v1/user` endpoint and creates/updates the matching local profile by Supabase user UUID. Passwords are never stored in the application database. Store tokens using the frontend's approved session strategy and never put the internal agent API key in browser code.

All `/api/v1/users` administration routes require a Supabase `app_metadata.role = "admin"` or `"admin"` in `app_metadata.roles`. Set this claim only from a trusted admin environment; users cannot grant themselves an `app_metadata` role. `/api/v1/users/me` is available to any authenticated user. Items are private to the authenticated owner; the backend ignores client-supplied ownership except to reject attempts to create an item for another user.

To grant the initial administrator, use the Supabase SQL Editor from a trusted project-admin account and replace the UUID with the account's Supabase Auth user ID:

```sql
UPDATE auth.users
SET raw_app_meta_data =
    COALESCE(raw_app_meta_data, '{}'::jsonb) || '{"role":"admin"}'::jsonb
WHERE id = '<SUPABASE_AUTH_USER_UUID>';
```

Sign out and sign in again after changing the role so Supabase issues a token with the updated `app_metadata`.

The database migration adds a nullable unique `users.auth_user_id` to preserve existing records. If an existing local profile has the same email but is not linked to the Supabase UUID, the backend will not silently link it; an administrator must review and reconcile that profile.

## Docker

After creating and configuring `.env`, run:

```powershell
docker compose up --build
```

## API

- `GET /health`, `GET /ready`
- `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, `GET/PATCH /api/v1/auth/me`
- `GET/PATCH /api/v1/users/me`; admin-only `GET /api/v1/users`, `GET /api/v1/users/{id}`, and `PATCH /api/v1/users/{id}`
- Authenticated, owner-scoped `POST/GET /api/v1/items/`, `GET/PATCH/DELETE /api/v1/items/{item_id}`

## Tests

```powershell
python -m pip install -e ".[dev]"
pytest
```

Tests use an isolated in-memory SQLite database and do not connect to Supabase.
