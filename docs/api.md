# API Documentation (D8)

This document outlines the core REST endpoints for the AISYS Library Management System.

All endpoints are prefixed with `/api/v1`.

## 1. Authentication

### `POST /auth/login`
- **Description:** Username and password login for library staff.
- **Request Body (Form Data):** `username`, `password`
- **Response:** `{"access_token": "...", "token_type": "bearer", "role": "librarian", "username": "admin"}`

### `POST /auth/smartcard-login`
- **Description:** AC07 — Staff login via smart-card ID.
- **Request Body (JSON):** `{"card_uid": "CARD-ADMIN-0001"}`
- **Response:** JWT access token with RBAC role.

## 2. Circulation

### `POST /circulation/checkout`
- **Description:** AC03, AC04 — Check out an item to a member.
- **Request Body (JSON):** `{"member_id": "uuid", "item_id": "uuid", "protocol": "direct"}`
- **Returns:** Loan details or HTTP 422 with block reason (e.g. `FINE_LIMIT_EXCEEDED`).

### `POST /circulation/checkin`
- **Description:** AC03 — Return an item and calculate fines.
- **Request Body (JSON):** `{"item_id": "uuid"}`
- **Returns:** Success status and optional `fine_levied`.

### `POST /circulation/renew`
- **Description:** Renew an active loan.
- **Request Body (JSON):** `{"loan_id": "uuid"}`
- **Returns:** New due date.

## 3. Catalogue

### `GET /catalogue/search`
- **Description:** FR02 — Full text search of the catalogue.
- **Query Params:** `q` (search string), `limit`, `offset`
- **Returns:** List of matching bibliographic records.

### `POST /catalogue`
- **Description:** Create a new bibliographic record.
- **Request Body (JSON):** `{"title": "...", "author": "...", "isbn": "..."}`
- **Returns:** Created record with UUID.

## 4. Members

### `POST /members/{member_id}/block`
- **Description:** AC04 — Manually block a member from circulation.
- **Request Body (JSON):** `{"reason": "Lost card"}`

## 5. RFID Middleware

### `POST /rfid/tag-item`
- **Description:** AC02 — Associate an RFID tag UID with a specific item ID.
- **Request Body (JSON):** `{"item_id": "uuid", "tag_uid": "TAG-12345"}`

### `POST /rfid/gate/simulate-unauthorised-removal`
- **Description:** AC06 — Simulate an alarm event at the security gate.
- **Query Params:** `accession_number`, `gate_id`
- **Returns:** Gate event details, including CCTV image path and notification queued status.

## 6. Reports

### `GET /reports/dashboard`
- **Description:** AC08 — Generate live dashboard statistics.
- **Returns:** JSON object containing `total_items`, `checked_out`, `total_members`, `tagged_items`, `unpaid_fines_total`, `gate_events_today`.

## 7. Health

### `GET /health`
- **Description:** NFR07 — System health check.
- **Returns:** `{"status": "ok", "database": "ok", "version": "0.1.0", ...}`
