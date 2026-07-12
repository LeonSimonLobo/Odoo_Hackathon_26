# AssetFlow — 8-Hour Build Plan (Python + Next.js Stack)

## 0. The Core Decision: Pick a Stack that Removes Plumbing

With 10 screens, 4 roles, and 5 interlocking workflows (allocation conflicts, booking overlaps, maintenance approval, audit cycles, notifications), a relational database is essential. The team has selected a **Python backend with SQLAlchemy (SQLite for local, PostgreSQL ready)** and a **Next.js + TypeScript + Tailwind CSS** frontend.

**Selected Stack**

| Layer | Choice | Why |
|---|---|---|
| **Database** | **SQLite (development) / PostgreSQL (production)** | Relational tables, foreign keys, transaction safety, and quick local testing. |
| **Backend / ORM** | **Python (FastAPI / Express hybrid) + SQLAlchemy 2.0** | Robust ORM models, relations, and database-level event listeners for business rules. |
| **Realtime** | **FastAPI WebSockets / Long-Polling** | Powers dynamic updates to the Dashboard KPIs and notifications feed. |
| **Auth** | **JWT Token-based Auth** (by Teammate 1) | Custom auth with a roles column in `employees` table: Admin promotes roles from the directory. |
| **Frontend** | **Next.js (App Router) + TypeScript + Tailwind CSS** | Clean React components, nested routing, and modern UI library elements. |
| **Deployment** | Frontend → Vercel. Backend → Render / Docker VPS. | Highly portable, production-ready environment setup. |
| **Version control** | GitHub (PRs required, distinct roles) | Satisfies teamwork guidelines and prevents single-repo management bottlenecks. |

---

## 1. Data Model (SQLAlchemy / SQL)

All tables, fields, and constraints are already implemented in [models.py](file:///C:/Users/mhask/Desktop/Odoo_Hackathon/Odoo_Hackathon_26/backend/models.py):

```
departments
  - id (Integer, PK)
  - name (String, Unique)
  - parent_department_id (FK -> departments.id, Nullable)
  - department_head_id (FK -> employees.id, Nullable)
  - status (String, default "active")

employees
  - id (Integer, PK)
  - name (String)
  - email (String, Unique)
  - password_hash (String)
  - department_id (FK -> departments.id, Nullable)
  - role (String, default "employee") -- employee | department_head | asset_manager | admin
  - status (String, default "active")

asset_categories
  - id (Integer, PK)
  - name (String, Unique)
  - description (String, Nullable)
  - schema_attributes (JSON, Nullable)  -- e.g. { "warranty_period_months": 24 }

assets
  - id (Integer, PK)
  - name (String)
  - category_id (FK -> asset_categories.id)
  - asset_tag (String, Unique)          -- AF-0001
  - serial_number (String, Unique, Nullable)
  - acquisition_date (Date)
  - acquisition_cost (Float)
  - condition (String)                  -- new | good | fair | poor
  - location (String)
  - photo_url (String, Nullable)
  - document_url (String, Nullable)
  - is_shared (Boolean, default False)  -- Bookable resource flag
  - status (String, default "available") -- available | allocated | reserved | under_maintenance | lost | retired | disposed

asset_allocations
  - id (Integer, PK)
  - asset_id (FK -> assets.id)
  - allocated_to_type (String)          -- employee | department
  - allocated_employee_id (FK -> employees.id, Nullable)
  - allocated_department_id (FK -> departments.id, Nullable)
  - allocated_by_id (FK -> employees.id)
  - allocation_date (DateTime)
  - expected_return_date (DateTime, Nullable)
  - actual_return_date (DateTime, Nullable)
  - condition_check_in_notes (String, Nullable)
  - status (String, default "active")   -- active | returned | transferred

transfer_requests
  - id (Integer, PK)
  - asset_id (FK -> assets.id)
  - requestor_employee_id (FK -> employees.id)
  - target_employee_id (FK -> employees.id, Nullable)
  - target_department_id (FK -> departments.id, Nullable)
  - current_holder_employee_id (FK -> employees.id, Nullable)
  - status (String, default "pending")  -- pending | approved | rejected
  - comments (String, Nullable)
  - actioned_by_id (FK -> employees.id, Nullable)
  - actioned_at (DateTime, Nullable)

resources
  - id (Integer, PK)
  - name (String)
  - type (String)                       -- room | vehicle | equipment
  - asset_id (FK -> assets.id, Nullable)
  - description (String, Nullable)
  - status (String, default "active")

resource_bookings
  - id (Integer, PK)
  - resource_id (FK -> resources.id)
  - booked_by_employee_id (FK -> employees.id)
  - start_time (DateTime)
  - end_time (DateTime)
  - status (String, default "upcoming")  -- upcoming | ongoing | completed | cancelled

maintenance_requests
  - id (Integer, PK)
  - asset_id (FK -> assets.id)
  - raised_by_employee_id (FK -> employees.id)
  - description (String)
  - priority (String, default "medium")  -- low | medium | high | critical
  - photo_url (String, Nullable)
  - status (String, default "pending")  -- pending | approved | rejected | technician_assigned | in_progress | resolved
  - technician_name (String, Nullable)
  - actioned_by_id (FK -> employees.id, Nullable)
  - actioned_at (DateTime, Nullable)
  - resolution_notes (String, Nullable)

audit_cycles
  - id (Integer, PK)
  - name (String)
  - scope_type (String)                 -- department | location | all
  - scope_department_id (FK -> departments.id, Nullable)
  - scope_location (String, Nullable)
  - start_date (Date)
  - end_date (Date)
  - status (String, default "open")     -- open | closed

audit_cycle_auditors (Join Table)
  - audit_cycle_id (FK -> audit_cycles.id, PK)
  - auditor_employee_id (FK -> employees.id, PK)

audit_items
  - id (Integer, PK)
  - audit_cycle_id (FK -> audit_cycles.id)
  - asset_id (FK -> assets.id)
  - verification_status (String, default "pending") -- pending | verified | missing | damaged
  - notes (String, Nullable)
  - verified_by_employee_id (FK -> employees.id, Nullable)
  - verified_at (DateTime, Nullable)

notifications
  - id (Integer, PK)
  - employee_id (FK -> employees.id)
  - type (String)
  - title (String)
  - message (String)
  - is_read (Boolean, default False)
  - created_at (DateTime)

activity_logs
  - id (Integer, PK)
  - employee_id (FK -> employees.id, Nullable)
  - action (String)
  - details (JSON, Nullable)
  - created_at (DateTime)
```

### Business-Level Guardrails (Enforced in [models.py](file:///C:/Users/mhask/Desktop/Odoo_Hackathon/Odoo_Hackathon_26/backend/models.py))

* **Double-Allocation Block**: Intercepted in `before_flush`. If an asset has an active allocation, trying to insert/update another active allocation raises a `ValueError` detailing the current holder's name. It automatically updates the parent `Asset.status` to `allocated`.
* **Booking Overlap Prevention**: Checked in `before_flush`. Computes interval math to prevent overlapping bookings on the same resource, rejecting double-bookings for rooms/vehicles while permitting adjacent slots.
* **Maintenance → Asset Sync**: Triggers transition of parent asset status to `under_maintenance` when request is approved/assigned, and reverts to `available` upon resolution.
* **Audit Close → Status Cascade**: Closing an `AuditCycle` automatically sets any missing items to status `lost` and damaged items to status `under_maintenance`.

---

## 2. Project File Structure

The project workspace uses the following layout:

```
Odoo_Hackathon_26/
├── backend/
│   ├── database.py              # SQLAlchemy connection, SessionLocal, Base model
│   ├── models.py                # All 14 SQLAlchemy models, relations, event triggers
│   ├── seed.py                  # Demo database creation and mock data seeding
│   ├── verify_db.py             # Unit tests checking constraints and workflows
│   ├── schema.sql               # Reference raw SQL DDL file
│   ├── assetflow.db             # The local SQLite database file
│   ├── requirements.txt         # Python libraries (sqlalchemy, pydantic, python-dotenv)
│   ├── package.json             # Backend Node config (Express setup)
│   └── tsconfig.json            # TypeScript configuration
├── frontend/
│   ├── app/                     # Next.js App Router (pages & nested layouts)
│   │   ├── layout.tsx
│   │   ├── page.tsx             # Root page
│   │   ├── globals.css
│   │   └── dashboard/           # Dashboard UI Screen
│   ├── public/                  # Mock images and static resources
│   ├── package.json             # Frontend dependencies
│   ├── tsconfig.json            # TypeScript config
│   └── next.config.ts
├── .gitignore                   # Ignores node_modules, .next, .venv, *.db and env files
└── README.md
```

---

## 3. Team Member Allocation & Timeline

With a 3-member team, tasks are assigned to optimize parallel tracks:

### Team Roles:
* **Developer A (Auth)**: Building Login/Signup screens, custom backend JWT auth, password hashing, and endpoint route guards.
* **Developer B (Database/API - USER & AI)**: Set up the SQLAlchemy database, hooks, migrations, backend API routes (endpoints for registry, allocations, resource bookings, maintenance boards, and KPI aggregation).
* **Developer C (Mockup UI & Frontend)**: Developing Next.js layouts, components (status badges, charts, calendar view), and wireframing pages.

---

### Hour-by-Hour Timeline (8-Hour Hackathon)

#### **Hour 0 – 0:30 | Core Initialization**
* Initialize GitHub repo with branch protection rules.
* Backend DB ready (`database.py`, `models.py`, `seed.py` successfully completed and verified).
* Next.js frontend running.

#### **Hour 0:30 – 2:30 | Auth & Setup Screens**
* **Dev A (Auth)**: Set up custom JWT authentication endpoints in the backend and cookies/localstorage handlers.
* **Dev B (DB/API)**: Create REST API endpoints for Org Setup (Departments management, Categories creation, Employee directory role promotion).
* **Dev C (UI)**: Develop Next.js Org Setup UI Screen (Tab A: Departments list/create, Tab B: Category fields, Tab C: Employee promotions) and link to backend APIs.

#### **Hour 2:30 – 4:30 | Inventory & Conflict Workflows**
* **Dev A (Auth)**: Add role-based middleware to endpoints (e.g. Org Setup = Admin-only, Maintenance = Asset Manager, etc.).
* **Dev B (DB/API)**: Set up Asset Registration endpoint, checkout/allocation endpoint, and resource booking router.
* **Dev C (UI)**: Build Asset Registry UI (search, filter, category fields) and Allocations Screen (checkout form, transfer buttons, return checklists).
* *Milestone Check*: Verify that trying to allocate an already-held asset correctly prompts the frontend with the holder's name and triggers the Transfer Request flow.

#### **Hour 4:30 – 5:30 | Shared Bookings & Maintenance Board**
* **Dev A (Auth)**: Set up Activity Logs helper and notification trigger functions.
* **Dev B (DB/API)**: Create overlap-checked booking endpoints, and the maintenance board state transition routes.
* **Dev C (UI)**: Build Resource Bookings screen (showing calendar views, booking buttons) and Maintenance Workflow Board.

#### **Hour 5:30 – 6:30 | Dashboard KPIs & Audits**
* **Dev B (DB/API)**: Code the KPI summary endpoints (Overdue alerts, Maintenance counts, Available counts) and the Audit Cycle endpoints.
* **Dev C (UI)**: Build the Dashboard KPI panel and the Audit verification page (mark verified/missing/damaged).
* **Dev A (Auth)**: Connect notifications realtime polling or Websocket feed.

#### **Hour 6:30 – 7:15 | Polish & Demo Seeding**
* Apply responsive styles to Next.js dashboard, calendar, and lists.
* Run `python seed.py` on the server so the system has rich test data for presentation.
* Style consistent loading spinner states and error toast notifications.

#### **Hour 7:15 – 8:00 | Deploy & Practice Demo**
* Deploy Frontend to Vercel and Backend to Render/VPS.
* Run end-to-end demo path:
  1. Signup (default: Employee).
  2. Admin log-in → promotes user to Asset Manager/Dept Head.
  3. Register asset → checkout → attempt double-checkout (demonstrates block).
  4. Book shared room → attempt overlapping slot (demonstrates rejection).
  5. Close audit cycle with missing items → check asset changes status to `Lost`.
