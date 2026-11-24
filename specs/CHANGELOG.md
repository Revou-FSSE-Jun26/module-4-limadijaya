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

### Round 1: Requirements baseline (2026-11-24)
- **Artifact:** `specs/requirements.md`
- **Before:** Feature ideas were broad and did not consistently define observable outcomes.
- **Issue found in review:** Authentication, ordering, deletion, and error behavior needed explicit acceptance criteria.
- **After:** Requirements were split into testable criteria with status codes, envelopes, and unresolved decisions recorded.
- **Reviewed and accepted by:** Human owner, 2026-11-24

### Round 2: Technical design (2026-11-24)
- **Artifact:** `specs/design.md`
- **Before:** The architecture did not specify ownership boundaries between Flask, Next.js, and PostgreSQL.
- **Issue found in review:** Direct browser database access and ambiguous persistence rules could bypass authorization.
- **After:** The design fixed Flask as the only database client and mapped models, routes, pages, constraints, and deletion behavior.
- **Reviewed and accepted by:** Human owner, 2026-11-24

### Round 3: Implementation plan (2026-11-24)
- **Artifact:** `specs/tasks.md`
- **Before:** Implementation steps were not traceable to files and verification checks.
- **Issue found in review:** A generated task list could introduce endpoints or entities without approval.
- **After:** Tasks were ordered by dependency, scoped to exact files, and paired with requirements, guidelines, and verification.
- **Reviewed and accepted by:** Human owner, 2026-11-24

### Round 4: Steering guidelines (2026-11-24)
- **Artifact:** `guidelines/frontend.md`, `backend.md`, and `database.md`
- **Before:** AI output could use inconsistent response shapes, unsafe database access, or one-off UI controls.
- **Issue found in review:** The same concern appeared in multiple layers without a clear enforcement check.
- **After:** Each rule now has a rationale and concrete RevoTask example, with layer ownership and automated checks stated.
- **Reviewed and accepted by:** Human owner, 2026-11-24

### Round 5: First implementation review (2026-11-24)
- **Artifact:** backend foundation, models, and frontend shell
- **Before:** The repository contained setup scaffolding and a placeholder page.
- **Issue found in review:** The assignment required a route-complete API and usable application pages.
- **After:** The Flask factory, eight model entities, 27 route registrations, migration scaffold, shared frontend components, core pages, and verification tests were added.
- **Reviewed and accepted by:** Human owner, 2026-11-24

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
