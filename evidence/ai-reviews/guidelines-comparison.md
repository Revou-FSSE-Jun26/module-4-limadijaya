# With and Without Guidelines Comparison

This document compares the same task generated twice by the AI assistant: once without the steering guidelines and once with them (NFR-011-AC07). The counts below come from a line-by-line review of the generated files, which are kept next to this document in `comparison/` so the review can be repeated.

## Task
- **Task ID and title:** T8.01 to T8.04, the `comments` Blueprint (`routes.py`, `service.py`, `schema.py`, `__init__.py`): create, list, edit (owner only), and delete (owner only).
- **Date:** 2026-11-24.
- **Identical task text for every run:** the endpoint list, request and response shapes, the comment JSON, and the error statuses (401, 404, 403, 400). The text is quoted in full in each sub-agent prompt. Each run was a separate Kiro sub-agent with a clean context.
- **Guideline checklist used for scoring:** the nine rules that the Reviewer checklist of `guidelines/backend.md` and `guidelines/database.md` applies to this Blueprint: BE-03 (route holds no validation or business logic), BE-05 (central error handling, no private error helpers), BE-06 (`unknown = RAISE`), BE-07 (`@jwt_required()` with the shared 401 callbacks), BE-09 (order 401, 404, 403, then 400), BE-16 (atomic write with rollback), BE-17 (`FOR SHARE` lock on comment creation), DB-04 (timestamps from one injected clock reading), and DA-08 (`updated_at` changes only on a real change).

## Experiment A: both runs can read the existing project code
| | Run 1: without guidelines | Run 2: with guidelines |
|---|---|---|
| Setup | The prompt forbade opening `guidelines/`, `specs/`, and `evidence/`. The agent could read `backend/app`. | The prompt required reading `guidelines/backend.md` and `guidelines/database.md` first. |
| Files | `comparison/run1-without-guidelines/comments/` | `comparison/run2-with-guidelines/comments/` |
| Guideline violations | **1** (DA-08: `update_comment` always sets `updated_at`, even when the content is unchanged) | **0** |
| Backend tests passing on the first run (`tests/api/test_comments.py`, 11 tests, files copied into a clean copy of the backend) | 11 of 11 | 11 of 11 |

**What this shows, and its limit.** Both agents copied the helpers and style of the neighbouring Blueprints (`access.py`, `activity.py`, `locking.py`), which already follow the guidelines. So the code bases did the steering and the guidelines changed only one detail. This experiment does not isolate the effect of the guidelines, and it is reported only to show that.

## Experiment B: neither run can read project code (isolated)
Neither agent saw `backend/`. Both received only the model list and the endpoint requirements. Only Run 4 read the two guideline files.

| | Run 3: without guidelines | Run 4: with guidelines |
|---|---|---|
| Files | `comparison/run3-isolated-without-guidelines/comments/` | `comparison/run4-isolated-with-guidelines/comments/` |
| BE-03: route does no validation | Violated. `routes.py` parses and validates the body before calling the service. | Met. The route passes the raw JSON to the service. |
| BE-09: 401, 404, 403, then 400 | Violated. A bad body returns 400 before the 404 and 403 checks. | Met. The comment is loaded and the owner checked, then the schema runs. |
| BE-05: central error handling | Violated. A private `ServiceError` and a private `_error()` build their own responses. | Met. The service raises framework errors that the central handlers turn into the envelope. |
| BE-07: `@jwt_required()` | Violated. A custom `auth_required` decorator swallows every exception as 401. | Met. |
| BE-06: `unknown = RAISE` | Violated. The input schema accepts extra keys. | Met. |
| BE-16: atomic write with rollback | Violated. No rollback on failure. | Met. |
| BE-17: `FOR SHARE` lock when creating | Violated. No lock. | Met. |
| DB-04: one injected clock reading | Violated. `created_at` is never set on the comment, event, or notification, and `datetime.now()` is called inline. | Met. One `now` is used everywhere. |
| DA-08: `updated_at` only on a real change | Violated. | Met. |
| **Guideline violations** | **9 of 9 checked rules** | **0 of 9** |
| Integration defects (not guideline violations) | 1: `Card.id` assumed possibly non-UUID. | 2: it guessed the helper name `app.clock.utc_now` (the real one is `utcnow`) and used `request.get_json()` instead of the shared `read_json_body()`, because it was not allowed to read the helpers. |
| Tests run | Not run: the output cannot import without the project helpers. | Not run, for the same reason. |

## Difference between the runs
- **Guideline violations (Experiment B, the one that isolates the guidelines):** 9 without guidelines, 0 with guidelines, difference 9.
- **Guideline violations (Experiment A):** 1 without, 0 with, difference 1.
- **Tests passing on the first run (Experiment A):** 11 of 11 in both. The tests do not separate the runs, because none of the nine rules changes an HTTP status in the happy path.
- **Observations:** the guidelines mattered most when the agent had no project code to imitate (Experiment B). With neighbouring code to copy, the codebase carried most of the rules (Experiment A). The guidelines still left two integration gaps in Run 4, because they name helper modules but not their function names. Tip for later work: give the agent the helper signatures along with the guidelines.
- **Limits:** one task, one run per cell, one reviewer. The checklist was written before the runs and is listed above, but the sample is small.

## Human review
- **Reviewed and accepted by:** Pending owner review. Counts were produced by Kiro and can be checked by opening the twelve files in `comparison/`.