AISYS_LMS/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory
│   ├── core/
│   │   ├── config.py              # Settings (pydantic-settings)
│   │   ├── security.py            # Auth helpers (JWT, password hash)
│   │   ├── logging.py             # structlog config
│   │   └── dependencies.py        # FastAPI dependency injection
│   ├── db/
│   │   ├── base.py                # SQLAlchemy Base, engine, session
│   │   └── session.py             # Async session factory
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── catalogue.py           # BibliographicRecord, Item
│   │   ├── member.py
│   │   ├── circulation.py         # Loan, Fine, Renewal
│   │   ├── rfid.py                # RfidTag, GateEvent
│   │   ├── notification.py
│   │   └── audit.py               # AuditLog
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── user.py
│   │   ├── catalogue.py
│   │   ├── member.py
│   │   ├── circulation.py
│   │   ├── rfid.py
│   │   └── notification.py
│   ├── repositories/              # Data-access layer (pure DB ops)
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── catalogue.py
│   │   ├── member.py
│   │   ├── circulation.py
│   │   └── rfid.py
│   ├── services/                  # Business logic layer
│   │   ├── auth.py
│   │   ├── catalogue.py
│   │   ├── circulation.py
│   │   ├── tagging.py
│   │   ├── inventory.py
│   │   ├── gate_events.py
│   │   ├── reporting.py
│   │   └── notifications.py
│   ├── rfid/                      # RFID middleware layer
│   │   ├── adapters/
│   │   │   ├── base.py            # Abstract adapter interface
│   │   │   ├── mock_staff.py      # Mock staff reader
│   │   │   ├── mock_handheld.py   # Mock handheld reader
│   │   │   ├── mock_gate.py       # Mock security gate
│   │   │   └── mock_smartcard.py  # Mock smart-card provider
│   │   ├── ncip/
│   │   │   ├── client.py          # NCIP 2.0 adapter boundary
│   │   │   └── mock.py
│   │   ├── sip2/
│   │   │   ├── client.py          # SIP2 adapter boundary
│   │   │   └── mock.py
│   │   └── events.py              # Event bus / handlers
│   ├── integrations/              # Integration layer
│   │   ├── email/
│   │   │   ├── base.py
│   │   │   └── mock.py
│   │   ├── sms/
│   │   │   ├── base.py
│   │   │   └── mock.py
│   │   ├── print_service/
│   │   │   ├── base.py
│   │   │   └── mock.py
│   │   └── cctv/
│   │       ├── base.py
│   │       └── mock.py
│   ├── api/                       # FastAPI routers
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── catalogue.py
│   │   │   ├── members.py
│   │   │   ├── circulation.py
│   │   │   ├── rfid.py
│   │   │   ├── inventory.py
│   │   │   ├── gate_events.py
│   │   │   ├── reports.py
│   │   │   ├── notifications.py
│   │   │   ├── migration.py
│   │   │   └── health.py
│   │   └── router.py
│   └── web/                       # Jinja2 web (OPAC + staff UI)
│       ├── router.py
│       └── templates/
│           ├── base.html
│           ├── dashboard.html
│           ├── catalogue/
│           ├── circulation/
│           ├── members/
│           ├── rfid/
│           └── reports/
├── migrations/                    # Alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── cli/                           # Typer CLI (migration, seed, admin)
│   ├── __init__.py
│   ├── main.py
│   ├── migrate.py
│   └── seed.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── acceptance/                # AC01–AC10 scenarios
├── docs/
│   ├── rtm.md                     # Requirements Traceability Matrix (D1)
│   ├── architecture.md            # Architecture decisions (D2)
│   ├── api.md
│   └── assumptions.md
├── data/
│   └── synthetic/                 # Synthetic seed spreadsheets
├── static/                        # CSS, JS, icons
│   ├── css/
│   └── js/
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml             # For local dev + CI
├── Dockerfile
├── pyproject.toml
└── README.md
