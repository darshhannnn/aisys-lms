# Assumptions, Clarifications, and Excluded Work (D0)

## Assumptions

1. **Synthetic Data Exclusivity:** All testing, development, and migration will rely strictly on synthetic dummy data. No real institutional data (PII) is involved in this prototype.
2. **Offline Hardware Availability:** Since physical hardware (RFID staff readers, security gates, smart-card infrastructure, and CCTV systems) is unavailable for the candidate prototype, the system is designed to inject software Mocks representing these boundaries.
3. **Smart Card Infrastructure:** It is assumed that the production deployment will provide a credential provider (like LDAP or an AD domain) to which the smart cards map. In the mock, a synthetic mapping dictionary is used to demonstrate RBAC validation (AC07).
4. **Environment:** The deployment is assumed to be an isolated or offline network. This informs the architectural choice to use Python dependencies that can be bundled into wheels, a self-contained Docker container setup, and avoiding external cloud APIs (e.g., using `mock` adapters for Email/SMS instead of requiring real SMTP).
5. **Full-Text Search:** To reduce system complexity in an offline environment, we assume the use of standard database full-text capabilities (SQLite `LIKE` / Postgres `to_tsvector`) rather than requiring a dedicated search appliance like Elasticsearch.

## Clarification Log

- **Clarification 1 (Dependencies Build failure):** The development host environment (Python 3.14 pre-release on Windows with spaces in user paths) prevents compilation of C-extensions like `pydantic-core` and `asyncpg`. 
  - *Resolution:* The architecture is designed to fall back to `SQLite` and relies heavily on Docker (`docker-compose`) to abstract away local host limitations during evaluation. The code strictly avoids host-specific dependencies.
- **Clarification 2 (Migration Staging):** The ~20,000 record spreadsheet import requirement (FR10, AC01) assumes records can be loaded into an isolated `staging` table for validation and de-duplication before migrating to production tables.

## Excluded Work

As defined in Section 3 of the SOP:
- Physical manufacture, installation, or repair of any RFID hardware or networking.
- Accessing production systems, live institutional databases, or real networks.
- Providing authorized certifications (e.g., ISO, SIP2 standard compliance) beyond functional demonstration using mocked interfaces.
- Real SMTP/SMS gateway configurations.
