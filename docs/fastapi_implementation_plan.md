# FastAPI Asset Inventory App Plan

## 1) Product Goals
- Track assets and consumable inventory across locations.
- Provide role-based workflows for admins, inventory managers, auditors, and viewers.
- Support complete lifecycle: procurement, assignment, transfer, maintenance, depreciation, disposal.
- Offer auditable history and operational dashboards.

## 2) Core MVP Scope

### Modules
1. **Authentication & Authorization**
   - JWT login + refresh tokens.
   - Role-based access control (RBAC).
2. **Asset Registry**
   - CRUD assets (tag, serial, category, status, location, owner).
   - Asset status transitions with validation.
3. **Inventory Management**
   - Stock items (SKU, unit, reorder threshold, location bins).
   - Inbound/outbound stock transactions.
4. **People & Departments**
   - Assign assets to users/departments.
5. **Vendors & Procurement**
   - Vendor catalog and purchase records.
6. **Audit Trail**
   - Immutable event log of all critical changes.
7. **Reporting**
   - Basic dashboard endpoints: totals by status/category/location, low-stock list.

### Out of Scope for MVP
- Barcode/RFID integrations.
- Predictive forecasting.
- Complex approval workflows.

## 3) Recommended Architecture (FastAPI)

- **API Framework**: FastAPI
- **ASGI Server**: Uvicorn (Gunicorn+Uvicorn workers in production)
- **ORM**: SQLAlchemy 2.x + Alembic migrations
- **Validation**: Pydantic v2 models
- **Database**: PostgreSQL
- **Caching / Queues (optional phase 2)**: Redis + Celery/RQ
- **Auth**: OAuth2 password flow + JWT, hashed passwords (Argon2/Bcrypt)
- **Testing**: Pytest + httpx + Testcontainers (or Docker Compose)
- **Observability**: Structlog/loguru + OpenTelemetry (phase 2)

## 4) Suggested Project Structure

```text
app/
  main.py
  api/
    v1/
      routers/
        auth.py
        assets.py
        inventory.py
        assignments.py
        vendors.py
        reports.py
  core/
    config.py
    security.py
    dependencies.py
  db/
    base.py
    session.py
    models/
      user.py
      role.py
      asset.py
      inventory_item.py
      stock_txn.py
      assignment.py
      vendor.py
      purchase.py
      audit_log.py
  schemas/
    auth.py
    asset.py
    inventory.py
    assignment.py
    vendor.py
    report.py
  services/
    asset_service.py
    inventory_service.py
    assignment_service.py
    reporting_service.py
  repositories/
    asset_repo.py
    inventory_repo.py
    user_repo.py
  tests/
alembic/
```

## 5) Data Model (MVP)

### Primary Entities
- `users`: id, email, full_name, password_hash, is_active, created_at
- `roles`: id, name
- `user_roles`: user_id, role_id
- `locations`: id, name, code
- `departments`: id, name, code
- `asset_categories`: id, name
- `assets`: id, asset_tag, serial_no, category_id, status, location_id, department_id, purchase_id, warranty_end, created_at
- `assignments`: id, asset_id, assignee_user_id, assigned_at, returned_at, condition_out, condition_in
- `inventory_items`: id, sku, name, unit, qty_on_hand, reorder_level, location_id
- `stock_transactions`: id, item_id, txn_type(IN/OUT/ADJUST), qty, reason, reference, performed_by, created_at
- `vendors`: id, name, email, phone
- `purchases`: id, vendor_id, po_number, invoice_number, purchased_at, total_amount
- `audit_logs`: id, actor_user_id, entity_type, entity_id, action, before_json, after_json, created_at

### Recommended Enumerations
- `asset_status`: `in_stock`, `assigned`, `in_repair`, `retired`, `disposed`
- `txn_type`: `in`, `out`, `adjustment`

## 6) API Endpoints (v1)

### Auth
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

### Assets
- `POST /api/v1/assets`
- `GET /api/v1/assets`
- `GET /api/v1/assets/{asset_id}`
- `PATCH /api/v1/assets/{asset_id}`
- `POST /api/v1/assets/{asset_id}/status`

### Assignments
- `POST /api/v1/assignments`
- `POST /api/v1/assignments/{id}/return`
- `GET /api/v1/assignments?active=true`

### Inventory
- `POST /api/v1/inventory/items`
- `GET /api/v1/inventory/items`
- `POST /api/v1/inventory/transactions`
- `GET /api/v1/inventory/low-stock`

### Vendors / Procurement
- `POST /api/v1/vendors`
- `GET /api/v1/vendors`
- `POST /api/v1/purchases`

### Reports
- `GET /api/v1/reports/summary`
- `GET /api/v1/reports/assets-by-status`
- `GET /api/v1/reports/inventory-valuation`

## 7) Security & Compliance Checklist
- Enforce RBAC at route and service levels.
- Validate asset status transitions with explicit rules.
- Keep immutable audit logs for CUD actions.
- Add rate limiting (API gateway or middleware).
- Use secrets manager/environment vars for credentials.
- Enable CORS only for approved frontend origins.

## 8) Delivery Plan (4 Sprints)

### Sprint 1 (Foundation)
- Repository scaffolding and environment setup.
- Auth, user model, role model.
- Base migrations and health endpoint.

### Sprint 2 (Asset + Assignment)
- Asset CRUD and status transitions.
- Assignment/return workflow.
- Basic tests for critical flows.

### Sprint 3 (Inventory + Procurement)
- Inventory item CRUD + stock transactions.
- Vendor and purchase records.
- Low-stock reporting endpoint.

### Sprint 4 (Audit + Reporting + Hardening)
- Audit logging for all write operations.
- Summary/report endpoints.
- Performance tuning, pagination/filtering, API docs polish.

## 9) Definition of Done (MVP)
- All MVP endpoints implemented and documented in OpenAPI.
- Alembic migrations reproducibly create schema.
- Test suite passes in CI (unit + API integration).
- Role-based permissions verified for sensitive routes.
- Deployment artifacts prepared (Dockerfile, compose, env template).

## 10) First Build Tasks (Actionable Next Steps)
1. Scaffold FastAPI app with modular router structure.
2. Add PostgreSQL connection config and session dependency.
3. Create initial Alembic migration for users/roles/assets/inventory.
4. Implement login + JWT + protected endpoint.
5. Implement asset CRUD with filtering and pagination.
6. Add assignment and stock transaction endpoints with validations.
7. Add audit log middleware/service for write operations.
8. Add pytest setup and baseline CI pipeline.
