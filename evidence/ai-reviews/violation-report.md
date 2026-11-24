# Guideline Violation Report

This report documents guideline violations found in AI-generated output during review (NFR-011-AC02). Every entry has the four labeled fields required by NFR-011-AC04. The guidelines are `guidelines/frontend.md` (FE-nn), `guidelines/backend.md` (BE-nn), and `guidelines/database.md` (DB-nn).

Review status: entries 1 to 5 were found by Kiro's own tests, lint, and comparison runs during the build phase. The owner has not reviewed them yet.

### Violation 1: empty password accepted by a no-op validator
- **Date and task:** 2026-11-24, T4.02 (`POST /api/auth/register`).
- **Guideline violated:** BE-06, "Marshmallow validates every input strictly".
- **Offending code or evidence:** `backend/app/blueprints/auth/schema.py`: `password = fields.String(required=True, validate=lambda v: len(v) > 0)`. In Marshmallow 4 a validator that returns `False` does not reject the value. The test `test_register_validation_errors_are_400` failed: `assert 201 == 400` for `password=""`.
- **Correction:** `validate=validate.Length(min=1)`.
- **Verification of the correction:** the same test passes, and the whole backend suite is green (132 passed).

### Violation 2: raw `<button>` in AI-written test code
- **Date and task:** 2026-11-24, T10.08 (`BaseModal` test).
- **Guideline violated:** FE-11, "Reuse `BaseButton`, `BaseBadge`, and `BaseModal`" (a raw `<button>` is not allowed outside `BaseButton.tsx`).
- **Offending code or evidence:** `frontend/tests/unit/BaseComponents.test.tsx` line 54: `<button id="opener">open</button>`. `npx eslint .` reported `Use BaseButton instead of a raw <button> (FE-11)`.
- **Correction:** the opener became `<a id="opener" href="#top">open</a>`.
- **Verification of the correction:** `npx eslint .` exits 0 and the 36 Vitest tests pass.

### Violation 3: duplicated, hand-written query validation
- **Date and task:** 2026-11-24, T7.06 (`GET /api/cards?assignee=me`).
- **Guideline violated:** BE-06 (one strict schema validates each input) and BE-03 (rules live in the schema, not in ad-hoc code).
- **Offending code or evidence:** `backend/app/blueprints/cards/schema.py` had a custom `load_checked()` method, and `service.py` called `load_query()` and then `load_checked()` on the same query.
- **Correction:** `assignee = fields.String(required=True, validate=validate.Equal("me"))` and a single `load_query()` call.
- **Verification of the correction:** `test_my_tasks_requires_assignee_me` passes: missing, wrong, and extra parameters all return 400.

### Violation 4: unchanged comment edit rewrites `updated_at` (found in the comparison run)
- **Date and task:** 2026-11-24, T8.03 comparison Run 1 (no guidelines, with project code available).
- **Guideline violated:** DA-08 as applied by BE-16 and DB-04, "`updated_at` changes only when a row's business fields change".
- **Offending code or evidence:** `evidence/ai-reviews/comparison/run1-without-guidelines/comments/service.py`, `update_comment`: `comment.content = data["content"]; comment.updated_at = utcnow()` with no comparison to the stored value.
- **Correction:** the shipped `backend/app/blueprints/comments/service.py` writes only inside `if comment.content != data["content"]:`.
- **Verification of the correction:** reviewed against Run 2, which has the guard. A dedicated test for the no-op edit is listed as remaining work.

### Violation 5: nine guideline breaks in an isolated generation (found in the comparison run)
- **Date and task:** 2026-11-24, T8.01 to T8.04 comparison Run 3 (no guidelines, no project code).
- **Guideline violated:** BE-03, BE-05, BE-06, BE-07, BE-09, BE-16, BE-17, DB-04, DA-08. The table in `guidelines-comparison.md` lists each rule with the exact evidence.
- **Offending code or evidence:** `comparison/run3-isolated-without-guidelines/comments/routes.py` validates the body in the route before authorization, defines its own `auth_required` and `_error()`, and `service.py` never sets `created_at` or takes a lock.
- **Correction:** none of Run 3's code was shipped. The shipped Blueprint follows each rule, and Run 4 shows the same task with the guidelines applied (0 of 9 violated).
- **Verification of the correction:** `pytest tests/api/test_comments.py` passes (201, 400 missing content, 401 unauthenticated, 403 not the owner, 404 non-member).

### Template (copy for each new violation)
```markdown
### Violation N: <short title>
- **Date and task:** <date>, <task ID>
- **Guideline violated:** <guideline ID and its rule>
- **Offending code or evidence:** <file and line, and the quoted code or output>
- **Correction:** <what was changed>
- **Verification of the correction:** <the command, test, or review step, and its result>
```