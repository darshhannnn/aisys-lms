# AISYS RFID-Enabled Library Management System

A candidate prototype of an RFID-enabled library management system (ILMS) built with FastAPI, designed for offline deployment on Windows 11/Windows Server 2022.

## Features

- **RFID Integration**: Mock adapters for staff readers, handheld scanners, security gates, and smart-card authentication
- **Circulation Management**: Check-out, check-in, renewals, and fine management
- **Catalogue System**: Bibliographic records with full-text search
- **Member Management**: Patron records with circulation blocking
- **Notifications**: Email, SMS, and print notification support (mock providers)
- **Security Gate Events**: Real-time alerting for unauthorized item removal
- **Inventory Management**: RFID-based shelf inventory scanning
- **Dashboard & Reports**: Statistics and reporting capabilities
- **Glassmorphism UI**: Modern web interface with glassmorphism design

## Architecture

The system follows a layered architecture:

- **Presentation Layer**: FastAPI REST APIs + Jinja2 web templates
- **Application Layer**: Business logic services
- **RFID Middleware Layer**: Hardware-agnostic adapter pattern
- **Data Layer**: SQLAlchemy ORM with SQLite (PostgreSQL support available)
- **Integration Layer**: Mock providers for email, SMS, print, CCTV
- **Operations Layer**: Configuration, logging, migrations

## Requirements

- Python 3.11+
- SQLite (default) or PostgreSQL 16
- Docker (optional, for containerized deployment)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd AISYS
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Copy environment configuration:
```bash
cp .env.example .env
```

5. Run database migrations:
```bash
python -m alembic upgrade head
```

6. Seed sample data (optional):
```bash
aisys seed all
```

7. Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

1. Build the Docker image:
```bash
docker-compose build
```

2. Start the services:
```bash
docker-compose up -d
```

## Usage

### API Documentation

Once the server is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Web Interface

Access the web UI at:
- Dashboard: http://localhost:8000/
- Catalogue: http://localhost:8000/catalogue
- Circulation: http://localhost:8000/circulation
- Members: http://localhost:8000/members
- RFID Operations: http://localhost:8000/rfid
- Reports: http://localhost:8000/reports

### CLI Commands

```bash
# Show version
aisys version

# Database migrations
aisys migrate upgrade
aisys migrate downgrade
aisys migrate current

# Data seeding
aisys seed users
aisys seed catalogue
aisys seed members
aisys seed all
```

## Configuration

Configuration is managed through environment variables (`.env` file):

```env
# Application
APP_NAME=AISYS Library Management System
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite+aiosqlite:///./aisys_lms.db

# Server
HOST=0.0.0.0
PORT=8000

# RFID Middleware
RFID_ADAPTER=mock
RFID_EVENT_TIMEOUT_SECONDS=10
RFID_RETRY_ATTEMPTS=3

# Notifications
EMAIL_ADAPTER=mock
SMS_ADAPTER=mock
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

The project uses Ruff for linting and formatting:

```bash
ruff check app/
ruff format app/
```

### Type Checking

```bash
mypy app/
```

## Project Structure

```
AISYS_LMS/
├── app/
│   ├── api/              # FastAPI routers
│   ├── core/             # Configuration, security, logging
│   ├── db/               # Database session management
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── repositories/     # Data-access layer
│   ├── services/         # Business logic layer
│   ├── rfid/             # RFID middleware and adapters
│   ├── integrations/     # External service integrations
│   └── web/              # Jinja2 web templates
├── migrations/           # Alembic database migrations
├── cli/                  # Typer CLI commands
├── tests/                # Unit, integration, acceptance tests
├── static/               # CSS, JS, static assets
├── docs/                 # Documentation (RTM, architecture)
└── pyproject.toml        # Project configuration
```

## Documentation

- [Requirements Traceability Matrix](docs/rtm.md)
- [Architecture Document](docs/architecture.md)
- [Assumptions & Clarifications](docs/assumptions.md)

## Security Notes

- All data used in this prototype is synthetic
- No real personal data, credentials, or production records are used
- Passwords are hashed using bcrypt
- JWT tokens are used for authentication
- Audit logging captures all administrative actions

## License

Proprietary - AISYS Candidate Prototype

## Support

For support, please refer to the project documentation or contact the development team.
