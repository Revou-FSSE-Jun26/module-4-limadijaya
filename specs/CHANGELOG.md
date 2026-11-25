# RevoTask Changelog

This file records two things:

1. **Refinement rounds** of the AI-assisted workflow (NFR-011-AC01). Each round has a "Before" entry that quotes or summarizes the artifact before refinement, and an "After" entry for the artifact after refinement. At least five rounds are required. Rounds are added as they happen.
2. **Implementation log**: what was done in each task, with its commit and its verification evidence (NFR-011-AC03, human review before acceptance).

Only facts that were verified are recorded here. A commit ID is written only after the commit exists.

---

## Refinement rounds

### Template (copy for each round)
```markdown
### Round N: <artifact> (<date>)
- **Artifact:** <file or section that was refined>
- **Before:** <quote or summary of the artifact before refinement>
- **Issue found in review:** <what the human reviewer found>
- **After:** <quote or summary of the artifact after refinement>
- **Reviewed and accepted by:** <name>, <date>
```

Rounds 1 to 7 are spec refinement rounds. The Before text is quoted from the parent commit and the After text from the commit named in each round (`git show <commit>` shows the exact diff). Each commit exists only because the owner accepted it. Rounds 8 to 12 are implementation review rounds from the build phase. The owner reviewed and accepted rounds 8 to 11 on 2026-11-25.

### Round 1: requirements.md, administrator permissions (2026-11-20, commit `127a60f`)
- **Artifact:** `specs/requirements.md`, roles and permissions.
- **Before:** "Board Administrator: A user who manages a board. Holds all Board Member capabilities plus administrator-only operations." The list of administrator-only operations was not stated, and `PATCH /api/boards/{id}` was a plain "MUST update a board's name" with no role.
- **Issue found in review:** "Administrator-only operations" was undefined, so no test could check a 403.
- **After:** The definition names exactly five administrator-only operations in a permission table (Board Member vs Board Administrator), says administrator status is per board and grants nothing on another board, and each operation gets an acceptance criterion with its 403 case.
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-20.

### Round 2: requirements.md, soft delete (2026-11-20, commit `8af251a`)
- **Artifact:** `specs/requirements.md`, delete behavior of boards, columns, and cards.
- **Before:** "`DELETE /api/columns/{id}` MUST delete a column. The treatment of its cards is unresolved (UD-23)." and "`DELETE /api/boards/{id}` MUST delete a board."
- **Issue found in review:** The Card model required `deleted_at`, but nothing said what a deleted card or column returns, or what happens to its comments.
- **After:** New assumption A-03 (card delete is soft), A-15 (consequences of soft deletion), and criteria such as BOARD-003-AC07 ("columns with a non-null `deleted_at` are absent from the response, and so are all cards that belong to them") and a 404 row for soft-deleted resources.
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-20.

### Round 3: requirements.md, notifications (2026-11-20, commit `0491142`)
- **Artifact:** `specs/requirements.md`, notifications and card assignment.
- **Before:** "The system MUST create notifications for the events approved in UD-08." and a 404 row for notifications marked "Proposed, not approved (UD-19)".
- **Issue found in review:** "The events approved in UD-08" is a reference, not a testable rule, and a notification of another user could leak existence through a different status code.
- **After:** Explicit triggers and field names (A-04), a 404 with the same body for another user's notification and for a missing one, a 400 with an identical body for an unknown or non-member `assignee_id`, and a 400 when `assignee_id` is sent at card creation.
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-20.

### Round 4: requirements.md, analytics (2026-11-20, commit `458e76a`)
- **Artifact:** `specs/requirements.md`, `GET /api/boards/{id}/analytics`.
- **Before:** "The analytics MUST include the number of cards completed this week." with "this week" left open (UD-14), and member activity "taken from the activity-event records" with no event list.
- **Issue found in review:** "This week" had no time zone or boundary, so a test could not be written.
- **After:** One approved window (UTC, Monday 00:00:00 inclusive to next Monday exclusive), the exact response JSON with four always-present keys, a 400 for any query parameter, and the three counted event types.
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-20.

### Round 5: requirements.md, HTTP response contracts (2026-11-20, commit `f1f2ba0`)
- **Artifact:** `specs/requirements.md`, Section 2.3 response conventions.
- **Before:** Status-code rows such as "200 Successful read, update, or delete" were all "Proposed, not approved (UD-19)".
- **Issue found in review:** A generated spec that mixes proposals with rules makes it unclear what to implement.
- **After:** Every row of the status table is approved. Added: a success body never has `error`, an error body never has `data`, `error` is a non-empty string, DELETE returns `{ "data": { "id": "<uuid>" } }` with 200 and never 204, and a `[Proposed, not approved]` label that is allowed only in Section 8.1.
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-20.

### Round 6: requirements.md, column reorder contract (2026-11-20, commit `623781a`)
- **Artifact:** `specs/requirements.md`, `PATCH /api/boards/{id}/columns/reorder`.
- **Before:** "MUST persist a new column order using positive FLOAT order values. The request and response shape is unresolved (UD-20)."
- **Issue found in review:** An endpoint with no request or response shape cannot have a Marshmallow schema.
- **After:** Request `{columns: [{id, order}]}` (partial lists allowed), response is an array of all active columns in ascending `order`, plus assumptions A-01 (new items get a position above every live sibling), A-04 (field names) and A-05 (list ordering).
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-20.

### Round 7: requirements.md, card position and rebalancing (2026-11-20, commit `d2879df`)
- **Artifact:** `specs/requirements.md`, `PATCH /api/cards/{id}/position`.
- **Before:** "MUST move a card to a column and position. Positions MUST be positive float values." and an open decision UD-06 on rebalancing.
- **Issue found in review:** FLOAT midpoints run out of precision, and creating a card while another card moves could produce duplicate positions.
- **After:** The body is exactly `{column_id, order}`. A tie on `order` renumbers the destination column in one transaction and returns `rebalanced: true`. CARD-002-AC10 makes card creation take the same column lock as a move.
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-20.

### Round 8: backend code, Marshmallow 4 password validator (2026-11-24, build phase)
- **Artifact:** `backend/app/blueprints/auth/schema.py`.
- **Before:** `password = fields.String(required=True, validate=lambda v: len(v) > 0)`. The AI draft assumed a validator that returns `False` rejects the value, as in Marshmallow 3.
- **Issue found in review:** `test_register_validation_errors_are_400` failed on its first run: `register(password="")` returned 201 instead of 400. Marshmallow 4 only rejects a value when the validator raises `ValidationError`. Guideline BE-06 (validate every input strictly).
- **After:** `validate=validate.Length(min=1)`. The test passes and an empty password now returns 400.
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-25.

### Round 9: backend code, duplicated query validation (2026-11-24, build phase)
- **Artifact:** `backend/app/blueprints/cards/schema.py` and `service.py` (`GET /api/cards?assignee=me`).
- **Before:** A hand-written `load_checked()` method on the schema, called after `load_query()`, so the query was validated twice and the second check lived outside the schema rules.
- **Issue found in review:** Duplicate validation and a business check inside a custom method (BE-03 layering, BE-06 one strict schema).
- **After:** One declarative rule, `assignee = fields.String(required=True, validate=validate.Equal("me"))`, and one `load_query()` call. Tests cover missing, wrong, and extra parameters (all 400).
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-25.

### Round 10: frontend code, raw button in a test (2026-11-24, build phase)
- **Artifact:** `frontend/tests/unit/BaseComponents.test.tsx`.
- **Before:** The AI-written modal test used `<button id="opener">open</button>` as the element that opens the dialog.
- **Issue found in review:** `npx eslint .` failed with "Use BaseButton instead of a raw <button> (FE-11)". The lint rule added in T1.06 caught the violation.
- **After:** The opener is an `<a href="#top">`. Lint passes and the focus-return assertion is unchanged.
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-25.

### Round 11: design.md and guidelines, shared component folder (2026-11-24, build phase)
- **Artifact:** `specs/design.md` section 2.1 and `frontend/eslint.config.mjs`.
- **Before:** The layout placed `BaseButton`, `BaseBadge`, and `BaseModal` in `components/ui/`.
- **Issue found in review:** The assignment brief and its grading checklist name `components/shared/`. A folder name that differs from the brief would fail a literal check.
- **After:** The three components live in `frontend/src/components/shared/`. The design tree and the ESLint exception that lets only `BaseButton.tsx` render a `<button>` use the new path.
- **Reviewed and accepted by:** Limadijaya Suhendra, 2026-11-25.

### Round 12: test guard defeated by the new .env loading (2026-11-25, owner's local test run)
- **Artifact:** `backend/tests/conftest.py` and `backend/tests/test_database_guard.py`.
- **Before:** `conftest.py` called `load_dotenv(".../backend/.env")` on every run so a developer could keep `TEST_DATABASE_URL` in `backend/.env`. That line was added in the build phase and was tested only on a machine with no `.env`.
- **Issue found in review:** the owner ran `pytest -v` on their own machine with a real `backend/.env`: 234 passed and 1 failed. `test_pytest_startup_fails_closed_for_unsafe_settings[test-url-missing]` expected exit code 4 and got 0. The test removes `TEST_DATABASE_URL` to prove the guard refuses to start without it, and `load_dotenv` read the value straight back from `.env`, so the guard passed. Guideline DB-02 (production and test databases are separate, and the guard must fail closed).
- **After:** `.env` is loaded only when `REVOTASK_NO_DOTENV` is not `1`, and the startup test sets `REVOTASK_NO_DOTENV=1` for its subprocess. With the same `.env` in place, `pytest tests/test_database_guard.py` reports 103 passed.
- **Reviewed and accepted by:** Kiro found the cause from the owner's test output. Owner acceptance pending.
---

## Implementation log

### 2026-11-24

| Commit | Task | Summary |
|---|---|---|
| `9a81c91` | T1.01 | Approved specification baseline. DA-01 to DA-19 recorded as approved by the human owner. |
| `fca2c9c` | T1.02 | Repository skeleton: `README.md`, `.gitignore`, `backend/`, `frontend/`, `evidence/ai-reviews/`. |
| `f064516` | T1.03 | Backend Python project: dependency files, `pytest.ini`, `wsgi.py`, `backend/.env.example`. |
| `c91cf5b` | T1.04 | Local PostgreSQL test database documentation and the test production-safety guard. |

**T1.03 notes**
- `pip install` in the Python 3.12 virtual environment first failed with `CERTIFICATE_VERIFY_FAILED`. Norton Antivirus inspects HTTPS traffic and re-signs it with its own root certificate, which pip 24.0's bundled certificate list does not contain.
- The issue was resolved, with certificate verification kept on, by using pip's truststore feature, which reads the Windows certificate store: `.\backend\.venv\Scripts\python.exe -m pip install --use-feature=truststore -r backend\requirements-dev.txt`.
- All ten approved direct Python dependencies were installed at their pinned versions, and `pip check` reported no broken requirements.

**T1.04 notes**
- A dedicated local PostgreSQL database `revotask_test` and a restricted role `revotask_test_user` were created and authenticated by the human owner.
- The guard in `backend/tests/conftest.py` refuses to start a test session unless `TEST_DATABASE_URL` names that local database.
- 103 permanent guard tests in `backend/tests/test_database_guard.py` passed, with 0 failures.

**T1.05 to T1.07 (human-approved, not yet committed)**
- T1.05: Next.js frontend scaffold. `npm run build` passed, and `npm run dev` served the placeholder page.
- T1.06: frontend lint, unit test, and Playwright configuration. A sample file containing each forbidden pattern made lint fail, and one trivial Vitest test passed.
- T1.07: this changelog and the two AI review evidence templates.
- Commit ID: none yet. It is added after the commit exists.

**Decisions approved by the human owner for T1.05 to T1.07**
- `frontend/next-env.d.ts` is generated by Next.js and is ignored by Git (`.gitignore`).
- Approved additions beyond the T1.05 file list:
  - the temporary placeholder `frontend/src/app/page.tsx`, which must be removed in T11.01 because `(app)/page.tsx` will serve `/`
  - `frontend/postcss.config.mjs`, required by Tailwind CSS 4
  - `"type": "module"` in `frontend/package.json`
  - Tailwind CSS 4 loading `tailwind.config.ts` through the `@config` directive
- The Playwright base URL variable is named `PLAYWRIGHT_BASE_URL`. This names the variable only and does not resolve UD-16.
- `@vitejs/plugin-react` and `@testing-library/jest-dom` are not used for now.

**Technical debt**
- **ESLint 9.39.5 is deprecated upstream** (npm reports "no longer supported"). It is kept for compatibility: `eslint-config-next` 16.4.6 depends on `eslint-plugin-react`, whose peer range supports ESLint up to 9 and not 10. Revisit when `eslint-config-next` supports ESLint 10.


### 2026-11-24 build phase (Milestones 2 to 14 implemented, local verification)
| Commit | Scope | Summary |
|---|---|---|
| `d3edec9` | Milestones 2 to 9 | Eight models, the initial migration (with RLS), the application factory, eight Blueprints, and 132 pytest tests (the 103 guard tests from T1.04 run on top of these). |
| `f612e5d` | Milestones 10 to 13 | Next.js pages, shared components, hooks, API client, BFF proxy, Vitest tests (36), and the Playwright suite (6 tests). |

**Decisions the owner delegated to Kiro.** On 2026-11-24 the owner wrote "From now on I depend on you to complete the assignment". Kiro took the decisions below to unblock the work. The owner reviewed this table and approved every decision in it on 2026-11-25 ("I agree all of them"). Kiro transcribed the approval and did not approve anything itself.
| UD | Decision taken | Where |
|---|---|---|
| UD-01 | Token lifetime 3600 s. The value is still required from the environment, with no default in code. | `render.yaml`, `.env.example` |
| UD-02 | No refresh token. An expired session returns to `/login`. | no route exists, tested |
| UD-09 | `GET /api/notifications` returns `data = {items, page, per_page, total, unread_count}`. Defaults: `page=1`, `per_page=20`, maximum 100, and a larger value returns 400. | `notifications/service.py` |
| UD-15 | Coverage is measured, not gated. | no threshold |
| UD-16 | Two environments: local and production. Playwright runs against the URL in `PLAYWRIGHT_BASE_URL`. | `playwright.config.ts` |
| UD-17 | No CI workflow. | none |
| UD-21 | Password rule stays "non-empty". | `auth/schema.py` |
| UD-22 | Every Playwright run registers its own throwaway users through the public register endpoint. | `e2e/helpers.ts` |

**Other implementation notes**
- Next.js 16 renamed `middleware.ts` to `proxy.ts`. The session redirect lives in `frontend/src/proxy.ts`.
- `pip` and `npm` both failed on a TLS inspection certificate. Fixed with `pip --use-feature=truststore` and `NODE_OPTIONS=--use-system-ca`, with verification left on.
- A Windows excluded port range blocks port 5000, so local runs use 5055.
- Not done yet: concurrency tests (T6.06, T7.08), SQL-capture tests, the Render benchmark (V-01, V-02), deployment to a public URL, and the Playwright run against that URL.
### 2026-11-25 Supabase database (T15.01, T15.03)
- The owner supplied the Supabase project. The direct host (`db.<ref>.supabase.co`) has only an AAAA record, and the dev machine and the usual hosts are IPv4 only, so the connection failed with "could not translate host name".
- The session-mode pooler of the same project (`aws-1-ap-northeast-1.pooler.supabase.com:5432`, user `postgres.<ref>`) accepted the credentials. Before migrating, a read-only query showed the `public` schema was empty.
- `flask db upgrade` applied `0001_initial`. Verified: 8 application tables plus `alembic_version`, RLS enabled on all 8 (DA-17, V-03 for the schema part), no policies.
- All Blueprints were exercised against that database through the Flask test client: health, register, login, me, boards, columns, cards, move, comments, my tasks, notifications, analytics, a 401 check, and a board delete with cascade (V-04 passes on the real Supabase PostgreSQL). The throwaway rows were deleted and the table counts returned to 0. Calls took 0.3 to 1.4 s from the dev machine to Tokyo, which is not a deployment latency figure (V-02 and the NFR-005 benchmark are still to be run from the hosting region).
- The password was shared in the chat. It was used only as a process environment variable and is in no file. **Rotate the database password in Supabase before the repository goes public.**
### 2026-11-25 Live deployment (T15.02, T15.04, T15.05, T15.07, T15.08)
- The first Render deploy hung because the new organisation repository was empty. After `git push -u origin main`, Render built and started with `flask db upgrade && gunicorn` (the migration was already at head).
- `backend/scripts/smoke_api.py` against `https://module-4-limadijaya.onrender.com`: 19 of 19 checks passed (`evidence/render-smoke.txt`).
- The Vercel site at first rejected writes with 403 "Request origin is not allowed.", because `APP_ORIGIN` still held the placeholder. That confirmed the CSRF check works. After the owner set `APP_ORIGIN` and `FRONTEND_ORIGIN`, registration through the proxy worked and the API's CORS header named the Vercel origin.
- **Playwright against the live URL: 6 of 6 passed** (4 auth scenarios, the 8-step Kanban journey including drag-and-drop persisted after a reload, and the 360 px test).
- **Defect found on the live site and fixed:** the 360 px board page was 636 px wide. The responsive test had passed because it used only 2 columns. Cause: Tailwind's `sr-only` labels are `position: absolute`, and inside the horizontally scrolling columns container they positioned against the page, so off-screen columns widened the document. Fix: `relative` on the scroller (commit `70d6607`). The test now uses 4 columns. Measured after the fix: `scrollWidth` 360 for a 360 px viewport.
- Latency: p95 0.7 to 1.2 s for reads (NFR-005 target 500 ms **not met**), caused by Render in Oregon and Supabase in Tokyo. Recorded in the README.
- All throwaway accounts from these runs (24 users, 13 boards) were deleted. The production tables are empty.
### 2026-11-25 Owner verification
- Postman Collection Runner against `https://module-4-limadijaya.onrender.com`: 19 of 19 requests passed, 0 failed, covering all eight Blueprints (`evidence/screenshots/postman.png`, `postman2.png`, `postman3.png`, collection in `evidence/postman/`).
- `pytest -v` on the owner's local PostgreSQL test database: 234 passed, 1 failed, then fixed in Round 12.
- The owner decided to keep the current Supabase password.