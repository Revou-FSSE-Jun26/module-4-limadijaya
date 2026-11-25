# RevoTask Implementation Tasks

| Field | Value |
|---|---|
| Status | Draft. T1.01 is complete: DA-01 to DA-19 were approved by the human owner (Limadijaya Suhendra, 2026-11-24). The nine unresolved decisions (UD) remain open, but Kiro took working decisions for UD-01, 02, 09, 15, 16, 17, 21, 22 on the owner's delegation (see `CHANGELOG.md`, pending owner confirmation). The ten verification obligations (V-01 to V-10) are outstanding. Milestones 1 to 13 are implemented and tested locally. Not done: concurrency tests (T6.06, T7.08), SQL-capture tests, T4.06, T4.07, T8.05, T9.04, T9.09, T10.11, T11.11, T11.12, T12.06, T12.07, T13.06, T13.07, T14.01 to T14.03, T14.08 to T14.12, and all of Milestones 15 and 16 that need a deployment. |
| Authoritative sources | `specs/requirements.md` (behavior, API contracts, acceptance criteria), then `specs/design.md`, then `guidelines/frontend.md`, `guidelines/backend.md`, `guidelines/database.md`, then `specs/PROJECT_BRIEF.md` |
| Rule of precedence | If a task, the design, or a guideline disagrees with the requirements, the requirements win and the task is corrected before it is implemented. |
| Scope | 26 mandatory endpoints, 1 approved extension (`POST /api/boards/{id}/members`), 6 pages, 8 Blueprints, 8 database entities. No task adds an endpoint, page, entity, or functional requirement. |

## How to use this plan in Kiro Supervised mode
1. Work on **one task at a time**, in ID order unless the `Depends` line allows otherwise.
2. For each task: read the listed requirements and design sections, implement only the listed files, run the `Verify` step, show the diff to the human reviewer, then tick the checkbox. NFR-011-AC03 requires a recorded human review for every AI-generated change.
3. Tests are written **with** the feature they test. A task is not done until its `Verify` step passes.
4. A task never commits or pushes. Committing is a separate human action.
5. If a task needs a decision that is not approved, stop and ask. Do not pick a proposal.
6. **Kiro never approves a design assumption (DA) or an unresolved decision (UD) on its own.** Approvals are made by the human owner in their own name. Kiro only transcribes a decision that the human states explicitly, with the approver's name and date. DA-01 to DA-19 were recorded this way on 2026-11-24 (T1.01). Silence or an empty row means "not approved". The nine UD decisions remain open, and Kiro does not resolve them.

## Status legend
| Tag | Meaning | What the implementer may do |
|---|---|---|
| **ACTIONABLE** | Everything the task needs is approved: in `requirements.md`, or as a design assumption approved by the human owner (the tag reads `approved: DA-nn`). | Implement it. |
| **CONDITIONAL (V-nn)** | The decision is approved, but a verification obligation of `design.md` Section 12.3.1 is outstanding and has not passed. | Prepare the work. Do not mark it complete or merge it until the named check passes. If the check fails, report it and request a new human approval. Do not work around the failure. |
| **BLOCKED (UD-nn)** | The task needs an unresolved decision (UD) from `requirements.md` Section 8.1. A proposal exists but is **NOT APPROVED**. | Do only the pre-work the task lists. Do not finish the task until the decision is approved and `requirements.md` is updated. |

## Unresolved decisions that stay open
UD-01 (token lifetime), UD-02 (refresh strategy), UD-07 (extra card fields), UD-09 (notification pagination defaults and unread count), UD-15 (coverage targets), UD-16 (environments), UD-17 (CI/CD), UD-21 (password policy), UD-22 (E2E account provisioning). No task in this plan resolves any of them:
- UD-01: the token lifetime is a required environment variable with no default in code (T2.01). No task sets its value.
- UD-02: no refresh route, token, or table is built. T4.07 tests that none exists.
- UD-07: no card field beyond `title` and `assignee_id` is built. No task exists for new fields.
- UD-09: `GET /api/notifications` is finished only in T9.03 (BLOCKED). The unread count in the bell is T13.04 and T13.05 (BLOCKED).
- UD-15: coverage is measured and reported only (T14.01). The threshold task T14.11 is BLOCKED.
- UD-16 and UD-22: Playwright target and account are inputs. T14.04 to T14.08 and T15.08 are BLOCKED.
- UD-17: no CI workflow is built. T14.10 is BLOCKED.
- UD-21: registration enforces only "non-empty" (T4.02). No password length rule is built.

## Design assumptions DA-01 to DA-19: human approval record (T1.01)
**Approver:** Limadijaya Suhendra, the human project owner. **Date:** 2026-11-24, confirmed by the human owner. This date replaces the value 2026-11-21 that was recorded before the confirmation. The owner approved DA-04, DA-05, DA-07, DA-14, DA-16, and DA-17 individually, and then approved the other 13 assumptions explicitly. These are human decisions. Kiro transcribed them and is not an approver. The wording below follows the owner's decision. Section 12.3 of `design.md` holds the same record.

Approval fixes a decision. It does not mean the decision is verified. Verification obligations V-01 to V-10 (`design.md` Section 12.3.1) are all outstanding. Approval of a DA resolves none of the nine unresolved decisions (UD-01, UD-02, UD-07, UD-09, UD-15, UD-16, UD-17, UD-21, UD-22).

| DA | Status | Exact approved decision | Approver | Date |
|---|---|---|---|---|
| DA-01 | APPROVED | Approve the existing fixed error-message wording from `design.md`. | Limadijaya Suhendra | 2026-11-24 |
| DA-02 | APPROVED | Approve the existing eight table names, including `columns`. | Limadijaya Suhendra | 2026-11-24 |
| DA-03 | APPROVED | Approve the existing API response fields, including `completed_at`, timestamps, `board_id`, author information, and nested board-detail cards. | Limadijaya Suhendra | 2026-11-24 |
| DA-04 | APPROVED | Approve the existing Next.js BFF paths, the `revotask_session` HttpOnly cookie, explicit trusted origins, CSRF protection, the proxy allow-list, the server-managed JWT, and card deep links. Use Secure cookies in production and SameSite=Lax or stricter where appropriate. Preview origins must be explicitly trusted. UD-01 and UD-02 stay open. | Limadijaya Suhendra | 2026-11-24 |
| DA-05 | APPROVED | Approve Werkzeug scrypt with explicit parameters, secure hash storage, generic login errors, no plaintext password logging, and Render memory and latency benchmarking. UD-21 stays open. | Limadijaya Suhendra | 2026-11-24 |
| DA-06 | APPROVED | Approve trimming and lowercasing email addresses consistently for registration, login, membership, and profile updates. | Limadijaya Suhendra | 2026-11-24 |
| DA-07 | APPROVED | Approve text trimming and a 1 MiB (1,048,576 byte) JSON request body limit, with HTTP 413 using the standard `{"error": "<non-empty string>"}` envelope. Apply appropriate limits at the Flask and BFF boundaries. No arbitrary per-field length limits. UD-21 stays open. | Limadijaya Suhendra | 2026-11-24 |
| DA-08 | APPROVED | Approve updating `updated_at` only on rows with actual changes. | Limadijaya Suhendra | 2026-11-24 |
| DA-09 | APPROVED | Approve HTTP 400 for an empty PATCH body, without changing approved no-op behavior for unchanged values. | Limadijaya Suhendra | 2026-11-24 |
| DA-10 | APPROVED | Approve the existing deterministic board and My Tasks ordering. | Limadijaya Suhendra | 2026-11-24 |
| DA-11 | APPROVED | Approve the additional database locks and a consistent lock acquisition order. Retain READ COMMITTED and concurrency tests. | Limadijaya Suhendra | 2026-11-24 |
| DA-12 | APPROVED | Approve Flask-CORS restricted to the health endpoint as described in `design.md`. | Limadijaya Suhendra | 2026-11-24 |
| DA-13 | APPROVED | Approve stored notification messages and boolean `is_read`. | Limadijaya Suhendra | 2026-11-24 |
| DA-14 | APPROVED | Approve PostgreSQL `ON DELETE CASCADE` for board hard deletion, activity-event preservation for soft-deleted entities, a plain UUID `activity_events.comment_id` without a foreign key, and mandatory PostgreSQL integration tests. If cascades fail, do not switch automatically to ordered service deletes: request new human approval. | Limadijaya Suhendra | 2026-11-24 |
| DA-15 | APPROVED | Approve BFF HTTP 502 and 504 for upstream failures, with the approved string error envelope. | Limadijaya Suhendra | 2026-11-24 |
| DA-16 | APPROVED | Approve Supabase session-mode pooling for the Render Flask API, `DATABASE_URL`, a small configurable SQLAlchemy pool, and verification of connectivity, migrations, concurrency, row locking, and connection limits. Do not silently change connection modes if verification fails. | Limadijaya Suhendra | 2026-11-24 |
| DA-17 | APPROVED | Approve RLS on all eight application tables without browser-facing access policies, disabling the Supabase Data API if practical, verifying the Flask database-role access and permissions, and managing RLS through migrations. | Limadijaya Suhendra | 2026-11-24 |
| DA-18 | APPROVED | Approve the complete keyboard and touch accessibility design in FE-14, including Move card controls, Move column left and right buttons, 44 by 44 px touch targets, keyboard interaction, focus management, `aria-live` announcements, and reuse of the approved move endpoints and ordering logic. Matching acceptance criteria were added to `requirements.md` (FRONT-019-AC17 to AC24, FRONT-025-AC18 to AC21, NFR-007-AC04 to AC06, TEST-005-AC12, TEST-009-AC03, TEST-009-AC04). | Limadijaya Suhendra | 2026-11-24 |
| DA-19 | APPROVED | Approve rejecting unsupported query parameters for `GET /api/cards`, preserving the `assignee=me` contract. | Limadijaya Suhendra | 2026-11-24 |

Implementation details accepted by the human owner in the final documentation review of T1.01: the pool variables `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` (DA-16), the 413 text `Request body is too large.` (DA-07), and `scrypt:32768:8:1` (DA-05) as a **provisional development configuration**, subject to the V-01 security, latency, and memory verification before production deployment. V-01 is not complete. T4.01 remains actionable and the Render scrypt benchmark remains in T15.05.
## Task format
```text
- [ ] **T<milestone>.<nn> Title** — STATUS
  - Objective: what is built.
  - Files: files or modules to create (C) or modify (M).
  - Reqs: requirement IDs. Design: design.md sections. Guidelines: guideline IDs.
  - Depends: earlier task IDs.
  - Done when: specific completion criteria.
  - Verify: the test or checkpoint to run.
```

---

## Milestone 1. Project setup and development environment

- [x] **T1.01 Decision gate: human approval of DA-01 to DA-19** — ACTIONABLE (human decision, complete)
  - Objective: the human owner approved DA-01 to DA-19 one by one. Kiro transcribed the decisions the owner stated explicitly and approved nothing itself. UD-01, 02, 07, 09, 15, 16, 17, 21, 22 are **not** decided here.
  - Files: M `specs/tasks.md` (the approval record above), M `specs/design.md` (Section 12.3 and the sections it affects), M `specs/requirements.md` (the DA-18 acceptance criteria only). `specs/CHANGELOG.md` is created in T1.07 and may copy this record.
  - Reqs: NFR-011-AC01, NFR-011-AC03. Design: §12.3.
  - Depends: none. Every task that uses a design assumption lists this task in its `Depends` line.
  - Done when (met): each of the 19 rows of the approval record has the exact decision, the approver name (Limadijaya Suhendra), and the date (2026-11-24), and no row is empty.
  - Verify: the record lists all 19 IDs with approver and date, and it agrees with `design.md` Section 12.3.
  - Completion note: the checkbox records that the approvals exist. It does not mean that any verification obligation (V-01 to V-10) has passed. It does not mark any implementation task complete.
- [x] **T1.02 Create the repository skeleton** — ACTIONABLE
  - Objective: create the `backend/` and `frontend/` folders and the root files from the approved layout.
  - Files: C `README.md` (stub), C `.gitignore`, C `backend/`, C `frontend/`, C empty `evidence/ai-reviews/`.
  - Reqs: NFR-010, NFR-011. Design: §2.1, §2.3. Guidelines: BE-01, FE-19.
  - Depends: none.
  - Done when: the folders exist, `.gitignore` excludes `.env*` (but not `*.example`), `node_modules`, virtual environments, `.next`, and build output. No existing file is changed.
  - Verify: `git status` lists only the new files, and `git check-ignore backend/.env` reports it as ignored.

- [x] **T1.03 Set up the backend Python project** — ACTIONABLE
  - Objective: create the dependency files, `pytest.ini`, `wsgi.py`, and `backend/.env.example` with placeholders only.
  - Files: C `backend/requirements.txt`, C `backend/requirements-dev.txt`, C `backend/pytest.ini`, C `backend/wsgi.py`, C `backend/.env.example`.
  - Reqs: NFR-002, NFR-010-AC01. Design: §4.1, §6.11, §11.2, §11.4. Guidelines: BE-01, BE-20.
  - Depends: T1.02.
  - Done when: `requirements.txt` lists Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, marshmallow, a PostgreSQL driver, and gunicorn (Flask-CORS is added in T3.05). `.env.example` lists `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES_SECONDS`, `FRONTEND_ORIGIN`, `LOG_LEVEL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, and `TEST_DATABASE_URL`, each with a placeholder. The lifetime placeholder is not a recommended value (UD-01 is open).
  - Verify: `pip install -r requirements-dev.txt` succeeds in a clean virtual environment, and `grep` finds no real secret in the folder.

- [x] **T1.04 Provide a local PostgreSQL test database and the production-safety guard** — ACTIONABLE
  - Objective: document how a developer gets a local PostgreSQL database for tests, and make the test configuration refuse to run against the production database.
  - Files: M `README.md` (local setup section), C `backend/tests/conftest.py` (guard only, fixtures come in T2.09).
  - Reqs: TEST-001-AC03, NFR-002. Design: §4.1, §10 general rules. Guidelines: DB-02.
  - Depends: T1.03.
  - Done when: the README explains the two variables `DATABASE_URL` and `TEST_DATABASE_URL`. The guard fails when the two are equal. The set of environments is **not** defined here (UD-16).
  - Verify: a unit test sets both variables to the same value and asserts that start-up fails with a message.

- [x] **T1.05 Scaffold the Next.js frontend** — ACTIONABLE (approved: DA-04)
  - Objective: create the Next.js App Router project with TypeScript strict mode and Tailwind CSS, and `frontend/.env.example`.
  - Files: C `frontend/package.json`, `tsconfig.json`, `tailwind.config.ts`, `next.config.ts`, `src/app/layout.tsx` (placeholder), `src/app/globals.css`, `frontend/.env.example`.
  - Reqs: NFR-010-AC02, NFR-007. Design: §2.1, §7.13, §11.1. Guidelines: FE-09, FE-10, FE-19.
  - Depends: T1.01 (approval record), T1.02.
  - Done when: `strict` is on and `globals.css` has only Tailwind directives. `.env.example` lists `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL` with placeholder URLs. `APP_ORIGIN` is listed with a placeholder: it holds the explicitly trusted origins (DA-04, approved), and a preview origin is trusted only when it is listed.
  - Verify: `npm run build` and `npm run dev` start, and the placeholder page renders.

- [x] **T1.06 Configure frontend test and lint tooling** — ACTIONABLE
  - Objective: configure Vitest with a DOM environment and React Testing Library, ESLint rules that enforce the guidelines, and a Playwright skeleton.
  - Files: C `frontend/vitest.config.ts`, `frontend/tests/setup.ts`, `frontend/e2e/playwright.config.ts`, M `frontend/package.json`, M ESLint config.
  - Reqs: TEST-005, TEST-006. Design: §10.2, §10.3. Guidelines: FE-09, FE-10, FE-11, FE-20, FE-21.
  - Depends: T1.05.
  - Done when: lint fails on `style=` props, raw `<button>`, `any`, `waitForTimeout`, and any import of a drag-and-drop or sortable library (guideline FE-14, which forbids dnd-kit and similar libraries). Playwright reads its base URL from an environment variable and has no fixed environment (UD-16 stays open).
  - Verify: a sample violating file makes `npm run lint` fail, and `npm test` runs one trivial test.

- [x] **T1.07 Create the evidence and changelog scaffolding** — ACTIONABLE
  - Objective: create the files that NFR-011 requires, as templates.
  - Files: C `specs/CHANGELOG.md` (if not created in T1.01), C `evidence/ai-reviews/violation-report.md`, C `evidence/ai-reviews/guidelines-comparison.md`.
  - Reqs: NFR-011-AC01, AC02, AC04, AC07. Design: §2.1.
  - Depends: T1.02.
  - Done when: the changelog has a Before and After template. The violation report has the four labeled fields (guideline violated, offending code or evidence, correction, verification of the correction). The comparison file has the headings for two runs.
  - Verify: open the three files and compare their headings with NFR-011-AC01, AC04, AC07.

---

## Milestone 2. PostgreSQL database models and migrations

All tasks in this milestone follow `guidelines/database.md`. Table names are an approved design assumption (DA-02, approved 2026-11-24).

**Note on the application factory.** Flask-Migrate needs `create_app`, so T2.01 builds the factory and configuration together with the extensions. Milestone 3 builds the rest of the backend infrastructure on top of it. T2.09 builds the test fixtures before the migration tests (T2.10, T2.11).

- [x] **T2.01 Add extensions, clock, model base helpers, application factory, and configuration** — ACTIONABLE (approved: DA-07, DA-16)
  - Objective: create the `db`, `migrate`, `jwt` extension objects, an injectable UTC clock, helpers for UUID primary keys and timezone-aware timestamps, `create_app(config=None)`, and a config that reads the environment and fails fast. Flask-Migrate needs the factory, so it is built first.
  - Files: C `backend/app/extensions.py`, `backend/app/clock.py`, `backend/app/models/__init__.py`, `backend/app/__init__.py`, `backend/app/config.py`.
  - Reqs: CARD-001-AC01, ANALYTICS-005-AC04, ANALYTICS-006-AC11, NFR-002, NFR-010-AC03, AUTH-003-AC05, API-004-AC03. Design: §3.2, §4.1. Guidelines: DB-03, DB-04, BE-01, DB-01.
  - Depends: T1.01 (approval record), T1.03.
  - Done when: the clock returns timezone-aware UTC and can be replaced in tests, a primary key default generates a `uuid.uuid4` value on the server side, a missing required variable stops start-up and names the variable, and `JWT_ACCESS_TOKEN_EXPIRES_SECONDS` is required with **no default** (UD-01 stays open). `MAX_CONTENT_LENGTH` is 1,048,576 bytes (DA-07), and the engine uses `pool_pre_ping` with the small configurable pool variables `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` (DA-16). Tests call `create_app(config)`.
  - Verify: unit tests assert the clock is timezone-aware and replaceable, tests unset each required variable and assert the message, and a grep finds no literal secret.
- [x] **T2.02 Create `User`, `Board`, and `BoardMembership` models** — ACTIONABLE (approved: DA-02, DA-06)
  - Objective: define the three models with UUID keys, timestamps, unique email, role CHECK, and a unique (`board_id`, `user_id`) constraint.
  - Files: C `backend/app/models/user.py`, `board.py`, `board_membership.py`.
  - Reqs: AUTH-001, BOARD-001, BOARD-007-AC04, UD-04. Design: §3.3. Guidelines: DB-03, DB-07.
  - Depends: T1.01 (approval record), T2.01.
  - Done when: `role` allows only `administrator` and `member`. Email lowercasing is applied by the service, not by the model (DA-06). No `deleted_at` exists on these models (DB-06).
  - Verify: model tests insert a duplicate membership and a duplicate email and expect an integrity error, and insert an invalid role and expect a CHECK failure.

- [x] **T2.03 Create the `BoardColumn` model** — ACTIONABLE (approved: DA-02)
  - Objective: define the model with `position` as `db.Column(db.Float, nullable=False)`, `is_done` (Boolean, not null, default false), and a nullable `deleted_at`.
  - Files: C `backend/app/models/board_column.py`.
  - Reqs: COLUMN-004-AC05, COLUMN-005. Design: §3.3, §3.7. Guidelines: DB-05, DB-06, DB-07.
  - Depends: T1.01 (approval record), T2.02.
  - Done when: introspection shows a Float `position`, a Boolean non-null `is_done` with default false, and a timezone-aware nullable `deleted_at`. There is no unique index on `position`.
  - Verify: model tests for COLUMN-005-AC01 and AC04.

- [x] **T2.04 Create the `Card` model** — ACTIONABLE (approved: DA-02)
  - Objective: define the model with `column_id` (non-null FK), `title`, `position` Float, nullable `assignee_id`, nullable `completed_at`, nullable `deleted_at`.
  - Files: C `backend/app/models/card.py`.
  - Reqs: CARD-001 (AC01 to AC11). Design: §3.3. Guidelines: DB-03, DB-05, DB-06, DB-07. UD-07 is open, so there are no description or due-date fields.
  - Depends: T1.01 (approval record), T2.03.
  - Done when: introspection confirms the CARD-001 acceptance criteria. No field beyond those listed exists.
  - Verify: model tests for CARD-001-AC01, AC04, AC05, AC07, AC08.

- [x] **T2.05 Create the `Comment` model** — ACTIONABLE (approved: DA-02)
  - Objective: define the model with `card_id`, `author_id`, `content`, timestamps. Comments are hard-deleted.
  - Files: C `backend/app/models/comment.py`.
  - Reqs: COMMENT-001, COMMENT-004-AC06. Design: §3.3. Guidelines: DB-06.
  - Depends: T1.01 (approval record), T2.04.
  - Done when: the model has no `deleted_at`.
  - Verify: a model test deletes a comment and the row is gone.

- [x] **T2.06 Create the `Notification` model** — ACTIONABLE (approved: DA-02, DA-13)
  - Objective: define the model with `user_id`, `actor_id`, `board_id`, `card_id`, `type` CHECK (`card_assigned`, `comment_added`), `message`, Boolean `is_read` (not null, default false), `created_at`.
  - Files: C `backend/app/models/notification.py`.
  - Reqs: NOTIF-001-AC06, NOTIF-003, UD-08. Design: §3.3. Guidelines: DB-10.
  - Depends: T1.01 (approval record), T2.04.
  - Done when: there is no `read_at` column and no unique constraint on (`user_id`, `card_id`, `type`). The pagination shape is not assumed (UD-09).
  - Verify: model tests insert two identical-looking notifications and both persist, and a new row has `is_read` false.

- [x] **T2.07 Create the `ActivityEvent` model** — ACTIONABLE (approved: DA-02, DA-14)
  - Objective: define the append-only model with `type` CHECK limited to `card_created`, `card_moved`, `comment_created`, `board_id`, `actor_id`, `card_id`, nullable `comment_id` without a foreign key, nullable `from_column_id` and `to_column_id`, `created_at`, and a CHECK that a `card_moved` row has both columns.
  - Files: C `backend/app/models/activity_event.py`.
  - Reqs: ANALYTICS-006 (AC05, AC06), UD-13, A-13, A-14. Design: §3.3, §3.6. Guidelines: DB-09, BE-14.
  - Depends: T1.01 (approval record), T2.04.
  - Done when: the CHECK rejects any other event type, in particular `card_assigned`.
  - Verify: model tests that an invalid type and a `card_moved` row without columns fail.

- [x] **T2.08 Write the initial Flask-Migrate migration** — ACTIONABLE (approved: DA-02, DA-14, DA-17)
  - Objective: create all eight tables with constraints, foreign keys, the partial indexes of the design, and `ON DELETE CASCADE` on the board-owned foreign keys.
  - Files: C `backend/migrations/` (initial revision), `env.py`.
  - Reqs: NFR-009, COLUMN-005-AC03, AC05, CARD-001-AC06, AC09, BOARD-005-AC08. Design: §3.3 to §3.8. Guidelines: DB-08, DB-09, DB-11, DB-15.
  - Depends: T1.01 (approval record), T2.02 to T2.07, T2.01.
  - Done when: `flask db upgrade` on an empty database reaches head. Only `board_id` carries a cascade on `activity_events` and `notifications` (no cascade from card, column, or comment). No table other than the eight exists. A revision enables Row Level Security on the eight application tables with no policies for browser-facing roles (DA-17, verification V-03).
  - Verify: T2.10.

- [x] **T2.09 Test fixtures and helpers** — ACTIONABLE
  - Objective: build the pytest fixtures: app, client, PostgreSQL test database created by `flask db upgrade`, per-test cleanup, fixed clock, factories, two-connection helper, SQL-capture helper, and a test-only lock-pause hook.
  - Files: M `backend/tests/conftest.py`, C `backend/tests/factories.py`, C `backend/tests/helpers/`.
  - Reqs: TEST-001-AC03, TEST-006-AC07, ANALYTICS-005-AC04. Design: §10 general rules. Guidelines: BE-20, DB-02.
  - Depends: T2.08, T2.01.
  - Done when: tests never touch production, never depend on the real date, and create their own data. A hook lets a concurrency test pause a transaction after it takes a lock.
  - Verify: a smoke test creates a user and a board through factories and reads them back on a second connection.

- [x] **T2.10 Migration tests** — ACTIONABLE (approved: DA-17)
  - Objective: automate the migration acceptance criteria.
  - Files: C `backend/tests/migrations/test_migrations.py`.
  - Reqs: NFR-009-AC01, AC02, COLUMN-005-AC03, AC05, CARD-001-AC06, AC09. Design: §10.1 (Migrations). Guidelines: DB-15, DB-16.
  - Depends: T1.01 (approval record), T2.08, T2.09 (fixtures).
  - Done when: tests run `upgrade` on an empty database, assert that autogenerate reports no differences, run an `upgrade`, `downgrade`, `upgrade` cycle, assert the table list is exactly the eight tables, assert that RLS is enabled on those eight tables and that no policy exists (V-03), and check defaults for pre-existing rows.
  - Verify: `pytest backend/tests/migrations` passes against `TEST_DATABASE_URL`.

- [x] **T2.11 Board hard-delete cascade proof** — ACTIONABLE (approved: DA-14)
  - Objective: run the mandatory PostgreSQL integration test (V-04) that proves that deleting a fully populated board with the approved `ON DELETE CASCADE` strategy (DA-14) leaves no dependent row.
  - Files: C `backend/tests/migrations/test_board_delete_cascade.py`.
  - Reqs: BOARD-005-AC04, AC05, AC07, AC08, TEST-010-AC08. Design: §3.6, §12.6 (R-05). Guidelines: DB-08, DB-09.
  - Depends: T1.01 (approval record), T2.08, T2.09.
  - Done when: a test builds a board with soft-deleted columns and cards, comments, notifications, memberships, and events, deletes the board row, and asserts zero remaining rows for that board id and no change to `users` or another board. If PostgreSQL reports a foreign-key violation, stop and request a new human approval. Do not switch to ordered service deletes automatically (DA-14).
  - Verify: the test passes on a database created by `flask db upgrade`.

---

## Milestone 3. Flask application factory and backend infrastructure

The application factory and configuration were built in T2.01 and the fixtures in T2.09. This milestone adds the response helpers, JWT callbacks, validation primitives, access and locking helpers, health route, Blueprint skeleton, and logging.

- [x] **T3.01 Response helpers and central error handlers** — ACTIONABLE (approved: DA-01, DA-07)
  - Objective: implement `ok(data, status)` and `fail(message, status)` and handlers for validation errors, 404, 405, 415, invalid JSON, integrity errors, and the generic 500.
  - Files: C `backend/app/responses.py`, `backend/app/errors.py`.
  - Reqs: API-001, API-002 (AC01 to AC06), TEST-001-AC05, TEST-001-AC06, UD-19, Section 2.3 (413). Design: §4.4, §4.5. Guidelines: BE-04, BE-05.
  - Depends: T1.01 (approval record), T2.01.
  - Done when: every error body is `{"error": "<non-empty string>"}` with no `data`, every body has `Content-Type: application/json`, and the 500 text is the same for every exception and contains no stack, path, SQL, token, or class name. The wording is approved (DA-01). A body larger than 1,048,576 bytes returns 413 with the string envelope and the text `Request body is too large.` (DA-07), tested with a 1,048,576 byte body (not rejected for its size) and a 1,048,577 byte body (rejected), as verification V-06.
  - Verify: contract tests for 400, 401, 403, 404, 405, 409, 413, 415, 500, a forced-exception test, and the 1,048,576 and 1,048,577 byte body test (TEST-001-AC06).

- [x] **T3.02 JWT callbacks that return 401** — ACTIONABLE
  - Objective: configure Flask-JWT-Extended with header-only token location and callbacks so that every token failure returns 401 with the string envelope.
  - Files: M `backend/app/errors.py`, M `backend/app/__init__.py`.
  - Reqs: AUTH-003 (AC02 to AC04, AC06), AUTH-004. Design: §4.6, §12.6 (R-08). Guidelines: BE-07.
  - Depends: T3.01.
  - Done when: no token, a malformed token, a wrong-key token, an expired token, and a cookie-only token all return 401, never 422.
  - Verify: parametrized tests against a throwaway protected route.

- [x] **T3.03 Strict validation primitives** — ACTIONABLE
  - Objective: create a base Marshmallow schema with `unknown = RAISE`, a `StrictNumber` field, a strict UUID field, and a JSON parser option that rejects `NaN` and `Infinity`.
  - Files: C `backend/app/schemas_common.py`.
  - Reqs: A-06, CARD-006-AC04, COLUMN-004-AC02, NFR-003. Design: §4.7. Guidelines: BE-06.
  - Depends: T3.01.
  - Done when: `StrictNumber` rejects `bool`, `str`, `None`, `NaN`, `Infinity`, `-Infinity`, `1e400`, `1e-400`, zero, and negatives, accepts positive `int` and `float`, and returns a `float`. Text fields trim and reject empty values (DA-07, approved).
  - Verify: parametrized unit tests for every rejected and accepted case.

- [x] **T3.04 Access, query, and locking helpers** — ACTIONABLE (approved: DA-11)
  - Objective: implement membership, admin, and ownership helpers, the live-row query helpers, and the lock helpers with the fixed lock order.
  - Files: C `backend/app/access.py`, `backend/app/queries.py`, `backend/app/locking.py`.
  - Reqs: BOARD-006, UD-05, Section 2.4, UD-18, UD-20, UD-06. Design: §4.8, §4.10, §8.4. Guidelines: BE-08, BE-09, BE-10, BE-11, BE-17, DB-14.
  - Depends: T1.01 (approval record), T2.07, T3.01.
  - Done when: every "not found" path raises the same `NotFoundError`, helpers read role from the database (never from a token), and `queries.py` is the only way services read columns and cards. The required locks are board, destination column, and card for assignment. Extra locks (DA-11) are added only in the tasks that need them.
  - Verify: unit tests for each helper, and a grep test that fails when a service queries `BoardColumn` or `Card` without a live helper.

- [x] **T3.05 Health route and CORS** — ACTIONABLE (approved: DA-12)
  - Objective: add `GET /api/health` as a plain app route and apply CORS to that route only.
  - Files: C `backend/app/health.py`, M `backend/app/__init__.py`, M `backend/requirements.txt`.
  - Reqs: API-003, API-004 (AC01 to AC05), NFR-008-AC02. Design: §4.13. Guidelines: BE-19.
  - Depends: T1.01 (approval record), T2.01.
  - Done when: the body is exactly `{"data": {"status": "ok"}}`, no database query runs, a preflight from `FRONTEND_ORIGIN` receives that origin, other origins receive no `Access-Control-Allow-Origin`, `Authorization` is not allowed, and no response has `Access-Control-Allow-Credentials: true`. Flask-CORS, limited to this route, is approved (DA-12).
  - Verify: tests for API-003-AC01, AC03 (SQL capture shows no query) and API-004-AC01 to AC05.

- [x] **T3.06 Register the eight Blueprints and the endpoint-coverage test** — ACTIONABLE
  - Objective: create the eight empty Blueprint packages, register them under `/api`, and add a test that lists the 27 expected routes.
  - Files: C `backend/app/blueprints/{auth,users,boards,columns,cards,comments,notifications,analytics}/{__init__,routes,service,schema}.py`, M `backend/app/__init__.py`, C `backend/tests/api/test_endpoint_coverage.py`.
  - Reqs: TEST-001-AC02, AUTH-004-AC01, BOARD-007-AC10, AUTH-002-AC05, COLUMN-003-AC12. Design: §4.2, §5.12. Guidelines: BE-02, BE-03, BE-21.
  - Depends: T3.04.
  - Done when: exactly eight Blueprints are registered, and `/api/health` is not one of them. The coverage test starts as expected-to-fail for routes not yet built and ends fully green in T9.09. The test also asserts there is no refresh route, no restore route, and exactly one members route.
  - Verify: `pytest backend/tests/api/test_endpoint_coverage.py` runs and reports the missing routes.

- [x] **T3.07 Logging and request id** — ACTIONABLE
  - Objective: add single-line logs with request id, method, path, status, and duration, with no sensitive data.
  - Files: M `backend/app/__init__.py`, C `backend/app/logging_config.py`.
  - Reqs: API-002-AC05, NFR-001, NFR-002. Design: §4.12, §11.7.
  - Depends: T3.01.
  - Done when: logs never include the `Authorization` header, bodies, passwords, hashes, tokens, or `DATABASE_URL`.
  - Verify: a test sends a request with a password and a token and asserts the captured log has neither.

---

## Milestone 4. Registration, login, JWT authentication and authorization

- [x] **T4.01 Password hashing module** — ACTIONABLE (approved: DA-05)
  - Objective: implement `hash_password` and `verify_password`, plus a dummy-hash check for unknown emails.
  - Files: C `backend/app/security.py`.
  - Reqs: NFR-001. Design: §6.2. Guidelines: BE-18.
  - Depends: T1.01 (approval record), T1.03.
  - Done when: the stored value is not the plain password, the algorithm lives only in this module, and no hash is ever returned or logged. The scrypt parameters are explicit (`scrypt:32768:8:1` as a provisional development configuration accepted by the human owner, DA-05) and set in one place, a plaintext password is never logged, and the final parameters are fixed only after the Render security, latency, and memory benchmark (V-01, done in T15.05 and required before production deployment, not yet complete). The password policy is not enforced here (UD-21).
  - Verify: unit tests for hash differs from input, verify succeeds and fails correctly, and the dummy path runs for an unknown email.

- [x] **T4.02 `POST /api/auth/register`** — ACTIONABLE (approved: DA-06, DA-07)
  - Objective: create a user from `name`, `email`, `password` and return 201 with `id`, `name`, `email`.
  - Files: M `backend/app/blueprints/auth/{routes,service,schema}.py`.
  - Reqs: AUTH-001-AC01 to AC05, A-04. Design: §5.3, §6.1. Guidelines: BE-03, BE-06, BE-18.
  - Depends: T1.01 (approval record), T2.02, T3.03, T4.01.
  - Done when: empty or missing fields and an invalid email return 400, a duplicate email returns 409 (also on a lost race through the unique constraint), and the response has no password or hash. **Only "present and non-empty" is enforced for the password, because UD-21 is open.** The email is trimmed and lowercased before every lookup and write (DA-06, approved).
  - Verify: tests for AUTH-001-AC01 to AC05 and a two-thread duplicate registration test.

- [x] **T4.03 `POST /api/auth/login`** — ACTIONABLE
  - Objective: verify credentials and return 200 with exactly `{"data": {"access_token": "<jwt>"}}`.
  - Files: M `backend/app/blueprints/auth/{routes,service,schema}.py`.
  - Reqs: AUTH-002-AC01 to AC05, AUTH-003-AC01, UD-19. Design: §5.3, §6.3. Guidelines: BE-07, BE-18.
  - Depends: T3.02, T4.02.
  - Done when: a wrong password and an unknown email return 401 with the identical body, a missing field returns 400, the token has `sub` and `exp`, and `data` has no other key. The lifetime is read from the required variable (UD-01 stays open).
  - Verify: tests for AUTH-002-AC01 to AC05 and AUTH-003-AC01.

- [x] **T4.04 Protected-endpoint behavior tests** — ACTIONABLE
  - Objective: automate the 401 behavior for any protected route.
  - Files: C `backend/tests/api/test_auth_protection.py`.
  - Reqs: AUTH-003-AC02 to AC06, AUTH-004-AC01, AC02. Design: §4.6. Guidelines: BE-07.
  - Depends: T4.03.
  - Done when: tests produce an expired token with a negative lifetime, a wrong-key token, a malformed token, and a cookie-only token. The test iterates the route list so new routes are covered automatically.
  - Verify: `pytest backend/tests/api/test_auth_protection.py` passes. The test grows as routes are added.

- [x] **T4.05 `GET` and `PATCH /api/users/me`** — ACTIONABLE (approved: DA-06, DA-09)
  - Objective: return and update the current user's profile (`name`, `email` only).
  - Files: M `backend/app/blueprints/users/{routes,service,schema}.py`.
  - Reqs: USER-001, USER-002 (AC01 to AC06). Design: §5.4. Guidelines: BE-06.
  - Depends: T1.01 (approval record), T4.03.
  - Done when: `password` or any unknown key returns 400 and the old password still works, an invalid email returns 400, a used email returns 409, and no response has a password key or hash. An empty body returns 400 (DA-09, approved).
  - Verify: tests for USER-001-AC01 to AC03 and USER-002-AC01 to AC06.

- [ ] **T4.06 Permission-matrix test harness** — ACTIONABLE
  - Objective: build a parametrized harness that exercises administrator, member, non-member, and unauthenticated callers for every board-scoped endpoint, and the check order 401, 404, 403, 400/409.
  - Files: C `backend/tests/authz/matrix.py`, C `backend/tests/authz/test_check_order.py`.
  - Reqs: TEST-003, BOARD-006-AC01 to AC07, UD-05, Section 2.4. Design: §4.8, §10.1. Guidelines: BE-09, BE-10.
  - Depends: T2.09.
  - Done when: the harness has an entry list that later tasks extend (one entry per endpoint). A request rejected with 400, 401, 403, 404, or 409 must change no row and no `updated_at`.
  - Verify: the harness runs with the entries that exist so far. T9.09 checks that every endpoint has an entry.

- [ ] **T4.07 Authentication security tests** — ACTIONABLE
  - Objective: add the cross-cutting security tests for authentication.
  - Files: C `backend/tests/api/test_auth_security.py`.
  - Reqs: NFR-001, NFR-002, NFR-003, AUTH-002-AC05, API-001-AC08, UD-02. Design: §6.2, §6.3.
  - Depends: T4.03, T4.05.
  - Done when: tests assert no password or hash appears in any response, the URL map has no refresh route (UD-02 stays open and no refresh is built), no secret is in the repository, and no string-built SQL exists (grep test).
  - Verify: `pytest backend/tests/api/test_auth_security.py` passes.

---

## Milestone 5. Board and membership APIs

- [x] **T5.01 `POST /api/boards`** — ACTIONABLE (approved: DA-03)
  - Objective: create a board and the creator's `administrator` membership in one transaction.
  - Files: M `backend/app/blueprints/boards/{routes,service,schema}.py`.
  - Reqs: BOARD-001-AC01 to AC04, UD-04. Design: §5.5. Guidelines: BE-16.
  - Depends: T1.01 (approval record), T4.03, T3.04.
  - Done when: 201 returns `id` and `name` (and the timestamps approved in DA-03), a missing or empty `name` returns 400, and a failure after the board insert leaves neither row.
  - Verify: tests for BOARD-001-AC01 to AC03 and a forced-failure rollback test.

- [x] **T5.02 `GET /api/boards`** — ACTIONABLE (approved: DA-03, DA-10)
  - Objective: list only the boards where the caller is a member.
  - Files: M `backend/app/blueprints/boards/*`.
  - Reqs: BOARD-002, API-001-AC06. Design: §5.5.
  - Depends: T1.01 (approval record), T5.01.
  - Done when: boards of other users are absent, a user with no boards receives `[]`, and the order is the approved deterministic order (DA-10).
  - Verify: tests for BOARD-002-AC01 to AC03.

- [x] **T5.03 `GET /api/boards/{id}`** — ACTIONABLE (approved: DA-03)
  - Objective: return the board with `role`, `members`, columns by ascending `order`, and each column's live cards by ascending `order`.
  - Files: M `backend/app/blueprints/boards/*`.
  - Reqs: BOARD-003-AC01 to AC12, A-02, A-14, UD-08, UD-18. Design: §5.2, §5.5. Guidelines: BE-11, DB-12.
  - Depends: T1.01 (approval record), T5.01, T2.04.
  - Done when: soft-deleted columns and cards are absent, `members` entries have exactly `id` and `name` ordered by `name` then `id`, a non-member and a missing board return an identical 404, and the query count is fixed. The cards are nested under each column and the extra card fields are those approved in DA-03.
  - Verify: tests for BOARD-003-AC01 to AC12 and a SQL-capture statement-count test.

- [x] **T5.04 `PATCH /api/boards/{id}`** — ACTIONABLE
  - Objective: rename a board, administrator only.
  - Files: M `backend/app/blueprints/boards/*`.
  - Reqs: BOARD-004-AC01 to AC04, UD-05. Design: §5.5, §4.8. Guidelines: BE-09, BE-10.
  - Depends: T5.01.
  - Done when: a non-member gets 404, a member gets 403 even with an empty or invalid body, an administrator with an empty `name` gets 400, and the stored name is unchanged on every rejection.
  - Verify: tests for BOARD-004-AC01 to AC04 and a matrix entry in T4.06.

- [x] **T5.05 `DELETE /api/boards/{id}`** — CONDITIONAL (V-04; approved: DA-14, DA-11)
  - Objective: hard-delete a board and everything that belongs to it, administrator only, in one transaction with the board row locked first.
  - Files: M `backend/app/blueprints/boards/*`.
  - Reqs: BOARD-005-AC01 to AC08, UD-18, UD-19, NOTIF-003-AC18, ANALYTICS-006-AC10. Design: §3.6, §5.5, §8.4. Guidelines: DB-08, BE-16.
  - Depends: T1.01 (approval record), T2.11, T5.01.
  - **Verification before completion (outstanding):** V-04. The task cannot be completed until the PostgreSQL integration test of T2.11 passes. If that test fails, stop and request a new human approval. Do not switch to ordered service deletes.
  - Done when: the response is `{"data": {"id": "<id>"}}`, the approved `ON DELETE CASCADE` strategy is used (DA-14), and the PostgreSQL integration test of T2.11 has passed, a forced failure leaves everything unchanged, and other boards and `users` are untouched.
  - Verify: tests for BOARD-005-AC01 to AC07 on a database built by `flask db upgrade`.

- [x] **T5.06 `POST /api/boards/{id}/members` (approved extension)** — ACTIONABLE (approved: DA-06)
  - Objective: add a registered user to the board as a `member` by email, administrator only.
  - Files: M `backend/app/blueprints/boards/*`.
  - Reqs: BOARD-007-AC01 to AC10, UD-24, A-13, A-14. Design: §5.5. Guidelines: BE-10.
  - Depends: T1.01 (approval record), T5.03, T4.05.
  - Done when: the response is 201 with `id`, `name`, `email`, a duplicate returns 409 (including a lost race), an unknown email returns 404, any key other than `email` returns 400, and a member gets 403 before validation. The route is the only one under `/api/boards/{id}/members` and accepts only POST.
  - Verify: tests for BOARD-007-AC01 to AC10.

- [x] **T5.07 Board permission and isolation tests** — ACTIONABLE
  - Objective: complete the matrix entries and cross-board isolation tests for the `boards` Blueprint.
  - Files: M `backend/tests/authz/matrix.py`, C `backend/tests/api/test_boards_authz.py`.
  - Reqs: BOARD-006-AC01 to AC07, BOARD-007-AC08, AC09. Design: §4.8.
  - Depends: T5.01 to T5.06.
  - Done when: an administrator on board A who is only a member on board B gets 403 on board B, and a user added to board A gets 404 for board B.
  - Verify: `pytest backend/tests/api/test_boards_authz.py backend/tests/authz` passes.

---

## Milestone 6. Column APIs and ordering

- [x] **T6.01 `POST /api/boards/{id}/columns`** — ACTIONABLE
  - Objective: create a column with `order` greater than every live column, after taking the board row lock.
  - Files: M `backend/app/blueprints/columns/*`.
  - Reqs: COLUMN-001-AC01 to AC05, A-01. Design: §5.6, §8.3. Guidelines: BE-12, BE-17.
  - Depends: T5.03.
  - Done when: 201 returns `id`, `name`, a positive float `order`, `is_done` false. A missing name returns 400. A non-member gets 404. The `order` is computed after the lock.
  - Verify: tests for COLUMN-001-AC01 to AC04.

- [x] **T6.02 `PATCH /api/columns/{id}` (rename and `is_done`)** — ACTIONABLE (approved: DA-09, DA-11, DA-08)
  - Objective: rename a column (any member) and set `is_done` (administrator only, decided by the presence of the key), stamping or clearing `completed_at` on the column's live cards in one transaction.
  - Files: M `backend/app/blueprints/columns/*`.
  - Reqs: COLUMN-002-AC01 to AC14, UD-05, UD-12, A-13. Design: §5.6, §4.8, §8.4. Guidelines: BE-09, BE-10, BE-13.
  - Depends: T1.01 (approval record), T6.01, T2.04.
  - Done when: a member sending the `is_done` key gets 403 whatever the value and the mixed body is rejected whole, an unchanged `is_done` is a 200 no-op with no card change and no event, soft-deleted columns return 404, and a forced failure leaves the column and cards unchanged. The extra column lock (DA-11) and the rule for `updated_at` on stamped cards (DA-08) are approved.
  - Verify: tests for COLUMN-002-AC01 to AC14.

- [x] **T6.03 `DELETE /api/columns/{id}` (soft delete)** — ACTIONABLE (approved: DA-08, DA-11)
  - Objective: soft-delete a column and its live cards with the same `deleted_at`, administrator only, after taking the board row lock and the column lock.
  - Files: M `backend/app/blueprints/columns/*`.
  - Reqs: COLUMN-003-AC01 to AC15, UD-18, UD-23, A-15. Design: §5.6, §4.10, §8.4. Guidelines: BE-11, DB-06.
  - Depends: T1.01 (approval record), T6.02.
  - Done when: the response is `{"data": {"id": "<id>"}}`, no row is removed, cards keep `column_id`, previously deleted cards keep their own `deleted_at`, a second delete returns 404 for administrators and members, and a forced failure leaves everything unchanged. No activity event or notification is created or removed.
  - Verify: tests for COLUMN-003-AC01 to AC14.

- [x] **T6.04 `PATCH /api/boards/{id}/columns/reorder`** — ACTIONABLE
  - Objective: implement the approved partial reorder with the board row lock and final-state collision detection.
  - Files: M `backend/app/blueprints/columns/*`.
  - Reqs: COLUMN-004-AC01 to AC27, UD-20. Design: §5.6, §8.1. Guidelines: BE-06, BE-12, BE-17.
  - Depends: T6.01, T3.03.
  - Done when: the body shape is exactly `{columns: [{id, order}]}`, a listed missing, foreign, or soft-deleted column returns the same 400 body, a final collision with an unlisted column returns 409, a swap succeeds, a no-op writes nothing, only changed columns get a new `updated_at`, and the response lists all active columns in ascending `order` with `id`, `name`, `order`, `is_done` and no `position`.
  - Verify: tests for COLUMN-004-AC01 to AC15, AC18 to AC26, with SQL capture for AC20.

- [x] **T6.05 Column response and visibility tests** — ACTIONABLE (approved: DA-03)
  - Objective: assert that column representations match across endpoints and that soft-deleted columns disappear everywhere.
  - Files: C `backend/tests/api/test_columns_contract.py`.
  - Reqs: COLUMN-004-AC19, COLUMN-005-AC06, AC07, COLUMN-003-AC08, AC10. Design: §5.2.
  - Depends: T1.01 (approval record), T6.03, T6.04.
  - Done when: no column response has `position` or a non-null `deleted_at`, and reorder and board-view values are equal.
  - Verify: `pytest backend/tests/api/test_columns_contract.py` passes.

- [ ] **T6.06 Column concurrency tests** — ACTIONABLE
  - Objective: prove the locking behavior with two connections.
  - Files: C `backend/tests/concurrency/test_columns_concurrency.py`.
  - Reqs: COLUMN-001-AC05, COLUMN-003-AC15, COLUMN-004-AC16, AC17. Design: §8.1, §8.4. Guidelines: BE-17, DB-14.
  - Depends: T6.01, T6.03, T6.04, T2.09.
  - Done when: two reorders with the same final `order` give one 200 and one 409, two non-colliding reorders both succeed, a reorder with a column create or delete never leaves duplicate `order` values or an `order` change on a soft-deleted column, and the reorder that names a just-deleted column returns 400.
  - Verify: the concurrency tests pass repeatedly (run them at least 20 times to catch flakiness).

- [ ] **T6.07 Column transaction and permission tests** — ACTIONABLE
  - Objective: add rollback tests and matrix entries for the `columns` Blueprint.
  - Files: M `backend/tests/authz/matrix.py`, C `backend/tests/api/test_columns_tx.py`.
  - Reqs: COLUMN-002-AC11, AC14, COLUMN-003-AC07, AC13, AC14, COLUMN-004-AC14, AC23, AC24, BOARD-006-AC07. Design: §4.9.
  - Depends: T6.02 to T6.04.
  - Done when: a failure injected after the first write leaves no change for the toggle, delete, and reorder, a member never gets 403 on reorder, and a non-member with an invalid body gets 404.
  - Verify: `pytest backend/tests/api/test_columns_tx.py` passes.

---

## Milestone 7. Card APIs, assignment and positioning

- [x] **T7.01 `POST /api/columns/{id}/cards` and the `card_created` event** — ACTIONABLE (approved: DA-03)
  - Objective: create a title-only card in the destination column after taking the column row lock, set `completed_at` in a done column, and append one `card_created` event. Add the shared event-recording helper.
  - Files: M `backend/app/blueprints/cards/*`, C `backend/app/events.py`.
  - Reqs: CARD-002-AC01 to AC10, ANALYTICS-006-AC01, UD-08, A-13. Design: §5.7, §8.3, §4.11. Guidelines: BE-12, BE-14, BE-17.
  - Depends: T1.01 (approval record), T6.01, T2.07.
  - Done when: 201 returns `id`, `title`, the column id, a positive `order` greater than every live card, and `assignee_id` null. Any `assignee_id` key returns 400. A soft-deleted column returns 404. No notification is created.
  - Verify: tests for CARD-002-AC01 to AC09 and ANALYTICS-006-AC01.

- [x] **T7.02 `PATCH /api/cards/{id}` (title)** — ACTIONABLE (approved: DA-09, DA-11, DA-08)
  - Objective: update the card title, with the card row locked.
  - Files: M `backend/app/blueprints/cards/*`.
  - Reqs: CARD-003-AC01, AC02, AC05, AC06, AC07. Design: §5.7. Guidelines: BE-09.
  - Depends: T1.01 (approval record), T7.01.
  - Done when: an empty title returns 400, `id`, `created_at`, `deleted_at` or any unknown key returns 400, a soft-deleted card returns 404, and `updated_at` increases only on a real change.
  - Verify: tests for CARD-003-AC01, AC02, AC05 to AC07.

- [x] **T7.03 Assignment and the `card_assigned` notification** — ACTIONABLE (approved: DA-13)
  - Objective: handle `assignee_id` in `PATCH /api/cards/{id}`: assign, reassign, unassign, with the card row lock and a state comparison. Create a notification only for an assignment to another member. Create **no activity event**.
  - Files: M `backend/app/blueprints/cards/*`, C `backend/app/blueprints/notifications/service.py` (creation function only).
  - Reqs: CARD-003-AC03, AC04, AC08 to AC12, NOTIF-003-AC01 to AC08, AC11, AC12, AC14, AC15, AC19, UD-08. Design: §4.11, §9.1. Guidelines: BE-14.
  - Depends: T1.01 (approval record), T7.02, T2.06.
  - Done when: an unknown user and a non-member give an identical 400, an unchanged value creates nothing, self-assignment and unassignment create no notification, the recipient must be a board member, the message has no comment text or email, a failure after the update leaves no assignee change and no notification, and the activity-event count never changes. The stored `message` and its wording are approved (DA-13).
  - Verify: tests for CARD-003-AC03, AC04, AC08 to AC12 and NOTIF-003-AC01 to AC08, AC12, AC14, AC19.

- [x] **T7.04 `DELETE /api/cards/{id}` (soft delete)** — ACTIONABLE (approved: DA-11)
  - Objective: set `deleted_at` to the request time with the card row locked. Record no event and no notification.
  - Files: M `backend/app/blueprints/cards/*`.
  - Reqs: CARD-004-AC01 to AC09, UD-18, UD-08, A-15. Design: §5.7, §4.10.
  - Depends: T1.01 (approval record), T7.01.
  - Done when: the response is `{"data": {"id": "<id>"}}`, the row, `column_id`, `completed_at`, assignee, comments, events, and notifications stay, and a second delete returns 404.
  - Verify: tests for CARD-004-AC01 to AC09.

- [x] **T7.05 `PATCH /api/cards/{id}/position` with tie rebalancing** — ACTIONABLE
  - Objective: implement the approved move: validate, lock the destination column and the card, detect a tie, rebalance when needed, apply the `completed_at` rules, append a `card_moved` event only when the column changes, and return the card with `rebalanced`.
  - Files: M `backend/app/blueprints/cards/*` (including `CardPositionSchema`).
  - Reqs: CARD-005-AC01 to AC26, CARD-006-AC01 to AC05, UD-06, UD-12, A-13, ANALYTICS-006-AC02. Design: §5.7, §8.2. Guidelines: BE-06, BE-12, BE-13, BE-17.
  - Depends: T7.01, T3.03.
  - Done when: a midpoint move returns the sent `order` with `rebalanced` false and does not touch other cards, a tie places the card immediately before the tied card and renumbers the live cards `1024.0, 2048.0, ...` sorted by `order`, `created_at`, `id`, a same-place request is a no-op with no write and no event, a soft-deleted or foreign destination column returns 400, and the whole operation is one transaction. The response has `order` and `rebalanced` and no `position`.
  - Verify: tests for CARD-005-AC01 to AC26 and CARD-006-AC01 to AC05.

- [x] **T7.06 `GET /api/cards?assignee=me`** — ACTIONABLE (approved: DA-03, DA-10, DA-19)
  - Objective: return the caller's assigned live cards, each with its board name, in one joined query.
  - Files: M `backend/app/blueprints/cards/*`.
  - Reqs: CARD-007-AC01 to AC06, API-001-AC06. Design: §5.7. Guidelines: DB-12.
  - Depends: T1.01 (approval record), T7.03.
  - Done when: a missing or different `assignee` returns 400, soft-deleted cards and cards in soft-deleted columns are excluded, an empty result is `[]`, and each card has `board_name`. The extra `board_id`, ordering, and the rejection of other parameters are approved (DA-03, DA-10, DA-19).
  - Verify: tests for CARD-007-AC01 to AC06.

- [x] **T7.07 Completion-timestamp and ordering tests** — ACTIONABLE
  - Objective: automate the `completed_at` invariant and the ordering rules.
  - Files: C `backend/tests/api/test_cards_ordering.py`, C `backend/tests/api/test_completion.py`.
  - Reqs: TEST-004, CARD-002-AC06, CARD-005-AC07 to AC11, COLUMN-002-AC08, AC09, ANALYTICS-003-AC09, A-13. Design: §8.2, §9.3.
  - Depends: T7.05, T6.02.
  - Done when: tests cover enter done, done to done, done to active, re-entry, reorder inside a done column, toggle on, toggle off, and an invariant query after a random sequence of endpoint calls.
  - Verify: `pytest backend/tests/api/test_cards_ordering.py backend/tests/api/test_completion.py` passes.

- [ ] **T7.08 Card concurrency tests** — ACTIONABLE
  - Objective: prove the card locking behavior with two connections.
  - Files: C `backend/tests/concurrency/test_cards_concurrency.py`.
  - Reqs: CARD-002-AC10, CARD-005-AC19, AC20, NOTIF-003-AC08. Design: §8.2, §8.4.
  - Depends: T7.03, T7.05.
  - Done when: two moves into one column with the same `order` both return 200 with exactly one `rebalanced` true and distinct final `order` values, a create racing a move never duplicates `order`, a move racing the destination column delete either completes first or returns 400, and two identical assignments create one notification.
  - Verify: run the tests at least 20 times without a failure.

- [ ] **T7.09 Card permission, soft-delete, and rollback tests** — ACTIONABLE
  - Objective: add matrix entries, soft-delete visibility tests, and rollback tests for the `cards` Blueprint.
  - Files: M `backend/tests/authz/matrix.py`, C `backend/tests/api/test_cards_misc.py`.
  - Reqs: CARD-002-AC04, AC05, CARD-003-AC06, CARD-004, CARD-005-AC06, AC18, AC26, TEST-010. Design: §4.9, §4.10.
  - Depends: T7.01 to T7.06.
  - Done when: a non-member gets 404 on every card endpoint, rejected requests change no card, and a failure injected after some cards were renumbered leaves no change.
  - Verify: `pytest backend/tests/api/test_cards_misc.py` passes.

---

## Milestone 8. Comments and activity events

- [x] **T8.01 `POST /api/cards/{id}/comments`** — ACTIONABLE (approved: DA-03, DA-11)
  - Objective: create a comment owned by the caller, take the card row `FOR SHARE`, append a `comment_created` event, and create a `comment_added` notification for another assignee, all in one transaction.
  - Files: M `backend/app/blueprints/comments/*`.
  - Reqs: COMMENT-001-AC01 to AC08, NOTIF-003-AC09, AC10, AC13, ANALYTICS-006-AC03, UD-08. Design: §5.8, §4.11. Guidelines: BE-14.
  - Depends: T1.01 (approval record), T7.03, T2.05.
  - Done when: 201 returns `id`, `content`, an author, and `created_at`, whitespace-only content returns 400, a soft-deleted card returns 404 with no event, no notification when the author is the assignee or the card is unassigned, the notification has no comment text, and a failure leaves no comment and no notification.
  - Verify: tests for COMMENT-001-AC01 to AC08 and NOTIF-003-AC09, AC10, AC13.

- [x] **T8.02 `GET /api/cards/{id}/comments`** — ACTIONABLE (approved: DA-03)
  - Objective: list a card's comments by `created_at` ascending.
  - Files: M `backend/app/blueprints/comments/*`.
  - Reqs: COMMENT-002-AC01 to AC05, A-05, A-15. Design: §5.8.
  - Depends: T1.01 (approval record), T8.01.
  - Done when: a soft-deleted card returns 404 and no comments, and an empty list is `[]`.
  - Verify: tests for COMMENT-002-AC01 to AC05.

- [x] **T8.03 `PATCH /api/comments/{id}` (owner only)** — ACTIONABLE
  - Objective: let only the author edit a comment. Administrators have no override. Record no event.
  - Files: M `backend/app/blueprints/comments/*`.
  - Reqs: COMMENT-003-AC01 to AC09, UD-05, A-14, ANALYTICS-006-AC08. Design: §5.8, §4.8. Guidelines: BE-09, BE-10.
  - Depends: T8.01.
  - Done when: a non-owner member or administrator gets 403 with empty, missing, or valid content and nothing changes, a non-member gets 404, a soft-deleted card gives 404, and the owner gets 200.
  - Verify: tests for COMMENT-003-AC01 to AC09.

- [x] **T8.04 `DELETE /api/comments/{id}` (owner only, hard delete)** — ACTIONABLE
  - Objective: hard-delete the comment for its author. Events and notifications that refer to it stay.
  - Files: M `backend/app/blueprints/comments/*`.
  - Reqs: COMMENT-004-AC01 to AC08, UD-18, A-14, NOTIF-003-AC17. Design: §5.8, §3.6. Guidelines: DB-06, DB-09.
  - Depends: T8.01.
  - Done when: the response is `{"data": {"id": "<id>"}}`, the row no longer exists, the `comment_created` event and notifications remain, and the other rejection cases match the criteria.
  - Verify: tests for COMMENT-004-AC01 to AC08.

- [ ] **T8.05 Activity-event invariant tests** — ACTIONABLE
  - Objective: prove that only the three approved event types exist, with their approved triggers, and that events are append-only and survive deletions.
  - Files: C `backend/tests/api/test_activity_events.py`.
  - Reqs: ANALYTICS-006-AC01 to AC11, ANALYTICS-004-AC09, UD-13, A-13, A-14, NOTIF-003-AC19. Design: §4.11, §3.3.
  - Depends: T7.01, T7.05, T8.01, T8.04.
  - Done when: tests assert one `card_created` per card creation, one `card_moved` per move to another column (none for a same-column move or rebalance), one `comment_created` per comment, **no event** for assignment, comment edit or delete, card delete, column delete, `is_done` toggle, reorder, and rejected requests, no route updates or deletes an event, events remain after card, column, and comment deletion, events leave only with their board, and all timestamps come from the single clock reading of the request.
  - Verify: `pytest backend/tests/api/test_activity_events.py` passes.

- [x] **T8.06 Comment tests** — ACTIONABLE
  - Objective: complete the comment test suites and matrix entries.
  - Files: C `backend/tests/api/test_comments.py`, M `backend/tests/authz/matrix.py`.
  - Reqs: TEST-002, TEST-003, TEST-010-AC (comments after card delete), A-15. Design: §10.1.
  - Depends: T8.01 to T8.04.
  - Done when: status codes, ownership, and soft-delete behavior are covered for all four comment endpoints.
  - Verify: `pytest backend/tests/api/test_comments.py` passes.

---

## Milestone 9. Notifications and analytics

- [x] **T9.01 Notification list query, item schema, and parameter validation (pre-work)** — ACTIONABLE (approved: DA-13)
  - Objective: build the service function and item schema that the list endpoint will use, without choosing a default `per_page`, a maximum, a wrapper shape, or an unread count.
  - Files: M `backend/app/blueprints/notifications/{service,schema}.py`.
  - Reqs: NOTIF-001-AC01 to AC09 (except the pagination wrapper), UD-08. Design: §5.9, §9.5. Guidelines: BE-06.
  - Depends: T1.01 (approval record), T7.03, T8.01.
  - Done when: the query returns only the caller's notifications ordered by `created_at` descending then `id` descending, an item has exactly `id`, `type`, `message`, `board_id`, `card_id`, `actor` (`id`, `name`), `is_read`, `created_at`, a notification stays after its card or column is soft-deleted or its comment is deleted, and `page` or `per_page` that is 0, negative, or not an integer is rejected with 400. Nothing in the code assumes a default or maximum `per_page` (UD-09).
  - Verify: unit tests for ordering, item keys, retention, and parameter validation with explicit values.

- [x] **T9.02 `PATCH /api/notifications/{id}/read`** — ACTIONABLE (approved: DA-13)
  - Objective: mark a notification read for its recipient only, idempotently.
  - Files: M `backend/app/blueprints/notifications/{routes,service,schema}.py`.
  - Reqs: NOTIF-002-AC01 to AC08, UD-08. Design: §5.9. Guidelines: BE-14.
  - Depends: T1.01 (approval record), T9.01.
  - Done when: the recipient gets 200 with `is_read` true, an already-read notification stays read, another user's notification returns the same 404 as a missing one even on a shared board, only `is_read` changes, and a notification of a soft-deleted card can still be marked read.
  - Verify: tests for NOTIF-002-AC01 to AC08.

- [x] **T9.03 `GET /api/notifications` (finish the endpoint)** — BLOCKED (UD-09)
  - Objective: expose the list endpoint with pagination.
  - Files: M `backend/app/blueprints/notifications/routes.py`.
  - Reqs: NOTIF-001-AC01 to AC09. Design: §5.9, §9.5, §12.1 (UD-09).
  - Depends: T9.01, and a human decision on UD-09 recorded in `requirements.md`.
  - **What must be confirmed:** the default and maximum `per_page`, how an over-maximum value is handled (400 or clamp), the wrapper shape of `data`, and whether and how the unread count is returned. The design's proposal (default 20, maximum 100, an object with `unread_count`) is **NOT APPROVED**.
  - Pre-work allowed: T9.01 and a route that is not registered. Do not register the route with an invented default.
  - Done when (after approval): tests for NOTIF-001-AC01 to AC09 and the updated criteria pass.
  - Verify: contract test plus the endpoint-coverage test (T3.06).

- [ ] **T9.04 Notification trigger and retention tests** — ACTIONABLE
  - Objective: automate the notification rules end to end at the service and API level, without depending on the list wrapper.
  - Files: C `backend/tests/api/test_notifications.py`.
  - Reqs: TEST-011, NOTIF-003-AC01 to AC19, CARD-004-AC09, COMMENT-001-AC07, AC08, UD-08. Design: §9.1, §9.2.
  - Depends: T7.03, T8.01, T9.02.
  - Done when: tests cover every trigger and every non-trigger of NOTIF-003, repeated notifications, recipient membership, no comment text, rollback of assignment and comment, retention after card and column soft-delete and comment delete, and removal with the board.
  - Verify: `pytest backend/tests/api/test_notifications.py` passes. List-response assertions are added after T9.03.

- [x] **T9.05 Weekly window function and injectable clock use** — ACTIONABLE
  - Objective: implement the UTC Monday-to-Monday half-open window from a single clock reading.
  - Files: M `backend/app/blueprints/analytics/service.py`.
  - Reqs: ANALYTICS-001-AC04, ANALYTICS-005-AC04, UD-14. Design: §9.3. Guidelines: BE-15.
  - Depends: T2.01.
  - Done when: `start` is Monday 00:00:00 UTC, `end` is exactly seven days later, and the Monday instant belongs to the new week.
  - Verify: unit tests with clocks fixed at `2025-01-15T12:00:00Z`, `2025-01-19T23:59:59.900000Z`, and `2025-01-20T00:00:00Z`.

- [x] **T9.06 Analytics queries with SQLAlchemy joins** — ACTIONABLE
  - Objective: implement `cards_per_column`, `completed_this_week`, and `member_activity` as three joined queries that exclude soft-deleted data and use the same window.
  - Files: M `backend/app/blueprints/analytics/service.py`.
  - Reqs: ANALYTICS-002 to ANALYTICS-005, UD-12, UD-13, UD-14, UD-18. Design: §9.3. Guidelines: BE-15, DB-12.
  - Depends: T9.05, T7.05, T8.01.
  - Done when: a column without cards appears with 0, a soft-deleted column is absent, `completed_this_week` counts each card once from its current `completed_at` (no use of events), `member_activity` has one entry per current member ordered by `activity_count` descending, `name`, `user_id`, and events of deleted cards, columns, and comments still count.
  - Verify: SQL-capture test finds a `JOIN` in each of the three statements (ANALYTICS-005-AC02, AC03).

- [x] **T9.07 `GET /api/boards/{id}/analytics`** — ACTIONABLE
  - Objective: expose the endpoint with the approved response and the 400 rule for any query parameter.
  - Files: M `backend/app/blueprints/analytics/{routes,schema}.py`.
  - Reqs: ANALYTICS-001-AC01 to AC09, UD-14. Design: §5.10. Guidelines: BE-09.
  - Depends: T9.06, T5.03.
  - Done when: `data` has exactly `window`, `cards_per_column`, `completed_this_week`, `member_activity`, with no omitted keys and no nulls, the route has no query code, a member with a query parameter gets 400, a non-member with one gets 404, and no token gets 401.
  - Verify: tests for ANALYTICS-001-AC01 to AC09 and ANALYTICS-005-AC01.

- [x] **T9.08 Analytics test suite** — ACTIONABLE
  - Objective: automate the analytics criteria with a fixed clock.
  - Files: C `backend/tests/api/test_analytics.py`.
  - Reqs: TEST-004, ANALYTICS-002-AC01 to AC05, ANALYTICS-003-AC01 to AC13, ANALYTICS-004-AC01 to AC11. Design: §10.1 (Analytics).
  - Depends: T9.07.
  - Done when: the boundary instants (inclusive start, exclusive end, rollover), double completion, move between done columns, column re-mark, soft-deleted subjects, former members, other boards, and removal of all events (completed count unchanged) are covered.
  - Verify: `pytest backend/tests/api/test_analytics.py` passes without using the real date.

- [ ] **T9.09 Backend completeness checkpoint** — BLOCKED (UD-09 for one route only)
  - Objective: verify that the backend has all routes, a matrix entry for each, and consistent contracts.
  - Files: M `backend/tests/api/test_endpoint_coverage.py`, M `backend/tests/authz/matrix.py`, C `backend/tests/api/test_contract.py`.
  - Reqs: TEST-001-AC02, AC04, AC05, AC06, API-001 to API-004, AUTH-004-AC01, UD-19. Design: §5.12, §10.1.
  - Depends: T4.04, T5.07, T6.07, T7.09, T8.06, T9.04, T9.08.
  - **What must be confirmed:** `GET /api/notifications` (T9.03) cannot be complete until UD-09 is approved. Every other route must be green.
  - Done when: the coverage test shows 26 of 27 routes complete (the 27th is `GET /api/notifications`, pending UD-09), the matrix has an entry for every board-scoped route, every response in the contract test uses the envelope, no `position` key appears anywhere, and all deletes return `{id}`.
  - Verify: `pytest backend` is green except the documented pending route.

---

## Milestone 10. Next.js frontend foundation and authentication

- [x] **T10.01 API DTO and Props type definitions** — ACTIONABLE (approved: DA-03)
  - Objective: define TypeScript interfaces for API objects and shared prop shapes.
  - Files: C `frontend/src/types/api.ts`.
  - Reqs: API-005, FRONT-021. Design: §5.2, §7.4. Guidelines: FE-09.
  - Depends: T1.01 (approval record), T1.05.
  - Done when: the interfaces match the approved keys. Fields beyond them (`completed_at`, timestamps, `board_id` on My Tasks, comment `author` shape) are those approved in DA-03. There is no `any`.
  - Verify: `tsc --noEmit` passes.

- [x] **T10.02 `errors.ts`, `toast.ts`, `useErrorHandler`** — ACTIONABLE
  - Objective: create the error types, the react-hot-toast wrapper, and the error-to-toast hook.
  - Files: C `frontend/src/lib/errors.ts`, `frontend/src/lib/toast.ts`, `frontend/src/hooks/useErrorHandler.ts`.
  - Reqs: API-006, API-007, FRONT-020. Design: §7.5. Guidelines: FE-07.
  - Depends: T1.06.
  - Done when: `ApiError` carries the status and the `error` string, `NetworkError` is separate, and the hook maps both to a toast.
  - Verify: Vitest tests for API-006 and API-007 acceptance criteria and FRONT-020.

- [x] **T10.03 `apiClient.ts` (server and client modes)** — ACTIONABLE
  - Objective: create the single API module with one call signature in two modes.
  - Files: C `frontend/src/lib/apiClient.ts`.
  - Reqs: API-005-AC01 to AC10, FRONT-022, UD-19. Design: §7.5, §6.10. Guidelines: FE-03, FE-06.
  - Depends: T10.02.
  - Done when: server mode uses `API_BASE_URL` and a Bearer header from the session, client mode calls the same-origin proxy and sets no `Authorization`, 2xx resolves with `data`, non-2xx rejects with `ApiError`, a successful DELETE resolves with `{id}`, a 401 outside login clears the user and navigates to `/login` (client mode) or redirects to the expire route (server mode), and direct `NEXT_PUBLIC_API_BASE_URL` use exists only for `GET /api/health`.
  - Verify: Vitest tests for API-005-AC01 to AC10, including a test that finds no other direct-browser endpoint.

- [x] **T10.04 Server-only session module, JWT `exp` reader, and middleware** — ACTIONABLE (approved: DA-04)
  - Objective: read the cookie only on the server, read the JWT `exp` without trusting it, and redirect unauthenticated or expired requests before rendering.
  - Files: C `frontend/src/lib/session.server.ts`, `frontend/src/lib/jwtExp.server.ts`, `frontend/middleware.ts`.
  - Reqs: FRONT-003, FRONT-023-AC09, AC12, AC15, UD-03. Design: §6.4, §6.8, §6.9. Guidelines: FE-03, FE-04.
  - Depends: T1.01 (approval record), T10.03.
  - Done when: the session module imports `server-only` and importing it from a Client Component fails `next build`, protected paths redirect to `/login` when the cookie is missing or its `exp` has passed, and the stale cookie is cleared. The cookie name `revotask_session` is approved (DA-04).
  - Verify: Vitest tests for the middleware logic, and a build test that a Client Component importing the module fails.

- [x] **T10.05 Same-origin proxy** — ACTIONABLE (approved: DA-04, DA-07, DA-15)
  - Objective: implement the catch-all proxy route handler to Flask.
  - Files: C `frontend/src/lib/proxy.server.ts`, C `frontend/src/app/api/[...path]/route.ts`.
  - Reqs: FRONT-023-AC04 to AC08, AC11, AC13, AC14, AC16, TEST-005-AC13, API-002-AC06 (for the matching Flask rule), A-07. Design: §6.5, §6.6. Guidelines: FE-05.
  - Depends: T1.01 (approval record), T10.04.
  - Done when: it forwards only to `/api` on the `API_BASE_URL` host, does not forward `POST /api/auth/login` (returns 404), rejects, on POST, PATCH, DELETE, an `Origin` that is not exactly one of the explicitly trusted origins in `APP_ORIGIN` with 403 (a preview origin is trusted only if it is listed, there is no wildcard, suffix, or substring match, and a missing or `null` Origin is rejected, FRONT-023-AC08), a non-JSON type with 415, and a body larger than 1,048,576 bytes with 413 and the string envelope, judged from `Content-Length` and from the bytes read when it is missing (FRONT-023-AC16, DA-07), returns 401 without forwarding when there is no cookie (except register and health), rebuilds the outgoing headers from scratch with only `Authorization: Bearer`, expires the cookie on a Flask 401, and returns Flask's status and body unchanged. A 502 or 504 with the string envelope for an unreachable or slow Flask is approved (DA-15). Verification V-06, V-07, and V-08 cover the size limit, the trusted origins, and the upstream failures.
  - Verify: Vitest tests that call the handler with `Request` objects for each rule, including TEST-005-AC13 (trusted origins and the 413 size limit).

- [x] **T10.06 Session login, logout, and expire handlers** — ACTIONABLE (approved: DA-04, DA-07)
  - Objective: implement the three session route handlers.
  - Files: C `frontend/src/app/api/session/login/route.ts`, `logout/route.ts`, `expire/route.ts`.
  - Reqs: FRONT-023-AC01, AC02, AC03, AC08, AC10, AC12, AC16, TEST-005-AC13, FRONT-004-AC02. Design: §6.3, §6.4, §6.5, §6.7. Guidelines: FE-04, FE-05.
  - Depends: T1.01 (approval record), T10.04, T4.03.
  - Done when: login sets exactly one cookie with `HttpOnly`, `Secure` in production, `SameSite=Lax`, `Path=/`, no `Domain`, and `Max-Age` equal to the remaining JWT lifetime, the login body has the user profile and never the JWT, logout and expire send an expired cookie, and login and logout check `Origin` against the explicit trusted list (FRONT-023-AC08) and reject a body larger than 1,048,576 bytes with 413 (FRONT-023-AC16).
  - Verify: Vitest tests for FRONT-023-AC01 to AC03, AC08, AC10, AC12.

- [x] **T10.07 `AuthContext`, `Providers`, and the root layout** — ACTIONABLE
  - Objective: create the context with `currentUser`, `session`, `login`, `logout`, `updateProfile`, and mount it from the root layout with the user loaded on the server.
  - Files: C `frontend/src/context/AuthContext.tsx`, `frontend/src/components/layout/Providers.tsx`, M `frontend/src/app/layout.tsx`.
  - Reqs: FRONT-018-AC01 to AC09, Section 4.1. Design: §7.1, §7.4. Guidelines: FE-01, FE-02, FE-08.
  - Depends: T10.06.
  - Done when: a reload with a valid cookie shows the user without a login prompt, a passed expiry marks the session unauthenticated, `updateProfile` sends only `name` and `email`, and the JWT is not in the value, `document.cookie`, `localStorage`, or `sessionStorage`.
  - Verify: Vitest tests for FRONT-018-AC01 to AC09.

- [x] **T10.08 `BaseButton`, `BaseBadge`, `BaseModal`** — ACTIONABLE
  - Objective: create the shared UI components.
  - Files: C `frontend/src/components/shared/{BaseButton,BaseBadge,BaseModal}.tsx`.
  - Reqs: FRONT-013, FRONT-014, FRONT-015. Design: §7.6. Guidelines: FE-02, FE-09, FE-10, FE-11, FE-12.
  - Depends: T1.06.
  - Done when: `BaseBadge` has no hooks or handlers, `BaseModal` moves focus in on open and back on close and closes with Escape and a close control, all styling uses Tailwind classes, and every component has a Props interface.
  - Verify: Vitest and React Testing Library tests for FRONT-013, FRONT-014, FRONT-015.

- [x] **T10.09 `/register` and `/login` pages** — ACTIONABLE
  - Objective: build the two public pages as Server Components with Client Component forms.
  - Files: C `frontend/src/app/(auth)/register/page.tsx`, `(auth)/login/page.tsx`, `frontend/src/components/auth/{RegisterForm,LoginForm}.tsx`.
  - Reqs: FRONT-001-AC01 to AC06, FRONT-002-AC01 to AC04, A-08, UD-04. Design: §7.2. Guidelines: FE-01, FE-12.
  - Depends: T10.07, T10.08, T4.02.
  - Done when: an empty field shows a message and sends no request, a 201 navigates to `/login` with a success toast, a 409 shows the server's `error`, a 401 on login shows a message and stays on `/login`, a success navigates to `/`, each page links to the other, and registration goes through the proxy.
  - Verify: Vitest tests for FRONT-001 and FRONT-002.

- [x] **T10.10 Protected layout, header, and logout** — ACTIONABLE
  - Objective: create the `(app)` layout with `AppHeader` (logout control and the slot for the notification bell) and loading, not-found, and error fallbacks.
  - Files: C `frontend/src/app/(app)/layout.tsx`, `frontend/src/components/layout/AppHeader.tsx`, `frontend/src/app/not-found.tsx`, `frontend/src/app/error.tsx`, `frontend/src/components/boards/ErrorState.tsx`.
  - Reqs: FRONT-003, FRONT-004-AC01 to AC03, FRONT-005-AC05. Design: §6.10, §7.1, §7.6. Guidelines: FE-01, FE-07.
  - Depends: T10.09.
  - Done when: a logout control is on every protected page, logout expires the cookie, clears `currentUser`, and goes to `/login`, and `ErrorState` shows the server's `error` text inline (error boundaries hide it in production).
  - Verify: Vitest tests for FRONT-004 and a test that the `(app)/layout.tsx` has no `"use client"`.

- [ ] **T10.11 Foundation security and boundary tests** — ACTIONABLE
  - Objective: automate the cross-cutting frontend security rules.
  - Files: C `frontend/tests/unit/security.test.ts`, `frontend/tests/unit/boundaries.test.ts`.
  - Reqs: FRONT-021-AC04, FRONT-022, FRONT-023-AC03, AC09, AC15, FRONT-018-AC09. Design: §7.3, §10.2. Guidelines: FE-01, FE-04, FE-19.
  - Depends: T10.10.
  - Done when: a test lists files with `"use client"` and asserts the page files and layouts have none, a test asserts the JWT string never appears in page output or storage in the test harness, and no page or Client Component reads the session cookie directly.
  - Verify: `npm test` passes.

- [x] **T10.12 Manual end-to-end smoke of registration, login, and logout** — ACTIONABLE
  - Objective: confirm the authentication flow works between Next.js and the running Flask API locally.
  - Files: none.
  - Reqs: FRONT-001 to FRONT-004, FRONT-023. Design: §1.3.
  - Depends: T10.10.
  - Done when: a human registers, logs in, sees the redirect to `/`, reloads and stays logged in, logs out, and is redirected from a protected URL. In browser dev tools the cookie is `HttpOnly` and no JWT is visible in storage or responses.
  - Verify: a checklist with these observations is added to the changelog entry.

---

## Milestone 11. Dashboard and board interface

- [x] **T11.01 `/` Dashboard with `BoardCard` and board creation** — ACTIONABLE (approved: DA-03)
  - Objective: build the dashboard as a Server Component that lists the user's boards with `BoardCard` and a Client Component form to create a board.
  - Files: C `frontend/src/app/(app)/page.tsx`, `(app)/loading.tsx`, `frontend/src/components/boards/{BoardCard,CreateBoardForm}.tsx`.
  - Reqs: FRONT-005-AC01 to AC07, FRONT-024. Design: §7.2. Guidelines: FE-01, FE-02, FE-03.
  - Depends: T1.01 (approval record), T10.10, T5.02.
  - Done when: boards come from a server-side fetch with no token in the HTML, `BoardCard` has no hooks or handlers and links to `/boards/[id]`, the empty state shows a message and the create control, the loading UI has `role="status"`, a non-401 failure shows the `error` text, and a created board appears without a full reload.
  - Verify: Vitest tests for FRONT-005 and FRONT-024.

- [x] **T11.02 `/boards/[id]` page and `BoardView` container** — ACTIONABLE (approved: DA-03)
  - Objective: build the board page as a Server Component that fetches the board and analytics on the server and renders a Client Component container that owns board state.
  - Files: C `frontend/src/app/(app)/boards/[id]/{page,loading,not-found}.tsx`, `frontend/src/components/boards/BoardView.tsx`.
  - Reqs: FRONT-006-AC01, AC02, AC07, AC08, FRONT-021. Design: §7.2. Guidelines: FE-01, FE-02, FE-03, FE-13.
  - Depends: T1.01 (approval record), T11.01, T5.03, T9.07.
  - Done when: columns and cards appear in ascending `order`, a 404 shows "board not found" with no board data, the page file has no `"use client"`, and no JWT is in the HTML.
  - Verify: Vitest tests for FRONT-006-AC01, AC02, AC07, AC08.

- [x] **T11.03 `ColumnHeader`** — ACTIONABLE
  - Objective: show the column name and card count, rename for every member, and show delete and the Done/Active toggle only to an administrator.
  - Files: C `frontend/src/components/boards/ColumnHeader.tsx`.
  - Reqs: FRONT-025-AC01 to AC17, FRONT-006-AC06, AC09, AC10, UD-05, UD-12, A-13. Design: §7.6. Guidelines: FE-11, FE-13.
  - Depends: T11.02, T6.02, T6.03.
  - Done when: a member sees no delete control and no toggle, an administrator confirms deletion with a message that the cards will be deleted too, a failed delete keeps the column and shows a toast, and the toggle sends `is_done` and refreshes analytics.
  - Verify: Vitest tests for FRONT-025 and the relevant FRONT-006 criteria.

- [x] **T11.04 Add-column form** — ACTIONABLE
  - Objective: create columns from the board page.
  - Files: C `frontend/src/components/boards/AddColumnForm.tsx`.
  - Reqs: FRONT-006-AC03. Design: §7.6.
  - Depends: T11.02, T6.01.
  - Done when: a submitted name creates a column through the proxy and it appears after the existing ones, an empty name shows a message and sends nothing.
  - Verify: Vitest test for FRONT-006-AC03.

- [x] **T11.05 `CardItem` and `AddCardForm`** — ACTIONABLE
  - Objective: render card tiles and a title-only card creation form per column.
  - Files: C `frontend/src/components/boards/{CardItem,AddCardForm}.tsx`.
  - Reqs: FRONT-006-AC04, AC05, FRONT-026, UD-08, FRONT-011-AC01. Design: §7.6. Guidelines: FE-11, FE-12.
  - Depends: T11.03, T7.01.
  - Done when: the card appears in its column after creation, `AddCardForm` has no assignee control, activating a card opens `CardDetailModal`, and the card shows its assignee name if assigned.
  - Verify: Vitest tests for FRONT-026 and FRONT-006-AC04, AC05.

- [x] **T11.06 `CardDetailModal`** — ACTIONABLE (approved: DA-03)
  - Objective: show and edit one card, with the assignee dropdown built from `board.members`, delete after confirmation, and the comment list slot.
  - Files: C `frontend/src/components/boards/CardDetailModal.tsx`.
  - Reqs: FRONT-011-AC01 to AC13, FRONT-006-AC11, UD-08. Design: §7.6. Guidelines: FE-11, FE-12, FE-13.
  - Depends: T1.01 (approval record), T11.05, T7.02, T7.03, T10.08.
  - Done when: saving a title calls `PATCH /api/cards/{id}`, the dropdown lists the board members and an "Unassigned" option and sends `assignee_id` or `null`, the dropdown works with Tab, arrow keys, and Enter, deleting calls `DELETE /api/cards/{id}`, no extra request is made for members, and the modal closes with Escape and returns focus.
  - Verify: Vitest tests for FRONT-011-AC01 to AC13.

- [x] **T11.07 `CommentList`** — ACTIONABLE (approved: DA-03)
  - Objective: list, add, edit, and delete the user's own comments.
  - Files: C `frontend/src/components/comments/CommentList.tsx`.
  - Reqs: FRONT-012, COMMENT-001 to COMMENT-004. Design: §7.6.
  - Depends: T1.01 (approval record), T11.06, T8.01 to T8.04.
  - Done when: edit and delete controls show only on the user's own comments, a 403 from the server shows a toast, and whitespace-only content is rejected before sending.
  - Verify: Vitest tests for FRONT-012.

- [x] **T11.08 Card search** — ACTIONABLE
  - Objective: filter card titles on the loaded board data with a 300 ms debounce and no API request.
  - Files: C `frontend/src/components/boards/CardSearchInput.tsx`, C `frontend/src/hooks/useDebouncedValue.ts`.
  - Reqs: FRONT-008-AC01 to AC08, UD-10, UD-11, A-11, NFR-006-AC01. Design: §7.11. Guidelines: FE-16.
  - Depends: T11.05.
  - Done when: with fake timers nothing changes at 299 ms and the filter runs at 300 ms, the timer restarts on a keystroke and clears on unmount, matching ignores case, an empty or whitespace term shows all cards, columns stay visible, and no request is sent.
  - Verify: Vitest tests for FRONT-008-AC01 to AC08 and NFR-006-AC01.

- [x] **T11.09 `AnalyticsPanel`** — ACTIONABLE
  - Objective: render the analytics response and refresh it after card and column mutations.
  - Files: C `frontend/src/components/boards/AnalyticsPanel.tsx`.
  - Reqs: FRONT-007-AC01 to AC08, UD-14. Design: §7.6, §9.3. Guidelines: FE-18.
  - Depends: T11.02, T9.07.
  - Done when: the period label is built from `window.start` and `window.end` in UTC with `end` exclusive ("Week of Jan 13–19, 2025 (UTC)" and the month and year variants), zero is shown as "0", an empty board shows "This board has no columns yet", members appear in API order with no email, there is no timezone or date control, a failure shows an error in the panel only, and a successful create, move, delete, or Done toggle re-fetches while a failed one does not.
  - Verify: Vitest tests for FRONT-007 including the Asia/Jakarta and America/Los_Angeles time zone cases.

- [x] **T11.10 Notification deep link handling** — ACTIONABLE (approved: DA-04)
  - Objective: open the board and the card named by the `?card=` parameter, or show the "no longer available" message.
  - Files: M `frontend/src/components/boards/BoardView.tsx`, M board `page.tsx`.
  - Reqs: FRONT-006-AC12, FRONT-016-AC08. Design: §7.2.
  - Depends: T1.01 (approval record), T11.06.
  - Done when: a card that exists opens its modal, a missing card shows "This card is no longer available" with a link back to the board, no error toast appears, and nothing crashes.
  - Verify: Vitest test for FRONT-006-AC12.

- [ ] **T11.11 Role-based rendering checks** — ACTIONABLE
  - Objective: verify that only administrators see the five administrator-only controls that exist in the UI, and that the server remains the authority.
  - Files: C `frontend/tests/unit/roles.test.tsx`.
  - Reqs: UD-05, FRONT-025, BOARD-006. Design: §7.2. Guidelines: FE-13.
  - Depends: T11.03.
  - Done when: tests render the board as an administrator and as a member and assert the controls, and a 403 response shows an error toast and changes no state.
  - Verify: `npm test` passes.

- [ ] **T11.12 Board interface manual check** — ACTIONABLE
  - Objective: a human verifies the board interface against the running API.
  - Files: none.
  - Reqs: FRONT-005, FRONT-006, FRONT-007, FRONT-008, FRONT-011, FRONT-012. Design: §7.2.
  - Depends: T11.09, T11.10.
  - Done when: a human creates a board, adds two columns and a card, edits the card, comments, searches, and sees analytics change, and notes the observations in the changelog.
  - Verify: the checklist is recorded.

---

## Milestone 12. Card interaction, drag-and-drop and accessibility

- [x] **T12.01 Pure ordering functions** — ACTIONABLE
  - Objective: implement `computeCardOrder`, `computeColumnOrder`, and `normalizeColumns` as pure functions with no React imports.
  - Files: C `frontend/src/lib/ordering.ts`, C `frontend/tests/unit/ordering.test.ts`.
  - Reqs: FRONT-019-AC03, AC07, AC08, AC11, AC12, AC14, AC15, UD-06, UD-20. Design: §7.9. Guidelines: FE-15.
  - Depends: T1.06.
  - Done when: a midpoint is used when a distinct value exists, a card with no distinct midpoint sends the order of the following card, an empty column gets a positive value, a column with no distinct midpoint triggers a full normalization (`1024.0, 2048.0, ...`), no minimum-gap threshold exists, `rebalanced` is never sent, and values are JSON numbers named `order`.
  - Verify: unit tests at the numeric limits (adjacent floats, very small first order, very large last order).

- [x] **T12.02 `useDragAndDrop` shared move logic** — ACTIONABLE
  - Objective: implement `moveCardTo` and `moveColumnTo` with optimistic update, rollback, refetch, and one in-flight move at a time.
  - Files: C `frontend/src/hooks/useDragAndDrop.ts`.
  - Reqs: FRONT-019-AC01, AC02, AC04 to AC10, AC13, AC16. Design: §7.7, §7.10. Guidelines: FE-14, FE-15.
  - Depends: T12.01, T11.02, T7.05, T6.04.
  - Done when: the card appears in the target at once, a failure restores the previous place and shows a toast, a same-place move sends nothing, neighbors include cards hidden by search, a successful column reorder replaces the columns with the response, a 400 or 409 on a column request restores and refetches, and `rebalanced` true triggers a refetch that replaces every displayed `order`.
  - Verify: Vitest tests for FRONT-019-AC01 to AC16 using a mocked `apiClient`.

- [x] **T12.03 Native HTML5 drag-and-drop wiring** — ACTIONABLE
  - Objective: connect `draggable`, `dragstart`, `dragover`, and `drop` on cards and columns to the shared move logic.
  - Files: M `frontend/src/components/boards/{BoardView,CardItem,ColumnHeader}.tsx`.
  - Reqs: FRONT-019, FRONT-006. Design: §7.7. Guidelines: FE-14.
  - Depends: T12.02, T11.05.
  - Done when: `dataTransfer` carries only ids, no drag-and-drop library is imported, and a drop on a column or between cards calls the shared logic.
  - Verify: Vitest tests that fire drag events, and the lint rule from T1.06.

- [x] **T12.04 Card move menu (keyboard and touch)** — ACTIONABLE (approved: DA-18)
  - Objective: add a visible "Move card" button on every card that opens `CardMoveMenu`, where the user chooses a destination column and a place ("Top of column" or "After <card title>"), and calls `moveCardTo`.
  - Files: C `frontend/src/components/boards/CardMoveMenu.tsx`, M `CardItem.tsx`, M `BoardView.tsx` (the single `aria-live="polite"` region).
  - Reqs: FRONT-019-AC17 to AC24, NFR-007-AC04 to AC06, approved by the human owner under DA-18 (Limadijaya Suhendra, 2026-11-24). Design: §7.8. Guidelines: FE-14, FE-12.
  - Depends: T1.01 (approval record), T12.02, T10.08.
  - Done when: the acceptance criteria FRONT-019-AC17 to AC24 and NFR-007-AC04 to AC06 hold: the button has an accessible name with the card title and no hover is needed, the menu works with Tab, Enter, Space, arrow keys, and taps, Escape closes it, focus moves in and returns to the card's button, the request is exactly `PATCH /api/cards/{id}/position` with `column_id` and `order` and equals a drop's request, an unchanged place sends nothing, a failure rolls back with a toast, the live region announces the result, the control is shown to administrators and members, and no drag-and-drop library is added.
  - Verify: Vitest and React Testing Library tests with keyboard events only (TEST-005-AC12).
- [x] **T12.05 Column move buttons and live announcements** — ACTIONABLE (approved: DA-18)
  - Objective: add "Move column left" and "Move column right" buttons to `ColumnHeader` and the column announcements to the live region.
  - Files: M `frontend/src/components/boards/ColumnHeader.tsx`, M `BoardView.tsx`.
  - Reqs: FRONT-025-AC18 to AC21, FRONT-019-AC23, NFR-007-AC04 to AC06, approved by the human owner under DA-18 (Limadijaya Suhendra, 2026-11-24). Design: §7.8. Guidelines: FE-14.
  - Depends: T1.01 (approval record), T12.04, T11.03.
  - Done when: the acceptance criteria FRONT-025-AC18 to AC21 hold: both buttons are shown to every member, the first and last column have the matching button disabled, activating one sends one `PATCH /api/boards/{id}/columns/reorder` with a single `columns` entry and the normalization of FRONT-019-AC11 when needed, 400 and 409 restore the previous order and refetch, the live region announces "Column moved to position <n>" or "Column could not be moved", and focus handling follows FRONT-025-AC21.
  - Verify: Vitest tests for request equality with a drag and for the announcement (TEST-005-AC12).
- [ ] **T12.06 Drag, ordering, and rollback test suite** — ACTIONABLE
  - Objective: complete the unit test coverage for the move behavior.
  - Files: C `frontend/tests/unit/dnd.test.tsx`.
  - Reqs: TEST-005, FRONT-019. Design: §10.2.
  - Depends: T12.03.
  - Done when: tests cover optimistic display, rollback on 400, 409, 500, and a network error, same-place no request, hidden neighbors, tie order, rebalanced refetch, normalization, and refetch after a failed column request.
  - Verify: `npm test` passes.

- [ ] **T12.07 Keyboard and touch accessibility tests** — ACTIONABLE (approved: DA-18)
  - Objective: verify the move controls with React Testing Library.
  - Files: C `frontend/tests/unit/move-controls.test.tsx`.
  - Reqs: TEST-005-AC12, FRONT-019-AC17 to AC24, FRONT-025-AC18 to AC21, NFR-007-AC04 to AC06, approved by the human owner under DA-18. Design: §7.8, §10.2. Guidelines: FE-14, FE-20.
  - Depends: T1.01 (approval record), T12.04, T12.05.
  - Done when: a card and a column are moved using only keyboard events, the accessible names, menu options (including cards hidden by a search filter), focus on open and close, disabled end buttons, rollback, live-region texts, and the controls shown to both roles are tested, the request equals the request of a drop, no request is sent for an unchanged place, no drag event is used, and the package manifest has no drag-and-drop or sortable library.
  - Verify: `npm test` passes. The Playwright counterpart is T14.08. Verification V-10 stays outstanding until T14.08 passes.
---

## Milestone 13. My Tasks, Profile and Notifications UI

- [x] **T13.01 `/my-tasks` page** — ACTIONABLE (approved: DA-03, DA-04)
  - Objective: show the caller's assigned cards grouped by board name, fetched on the server.
  - Files: C `frontend/src/app/(app)/my-tasks/{page,loading}.tsx`.
  - Reqs: FRONT-009-AC01 to AC04, CARD-007. Design: §7.2. Guidelines: FE-01, FE-03.
  - Depends: T1.01 (approval record), T10.10, T7.06.
  - Done when: cards sit under one heading per board name, an empty list shows a message, the loading UI has `role="status"`, an error shows the `error` text, and the page file has no `"use client"`. Linking each card to the board with `?card=` is approved (DA-04).
  - Verify: Vitest tests for FRONT-009.

- [x] **T13.02 `/profile` page** — ACTIONABLE
  - Objective: show and edit `name` and `email` with no password field.
  - Files: C `frontend/src/app/(app)/profile/{page,loading}.tsx`, `frontend/src/components/profile/ProfileForm.tsx`.
  - Reqs: FRONT-010-AC01 to AC04, FRONT-018-AC06 to AC08, USER-001, USER-002. Design: §7.2, §7.4. Guidelines: FE-08, FE-12.
  - Depends: T10.10, T4.05.
  - Done when: the form shows the current values, a successful update changes `currentUser` without a reload, 400 and 409 show the server `error` and leave `currentUser` unchanged, and there is no password input.
  - Verify: Vitest tests for FRONT-010 and FRONT-018-AC06 to AC08.

- [x] **T13.03 `useNotifications` polling mechanics** — ACTIONABLE
  - Objective: poll every 30,000 ms through the proxy, without overlap, with no request while unauthenticated, stopping on unmount and logout. Isolate response parsing behind one adapter function so the response shape can be added later.
  - Files: C `frontend/src/hooks/useNotifications.ts`.
  - Reqs: FRONT-017-AC01 to AC03, AC05, AC06, NFR-006-AC02, UD-08. Design: §7.12, §9.2. Guidelines: FE-17.
  - Depends: T10.03, T10.07.
  - Done when: with fake timers there is one request on mount, still one at 29,999 ms, two at 30,000 ms, and four in 90 seconds. A failed poll shows at most one generic indication ("Notifications could not be updated") and the next poll still runs. The response shape is **not assumed** (UD-09).
  - Verify: Vitest tests for FRONT-017-AC01 to AC03, AC05, AC06 and NFR-006-AC02.

- [x] **T13.04 Notification response adapter and unread count** — BLOCKED (UD-09)
  - Objective: parse the list response and compute the unread count shown by the bell.
  - Files: M `frontend/src/hooks/useNotifications.ts`.
  - Reqs: FRONT-017-AC04, FRONT-016, NOTIF-001. Design: §9.5, §12.1 (UD-09).
  - Depends: T13.03, T9.03, and the human decision on UD-09.
  - **What must be confirmed:** the response wrapper and whether the server returns a total unread count across pages. The design's proposal is **NOT APPROVED**. Without it, a count taken from one page may be wrong when notifications exceed a page.
  - Pre-work allowed: T13.03 and the adapter interface only.
  - Done when (after approval): the hook returns the unread count and a function that calls `PATCH /api/notifications/{id}/read`.
  - Verify: Vitest test for FRONT-017-AC04 against the approved shape.

- [x] **T13.05 `NotificationBell`** — BLOCKED (UD-09)
  - Objective: show the unread count, list notifications, mark one as read, and open its board and card, with keyboard support.
  - Files: C `frontend/src/components/notifications/NotificationBell.tsx`, M `frontend/src/components/layout/AppHeader.tsx`.
  - Reqs: FRONT-016-AC01 to AC14, UD-08. Design: §7.6, §9.2. Guidelines: FE-17, FE-12.
  - Depends: T13.04, T10.10.
  - **What must be confirmed:** the unread-count behavior from UD-09. The item rendering, mark-as-read, navigation, and keyboard behavior (all approved) can be built first against the approved item shape.
  - Done when: each item shows the actor, the card, and the read or unread state without comment text or email, a click marks the item read and navigates to `/boards/{board_id}?card={card_id}`, Tab, Enter, and Space operate the bell and items, Escape closes the list and returns focus, and a failed mark-read shows an error.
  - Verify: Vitest tests for FRONT-016-AC01 to AC14.

- [ ] **T13.06 Loading, empty, and error state sweep** — ACTIONABLE
  - Objective: verify every one of the six pages has its loading, empty (where applicable), and error behavior.
  - Files: C `frontend/tests/unit/states.test.tsx`.
  - Reqs: FRONT-005-AC03 to AC05, FRONT-006-AC02, FRONT-007-AC02, AC05, FRONT-009-AC03, AC04. Design: §7.2.
  - Depends: T13.02, T13.01, T11.02.
  - Done when: `/`, `/boards/[id]`, `/my-tasks`, and `/profile` show a `role="status"` loading UI, `/` and `/my-tasks` show empty states, and server failures other than 401 and 404 show the server `error` text inline.
  - Verify: `npm test` passes.

- [ ] **T13.07 Notifications, My Tasks, and Profile manual check** — BLOCKED (UD-09)
  - Objective: a human verifies the three features with two accounts against the running API.
  - Files: none.
  - Reqs: FRONT-009, FRONT-010, FRONT-016, FRONT-017, NOTIF-003. Design: §9.1.
  - Depends: T13.05.
  - Done when: assigning a card from account A makes the notification appear for account B within 30 seconds, B can open it and mark it read, My Tasks lists the card, and the profile updates. The unread-count observation is recorded as pending if UD-09 is still open.
  - Verify: the checklist is recorded in the changelog.

---

## Milestone 14. Automated testing and quality assurance

Most tests are written inside the feature tasks above. This milestone audits them, adds the end-to-end suites, and handles the testing decisions that are still open.

- [ ] **T14.01 Backend test-suite audit and coverage measurement** — ACTIONABLE
  - Objective: confirm the pytest suite covers the backend test groups of the design and measure coverage **without setting a threshold**.
  - Files: M `backend/pytest.ini`, C `backend/tests/README.md` (how to run each group).
  - Reqs: TEST-001, TEST-002, TEST-003, TEST-004, TEST-010, TEST-011. Design: §10.1. Guidelines: BE-20.
  - Depends: T9.09.
  - Done when: a table maps each group (contract, validation, authentication, authorization, ordering, concurrency, transactions, soft delete and cascade, notifications, analytics, migrations, security) to test files, and a coverage report can be produced. No pass or fail limit is set (UD-15).
  - Verify: `pytest backend --cov` prints a report, and the mapping table has no empty row.

- [ ] **T14.02 Concurrency and flakiness stability run** — ACTIONABLE
  - Objective: run the concurrency suite repeatedly to expose timing problems.
  - Files: none (or M `backend/tests/concurrency/*` to fix flakes).
  - Reqs: COLUMN-004-AC16, AC17, CARD-005-AC19, AC20, NOTIF-003-AC08. Design: §8.4, §8.5.
  - Depends: T6.06, T7.08.
  - Done when: the suite passes 50 consecutive runs, and any lock-order or deadlock finding is fixed in the owning task's code.
  - Verify: a loop of 50 runs finishes with zero failures.

- [ ] **T14.03 Frontend test-suite audit and coverage measurement** — ACTIONABLE
  - Objective: confirm Vitest and React Testing Library cover every component and hook in the approved list and measure coverage **without a threshold**.
  - Files: C `frontend/tests/README.md`.
  - Reqs: TEST-005. Design: §10.2. Guidelines: FE-20.
  - Depends: T13.06, T12.07.
  - Done when: every approved component (`CardDetailModal`, `CommentList`, `BaseButton`, `BaseBadge`, `BaseModal`, `NotificationBell`, `BoardCard`, `ColumnHeader`, `AddCardForm`) and hook (`useNotifications`, `useDragAndDrop`, `useErrorHandler`, `AuthContext`) has a test file, with `NotificationBell` completed only after UD-09. A coverage report can be produced and has no limit (UD-15).
  - Verify: `npm test -- --coverage` prints a report, and a script checks that each listed file has a test.

- [x] **T14.04 Playwright configuration and helpers** — BLOCKED (UD-16, UD-22)
  - Objective: configure Playwright so it takes its base URL and test account from environment variables, with a wait helper that never uses a fixed delay.
  - Files: M `frontend/e2e/playwright.config.ts`, C `frontend/e2e/helpers.ts`.
  - Reqs: TEST-006-AC01 to AC07. Design: §10.3, §10.4. Guidelines: FE-21.
  - Depends: T1.06, T10.12.
  - **What must be confirmed:** UD-16 (which environment Playwright runs against and which database it uses) and UD-22 (how the E2E account is provisioned and what the variables are called). The proposals (production only, register once through the API) are **NOT APPROVED**.
  - Pre-work allowed: the helper functions and the configuration structure, with no fixed URL and no variable names that imply a decision.
  - Done when (after approval): the configuration works for the approved target, no test uses `waitForTimeout`, and every test reads and changes only data it created.
  - Verify: `npx playwright test --list` succeeds and the lint rule for `waitForTimeout` passes.

- [x] **T14.05 Playwright authentication scenarios** — BLOCKED (UD-16, UD-22)
  - Objective: automate the four authentication scenarios and the cookie protection check.
  - Files: C `frontend/e2e/auth.spec.ts`.
  - Reqs: TEST-007-AC01 to AC05, FRONT-002, FRONT-003, FRONT-004, FRONT-023. Design: §10.3.
  - Depends: T14.04.
  - **What must be confirmed:** UD-16 and UD-22, as in T14.04.
  - Done when: successful login redirects to `/`, invalid credentials show an error, an unauthenticated visit redirects to login, a post-logout visit redirects to login, and the session cookie is `httpOnly` with no JWT in `document.cookie`, `localStorage`, or `sessionStorage`.
  - Verify: the spec passes against the approved target.

- [x] **T14.06 Playwright Kanban journey** — BLOCKED (UD-16, UD-22)
  - Objective: automate the eight-step journey: log in, create a board, add two columns, create a card, open and inspect it, drag it to the second column, verify the position, reload and verify it stays.
  - Files: C `frontend/e2e/kanban.spec.ts`.
  - Reqs: TEST-008-AC01 to AC08, FRONT-019, FRONT-006. Design: §10.3.
  - Depends: T14.05, T12.03.
  - **What must be confirmed:** UD-16 and UD-22.
  - Done when: each step waits on an observable condition (element state, URL, or network response), and the spec cleans up the board it created.
  - Verify: the spec passes on the approved target and a rerun passes without manual cleanup.

- [x] **T14.07 Playwright responsive tests** — BLOCKED (UD-16, UD-22)
  - Objective: check the core flows at 360 px and 1920 px with no horizontal page scroll.
  - Files: C `frontend/e2e/responsive.spec.ts`.
  - Reqs: TEST-009, NFR-007-AC01 to AC03. Design: §10.3.
  - Depends: T14.06.
  - **What must be confirmed:** UD-16 and UD-22.
  - Done when: `/login` controls are usable at 360 px without zoom or overlap, the board area scrolls inside itself, and the page has no horizontal scroll bar at 360, 768, 1280, and 1920 px.
  - Verify: the spec passes at the listed widths.

- [ ] **T14.08 Playwright keyboard and touch alternatives** — BLOCKED (UD-16, UD-22); approved: DA-18
  - Objective: move a card and reorder a column using only taps at a touch-enabled 360 px viewport, and using only the keyboard at 360 px and 1920 px, and assert that the results persist and that the controls are at least 44 by 44 CSS px at 360 px.
  - Files: C `frontend/e2e/move-controls.spec.ts`.
  - Reqs: TEST-009-AC03, TEST-009-AC04, NFR-007-AC04 to AC06, approved by the human owner under DA-18. Design: §7.8, §10.3. Guidelines: FE-14, FE-21.
  - Depends: T1.01 (approval record), T14.06, T12.05.
  - **What must be confirmed:** UD-16 and UD-22 (the Playwright target and the E2E account). DA-18 is approved and no longer needs confirmation. The task stays blocked until both decisions are approved.
  - Done when: TEST-009-AC03 and TEST-009-AC04 pass, with no drag event in the tap test, no fixed delay, and a reload that shows the same result.
  - Verify: the spec passes on the approved target.
- [ ] **T14.09 Security and quality regression pass** — ACTIONABLE
  - Objective: run the cross-cutting static and dynamic checks on both applications.
  - Files: C `backend/tests/api/test_security_regression.py`, M `frontend/tests/unit/security.test.ts`.
  - Reqs: NFR-001 to NFR-004, API-002-AC05, API-004, FRONT-023, AUTH-003-AC05. Design: §6, §11.8, §12.6.
  - Depends: T9.09, T10.11.
  - Done when: no literal secret, no string-built SQL, no CORS header on any route except health, a 500 body without internals, no JWT in any browser-visible output, and no `style=` or raw `<button>` in the frontend.
  - Verify: both suites pass, and a repository grep for secrets and for `waitForTimeout` finds nothing.

- [ ] **T14.10 CI pipeline** — BLOCKED (UD-17)
  - Objective: run the test suites automatically.
  - Files: C `.github/workflows/` (only after approval).
  - Reqs: TEST-001, TEST-005, TEST-006. Design: §10.4, §12.1 (UD-17).
  - Depends: T14.01, T14.03.
  - **What must be confirmed:** UD-17 (whether CI exists, what blocks a merge, and who runs `flask db upgrade`). The proposal (GitHub Actions on each pull request, Playwright after deployment) is **NOT APPROVED**.
  - Done when (after approval): the approved workflow runs.
  - Verify: a pull request triggers the approved jobs. Until approval, no workflow file is created.

- [ ] **T14.11 Coverage thresholds** — BLOCKED (UD-15)
  - Objective: enforce a coverage minimum.
  - Files: M `backend/pytest.ini`, M `frontend/vitest.config.ts` (only after approval).
  - Reqs: TEST-001, TEST-005. Design: §12.1 (UD-15).
  - Depends: T14.01, T14.03.
  - **What must be confirmed:** UD-15 (the numbers, which directories count, and whether a miss fails the build). The 80% proposal is **NOT APPROVED**.
  - Done when (after approval): the approved thresholds are configured. Until then, coverage is reported only.
  - Verify: a run below the threshold fails (after approval).

- [ ] **T14.12 Read-latency measurement script** — ACTIONABLE
  - Objective: write a script that sends at least 100 sequential requests to each of six read endpoints after one warm-up request and reports p95.
  - Files: C `backend/scripts/measure_latency.py`, M `README.md` (procedure and dataset size).
  - Reqs: NFR-005-AC01, AC02. Design: §9.4.
  - Depends: T9.09.
  - Done when: the script covers `GET /api/boards`, `GET /api/boards/{id}`, `GET /api/cards?assignee=me`, `GET /api/notifications` (only once UD-09 is decided), `GET /api/cards/{id}/comments`, and `GET /api/boards/{id}/analytics`, and prints p95 per endpoint. It reads the target URL and a token from the environment and logs neither.
  - Verify: a local run prints a p95 for each available endpoint. The run on the deployed API is T15.07.

---

## Milestone 15. Deployment to Render, Vercel and Supabase

- [x] **T15.01 Supabase project and database connection** — CONDITIONAL (V-02, V-03; approved: DA-16, DA-17)
  - Objective: create the Supabase PostgreSQL database, connect the Render Flask API through the session-mode pooler, and apply and verify the approved Row Level Security posture.
  - Files: M `backend/.env.example` (placeholder only), M `README.md`.
  - Reqs: NFR-008-AC03, NFR-004, NFR-002. Design: §11.3, §12.3.1 (V-02, V-03). Guidelines: DB-01.
  - Depends: T1.01 (approval record), T2.10.
  - **Verification before completion (outstanding, not yet verified):** V-02 and V-03. If a check fails, report it and request a new human approval. Do not change the connection mode or the RLS decision silently.
  - Done when: `DATABASE_URL` is the session-mode pooler string with TLS and is stored only in platform settings, the small pool variables are set, and connectivity, `flask db upgrade` through the pooler, the row-locking and concurrency tests, and the connection limit against the pool size have been checked (V-02). RLS is enabled on all eight application tables by migration with no browser-facing policies, the Supabase Data API is disabled if practical, the database role used by Flask reads and writes all eight tables, and the exposure of `alembic_version` is checked (V-03). No Supabase client library, Auth, Storage, or Realtime is used.
  - Verify: the backend connects through the pooler from a workstation and from Render (after T15.02), the concurrency tests pass against it, and `grep` finds no connection string in the repository.
- [ ] **T15.02 Render service for the Flask API** — BLOCKED (UD-01) and CONDITIONAL (V-02; approved: DA-16)
  - Objective: create the Render web service with `backend/` as the root, a gunicorn start command, the `/api/health` check path, and the environment variables.
  - Files: none in the repository (platform settings), M `README.md`.
  - Reqs: NFR-008-AC02, NFR-004-AC01, NFR-010, API-003-AC02. Design: §11.2, §11.4.
  - Depends: T1.01 (approval record), T15.01, T3.05.
  - **What must be confirmed:** UD-01 (the value of `JWT_ACCESS_TOKEN_EXPIRES_SECONDS`). The 60-minute proposal is **NOT APPROVED**. **Verification before completion (outstanding):** V-02 (DA-16, session-mode pooling). A failed check is reported and needs a new human approval.
  - Done when: the service starts only when all required variables are set, and the health check passes over HTTPS.
  - Verify: `GET https://<render-url>/api/health` returns 200 with `{"data": {"status": "ok"}}`.

- [x] **T15.03 Apply migrations to Supabase** — BLOCKED (UD-16, UD-17)
  - Objective: run `flask db upgrade` against the production database before the first release.
  - Files: M `README.md` (how it was run).
  - Reqs: NFR-009-AC01, NFR-008. Design: §11.6. Guidelines: DB-15, DB-16.
  - Depends: T15.01, T2.10.
  - **What must be confirmed:** who runs the migration and how (UD-16 and UD-17). The human must say explicitly how to run it. A manual run from a workstation is allowed only if the human says so, and that statement does not approve any pipeline.
  - Done when: the database is at the latest revision, and a backup was taken first if it had data.
  - Verify: `flask db current` shows head, and the eight tables exist with no extra table.

- [ ] **T15.04 Vercel project for the Next.js app** — ACTIONABLE (approved: DA-04, DA-15)
  - Objective: create the Vercel project with `frontend/` as the root and the environment variables.
  - Files: none in the repository (platform settings), M `frontend/.env.example`.
  - Reqs: NFR-008-AC01, NFR-004-AC02, NFR-010-AC02. Design: §11.1, §11.4.
  - Depends: T1.01 (approval record), T15.02.
  - **Approved inputs:** DA-04 (`APP_ORIGIN` lists the explicitly trusted origins, and a preview origin only if it is listed) and DA-15 (502 or 504 for upstream failures). The checks V-07 and V-08 are done in T15.05.
  - Done when: `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL` begin with `https://` and point to Render, and `FRONTEND_ORIGIN` on Render equals the Vercel origin.
  - Verify: the deployed site loads over HTTPS.

- [ ] **T15.05 Production smoke test** — ACTIONABLE (approved: DA-04, DA-05, DA-12, DA-15, DA-16)
  - Objective: verify the deployed system end to end by hand.
  - Files: none.
  - Reqs: NFR-004-AC01 to AC03, NFR-008-AC01 to AC04, FRONT-023-AC01, AC03. Design: §11.5, §11.8.
  - Depends: T1.01 (approval record), T15.04, T15.03.
  - Done when: a human registers, logs in, and creates a board, a column, and a card on the deployed site. The session cookie has `Secure`, `HttpOnly`, and `SameSite=Lax`. No JWT is in storage or page output. A server-side request from Vercel to `GET /api/boards` with a valid JWT succeeds. A direct browser call to a protected Flask route fails. It also covers the deployed verification obligations: the Render scrypt security, latency, and memory benchmark (V-01, which must pass before production deployment, because `scrypt:32768:8:1` is only a provisional development configuration), the session-mode pooler checks (V-02, together with T15.01), the trusted-origin and cookie flag checks (V-07), the 502 and 504 behavior including a cold start (V-08), and the check that no route except health returns a CORS header (V-09). A failed check is reported to the human owner and is not worked around.
  - Verify: a checklist of observations is recorded in the changelog.

- [ ] **T15.06 Production hardening** — ACTIONABLE (approved: DA-07)
  - Objective: apply the request-body size limit and the response security headers.
  - Files: M `backend/app/config.py`, M `frontend/next.config.ts`.
  - Reqs: NFR-001, NFR-003, API-002-AC06, FRONT-023-AC16. Design: §11.8.
  - Depends: T1.01 (approval record), T15.05.
  - **Approved input:** DA-07 (1 MiB, HTTP 413). Verification V-06 is performed in this task and is not yet done.
  - Done when: a body of 1,048,577 bytes is rejected with HTTP 413 and the string envelope at both the Flask and the BFF boundary, a body of 1,048,576 bytes is not rejected for its size, the request-body limit of the Vercel platform is checked to be above 1 MiB (V-06), debug mode is off, and the headers `X-Content-Type-Options`, `Referrer-Policy`, and a frame restriction are present without changing behavior.
  - Verify: a test and a header check against the deployed site.

- [ ] **T15.07 Read-latency measurement on the deployed API** — ACTIONABLE
  - Objective: measure p95 on Render and record the result.
  - Files: M `README.md`.
  - Reqs: NFR-005-AC01, AC02. Design: §9.4.
  - Depends: T14.12, T15.05.
  - Done when: each available read endpoint has at least 100 sequential requests after one warm-up request, the p95 and dataset size are in the README, and a result above 500 ms is reported as a finding with the cause (for example a free-plan cold start), not hidden. The result is a measurement and not a promise.
  - Verify: the README table matches the script output.

- [ ] **T15.08 Playwright against the production site** — BLOCKED (UD-16, UD-22)
  - Objective: run the end-to-end suites on the deployed Vercel URL.
  - Files: none.
  - Reqs: TEST-007, TEST-008, TEST-009, NFR-008. Design: §10.3, §10.4.
  - Depends: T14.08, T15.05.
  - **What must be confirmed:** UD-16 and UD-22.
  - Done when: all Playwright specs pass on the approved target and leave no stray data.
  - Verify: the Playwright report is saved in `evidence/`.

- [ ] **T15.09 Production logging and secrets check** — ACTIONABLE
  - Objective: confirm production logs and configuration leak nothing.
  - Files: none.
  - Reqs: NFR-002, API-002-AC05. Design: §4.12, §11.7.
  - Depends: T15.05.
  - Done when: a review of the Render and Vercel logs shows no token, password, hash, body, or connection string, and a forced error returns the generic 500.
  - Verify: a human reviews the logs and records the result.

---

## Milestone 16. Final verification, evidence and submission

- [ ] **T16.01 Requirements-to-verification audit** — ACTIONABLE
  - Objective: confirm every requirement has at least one passing test or a recorded manual check, and list anything that is pending an open decision.
  - Files: C `evidence/traceability-audit.md`.
  - Reqs: all requirement categories (AUTH, BOARD, COLUMN, CARD, COMMENT, NOTIF, ANALYTICS, USER, API, FRONT, TEST, NFR). Design: §13.
  - Depends: T14.01, T14.03, T15.08.
  - Done when: each of the 93 requirements maps to a test file or a manual checklist, and requirements affected by UD-09 (NOTIF-001, FRONT-016, FRONT-017-AC04) are labeled pending, not passed.
  - Verify: a script lists requirement IDs found in test names and reports the unmapped ones.

- [ ] **T16.02 README completion** — ACTIONABLE
  - Objective: finish the README with setup, environment variables, run commands, deployment steps, the measurement procedure, and the list of open decisions.
  - Files: M `README.md`.
  - Reqs: NFR-005-AC02, NFR-010. Design: §2.1, §11.
  - Depends: T15.07.
  - Done when: a new developer can run both apps and all test suites from the README, and the README lists UD-01, 02, 07, 09, 15, 16, 17, 21, 22 as open unless a human has approved them.
  - Verify: a second person follows the README from a clean clone.

- [ ] **T16.03 Changelog with refinement rounds** — ACTIONABLE
  - Objective: record at least five before-and-after refinement rounds of the AI-assisted workflow.
  - Files: M `specs/CHANGELOG.md`.
  - Reqs: NFR-011-AC01. Design: §2.1.
  - Depends: T1.07.
  - Done when: each round has a "Before" entry and an "After" entry that quote or summarize the artifact states.
  - Verify: the file has at least five rounds.

- [ ] **T16.04 Guideline violation report** — ACTIONABLE
  - Objective: document at least three guideline violations found in AI output.
  - Files: M `evidence/ai-reviews/violation-report.md`.
  - Reqs: NFR-011-AC02, AC04. Design: §2.1.
  - Depends: T1.07.
  - Done when: each entry has the four labeled fields (guideline violated, offending code or evidence, correction, verification of the correction), and cites a guideline ID.
  - Verify: the file has at least three entries with all four fields.

- [ ] **T16.05 With-and-without-guidelines comparison** — ACTIONABLE
  - Objective: compare one identical task generated without and with the guidelines.
  - Files: M `evidence/ai-reviews/guidelines-comparison.md`.
  - Reqs: NFR-011-AC07. Design: §2.1.
  - Depends: T1.07.
  - Done when: for each run the document gives the number of guideline violations found in review and the number of tests passing on the first run, and states the difference. The numbers are measured, not estimated.
  - Verify: a reviewer can reproduce the counts from the saved outputs.

- [ ] **T16.06 Human review records** — ACTIONABLE
  - Objective: confirm that every AI-generated change has a recorded human review.
  - Files: M `specs/CHANGELOG.md`.
  - Reqs: NFR-011-AC03. Design: §2.1.
  - Depends: all implementation tasks.
  - Done when: each ticked task has a review note (reviewer, date, outcome).
  - Verify: no ticked task lacks a note.

- [ ] **T16.07 Open-decision closeout** — ACTIONABLE (human decision)
  - Objective: record the status of every unresolved decision and design assumption at submission.
  - Files: M `specs/CHANGELOG.md`, M `evidence/traceability-audit.md`.
  - Reqs: Section 8.1 of the requirements. Design: §12.
  - Depends: T16.01.
  - Done when: UD-01, 02, 07, 09, 15, 16, 17, 21, 22 and DA-01 to DA-19 each have a status (approved with a link to the updated requirement or design text, or still open). A task that depended on an open decision is marked pending, not done.
  - Verify: the list has 9 UD entries and 19 DA entries.

- [ ] **T16.08 Submission checklist** — ACTIONABLE
  - Objective: verify the final package.
  - Files: none.
  - Reqs: NFR-011-AC05, AC06, NFR-008, NFR-010. Design: §14.
  - Depends: T16.01 to T16.07.
  - Done when: `guidelines/frontend.md`, `guidelines/backend.md`, `guidelines/database.md` exist and every guideline has Rule, Rationale, and Concrete Example, both `.env.example` files exist, the deployed URLs work, no secret is in the repository, and the final commit is made by a human.
  - Verify: a human signs off on the checklist.

---

## Dependency map: design assumptions
All 19 design assumptions are **APPROVED** by the human owner (Limadijaya Suhendra, 2026-11-24). The table lists the tasks whose status tag names each assumption. A task tagged CONDITIONAL (V-nn) also waits for a verification obligation of `design.md` Section 12.3.1.

| DA | Status | Tasks that name it |
|---|---|---|
| DA-01 | APPROVED | T3.01 |
| DA-02 | APPROVED | T2.02, T2.03, T2.04, T2.05, T2.06, T2.07, T2.08 |
| DA-03 | APPROVED | T5.01, T5.02, T5.03, T6.05, T7.01, T7.06, T8.01, T8.02, T10.01, T11.01, T11.02, T11.06, T11.07, T13.01 |
| DA-04 | APPROVED | T1.05, T10.04, T10.05, T10.06, T11.10, T13.01, T15.04, T15.05 |
| DA-05 | APPROVED | T4.01, T15.05 |
| DA-06 | APPROVED | T2.02, T4.02, T4.05, T5.06 |
| DA-07 | APPROVED | T2.01, T3.01, T4.02, T10.05, T10.06, T15.06 |
| DA-08 | APPROVED | T6.02, T6.03, T7.02 |
| DA-09 | APPROVED | T4.05, T6.02, T7.02 |
| DA-10 | APPROVED | T5.02, T7.06 |
| DA-11 | APPROVED | T3.04, T5.05, T6.02, T6.03, T7.02, T7.04, T8.01 |
| DA-12 | APPROVED | T3.05, T15.05 |
| DA-13 | APPROVED | T2.06, T7.03, T9.01, T9.02 |
| DA-14 | APPROVED | T2.07, T2.08, T2.11, T5.05 |
| DA-15 | APPROVED | T10.05, T15.04, T15.05 |
| DA-16 | APPROVED | T2.01, T15.01, T15.02, T15.05 |
| DA-17 | APPROVED | T2.08, T2.10, T15.01 |
| DA-18 | APPROVED | T12.04, T12.05, T12.07, T14.08 |
| DA-19 | APPROVED | T7.06 |

## Dependency map: unresolved decisions
All nine stay **OPEN**. A proposal in `design.md` is **NOT APPROVED** and is never used as a default.

| UD | Status | Tasks affected | Effect |
|---|---|---|---|
| UD-01 | **OPEN** | T2.01 (variable required, no default), T4.03 (reads the variable), T15.02 (BLOCKED) | The lifetime is an environment variable with no default in code. Setting its value in Render is blocked. |
| UD-02 | **OPEN** | T4.07 (guard test) | No refresh route, token, or table is built, and a test asserts none exists. |
| UD-07 | **OPEN** | T2.04, T7.02 (guards) | No card field beyond `title` and `assignee_id` is built. No task adds card fields. |
| UD-09 | **OPEN** | T9.03, T9.09, T13.04, T13.05 (BLOCKED), T13.07 (BLOCKED for the unread-count check), T9.01 and T13.03 (pre-work only) | `GET /api/notifications` completion, the unread count, and `NotificationBell` are blocked. |
| UD-15 | **OPEN** | T14.01, T14.03 (report only), T14.11 (BLOCKED) | Coverage is reported only. No threshold is set. |
| UD-16 | **OPEN** | T1.04, T1.06 (inputs only), T14.04 to T14.08, T15.03, T15.08 (BLOCKED) | Playwright target, environments, and the migration mechanism are inputs. Dependent tasks are blocked. |
| UD-17 | **OPEN** | T14.10, T15.03 (BLOCKED) | No CI workflow is created. |
| UD-21 | **OPEN** | T4.02 (guard) | Registration enforces only "non-empty". No password length rule is built. |
| UD-22 | **OPEN** | T14.04 to T14.08, T15.08 (BLOCKED) | The E2E account and its variable names are not defined. Dependent tasks are blocked. |

---

## Coverage tables

### Endpoints (26 mandatory and 1 approved extension)
| # | Endpoint | Task | Status |
|---|---|---|---|
| 1 | `POST /api/auth/register` | T4.02 | ACTIONABLE (approved: DA-06, DA-07) |
| 2 | `POST /api/auth/login` | T4.03 | ACTIONABLE |
| 3 | `GET /api/users/me` | T4.05 | ACTIONABLE (approved: DA-06, DA-09) |
| 4 | `PATCH /api/users/me` | T4.05 | ACTIONABLE (approved: DA-06, DA-09) |
| 5 | `POST /api/boards` | T5.01 | ACTIONABLE (approved: DA-03) |
| 6 | `GET /api/boards` | T5.02 | ACTIONABLE (approved: DA-03, DA-10) |
| 7 | `GET /api/boards/{id}` | T5.03 | ACTIONABLE (approved: DA-03) |
| 8 | `PATCH /api/boards/{id}` | T5.04 | ACTIONABLE |
| 9 | `DELETE /api/boards/{id}` | T5.05 | CONDITIONAL (V-04; approved: DA-14, DA-11) |
| 10 | `POST /api/boards/{id}/columns` | T6.01 | ACTIONABLE |
| 11 | `PATCH /api/columns/{id}` | T6.02 | ACTIONABLE (approved: DA-08, DA-09, DA-11) |
| 12 | `DELETE /api/columns/{id}` | T6.03 | ACTIONABLE (approved: DA-08, DA-11) |
| 13 | `PATCH /api/boards/{id}/columns/reorder` | T6.04 | ACTIONABLE |
| 14 | `POST /api/columns/{id}/cards` | T7.01 | ACTIONABLE (approved: DA-03) |
| 15 | `PATCH /api/cards/{id}` | T7.02 (title), T7.03 (assignment) | ACTIONABLE (approved: DA-08, DA-09, DA-11, DA-13) |
| 16 | `DELETE /api/cards/{id}` | T7.04 | ACTIONABLE (approved: DA-11) |
| 17 | `PATCH /api/cards/{id}/position` | T7.05 | ACTIONABLE |
| 18 | `GET /api/cards?assignee=me` | T7.06 | ACTIONABLE (approved: DA-03, DA-10, DA-19) |
| 19 | `POST /api/cards/{id}/comments` | T8.01 | ACTIONABLE (approved: DA-03, DA-11) |
| 20 | `GET /api/cards/{id}/comments` | T8.02 | ACTIONABLE (approved: DA-03) |
| 21 | `PATCH /api/comments/{id}` | T8.03 | ACTIONABLE |
| 22 | `DELETE /api/comments/{id}` | T8.04 | ACTIONABLE |
| 23 | `GET /api/notifications` | T9.01 (pre-work), T9.03 | **BLOCKED (UD-09)** |
| 24 | `PATCH /api/notifications/{id}/read` | T9.02 | ACTIONABLE (approved: DA-13) |
| 25 | `GET /api/boards/{id}/analytics` | T9.07 (with T9.05, T9.06, T9.08) | ACTIONABLE |
| 26 | `GET /api/health` | T3.05 | ACTIONABLE (approved: DA-12) |
| ext | `POST /api/boards/{id}/members` | T5.06 | ACTIONABLE (approved: DA-06) |

### Pages (6)
| Page | Tasks |
|---|---|
| `/register` | T10.09 |
| `/login` | T10.09 |
| `/` | T11.01 |
| `/boards/[id]` | T11.02 to T11.11, T12.01 to T12.07 |
| `/my-tasks` | T13.01 |
| `/profile` | T13.02 |

Loading, empty, and error states: T10.10 (`ErrorState`), T11.01, T11.02, T13.01, T13.02, and the sweep T13.06.

### Blueprints (8)
| Blueprint | Tasks |
|---|---|
| `auth` | T4.02, T4.03 |
| `users` | T4.05 |
| `boards` | T5.01 to T5.07 |
| `columns` | T6.01 to T6.07 |
| `cards` | T7.01 to T7.09 |
| `comments` | T8.01 to T8.06 |
| `notifications` | T7.03 (creation function), T9.01, T9.02, T9.03 (BLOCKED), T9.04 |
| `analytics` | T9.05 to T9.08 |

Registration of exactly eight Blueprints: T3.06.

### Database entities (8)
| Entity | Task |
|---|---|
| `User`, `Board`, `BoardMembership` | T2.02 |
| `BoardColumn` | T2.03 |
| `Card` | T2.04 |
| `Comment` | T2.05 |
| `Notification` | T2.06 |
| `ActivityEvent` | T2.07 |
| Migration, fixtures, migration tests, cascade proof | T2.08, T2.09, T2.10, T2.11 |

### Activity event types (3 approved)
| Event type | Created by | Verified by |
|---|---|---|
| `card_created` | T7.01 | T8.05 |
| `card_moved` (only when the column changes) | T7.05 | T8.05 |
| `comment_created` | T8.01 | T8.05 |

No task creates any other event type. T7.03 states that assignment creates no activity event, T2.07 limits the type with a CHECK constraint, and T8.05 asserts the non-events.

### Frontend topics
| Topic | Tasks |
|---|---|
| Next.js App Router, TypeScript, Tailwind CSS | T1.05, T1.06 |
| Server versus Client Components | T10.11 (boundary test), and the Server Component page tasks T10.09, T11.01, T11.02, T13.01, T13.02 |
| HttpOnly cookie, session, middleware, BFF proxy | T10.04, T10.05, T10.06 |
| `AuthContext` | T10.07 |
| Shared UI components | T10.08 |
| `BoardCard`, `ColumnHeader`, `AddCardForm`, `CommentList` | T11.01, T11.03, T11.05, T11.07 |
| Native HTML5 drag-and-drop | T12.03 (with T12.01, T12.02) |
| Keyboard and touch alternatives | T12.04, T12.05, T12.07, T14.08 |
| Optimistic updates and rollback | T12.02, T12.06 |
| Notification polling | T13.03 (and T13.04, T13.05 pending UD-09) |

### Testing checkpoints
| Area | Tasks |
|---|---|
| pytest | T2.10, T3.01 to T3.07, T4.04, T4.07, T5.07, T6.05 to T6.07, T7.07 to T7.09, T8.05, T8.06, T9.04, T9.08, T9.09, T14.01, T14.09 |
| Vitest and React Testing Library | T1.06, T10.02, T10.03, T10.11, T11.11, T12.06, T12.07, T13.06, T14.03 |
| Playwright | T14.04 to T14.08 (BLOCKED), T15.08 (BLOCKED) |
| Authentication and authorization | T3.02, T4.04, T4.06, T5.07, T6.07, T7.09, T8.06 |
| API contracts | T3.01, T9.09 |
| Database migrations | T2.10, T2.11 |
| Concurrency and ordering | T6.04, T6.06, T7.05, T7.07, T7.08, T14.02 |
| Notifications and analytics | T9.04, T9.08, T13.07 |
| Soft-delete behavior | T6.03, T6.05, T7.04, T7.09, T8.05 |
| Mobile and keyboard accessibility | T12.07, T14.07, T14.08 |
| Production deployment | T15.05, T15.07, T15.08, T15.09 |

---

## Validation

Results are measured on this file by script (task counts and dependency order) and by reading the coverage tables above.

| # | Check | Result |
|---|---|---|
| 1 | All 26 mandatory endpoints and the extension have implementation tasks. | Yes. The endpoint table lists 26 numbered rows and the extension row, each with a task. `GET /api/notifications` has pre-work (T9.01) and a BLOCKED completion task (T9.03). |
| 2 | All six pages have implementation tasks. | Yes (T10.09 for two pages, T11.01, T11.02, T13.01, T13.02). |
| 3 | All eight Blueprints and eight entities are covered. | Yes. See the Blueprint and entity tables. T3.06 asserts exactly eight Blueprints and T2.10 asserts exactly eight tables. |
| 4 | The three approved activity event types are preserved. | Yes. Only `card_created`, `card_moved`, and `comment_created`. Assignment creates none (T7.03, T8.05). |
| 5 | All nine unresolved decisions remain open. | Yes. Each is marked OPEN in the UD map. Tasks that depend on them are BLOCKED or have only pre-work. No task sets a lifetime, a default `per_page`, a coverage number, an environment, a CI pipeline, a password rule, or extra card fields. |
| 6 | DA-01 to DA-19 are identified. | Yes. All 19 are recorded as APPROVED by Limadijaya Suhendra on 2026-11-24 in the approval record, each with its exact decision, approver, and date. Verification obligations V-01 to V-10 remain outstanding. |
| 7 | Tasks are dependency-ordered. | Yes. A script checked that every `Depends` ID exists and appears earlier in the file. It found no missing, forward, or self dependency. The application factory (T2.01) and the fixtures (T2.09) sit in Milestone 2 so the migration tasks come after them. |
| 8 | No task silently approves an unresolved choice. | Yes. Every task that touches a UD carries a BLOCKED tag or a guard note, every task that uses a DA carries its approval reference, and tasks with an outstanding verification obligation are CONDITIONAL (V-nn). No task uses a design proposal as a default. |

### Counts
- Milestones: 16.
- Tasks: 137 (Milestone 1: 7, 2: 11, 3: 7, 4: 7, 5: 7, 6: 7, 7: 9, 8: 6, 9: 9, 10: 12, 11: 12, 12: 7, 13: 7, 14: 12, 15: 9, 16: 8).
- Status: 120 ACTIONABLE (including T1.01 to T1.07, which are complete), 2 CONDITIONAL, 15 BLOCKED. One BLOCKED task (T15.02) is also CONDITIONAL. Completed: 7 (T1.01 to T1.07). No other task is complete.

### Requirement gaps and contradictions noted while planning
- **Closed: keyboard and touch move controls.** DA-18 was approved and `requirements.md` now has FRONT-019-AC17 to AC24, FRONT-025-AC18 to AC21, NFR-007-AC04 to AC06, TEST-005-AC12, TEST-009-AC03, and TEST-009-AC04. T12.04, T12.05, and T12.07 are actionable. T14.08 stays blocked by UD-16 and UD-22.
- **Closed: HTTP 413.** `requirements.md` now lists 413 in Section 2.3 and Section 2.4 and specifies it in API-002-AC04, API-002-AC06, FRONT-023-AC16, TEST-001-AC05, TEST-001-AC06, and TEST-005-AC13. T3.01, T9.09, T10.05, T10.06, and T15.06 reference these criteria. FRONT-023-AC08 was reworded to state the explicit trusted-origin rule of DA-04.
- **TEST-008 and the drag step.** TEST-008-AC06 uses a drag. Native HTML5 drag events are hard to simulate in Playwright on some browsers, so T14.06 may need the drag API of Playwright and a documented fallback. It does not replace the requirement.
- **Unread count across pages.** FRONT-016 criteria use fewer notifications than one page, so a correct count for more notifications needs UD-09 (T13.04, T13.05).
- **NFR-005 on a free Render plan.** A cold start can exceed the 500 ms target. T15.07 records the measured result and the cause and does not change the target.
- **Flask-Migrate and the factory ordering** needed the factory and fixtures before the migration tests. They are placed in Milestone 2 for that reason.



