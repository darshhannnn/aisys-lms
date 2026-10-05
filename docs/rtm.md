# Requirements Traceability Matrix (RTM)

## Functional Requirements (FR)

| Req ID | Description | Component / Module | Test Strategy / Acceptance Criteria | Status |
|---|---|---|---|---|
| **FR01** | Core ILMS operations (acquisition, catalogue, etc.) | `app.models.catalogue`, `app.api.v1.catalogue` | Verified via AC02 (bibliographic item creation & validation) | Done |
| **FR02** | Web UI and full-text search (real-time indexing) | `app.models.catalogue` (tsvector), `app.web.router` | Search endpoint tested using partial/full text matches | Done |
| **FR03** | RFID interoperability & middleware boundaries | `app.rfid.adapters.*`, `app.rfid.ncip` | Verified via AC02, AC03, AC05, AC06, AC07 mock integrations | Done |
| **FR04** | Circulation rules, renewals, member blocking | `app.api.v1.circulation`, `app.models.member` | Verified via AC03 (check-out/in) and AC04 (circulation blocking) | Done |
| **FR05** | RFID tag validation and item association | `app.api.v1.rfid`, `app.models.rfid` | Verified via AC02 (associating tag to bibliographic item) | Done |
| **FR06** | Inventory/shelf management operations | `app.api.v1.inventory`, `app.services.inventory` | Verified via AC05 (handheld inventory mock scenario) | Done |
| **FR07** | Security gate events and notifications | `app.api.v1.rfid`, `app.rfid.adapters.mock_gate` | Verified via AC06 (unauthorised removal from gate) | Done |
| **FR08** | Dashboards and reporting | `app.api.v1.reports`, `app.web.templates.dashboard.html` | Verified via AC08 (dashboard generation & filterable statistics) | Done |
| **FR09** | Notifications (email, SMS, print) | `app.core.config`, external mock adapters | Verified via AC06 (notification queued flag) | Done |
| **FR10** | Data migration from spreadsheet files | `cli.migrate`, `app.services.spreadsheet_import` | Verified via AC01 (import process, duplicate handling, reconciliation) | Done |
| **FR11** | Administration, auth, health check | `app.api.v1.auth`, `app.api.v1.health`, `app.models.user` | Verified via AC07 (staff smart-card login & RBAC enforcement) | Done |
| **FR12** | Offline lifecycle, upgrade and patch support | `install.bat`, `docker-compose.yml` | Verified via AC09 (offline installation and update simulation) | Done |

## Non-Functional Requirements (NFR)

| Req ID | Description | Approach |
|---|---|---|
| **NFR01** | Data integrity and migration safety | All migrations happen in isolation; original ILMS db is untampered. Staging tables are used before import. |
| **NFR02** | Security, privacy, audit logging | `app.models.audit.AuditLog` immutably captures state changes; least privilege RBAC; JWT based session. |
| **NFR03** | Compatibility (Win 11 / WS2022) | Entire stack runs in standard Python / Docker environments capable of offline Windows deployment. |
| **NFR04** | Licensing and BOM | Identified in `pyproject.toml`; offline installation package includes pinned dependencies. |
| **NFR05** | Testability | Tests (unit, integration, acceptance) cover AC01-AC10 scenarios using synthetic data and adapter mocks. |
| **NFR06** | Maintainability | Adheres to layered architecture, config outside code (Pydantic settings), versioned migrations (Alembic). |
| **NFR07** | Supportability | Built-in `/api/v1/health` endpoint; structured JSON logging (Structlog). |
| **NFR08** | Documentation | RTM, Architecture Document, API Specs (`/api/docs`), CLI help provided. |
| **NFR09** | Delivery | End-to-end working prototype delivered for stages 1 to 7 review. |

## Acceptance Scenarios Traceability

- **AC01:** Covers FR10, NFR01 (Spreadsheet import, valid records migrated, duplicate identification).
- **AC02:** Covers FR01, FR03, FR05 (Locate bibliographic item and associate RFID tag).
- **AC03:** Covers FR04 (Check-out/in/renew via flow, auditable transaction history).
- **AC04:** Covers FR04 (Block circulation for reference items or fine/limit exceedances).
- **AC05:** Covers FR06 (Handheld reader mock for shelf inventory).
- **AC06:** Covers FR07, FR09 (Unauthorised removal event from gate, CCTV image, email).
- **AC07:** Covers FR11, FR03 (Staff smart-card login mock and RBAC enforcement).
- **AC08:** Covers FR08 (Generate dashboard stats and reports).
- **AC09:** Covers FR12 (Offline installation & rollback process demo).
- **AC10:** Covers FR10, NFR01 (Restore from backup & data integrity validation).
