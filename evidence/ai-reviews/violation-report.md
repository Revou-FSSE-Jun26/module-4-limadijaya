# Guideline Violation Report

This report documents guideline violations found in AI-generated output during human review (NFR-011-AC02). At least three violations are required. Every entry has the four labeled fields required by NFR-011-AC04.

The guidelines are `guidelines/frontend.md` (FE-nn), `guidelines/backend.md` (BE-nn), and `guidelines/database.md` (DB-nn). Cite the exact guideline ID.

### Violation 1: Raw button in shared primitive
- **Date and task:** 2026-11-24, frontend foundation
- **Guideline violated:** FE-11: feature code MUST use the shared `BaseButton` primitive.
- **Offending code or evidence:** The first lint run reported `BaseButton.tsx` itself for its native `<button>` implementation.
- **Correction:** Scoped the rule exception to the one approved primitive with an explanatory ESLint comment.
- **Verification of the correction:** `npm run lint` passes with zero errors.

### Violation 2: Dashboard rendered without authentication context
- **Date and task:** 2026-11-24, frontend dashboard
- **Guideline violated:** FE-09: shared state and authenticated requests MUST be supplied through the application provider.
- **Offending code or evidence:** The existing scaffold test rendered the dashboard directly and failed with `AuthProvider is missing`.
- **Correction:** Added `Providers`/`AuthProvider` to the root layout and a safe empty context for isolated component rendering.
- **Verification of the correction:** `npm test` passes with 1 test passed.

### Violation 3: Placeholder-only application shell
- **Date and task:** 2026-11-24, T1.05 continuation review
- **Guideline violated:** FE-21: implementation MUST remain traceable to the approved application pages and features.
- **Offending code or evidence:** `src/app/page.tsx` only rendered “Under construction” while the assignment required dashboard and authenticated flows.
- **Correction:** Added login, register, dashboard, board detail, My Tasks, Profile, shared components, typed API client, and hooks.
- **Verification of the correction:** `npm run typecheck`, `npm run build`, and the frontend lint/test gates pass.

---

## Template (copy for each violation)

```markdown
### Violation N: <short title>
- **Date and task:** <date>, <task ID>
- **Guideline violated:** <guideline ID and its rule, for example "FE-11: feature components MUST NOT contain a raw <button>">
- **Offending code or evidence:** <file and line, and the quoted code or output that breaks the rule>
- **Correction:** <what was changed to comply, quoted or summarized>
- **Verification of the correction:** <the command, test, or review step that proves the correction, and its result>
```
