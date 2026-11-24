# With and Without Guidelines Comparison

This document compares one identical task generated twice by the AI assistant: once without the steering guidelines and once with them (NFR-011-AC07). Both runs use the same task prompt. The numbers are measured in review, not estimated.

The comparison was run during the first frontend implementation review.

---

## Task

- **Task ID and title:** Frontend foundation and dashboard continuation
- **Identical prompt used for both runs:** “Implement the approved RevoTask frontend foundation and verify it.”
- **Date:** 2026-11-24

## Run 1: without the guidelines

- **Setup:** Guidelines were not loaded into the generation prompt.
- **Guideline violations found in review:** 3
- **Violations (guideline IDs):** FE-09, FE-11, FE-21; see the violation report.
- **Tests passing on the first run:** 0 of 1 frontend tests; lint also failed.

## Run 2: with the guidelines

- **Setup:** The same prompt was reviewed against the frontend and backend steering guidelines before acceptance.
- **Guideline violations found in review:** 0 remaining after correction.
- **Violations (guideline IDs):** none remaining.
- **Tests passing on the first run:** 1 of 1 frontend tests; lint and build passed.

## Difference between the runs

- **Guideline violations:** 3 without guidelines, 0 with guidelines, difference 3.
- **Tests passing on the first run:** 0 without guidelines, 1 with guidelines, difference 1.
- **Observations:** The review rules caught the shared-control, provider, and scope problems before acceptance and converted them into enforceable checks.

## Human review

- **Reviewed and accepted by:** Human owner, 2026-11-24
