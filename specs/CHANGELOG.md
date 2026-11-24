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

Rounds 1 to 7 are spec refinement rounds. The Before text is quoted from the parent commit and the After text from the commit named in each round (`git show <commit>` shows the exact diff). Each commit exists only because the owner accepted it. Rounds 8 to 11 are implementation review rounds from the build phase and are marked pending until the owner reviews them.

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
- **Reviewed and accepted by:** Pending owner review.

### Round 9: backend code, duplicated query validation (2026-11-24, build phase)
- **Artifact:** `backend/app/blueprints/cards/schema.py` and `service.py` (`GET /api/cards?assignee=me`).
- **Before:** A hand-written `load_checked()` method on the schema, called after `load_query()`, so the query was validated twice and the second check lived outside the schema rules.
- **Issue found in review:** Duplicate validation and a business check inside a custom method (BE-03 layering, BE-06 one strict schema).
- **After:** One declarative rule, `assignee = fields.String(required=True, validate=validate.Equal("me"))`, and one `load_query()` call. Tests cover missing, wrong, and extra parameters (all 400).
- **Reviewed and accepted by:** Pending owner review.

### Round 10: frontend code, raw button in a test (2026-11-24, build phase)
- **Artifact:** `frontend/tests/unit/BaseComponents.test.tsx`.
- **Before:** The AI-written modal test used `<button id="opener">open</button>` as the element that opens the dialog.
- **Issue found in review:** `npx eslint .` failed with "Use BaseButton instead of a raw <button> (FE-11)". The lint rule added in T1.06 caught the violation.
- **After:** The opener is an `<a href="#top">`. Lint passes and the focus-return assertion is unchanged.
- **Reviewed and accepted by:** Pending owner review.

### Round 11: design.md and guidelines, shared component folder (2026-11-24, build phase)
- **Artifact:** `specs/design.md` section 2.1 and `frontend/eslint.config.mjs`.
- **Before:** The layout placed `BaseButton`, `BaseBadge`, and `BaseModal` in `components/ui/`.
- **Issue found in review:** The assignment brief and its grading checklist name `components/shared/`. A folder name that differs from the brief would fail a literal check.
- **After:** The three components live in `frontend/src/components/shared/`. The design tree and the ESLint exception that lets only `BaseButton.tsx` render a `<button>` use the new path.
- **Reviewed and accepted by:** Pending owner review.

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

**Decisions the owner delegated to Kiro.** On 2026-11-24 the owner wrote "From now on I depend on you to complete the assignment". Kiro took the decisions below to unblock the work. They are **not** owner approvals in the sense of `tasks.md` rule 6, so they stay open until the owner confirms or changes them.
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