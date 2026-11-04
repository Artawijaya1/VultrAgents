my-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Entry point, inisialisasi FastAPI, include router
│   │
│   ├── core/                    # Hal-hal inti yang dipakai seluruh aplikasi
│   │   ├── config.py            # Settings (pydantic-settings), baca dari .env
│   │   ├── security.py          # Hash password, JWT, OAuth2
│   │   ├── logging.py           # Konfigurasi logging
│   │   └── exceptions.py        # Custom exception & handler global
│   │
│   ├── api/                     # Layer HTTP (routing)
│   │   ├── deps.py              # Dependency umum (get_db, get_current_user)
│   │   └── v1/
│   │       ├── router.py        # Gabungan semua router v1
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── users.py
│   │           └── items.py
│   │
│   ├── models/                  # SQLAlchemy ORM models (tabel database)
│   │   ├── base.py
│   │   ├── user.py
│   │   └── item.py
│   │
│   ├── schemas/                 # Pydantic schemas (request & response)
│   │   ├── user.py
│   │   ├── item.py
│   │   └── token.py
│   │
│   ├── crud/                    # Akses data (repository layer)
│   │   ├── base.py              # CRUD generik
│   │   ├── user.py
│   │   └── item.py
│   │
│   ├── services/                # Business logic
│   │   ├── auth_service.py
│   │   └── user_service.py
│   │
│   ├── db/
│   │   ├── session.py           # Engine & session factory
│   │   └── init_db.py           # Seeding data awal
│   │
│   ├── middlewares/             # Custom middleware (CORS, logging, rate limit)
│   ├── utils/                   # Helper kecil yang tidak punya domain
│   └── tasks/                   # Background jobs (Celery / ARQ), opsional
│
├── migrations/                  # Alembic
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── conftest.py              # Fixture (test client, test DB)
│   ├── api/
│   │   └── test_users.py
│   ├── services/
│   └── crud/
│
├── scripts/                     # Script operasional (seed, backup, dll.)
├── .env                         # Jangan di-commit
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml               # Atau requirements.txt
└── README.md



APi Key 

Yang masih kurang di /internal (agents)
Kelompok	Endpoint tambahan	Kenapa dibutuhkan
Data baca	GET /purchase-orders/{id}/versions	Agent perlu membandingkan versi PO sebelum dan sesudah perubahan
	GET /vendors/{id}/performance	Konteks negosiasi dan analisis dampak
	GET /policies	Ambang batas dampak, batas approval, hari follow-up (jangan di-hardcode di agent)
	GET /invoices, GET /invoices/{id}	Sumber data fraud (duplikasi invoice, transaksi di bawah batas approval)
Workflow	GET /change-requests/{id}	Membaca status dan hasil analisis
	POST /change-requests/{id}/reject	Cabang tolak perubahan
	POST /purchase-orders/{id}/follow-ups	Mencatat follow-up (kirimnya tetap lewat approval)
Komunikasi	GET /communications/{id}	Membaca email vendor masuk
	POST /communications/{id}/classification	Menyimpan hasil klasifikasi: konfirmasi, minta perubahan, atau lainnya
Negosiasi	GET /negotiations/{id}	Status sesi dan opsi yang dipilih manusia
	PATCH /negotiations/{id}/drafts/{draft_id}	Revisi draf berdasarkan masukan officer
Fraud	GET /fraud/rules	Aturan dan ambang batas yang berlaku
	POST /fraud/alerts	Agent atau rule engine menulis alert baru
	GET /fraud/scans/{id}	Status dan hasil scan
Kelompok    Endpoint
Data baca    GET /purchase-orders/{id}, /vendors/{id}, /contracts/{id}, /contracts/search, /purchase-history, /price-history, /vendors/{id}/bank-accounts
Workflow    POST /purchase-orders/{id}/confirmations, /change-requests, /change-requests/{id}/analyze, /change-requests/{id}/accept
Komunikasi    POST /communications/draft, GET /purchase-orders/{id}/communications
Negosiasi    POST /negotiations/{id}/options, /negotiations/{id}/drafts, GET /negotiations/{id}/context
Fraud    POST /fraud/scans, GET /fraud/alerts/{id}, PATCH /fraud/alerts/{id} (isi penjelasan)
Approval    POST /approvals (ajukan), GET /approvals/{id} (cek status) 
Kelompok	Endpoint
Auth & user	POST /auth/login, /refresh, /logout; GET/PATCH /users/me
Chat	POST/GET /conversations, GET /conversations/{id}/messages, POST /conversations/{id}/messages (SSE), POST /messages/{id}/feedback
Runs	GET /runs/{id}, GET /runs/{id}/events, POST /runs/{id}/cancel, GET /runs/{id}/tool-calls
Approval	GET /approvals, GET /approvals/{id}, POST /approvals/{id}/approve, POST /approvals/{id}/reject
PO	GET/POST /purchase-orders, GET /purchase-orders/{id}, /versions, POST /{id}/send, /follow-ups, /cancel, /notify-stakeholders
Change request	GET /change-requests, GET /change-requests/{id}, POST /{id}/accept, /reject
Komunikasi	GET /purchase-orders/{id}/communications, POST /communications/{id}/send, PATCH /communications/{id} (edit draf)
Master data	GET/POST /vendors, GET /vendors/{id}, /contacts, /performance, GET /contracts, GET /contracts/{id}
Negosiasi	POST /negotiations, GET /negotiations/{id}, /context, /options, POST /options/{opt_id}/select, GET/PATCH /drafts, POST /drafts/{id}/send, POST /negotiations/{id}/outcome, GET /purchase-history, GET /price-history
Fraud	POST /fraud/scans, GET /fraud/alerts, GET /fraud/alerts/{id}, PATCH /fraud/alerts/{id}, POST /fraud/alerts/{id}/explain, POST /fraud/alerts/{id}/hold-payment, GET/POST/PATCH /fraud/rules, GET /fraud/dashboard
Invoice & rekening	GET/POST /invoices, GET /vendors/{id}/bank-accounts, POST /vendors/{id}/bank-accounts/change-requests, POST .../{id}/verify
Pendukung	GET /audit-logs, GET/POST /notifications, GET/PATCH /settings/policies, GET /usage, GET /health, GET /ready
Webhook	POST /webhooks/inbound-email (dari penyedia email, bukan frontend)

