# Life Purpose API

FastAPI starter backend with PostgreSQL (Supabase), SQLAlchemy 2, Alembic, and basic users/items CRUD. Authentication is intentionally not enabled yet.

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

Set `DATABASE_URL` in `.env` to the Supabase PostgreSQL connection string. Use the `psycopg` SQLAlchemy URL form:

```text
postgresql+psycopg://postgres:<URL-encoded-password>@<host>:5432/postgres?sslmode=require
```

Use the Supabase connection details shown in **Project Settings → Database**. If using the transaction pooler, use the pooler host, port, and username supplied by Supabase. URL-encode special characters in the password. Never commit `.env`.

Generate a private API key for agent-only endpoints and store it as `INTERNAL_API_KEY` in `.env` (do not commit or expose it in frontend code):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Send it in the `X-API-Key` header when calling `/api/v1/internal/*`. These endpoints return `503` until a key is configured, `401` for a missing/invalid key, and `501` when the key is valid but the endpoint's business logic has not yet been implemented. All paths and methods listed in `MD.md` are registered and visible in `/docs`. Except `/health` and `/ready`, the other listed API routes are currently `501` placeholders and are not protected by the agent key; add user authentication before implementing them.

Apply the initial schema and start the development server:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`; health and database readiness checks are at `/health` and `/ready`.

## Docker

After creating and configuring `.env`, run:

```powershell
docker compose up --build
```

## API

- `GET /health`
- `POST /api/v1/users/`, `GET /api/v1/users/`, `GET /api/v1/users/{user_id}`, `PATCH /api/v1/users/{user_id}`, `DELETE /api/v1/users/{user_id}`
- `POST /api/v1/items/`, `GET /api/v1/items/`, `GET /api/v1/items/{item_id}`, `PATCH /api/v1/items/{item_id}`, `DELETE /api/v1/items/{item_id}`

The auth router and token schema are reserved for a later implementation. The CRUD routes are not protected until authentication is added.

## Tests

```powershell
python -m pip install -e ".[dev]"
pytest
```

Tests use an isolated in-memory SQLite database and do not connect to Supabase.
