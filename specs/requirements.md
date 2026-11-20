# RevoTask Software Requirements Specification (SRS)

| Field | Value |
|---|---|
| Status | Draft for review. Not committed. |
| Primary sources | `specs/PROJECT_BRIEF.md`; the RevoTask assignment, Parts 1-3 (authoritative alongside the brief) |
| Out of scope for this document | Architecture, schemas, folder structure, and code. These belong in `design.md` and `tasks.md`, which are not part of this deliverable. |

## 1. Introduction

### 1.1 Purpose
This document defines testable requirements for RevoTask, a Trello-like task management web application. Each requirement has a unique ID and one or more acceptance criteria. Each acceptance criterion maps to a planned implementation target in Section 7.

### 1.2 Scope
RevoTask lets authenticated users manage boards, columns, and cards. Cards can be moved by drag-and-drop using positive FLOAT order values. Users can comment on cards, receive notifications, search cards, view their assigned tasks, manage their profile, and view board analytics.

### 1.3 Conventions
- **MUST** marks a mandatory requirement. **MAY** marks an optional behavior.
- **[Approved]** means the item comes from `PROJECT_BRIEF.md`, the assignment, or an explicit project decision.
- **[Proposed, not approved]** means the item is a suggestion awaiting a decision. Proposals appear only in Section 8.1 and in the derived assumptions in Section 1.4. Every row of the status-code table in Section 2.3 is approved.
- **[Approved]** decisions that were settled by human review are listed in Section 8.2 (Approved Decisions). They are requirements.
- **[Extension]** marks functionality outside the 26 mandatory endpoints. The only extension is `POST /api/boards/{id}/members` (BOARD-007), approved in UD-24.
- Requirement IDs use the form `CATEGORY-NNN`. Acceptance criterion IDs use the form `CATEGORY-NNN-ACnn`.
- Path parameters are written as `{id}`.
- Requirements and acceptance criteria that depend on an unresolved decision name the decision (written as `Blocked by UD-nn`) and are marked **Blocked**. A blocked criterion cannot be tested until the decision is approved.

### 1.4 Derived assumptions (to confirm)
These inferences are embedded in acceptance criteria. They are not open questions, but they are not stated verbatim in the brief. Confirm or correct them.

- **A-01** A new column or card is appended after the existing ones in its parent, with a positive float `order` (stored in the `position` attribute) greater than the `order` of every non-deleted sibling.
- **A-02** `GET /api/boards/{id}` returns the board with its columns and non-deleted cards, because the required endpoint set has no separate list endpoints for columns or cards.
- **A-03** `DELETE /api/cards/{id}` is a soft delete that sets `deleted_at`. This is implied by the required `deleted_at` field on Card. The deletion scope for the other entities (boards, columns, comments) is approved in UD-18 and UD-23.
- **A-04** Field names in request bodies: board `name`, column `name`, card `title`, comment `content`, user `name`, `email`, and `password`. Card position requests use `column_id` and `order`. Column reorder requests use a `columns` list whose entries have `id` and `order` (approved, UD-20). The response of `PATCH /api/cards/{id}/position` also has the boolean `rebalanced` (approved, UD-06). The public JSON field for a stored position is `order` in every request and response, while the database column and the SQLAlchemy model attribute are `position` and the endpoint path `/api/cards/{id}/position` is unchanged (approved, UD-20). The card assignment field is `assignee_id`: a UUID string to assign or `null` to unassign, accepted only by `PATCH /api/cards/{id}` and never by card creation (approved, UD-08).
- **A-05** Comments are listed by `created_at` ascending. Notifications are listed newest first. Columns, and the cards of a column, are listed by ascending `order`.
- **A-06** A request body containing a field that the endpoint does not accept is rejected with HTTP 400. This includes `password` on `PATCH /api/users/me`.
- **A-07** The JWT is held only in an HttpOnly cookie managed by the Next.js server layer (approved, UD-03). Browser JavaScript never reads or sends the JWT. The Next.js server forwards it to Flask as `Authorization: Bearer <token>`, which is the Flask-JWT-Extended default.
- **A-08** A successful login redirects to `/`.
- **A-09** A card assignee must be a member of the card's board.
- **A-10** Board analytics are displayed within `/boards/[id]`, and columns can be reordered by drag-and-drop on that page.
A-11 (card search matching), A-12 (page architecture), A-13 (completion timestamps and activity behavior), A-14 (comment events, activity window, duplicate membership, and board role), and A-15 (consequences of soft deletion) are approved. They are listed in Section 8.2 and keep their IDs. UD-18 and UD-23 (deletion strategy) are also approved. A-01 to A-10 remain derived assumptions to confirm.

## 2. System Overview

### 2.1 User roles [Approved]
| Role | Description |
|---|---|
| Board Member | A user who belongs to a board and works with its content. |
| Board Administrator | A user who manages a board. Holds all Board Member capabilities plus the five administrator-only operations below. |

Membership and administrator status are **board-specific**. A user can be an administrator on one board and a member on another, and being an administrator on one board grants no privilege on another. The creator of a board becomes that board's Board Administrator (approved, UD-04). Other users join a board as Board Members through the approved extension endpoint (UD-24). The permission table below is approved (UD-05).

| Operation | Board Member | Board Administrator |
|---|---|---|
| View a board, its columns, cards, comments, and analytics | Yes | Yes |
| Create a board (the creator becomes its administrator) | Any authenticated user | Any authenticated user |
| Create columns, rename columns, reorder columns | Yes | Yes |
| Create, edit, move, reorder, and delete cards | Yes | Yes |
| Create comments | Yes | Yes |
| Edit or delete own comments | Yes | Yes |
| Edit or delete another user's comment | No (403) | No (403) |
| **Administrator-only 1:** `PATCH /api/boards/{id}` (rename board) | No (403) | Yes |
| **Administrator-only 2:** `DELETE /api/boards/{id}` (delete board) | No (403) | Yes |
| **Administrator-only 3:** `POST /api/boards/{id}/members` (add member) | No (403) | Yes |
| **Administrator-only 4:** `PATCH /api/columns/{id}` when the body contains `is_done` | No (403) | Yes |
| **Administrator-only 5:** `DELETE /api/columns/{id}` (soft-delete column and its active cards) | No (403) | Yes |

A user who is not a member of the board receives the uniform 404 for every row of this table except board creation.

### 2.2 Architecture summary [Approved]
| Component | Platform |
|---|---|
| Frontend: Next.js App Router, React, TypeScript, Tailwind CSS, react-hot-toast | Vercel |
| Backend: Python Flask, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Marshmallow | Render |
| Database: PostgreSQL | Supabase |

```text
Browser -> Vercel (Next.js) -> HTTPS /api/* with JWT -> Render (Flask) -> SQLAlchemy -> Supabase (PostgreSQL)
```

### 2.3 API conventions
- All endpoints are under `/api` and exchange JSON.
- A successful response body is `{ "data": ... }`. An error response body is `{ "error": "<message>" }`. [Approved]
- Every endpoint except `POST /api/auth/register`, `POST /api/auth/login`, and `GET /api/health` requires a valid JWT. [Approved]
- A success response never contains an `error` key, an error response never contains a `data` key, the `error` value is a non-empty string, and every response that has a body uses `Content-Type: application/json`. [Approved, UD-19]
- A successful POST that creates a resource returns the created resource, and a successful PATCH returns the complete updated public resource. A successful DELETE returns `{ "data": { "id": "<uuid>" } }` with HTTP 200 and never HTTP 204. A successful GET that lists resources returns an array in `data`, which is `[]` when the list is empty. No success response contains a password, a password hash, or a token other than the `access_token` of the login response. [Approved, UD-19]
- The reorder response of `PATCH /api/boards/{id}/columns/reorder` is a specific approved contract: an array of all active columns in ascending `order` (UD-20, COLUMN-004). The response of `PATCH /api/cards/{id}/position` is also a specific approved contract: the moved card with its authoritative `order` and a boolean `rebalanced` (UD-06, CARD-005). The response contract of one endpoint is still pending and is an exception to the general body rules above until it is decided: the pagination shape of `GET /api/notifications` (UD-09). A more specific approved endpoint rule always overrides these general rules. [Approved, UD-19 and UD-20]

| Status | Situation | Label |
|---|---|---|
| 401 | Missing, invalid, or expired JWT | Approved |
| 404 | Authenticated user accesses a board they do not belong to, or any resource inside such a board | Approved |
| 403 | Authenticated board member attempts an administrator-only operation (the five operations in Section 2.1) | Approved (UD-05) |
| 403 | Authenticated non-owner edits or deletes another user's comment on a board they can access | Approved |
| 201 | Comment created | Approved |
| 400 | Comment created with missing content | Approved |
| 404 | An operation targets a soft-deleted column or a soft-deleted card (the rule for their comments is in the approved A-15) | Approved (UD-18, UD-23) |
| 409 | A user who is already a member of the board is added to that board again | Approved (A-14) |
| 404 | An email that belongs to no registered user is added to a board | Approved (A-13) |
| 200 | Successful GET, PATCH, or DELETE, successful login, successful notification mark-as-read, and the health check | Approved (UD-19) |
| 201 | Successful registration, board creation, column creation, card creation, comment creation, and board-member addition | Approved (UD-19) |
| 400 | Any other request validation failure, including a request body that is not valid JSON | Approved (UD-19) |
| 401 | Invalid or unknown login credentials | Approved (UD-19) |
| 404 | A notification belongs to another user, with the same status and body as a notification that does not exist | Approved (UD-08) |
| 400 | `assignee_id` names a user who does not exist or is not a member of the card's board, with an identical body for both cases | Approved (UD-08) |
| 400 | `assignee_id` is sent when creating a card | Approved (UD-08) |
| 400 | A member sends any query parameter to `GET /api/boards/{id}/analytics` | Approved (UD-14) |
| 404 | A resource that does not exist, or a route that does not match | Approved (UD-19) |
| 405 | A method that the route does not support (framework-level, Section 2.4) | Approved (UD-19) |
| 400 | A reorder request lists a column ID that does not exist, belongs to another board, or is soft-deleted, with an identical body for all three cases | Approved (UD-20) |
| 409 | A reorder request whose final `order` values collide with an active column that the request does not list | Approved (UD-20) |
| 409 | Registration or profile update with an email already in use | Approved (UD-19) |
| 415 | An unsupported content type (framework-level, Section 2.4) | Approved (UD-19) |
| 500 | Unhandled server error, with a generic message that exposes no stack trace, SQL statement, token, or internal exception detail | Approved (UD-19) |

### 2.4 Authorization check order [Approved, UD-05]
Every protected resource operation MUST apply these checks in this order and stop at the first one that fails:

1. **Authentication.** A missing, invalid, or expired JWT returns HTTP 401.
2. **Resource and membership.** A missing resource, a soft-deleted column or card, or a board the caller is not a member of returns the uniform HTTP 404. The status and body do not differ between a resource that does not exist and one the caller may not access.
3. **Permission.** An authenticated board member who lacks the required permission (one of the five administrator-only operations, or comment ownership) returns HTTP 403.
4. **Validation and conflict.** Request validation failures return HTTP 400, and semantic conflicts return HTTP 409.

Rules that follow from the order:
- A non-member never receives 403, whatever the request body.
- A member without the permission receives 403 before any field is validated, so an invalid, empty, or unchanged body does not change the answer. For a `PATCH /api/columns/{id}` body that contains the `is_done` key, a non-administrator receives 403 whatever the value, and a mixed body (for example `name` together with `is_done`) is rejected as a whole with no field applied.
- A soft-deleted column or card returns 404 to administrators and members alike, so a member's `DELETE /api/columns/{id}` on an already soft-deleted column returns 404, not 403.
- A rejected request changes no row (BOARD-006-AC07).

**Exception for framework-level parsing.** A request that cannot be parsed or routed may be rejected earlier by the framework: a body that is not valid JSON (HTTP 400), an unsupported content type (HTTP 415), an unsupported method (HTTP 405), or a route that does not match, including a path ID that is not a valid UUID (HTTP 404). These responses depend only on the shape of the request, never on whether the resource exists or on the caller's membership, so the uniform 404 rule for resource access is not weakened.

## 3. Backend Requirements

### 3.0 Endpoint coverage
| Endpoint | Requirement |
|---|---|
| POST /api/auth/register | AUTH-001 |
| POST /api/auth/login | AUTH-002 |
| POST /api/boards | BOARD-001 |
| GET /api/boards | BOARD-002 |
| GET /api/boards/{id} | BOARD-003 |
| PATCH /api/boards/{id} | BOARD-004 |
| DELETE /api/boards/{id} | BOARD-005 |
| POST /api/boards/{id}/columns | COLUMN-001 |
| PATCH /api/columns/{id} | COLUMN-002 |
| DELETE /api/columns/{id} | COLUMN-003 |
| PATCH /api/boards/{id}/columns/reorder | COLUMN-004 |
| POST /api/columns/{id}/cards | CARD-002 |
| PATCH /api/cards/{id} | CARD-003 |
| DELETE /api/cards/{id} | CARD-004 |
| PATCH /api/cards/{id}/position | CARD-005 |
| GET /api/cards?assignee=me | CARD-007 |
| POST /api/cards/{id}/comments | COMMENT-001 |
| GET /api/cards/{id}/comments | COMMENT-002 |
| PATCH /api/comments/{id} | COMMENT-003 |
| DELETE /api/comments/{id} | COMMENT-004 |
| GET /api/notifications | NOTIF-001 |
| PATCH /api/notifications/{id}/read | NOTIF-002 |
| GET /api/boards/{id}/analytics | ANALYTICS-001 |
| GET /api/users/me | USER-001 |
| PATCH /api/users/me | USER-002 |
| GET /api/health | API-003 |

The 26 endpoints above are mandatory and are unchanged. The table below lists approved extensions. They are not part of the 26 and are counted separately. No other membership endpoint is part of this specification.

| Extension endpoint | Requirement | Status |
|---|---|---|
| POST /api/boards/{id}/members | BOARD-007 | [Extension], approved (UD-24) |

### 3.1 Authentication (AUTH)

### AUTH-001 User registration
`POST /api/auth/register` MUST create a user account from a name, an email, and a password.

**Acceptance criteria**
- **AUTH-001-AC01** Given a name, a unique email, and a password, the request returns HTTP 201 and `data` contains the user's `id`, `name`, and `email`.
- **AUTH-001-AC02** The response body contains no `password` key and no password hash.
- **AUTH-001-AC03** If `name`, `email`, or `password` is missing or empty, the request returns HTTP 400 with an `error` message and no user is created.
- **AUTH-001-AC04** If the email already belongs to a user, the request returns HTTP 409 with an `error` message and the existing user is unchanged.
- **AUTH-001-AC05** If the email is not a syntactically valid email address, the request returns HTTP 400.

### AUTH-002 User login
`POST /api/auth/login` MUST exchange valid credentials for a JWT. The response is HTTP 200 with `{ "data": { "access_token": "<jwt>" } }` (approved, UD-19). The response is consumed by the Next.js authentication handler on the server and never by browser code (FRONT-023). It contains no refresh token, and no authentication endpoint is added to the Flask API. The Next.js server MAY derive the session expiry from the JWT `exp` claim, and the session interface MAY expose a non-sensitive `expires_at` value to the browser, but never the JWT. The token lifetime (UD-01) and the refresh policy (UD-02) are not decided here.

**Acceptance criteria**
- **AUTH-002-AC01** Given the email and password of a registered user, the request returns HTTP 200 and `data` is exactly `{ "access_token": "<jwt>" }`, where the value is a non-empty JWT string.
- **AUTH-002-AC02** Given a registered email and a wrong password, the request returns HTTP 401 with an `error` message and no token.
- **AUTH-002-AC03** Given an unregistered email, the request returns HTTP 401 with the same `error` message as AUTH-002-AC02, so the response does not reveal whether the email exists.
- **AUTH-002-AC04** If `email` or `password` is missing, the request returns HTTP 400.
- **AUTH-002-AC05** The successful login response has no key other than `access_token` in `data`, and in particular no `refresh_token`, no user profile, and no password or hash. The URL map contains no token-refresh route.

### AUTH-003 JWT expiry and rejection
Access tokens MUST carry an expiry. Protected endpoints MUST reject missing, invalid, and expired tokens with HTTP 401. The token lifetime and refresh strategy are unresolved (UD-01, UD-02).

**Acceptance criteria**
- **AUTH-003-AC01** A token issued by login decodes to a payload with an `exp` claim later than its issue time.
- **AUTH-003-AC02** A request to a protected endpoint with an expired token returns HTTP 401 with an `error` message.
- **AUTH-003-AC03** A request to a protected endpoint with no `Authorization` header returns HTTP 401 with an `error` message.
- **AUTH-003-AC04** A request to a protected endpoint with a malformed token or a token signed with a different key returns HTTP 401 with an `error` message.
- **AUTH-003-AC05** The JWT signing key is read from an environment variable, and the source repository contains no literal signing key.
- **AUTH-003-AC06** Flask accepts the JWT only from the `Authorization: Bearer` header. A request to a protected endpoint that carries a valid JWT only in a cookie and no `Authorization` header returns HTTP 401.

### AUTH-004 Endpoint protection
Every endpoint other than register, login, and health MUST require a valid JWT.

**Acceptance criteria**
- **AUTH-004-AC01** For each protected endpoint in Section 3.0, a request with no token returns HTTP 401.
- **AUTH-004-AC02** `POST /api/auth/register`, `POST /api/auth/login`, and `GET /api/health` do not return HTTP 401 when called with no token.

### 3.2 Board management and membership (BOARD)

### BOARD-001 Create board
`POST /api/boards` MUST create a board for the authenticated user. The creator MUST become the Board Administrator of that board (approved, UD-04).

**Acceptance criteria**
- **BOARD-001-AC01** Given a non-empty `name`, the request returns HTTP 201 and `data` contains the board `id` and `name`.
- **BOARD-001-AC02** If `name` is missing or empty, the request returns HTTP 400 and no board is created.
- **BOARD-001-AC03** After creating a board, the creating user receives HTTP 200 from `GET /api/boards/{id}` for that board.
- **BOARD-001-AC04** The creator is a Board Administrator of the new board. After the creator adds a column, the creator receives HTTP 200 from `PATCH /api/columns/{id}` with `is_done` set to true, which is an administrator-only operation.

### BOARD-002 List boards
`GET /api/boards` MUST return only boards that the authenticated user belongs to.

**Acceptance criteria**
- **BOARD-002-AC01** The response is HTTP 200 and `data` contains every board where the user is a member.
- **BOARD-002-AC02** Boards where the user is not a member are absent from `data`.
- **BOARD-002-AC03** A user with no boards receives HTTP 200 and an empty list in `data`.

### BOARD-003 Get board
`GET /api/boards/{id}` MUST return the board with its columns, its cards, and its members to its members. The member list is part of this response and populates the card assignee selector. No separate member-list endpoint exists (approved, UD-08 and UD-24).

**Acceptance criteria**
- **BOARD-003-AC01** A member receives HTTP 200 with the board, its columns ordered by ascending `order`, and each column's cards ordered by ascending `order`.
- **BOARD-003-AC02** Cards with a non-null `deleted_at` are absent from the response.
- **BOARD-003-AC03** An authenticated user who is not a member receives HTTP 404 with an `error` message.
- **BOARD-003-AC04** A request for a board ID that does not exist returns HTTP 404 with the same `error` message as BOARD-003-AC03.
- **BOARD-003-AC05** Each column in the response includes a boolean `is_done`.
- **BOARD-003-AC06** The response includes the requesting user's role on the board, which is `administrator` for a Board Administrator and `member` for a Board Member (A-14).
- **BOARD-003-AC07** Columns with a non-null `deleted_at` are absent from the response, and so are all cards that belong to them (approved, UD-18).
- **BOARD-003-AC08** The response contains `members`, a list with one entry for each member of the board, including the requesting user, ordered by `name` ascending and then by `id`.
- **BOARD-003-AC09** Each entry in `members` has exactly the keys `id` (a UUID string) and `name`, and no email address, password or password hash, role, or other profile field.
- **BOARD-003-AC10** The `members` list of a board never contains a user who belongs only to another board, and a user who is not a member of the board receives HTTP 404 and no member data.
- **BOARD-003-AC11** Adding `members` removes no previously required field: the response still contains the board `id` and `name`, the columns with `is_done`, the cards with `assignee_id`, and the requesting user's `role` (BOARD-003-AC05, AC06).
- **BOARD-003-AC12** After `POST /api/boards/{id}/members` adds a user, the user appears in the board's `members` list in a following `GET /api/boards/{id}`.

### BOARD-004 Update board
`PATCH /api/boards/{id}` MUST update a board's name. Only a Board Administrator of the board may rename it (approved, UD-05).

**Acceptance criteria**
- **BOARD-004-AC01** A Board Administrator sending a non-empty `name` receives HTTP 200 and `data` contains the new name.
- **BOARD-004-AC02** A Board Administrator sending an empty or missing `name` receives HTTP 400 and the stored name is unchanged.
- **BOARD-004-AC03** An authenticated user who is not a member receives HTTP 404, and the response is identical to the one for a board that does not exist.
- **BOARD-004-AC04** A Board Member who is not an administrator of the board receives HTTP 403 and the name is unchanged, including when the body is empty or invalid (approved, UD-05).

### BOARD-005 Delete board
`DELETE /api/boards/{id}` MUST hard-delete a board (approved, UD-18). Only a Board Administrator of the board may delete it (approved, UD-05). The same transaction MUST remove every dependent row: memberships, columns (including soft-deleted ones), cards (including soft-deleted ones), comments, notifications that refer to the board or its cards, and activity events of the board. Users are not deleted. The deletion order or foreign-key strategy MUST be defined explicitly in the schema or the service, and MUST NOT depend on database defaults.

**Acceptance criteria**
- **BOARD-005-AC01** A Board Administrator receives HTTP 200 with `data` exactly `{ "id": "<the deleted board's ID>" }` (approved, UD-19), and a following `GET /api/boards/{id}` by that user returns HTTP 404.
- **BOARD-005-AC02** An authenticated user who is not a member receives HTTP 404, the response is identical to the one for a board that does not exist, and the board still exists.
- **BOARD-005-AC03** A Board Member who is not an administrator of the board receives HTTP 403 (approved, UD-05), and the board and all its dependent rows (memberships, columns, cards, comments, notifications, activity events) are unchanged.
- **BOARD-005-AC04** For a board that holds every kind of dependent row, the request returns HTTP 200, and afterward no membership, column, card, comment, notification, or activity-event row that belongs to the board remains in the database. The dependent rows include columns and cards that were already soft-deleted.
- **BOARD-005-AC05** The request does not fail with a foreign-key violation or HTTP 500 when the board contains soft-deleted columns, soft-deleted cards, comments, notifications, and activity events.
- **BOARD-005-AC06** The deletion runs in one transaction. When a failure is forced after some dependent rows were removed, the board and all its dependent rows are unchanged afterward.
- **BOARD-005-AC07** The deletion removes no row that belongs to another board and no row in `users`.
- **BOARD-005-AC08** The deletion strategy is explicit: either every foreign key that leads to `boards` declares its delete behavior in a Flask-Migrate migration, or the service deletes the dependent rows in a documented order. A test that deletes a fully populated board passes against a database created by `flask db upgrade`.

### BOARD-006 Board-specific authorization
Membership and administrator status MUST be evaluated per board. The same check MUST apply to every board-scoped endpoint. The permission table in Section 2.1 and the check order in Section 2.3 are approved (UD-05). Exactly five operations are administrator-only: `PATCH /api/boards/{id}`, `DELETE /api/boards/{id}`, `POST /api/boards/{id}/members`, `PATCH /api/columns/{id}` when the body contains `is_done`, and `DELETE /api/columns/{id}`. All other board-scoped operations are open to every board member.

**Acceptance criteria**
- **BOARD-006-AC01** Given a user who is an administrator of board A and a non-administrator member of board B, each of the five administrator-only operations succeeds on board A and returns HTTP 403 on board B, and nothing on board B changes.
- **BOARD-006-AC02** For each board-scoped endpoint (board update, board delete, member add, columns, column reorder, cards, card position, comments, analytics), a non-member of the board receives HTTP 404.
- **BOARD-006-AC03** Each of the five administrator-only operations returns HTTP 403 to a Board Member who is not an administrator of that board, and nothing changes (approved, UD-05).
- **BOARD-006-AC04** A Board Member who is not an administrator succeeds at each member-allowed operation: viewing the board, columns, cards, comments, and analytics; creating and renaming columns; reordering columns; creating, editing, moving, reordering, and deleting cards; creating comments; and editing or deleting their own comments.
- **BOARD-006-AC05** For each board-scoped endpoint, the response sent to a non-member (status and body) is identical to the response sent for a resource ID that does not exist.
- **BOARD-006-AC06** The checks run in the order defined in Section 2.3: HTTP 401 for missing or invalid authentication, then 404 for a missing resource or a non-member, then 403 for a member without the required permission, then 400 or 409. A non-member who sends an administrator-only operation receives 404, not 403. A member who sends an administrator-only operation with an invalid body receives 403, not 400.
- **BOARD-006-AC07** A request rejected with 400, 401, 403, 404, or 409 changes no row, including `updated_at` values, and creates no activity event or notification. A mixed request is rejected as a whole, with no partial update.

### BOARD-007 Add board member by email [Extension]
`POST /api/boards/{id}/members` MUST let a Board Administrator add an existing registered user to the board as a Board Member, identified by email. Only administrators may call it (approved, UD-24 and UD-05). This endpoint is an approved extension (UD-24) outside the 26 mandatory endpoints. It relies on the board creator being an administrator (UD-04). The request body is `{ "email": "..." }`. No other membership endpoint (listing, removal, or role change) is part of this specification.

**Acceptance criteria**
- **BOARD-007-AC01** A Board Administrator sending the email of a registered user who is not yet a member receives HTTP 201 and `data` contains the user's `id`, `name`, and `email` with no password. After this, the added user receives HTTP 200 from `GET /api/boards/{id}` and sees the board in `GET /api/boards`.
- **BOARD-007-AC02** A Board Member who is not an administrator of the board receives HTTP 403 and no membership is created, including when the body is empty, invalid, or contains extra fields such as `role` (approved, UD-05).
- **BOARD-007-AC03** An authenticated user who is not a member of the board receives HTTP 404, and the response is identical for a board that does not exist.
- **BOARD-007-AC04** Adding an email that already belongs to a member of the same board returns HTTP 409 (approved, A-14) and the board still has one membership for that user.
- **BOARD-007-AC05** An email that belongs to no registered user returns HTTP 404 with an `error` message and no membership is created.
- **BOARD-007-AC06** A Board Administrator sending a missing, empty, or syntactically invalid `email` receives HTTP 400. A Board Administrator sending a body that contains any field other than `email`, such as `role`, receives HTTP 400.
- **BOARD-007-AC07** A request with no token returns HTTP 401.
- **BOARD-007-AC08** A user added to board A receives HTTP 404 from `GET /api/boards/{id}` for board B, where they were not added.
- **BOARD-007-AC09** A user added by this endpoint is a Board Member and not an administrator, so an administrator-only operation on that board returns HTTP 403 for them.
- **BOARD-007-AC10** The Flask URL map contains exactly one route matching `/api/boards/{id}/members`, and it accepts only POST.

### 3.3 Column management (COLUMN)

### COLUMN-001 Create column
`POST /api/boards/{id}/columns` MUST create a column in the board.

**Acceptance criteria**
- **COLUMN-001-AC01** Given a non-empty `name`, the request returns HTTP 201 and `data` contains a UUID `id`, the `name`, and a positive float `order`.
- **COLUMN-001-AC02** The new column's `order` is greater than the `order` of every non-deleted column in the board (A-01).
- **COLUMN-001-AC03** A missing or empty `name` returns HTTP 400 and no column is created.
- **COLUMN-001-AC04** A non-member of the board receives HTTP 404.
- **COLUMN-001-AC05** Creating a column acquires the same board row lock as the reorder endpoint and computes the new `order` after taking it, so a column creation that runs concurrently with a reorder never produces two active columns with the same `order` (approved, UD-20).

### COLUMN-002 Rename column
`PATCH /api/columns/{id}` MUST update a column's name for any board member. It MUST also let a Board Administrator mark or unmark the column as a done (completed) column through a boolean `is_done` field (approved, UD-12; field name in A-13). A request whose body contains the `is_done` key is an administrator-only operation (approved, UD-05). For a Board Member who is not an administrator, the key alone triggers HTTP 403 before any field is validated, whatever its value. When an administrator sends an `is_done` value equal to the column's stored value, the completion-state update is a no-op (approved, UD-05).

**Acceptance criteria**
- **COLUMN-002-AC01** A member sending a non-empty `name` receives HTTP 200 and `data` contains the new name.
- **COLUMN-002-AC02** An empty or missing `name` returns HTTP 400 and the stored name is unchanged.
- **COLUMN-002-AC03** A non-member of the column's board receives HTTP 404.
- **COLUMN-002-AC04** A column ID that does not exist returns HTTP 404.
- **COLUMN-002-AC05** A Board Administrator sending `is_done: true` receives HTTP 200 and `data` contains `is_done` true, and a following `GET /api/boards/{id}` shows that column with `is_done` true.
- **COLUMN-002-AC06** A Board Member who is not an administrator and sends a body that contains the `is_done` key receives HTTP 403 whatever the value is (true, false, equal to the stored value, or invalid), and the column's `is_done` is unchanged.
- **COLUMN-002-AC07** A Board Administrator sending a non-boolean `is_done` value receives HTTP 400 and the column is unchanged.
- **COLUMN-002-AC08** When an administrator marks a column done, each non-deleted card already in the column gets `completed_at` equal to the time of the request (A-13).
- **COLUMN-002-AC09** When an administrator unmarks a done column, `completed_at` is set to null for each card in the column (A-13).
- **COLUMN-002-AC10** A request from an administrator or a member for a soft-deleted column, with `name` or `is_done`, returns HTTP 404 and the column is unchanged (approved, UD-18).
- **COLUMN-002-AC11** A Board Member who is not an administrator and sends `name` together with `is_done` receives HTTP 403, and neither the name, `is_done`, `updated_at`, nor any card's `completed_at` changes (approved, UD-05).
- **COLUMN-002-AC12** When a Board Administrator sends `is_done` equal to the column's stored value (true on a done column, false on an active column), the response is HTTP 200, no card's `completed_at` changes, and no activity event or notification is created. Sending `is_done: true` twice in a row leaves every `completed_at` value from the first request unchanged (approved, UD-05).
- **COLUMN-002-AC13** When a Board Administrator sends `name` together with an `is_done` value equal to the stored value, a valid `name` is applied and the completion-state update is a no-op. A request that contains only the unchanged `is_done` modifies no field and no `updated_at`.
- **COLUMN-002-AC14** When `is_done` changes, the column update and the `completed_at` updates of its cards run in one transaction. When a failure is forced after the column was updated and before the cards were updated, the column and all its cards are unchanged afterward (approved, UD-05).

### COLUMN-003 Delete column
`DELETE /api/columns/{id}` MUST soft-delete a column and all of its currently active cards in one database transaction (approved, UD-18 and UD-23). Only a Board Administrator of the column's board may delete a column (approved, UD-05). The column and the affected cards MUST receive the same UTC `deleted_at` timestamp. The column row and the foreign key from each card to its column MUST be preserved: the column is not hard-deleted and its cards are not cascade-deleted. No endpoint restores a soft-deleted column or card.

**Acceptance criteria**
- **COLUMN-003-AC01** A Board Administrator receives HTTP 200 with `data` exactly `{ "id": "<the deleted column's ID>" }` (approved, UD-19), and `GET /api/boards/{id}` no longer lists the column.
- **COLUMN-003-AC02** A non-member of the column's board receives HTTP 404, the response is identical to the one for a column that does not exist, and the column still exists.
- **COLUMN-003-AC03** Deleting a column that contains 3 non-deleted cards returns HTTP 200, and afterward the column row and all 3 card rows still exist with a non-null `deleted_at`.
- **COLUMN-003-AC04** The column and the affected cards have identical `deleted_at` values, and the value is a UTC timestamp.
- **COLUMN-003-AC05** A card that was already soft-deleted before the column was deleted keeps its original `deleted_at` value. A card in another column of the same board is unchanged.
- **COLUMN-003-AC06** After deletion, every card of the column still has its original `column_id`, and the column row it references still exists. No card or column row is removed from the database.
- **COLUMN-003-AC07** The deletion is one transaction. When a failure is forced after the column was marked deleted and before the cards were marked, the column and all its cards are unchanged afterward.
- **COLUMN-003-AC08** After deletion, `GET /api/boards/{id}` lists neither the column nor any of its cards, and `GET /api/cards?assignee=me` lists none of its cards.
- **COLUMN-003-AC09** Sending `DELETE /api/columns/{id}` for an already soft-deleted column returns HTTP 404 to an administrator and to a member, and no `deleted_at` value changes.
- **COLUMN-003-AC10** After deletion, `PATCH /api/columns/{id}` (including `is_done`), `POST /api/columns/{id}/cards`, and any card operation on its cards return HTTP 404, and nothing changes.
- **COLUMN-003-AC11** After deletion, the `completed_at` and assignee values of the column's cards are unchanged (approved, A-15), and no activity event or notification is created or removed (approved, UD-08).
- **COLUMN-003-AC12** The URL map contains no route that restores or undeletes a column or a card.
- **COLUMN-003-AC13** A Board Member who is not an administrator of the column's board receives HTTP 403 (approved, UD-05). The column row, every card of the column, and all their `deleted_at` values, `updated_at` values, and `column_id` values are unchanged, and no activity event is created.
- **COLUMN-003-AC14** A user who is an administrator of another board and only a member of the column's board receives HTTP 403, and nothing changes.
- **COLUMN-003-AC15** Deleting a column takes the same board row lock as the reorder endpoint, so a deletion that runs concurrently with a reorder of the same board never leaves a changed `order` on the soft-deleted column and never fails with a server error (approved, UD-20).

### COLUMN-004 Reorder columns
`PATCH /api/boards/{id}/columns/reorder` MUST persist a new column order using positive FLOAT `order` values (approved, UD-20). It adds no endpoint, and any authenticated board member may call it, because it is not one of the five administrator-only operations. The request body is a JSON object with exactly the key `columns`, a non-empty array whose entries each have exactly `id` (a UUID) and `order` (a positive, finite JSON number):

```json
{ "columns": [ { "id": "<column-uuid>", "order": 1536.0 } ] }
```

A partial list is allowed. Each column ID and each `order` value may appear at most once in the request. After authentication and the board membership check, the service layer takes a row lock on the board, re-reads the board's active columns, applies the submitted values in memory, and validates that the final `order` values of all active columns are positive, finite, and pairwise distinct. It then writes all changes in one transaction. A submitted value that collides with an unlisted active column returns HTTP 409, and unlisted columns are never renumbered silently. The success response is HTTP 200 with every active column of the board in ascending `order`:

```json
{ "data": [ { "id": "<column-uuid>", "name": "To Do", "order": 1024.0, "is_done": false } ] }
```

A request whose values all equal the stored values is a no-op. An ordinary drag sends only the moved column with a value between its neighbors. When no distinct value exists between two neighbors, the frontend may normalize by sending every active column it has loaded, each once, through this same endpoint. There is no flag, endpoint, or response field for normalization, and the server treats such a request like any other (see the limitation in AC27).

**Acceptance criteria**
- **COLUMN-004-AC01** A valid reorder request from any board member returns HTTP 200, and a following `GET /api/boards/{id}` lists the active columns in ascending `order`, using the submitted value for each listed column and the stored value for every unlisted column.
- **COLUMN-004-AC02** An `order` that is 0, a negative number, a boolean, a string, null, `NaN`, `Infinity`, or a value that cannot be stored as a finite positive float (for example `1e400`, which parses as infinity, or `1e-400`, which parses as 0) returns HTTP 400, never HTTP 500, and no `order` value changes. No maximum `order` value is imposed.
- **COLUMN-004-AC03** A request that lists a column ID that does not exist, that belongs to another board, or that is soft-deleted returns HTTP 400 with the same generic `error` body for all three cases, so the response does not reveal whether the column exists, and no `order` value changes.
- **COLUMN-004-AC04** A non-member of the board receives HTTP 404, and the response is identical to the one for a board that does not exist.
- **COLUMN-004-AC05** The Column position attribute is declared as a SQLAlchemy `db.Float` column.
- **COLUMN-004-AC06** A request that lists a soft-deleted column returns HTTP 400 and no `order` value changes (approved, A-15), with the same response as in AC03. The `order` values of soft-deleted columns are never modified.
- **COLUMN-004-AC07** The request body must be a JSON object with exactly the key `columns`, a non-empty array of entries that each have exactly `id` and `order`. A body that is not valid JSON, is not an object, lacks `columns`, has an empty or non-array `columns`, has an extra top-level key (such as `name`), or has an entry with an extra key (such as `name`, `is_done`, or `position`) returns HTTP 400 and no column changes.
- **COLUMN-004-AC08** An entry whose `id` is not a valid UUID returns HTTP 400, and a request that contains the same column `id` twice returns HTTP 400. No column changes in either case.
- **COLUMN-004-AC09** A request that contains the same `order` value for two entries returns HTTP 400 and no column changes.
- **COLUMN-004-AC10** With three active columns A (1024.0), B (2048.0), and C (3072.0), a request with the single entry C at 1536.0 returns HTTP 200, and a following `GET /api/boards/{id}` lists A, C, B. The `order` and `updated_at` of A and B are unchanged.
- **COLUMN-004-AC11** A request that lists two columns applies both new `order` values together. A request that exchanges the `order` values of two columns succeeds and does not count as a collision.
- **COLUMN-004-AC12** A submitted `order` that equals the stored `order` of an active column that the request does not list returns HTTP 409 with an `error` message, and no column changes.
- **COLUMN-004-AC13** After every successful request, the `order` values of all active columns are positive, finite, and pairwise distinct, and every unlisted column keeps its exact stored `order`: an ordinary partial request never renumbers other columns.
- **COLUMN-004-AC14** The changes of one request are atomic. When a failure is forced after some columns were updated, no `order` value is changed afterward, and a request rejected with 400 or 409 changes nothing.
- **COLUMN-004-AC15** The service takes a row lock on the board (a `SELECT ... FOR UPDATE` on the board row) before it reads the board's active columns, and it validates against the columns read after the lock.
- **COLUMN-004-AC16** When two requests run concurrently and each sets a different column to the same final `order`, exactly one returns HTTP 200 and the other HTTP 409, and the final `order` values are pairwise distinct. Two concurrent requests that do not collide both return HTTP 200, and both changes are present afterward.
- **COLUMN-004-AC17** A reorder that runs concurrently with the creation or deletion of a column on the same board is serialized with it: the active columns never share an `order`, no `order` is written to a soft-deleted column, and a request that names a column soft-deleted by the earlier transaction returns HTTP 400.
- **COLUMN-004-AC18** The HTTP 200 response contains every active column of the board, not only the submitted ones, in ascending `order`, and no soft-deleted column. Each entry contains at least `id`, `name`, `order` (a positive float), and `is_done`, and no key named `position`, `deleted_at`, or `rebalanced`.
- **COLUMN-004-AC19** The `id`, `name`, `order`, and `is_done` values in the response equal the values of the same columns in a following `GET /api/boards/{id}`.
- **COLUMN-004-AC20** When every submitted `order` equals the stored value, the response is HTTP 200 with the complete array, no column row is updated (the recorded SQL has no `UPDATE` of columns), and no `updated_at` changes.
- **COLUMN-004-AC21** Only a column whose `order` changed gets a new `updated_at`, equal to the time of the request. The other columns keep their `updated_at`.
- **COLUMN-004-AC22** A reorder creates no activity event and no notification, and it changes no `is_done`, `completed_at`, or `deleted_at` value.
- **COLUMN-004-AC23** A Board Administrator and a Board Member who is not an administrator both receive HTTP 200 for a valid request, and a member never receives HTTP 403.
- **COLUMN-004-AC24** A request with no token returns HTTP 401 even when the body is invalid. A non-member with an invalid body receives HTTP 404, and a member with an invalid body receives HTTP 400 (Section 2.4).
- **COLUMN-004-AC25** The public field is `order`: the response and `GET /api/boards/{id}` expose the stored `position` as `order`, and a request entry that uses the key `position` instead of `order` returns HTTP 400 (A-06).
- **COLUMN-004-AC26** A request that lists every active column of the board exactly once with pairwise distinct positive values is applied like any other request: it returns HTTP 200 with the complete array, and the request contains no normalization flag.
- **COLUMN-004-AC27** Limitation of the shared payload: the server cannot tell a full normalization request from an ordinary partial request that lists every column. It detects only these stale cases, and in each nothing is applied: a listed column that was soft-deleted or does not exist returns HTTP 400, and a value that collides with a column the request does not list returns HTTP 409. A column that another user added after the client loaded the board is not detected: the request succeeds when the final values are distinct, and the added column keeps its stored `order`.

### COLUMN-005 Column data model
The Column model MUST define a Boolean `is_done` field that marks a done (completed) column (approved, UD-12 and A-13). It MUST also define a nullable UTC `deleted_at` timestamp for soft deletion (approved, UD-18).

**Acceptance criteria**
- **COLUMN-005-AC01** Introspection of the Column model shows `is_done` is a Boolean column that is not nullable and has a default of false.
- **COLUMN-005-AC02** A column created through `POST /api/boards/{id}/columns` has `is_done` equal to false in the response `data`.
- **COLUMN-005-AC03** A Flask-Migrate migration adds `is_done`, `flask db upgrade` on an empty database completes without error, and on a database with existing columns every existing column gets `is_done` equal to false.
- **COLUMN-005-AC04** Introspection of the Column model shows `deleted_at` is a nullable, timezone-aware date-time column, and a newly created column has `deleted_at` equal to null.
- **COLUMN-005-AC05** A Flask-Migrate migration adds `deleted_at`, `flask db upgrade` completes without error, and on a database with existing columns every existing column gets `deleted_at` equal to null.
- **COLUMN-005-AC06** No column response includes `deleted_at` as a non-null value, because soft-deleted columns are never returned by any endpoint.
- **COLUMN-005-AC07** Every column representation in an API response contains `order`, equal to the stored `position` value, and contains no key named `position` (approved, UD-20).

### 3.4 Card management and positioning (CARD)

### CARD-001 Card data model
The Card model MUST define a UUID primary key, `created_at`, `updated_at`, a nullable UTC `deleted_at`, a `position` attribute stored with `db.Column(db.Float)` (exposed through the API as `order`), a nullable `completed_at` timestamp (approved, UD-12), and a non-null foreign key `column_id` that references the Column model (approved, UD-23). Cards are soft-deleted (approved, UD-18).

**Acceptance criteria**
- **CARD-001-AC01** A newly created card has a primary key that parses as a valid UUID, and the key is generated without client input.
- **CARD-001-AC02** A newly created card has a non-null `created_at`.
- **CARD-001-AC03** After a card is updated, its `updated_at` is later than its `created_at`.
- **CARD-001-AC04** A newly created card has `deleted_at` equal to null.
- **CARD-001-AC05** Introspection of the Card model shows the position column is a SQLAlchemy `Float` type declared with `db.Column(db.Float)`.
- **CARD-001-AC06** A Flask-Migrate migration creates the card table with these columns, and `flask db upgrade` on an empty database completes without error.
- **CARD-001-AC07** Introspection of the Card model shows `completed_at` is a nullable date-time column, and a card created in a non-done column has `completed_at` equal to null.
- **CARD-001-AC08** Introspection of the Card model shows `deleted_at` is a nullable, timezone-aware date-time column.
- **CARD-001-AC09** Introspection of the database created by `flask db upgrade` shows a non-null foreign key from the card's `column_id` to the Column model's primary key.
- **CARD-001-AC10** After any sequence of the endpoints in Section 3.0, no card with a null `deleted_at` references a column with a non-null `deleted_at`.
- **CARD-001-AC11** Every card representation in an API response contains `order`, equal to the stored `position` value, and contains no key named `position` (approved, UD-20).

### CARD-002 Create card
`POST /api/columns/{id}/cards` MUST create a card in the column.

**Acceptance criteria**
- **CARD-002-AC01** Given a non-empty `title`, the request returns HTTP 201 and `data` contains a UUID `id`, the `title`, the column ID, and a positive float `order`.
- **CARD-002-AC02** The new card's `order` is greater than the `order` of every non-deleted card in the column (A-01).
- **CARD-002-AC03** A missing or empty `title` returns HTTP 400 and no card is created.
- **CARD-002-AC04** A non-member of the column's board receives HTTP 404.
- **CARD-002-AC05** A column ID that does not exist returns HTTP 404.
- **CARD-002-AC06** A card created in a done column has `completed_at` equal to its creation time (A-13).
- **CARD-002-AC07** The ID of a soft-deleted column returns HTTP 404 and no card is created (approved, UD-18).
- **CARD-002-AC08** A request body that contains `assignee_id`, with any value including `null`, returns HTTP 400, no card is created, and no notification is created. Card creation is title-only (approved, UD-08).
- **CARD-002-AC09** A successfully created card has `assignee_id` equal to null in the response `data`, and its creation creates no notification (approved, UD-08).
- **CARD-002-AC10** Creating a card takes the same row lock on the destination column as the card move endpoint and computes the new `order` after taking it, so a creation that runs concurrently with a move into the same column never produces two active cards with the same `order` (approved, UD-06).

### CARD-003 Update card
`PATCH /api/cards/{id}` MUST update card details, including the assignee. It is the only way to assign or unassign an existing card (approved, UD-08). The body field `assignee_id` is a UUID string to assign a board member or `null` to unassign, and omitting `assignee_id` leaves the current assignment unchanged. A `assignee_id` that equals the stored value is an unchanged assignment: it creates no notification, no activity event, and does not change `updated_at` by itself. Additional card fields are unresolved (UD-07).

**Acceptance criteria**
- **CARD-003-AC01** A member sending a non-empty `title` receives HTTP 200, `data` contains the new title, and `updated_at` increases.
- **CARD-003-AC02** An empty `title` returns HTTP 400 and the stored title is unchanged.
- **CARD-003-AC03** Sending `assignee_id` equal to the ID of a member of the card's board returns HTTP 200, `data` contains that `assignee_id`, and the card appears in that member's `GET /api/cards?assignee=me` response (A-09). Any board member may assign any board member.
- **CARD-003-AC04** Sending an `assignee_id` for a user who is not a member of the card's board, or for a user ID that does not exist, returns HTTP 400 with an identical response body for both cases, and the assignee is unchanged (approved, UD-08).
- **CARD-003-AC05** A request body containing `id`, `created_at`, or `deleted_at` returns HTTP 400 and no field changes.
- **CARD-003-AC06** A non-member of the card's board receives HTTP 404.
- **CARD-003-AC07** A request for a soft-deleted card returns HTTP 404 and the card is unchanged (approved, UD-18).
- **CARD-003-AC08** Sending `assignee_id: null` on an assigned card returns HTTP 200, `data` contains `assignee_id` equal to null, and the card is absent from the former assignee's `GET /api/cards?assignee=me` response (approved, UD-08).
- **CARD-003-AC09** A request that omits `assignee_id` leaves the card's assignee unchanged, including when other fields change.
- **CARD-003-AC10** Sending an `assignee_id` equal to the card's current value (including `null` on an unassigned card) returns HTTP 200, creates no notification, creates no activity event, and leaves `updated_at` unchanged when it is the only field sent. When it is sent together with another changed field, `updated_at` changes only because of that field.
- **CARD-003-AC11** An `assignee_id` that is neither a valid UUID string nor `null` returns HTTP 400 and the card is unchanged.
- **CARD-003-AC12** Every card in a response from `PATCH /api/cards/{id}`, `GET /api/boards/{id}`, and `POST /api/columns/{id}/cards` includes `assignee_id` as a UUID string or null.

### CARD-004 Delete card
`DELETE /api/cards/{id}` MUST remove a card from all views by setting `deleted_at` to the UTC time of the request (approved, UD-18). The card row, its `column_id`, its `completed_at`, its comments, and its activity events are kept. No endpoint restores a soft-deleted card.

**Acceptance criteria**
- **CARD-004-AC01** A member receives HTTP 200 with `data` exactly `{ "id": "<the deleted card's ID>" }` (approved, UD-19), and `GET /api/boards/{id}` no longer lists the card.
- **CARD-004-AC02** After deletion, the card row still exists in the database with a non-null `deleted_at`.
- **CARD-004-AC03** After deletion, the card is absent from `GET /api/cards?assignee=me`.
- **CARD-004-AC04** A non-member of the card's board receives HTTP 404 and the card is unchanged.
- **CARD-004-AC05** After deletion, the card's `deleted_at` is a UTC timestamp equal to the time of the request, and its `column_id`, `completed_at`, and `assignee` values are unchanged.
- **CARD-004-AC06** Sending `DELETE /api/cards/{id}` for an already soft-deleted card returns HTTP 404 and its `deleted_at` is unchanged.
- **CARD-004-AC07** After deletion, the card's comments still exist in the database, and `PATCH /api/cards/{id}`, `PATCH /api/cards/{id}/position`, and the card's comment endpoints return HTTP 404 (approved, A-15).
- **CARD-004-AC08** A successful `DELETE /api/cards/{id}` records no activity event and removes none, and it creates no notification and removes none (approved, UD-08).
- **CARD-004-AC09** After deletion, every notification that refers to the card remains in its recipient's `GET /api/notifications` and can still be marked as read (approved, UD-08).

### CARD-005 Move card (position update)
`PATCH /api/cards/{id}/position` MUST move a card to a column and an `order`. The `order` MUST be a positive float value, which the service layer stores in the card's `position` attribute. No endpoint, table, or page is added (approved, UD-06).

**Rebalancing (approved, UD-06).** A normal move stores the submitted `order`, which the frontend computes as a midpoint between the neighboring cards. When no distinct representable midpoint exists, the frontend sends an `order` equal to the `order` of the active card that must follow the moved card. The service layer treats an `order` that equals the `order` of another active card in the destination column as a tie, and it resolves the tie by rebalancing. The moved card is placed immediately before the tied card, and the destination column's active cards, including the moved card, receive evenly spaced positive FLOAT `order` values in their final sequence: 1024.0 for the first, 2048.0 for the second, 3072.0 for the third, and so on. The sequence is sorted by ascending `order`, then `created_at`, then `id`. Soft-deleted cards are not touched. No minimum-gap threshold exists, and a tie is the only trigger. The service layer takes a row lock on the destination column before it reads the column's active cards, and it applies the move, the rebalancing, the `completed_at` rules, and the activity event in one transaction. The success response is HTTP 200 with `data` set to the moved card, whose `order` is the authoritative final value, plus a boolean `rebalanced`, which is true only when other cards were renumbered. Rebalancing creates no activity event beyond the single card-moved event of ANALYTICS-006-AC02 and creates no notification.

**Acceptance criteria**
- **CARD-005-AC01** Given a valid UUID `column_id` of a column on the card's board and a positive float `order`, the request returns HTTP 200, and `GET /api/boards/{id}` lists the card in that column with the `order` returned in the response. That `order` equals the submitted `order` unless `rebalanced` is true (CARD-005-AC15).
- **CARD-005-AC02** An `order` of 0 or any negative number returns HTTP 400 and the card is unchanged.
- **CARD-005-AC03** An `order` that is missing or not numeric returns HTTP 400 and the card is unchanged.
- **CARD-005-AC04** A `column_id` that is missing or not a valid UUID returns HTTP 400 and the card is unchanged.
- **CARD-005-AC05** A `column_id` that does not identify a column on the card's board returns HTTP 400 and the card is unchanged.
- **CARD-005-AC06** A non-member of the card's board receives HTTP 404 and the card is unchanged.
- **CARD-005-AC07** Moving a card from a non-done column into a done column sets `completed_at` to the time of the request.
- **CARD-005-AC08** Moving a card from a done column into another done column leaves `completed_at` unchanged (A-13).
- **CARD-005-AC09** Moving a card from a done column into a non-done column sets `completed_at` to null.
- **CARD-005-AC10** After a card leaves a done column and enters a done column again, `completed_at` equals the time of the second entry and is later than its previous value.
- **CARD-005-AC11** Reordering a card within the same column leaves `completed_at` unchanged.
- **CARD-005-AC12** A request for a soft-deleted card returns HTTP 404 and the card is unchanged (approved, UD-18).
- **CARD-005-AC13** A `column_id` that identifies a soft-deleted column on the card's board returns HTTP 400 and the card is unchanged (approved, A-15).
- **CARD-005-AC14** With the destination column holding X (`order` 1024.0) and Y (`order` 2048.0), moving a card M with `order` 1536.0 returns HTTP 200, `data` contains `order` 1536.0 and `rebalanced` false, and the `order` and `updated_at` of X and Y are unchanged (approved, UD-06).
- **CARD-005-AC15** With the destination column holding X (1024.0) and Y (2048.0), moving M with `order` 2048.0 (equal to Y) returns HTTP 200 with `rebalanced` true and `order` 2048.0. A following `GET /api/boards/{id}` lists X at 1024.0, M at 2048.0, and Y at 3072.0, so M sits immediately before Y.
- **CARD-005-AC16** A tie is an equal `order` of another non-soft-deleted card in the destination column. An equal `order` of a soft-deleted card, of a card in another column, or of the moved card itself is not a tie and causes no rebalancing.
- **CARD-005-AC17** When rebalancing happens, every non-soft-deleted card of the destination column, including the moved card, gets the value 1024.0 times its 1-based place in the final sequence, ordered by ascending `order`, then `created_at`, then `id`. Soft-deleted cards keep their `order`.
- **CARD-005-AC18** The move, the rebalancing, the `completed_at` change, and the card-moved event are one transaction. When a failure is forced after some cards were renumbered, no card has a changed `order`, `column_id`, or `completed_at`, and no event exists afterward.
- **CARD-005-AC19** The service takes a row lock on the destination column before it reads that column's active cards. Two moves into the same column with the same `order` that run concurrently are serialized: both return HTTP 200, exactly one reports `rebalanced` true, and the active cards of the column have pairwise distinct `order` values afterward.
- **CARD-005-AC20** A move that runs concurrently with the soft-deletion of its destination column either succeeds before the deletion or returns the HTTP 400 of CARD-005-AC13, and no active card is left in a soft-deleted column.
- **CARD-005-AC21** The HTTP 200 response contains the moved card with `id`, `column_id`, `order` (the authoritative final value, equal to the card's `order` in a following `GET /api/boards/{id}`), and `rebalanced` (a boolean that is never null or omitted). It contains no key named `position`.
- **CARD-005-AC22** `rebalanced` is false for an ordinary move, for a move without a tie, and for a no-op. It appears only in this response and not in any other endpoint's response.
- **CARD-005-AC23** When the card is already in the requested column with an `order` equal to the requested one, the response is HTTP 200 with `rebalanced` false, no row is updated, `updated_at` is unchanged, and no event is recorded.
- **CARD-005-AC24** Rebalancing creates no additional activity event and no notification: a move to another column records exactly one card-moved event, a move inside the same column records none, and the `completed_at`, `deleted_at`, `assignee_id`, and `column_id` of the renumbered cards other than the moved card are unchanged.
- **CARD-005-AC25** Only a card whose `order` changed gets a new `updated_at`, equal to the time of the request. Other cards of the column keep their `updated_at`.
- **CARD-005-AC26** After every successful card move and card creation, the non-soft-deleted cards of the affected column have pairwise distinct `order` values. A request rejected with HTTP 400, 401, 404, or 409 changes no card's `order`.

### CARD-006 CardPositionSchema
`CardPositionSchema` (Marshmallow) MUST validate that `column_id` is a UUID and `order` is a positive float.

**Acceptance criteria**
- **CARD-006-AC01** Loading `{column_id: <valid UUID>, order: 1.5}` succeeds, and loading `order: 0.0001` also succeeds.
- **CARD-006-AC02** Loading `order` equal to 0, a negative number, a non-numeric string, or a missing value raises a validation error.
- **CARD-006-AC03** Loading `column_id` that is not a UUID string, or missing, raises a validation error.
- **CARD-006-AC04** Loading `order` that is a boolean, null, a numeric string, `NaN`, `Infinity`, or a value that cannot be stored as a finite positive float (for example `1e400` or `1e-400`) raises a validation error, and no maximum `order` is imposed (approved, UD-06).
- **CARD-006-AC05** Loading a body with a key other than `column_id` and `order` (for example `position` or `rebalanced`) raises a validation error (A-06).

### CARD-007 My Tasks data
`GET /api/cards?assignee=me` MUST return the cards assigned to the current user, with the name of each card's board.

**Acceptance criteria**
- **CARD-007-AC01** The response is HTTP 200 and `data` contains exactly the non-deleted cards assigned to the authenticated user.
- **CARD-007-AC02** Cards assigned to other users are absent from `data`.
- **CARD-007-AC03** Each card in `data` includes the name of its board.
- **CARD-007-AC04** A user with no assigned cards receives HTTP 200 and an empty list.
- **CARD-007-AC05** An `assignee` value other than `me`, or a missing `assignee` parameter, returns HTTP 400.
- **CARD-007-AC06** A card assigned to the user is absent from `data` when it was soft-deleted directly or when its column was soft-deleted.

### 3.5 Comments (COMMENT)

### COMMENT-001 Create comment
`POST /api/cards/{id}/comments` MUST add a comment owned by the authenticated user.

**Acceptance criteria**
- **COMMENT-001-AC01** A member sending non-empty `content` receives HTTP 201 and `data` contains the comment `id`, `content`, author, and `created_at`.
- **COMMENT-001-AC02** A request with `content` missing returns HTTP 400 and no comment is created.
- **COMMENT-001-AC03** A request with empty or whitespace-only `content` returns HTTP 400 and no comment is created.
- **COMMENT-001-AC04** A request with no token returns HTTP 401.
- **COMMENT-001-AC05** A non-member of the card's board receives HTTP 404 and no comment is created.
- **COMMENT-001-AC06** A request for a soft-deleted card returns HTTP 404, no comment is created, and no activity event is recorded (approved, A-15).
- **COMMENT-001-AC07** When the card has an assignee other than the comment's author, creating the comment also creates one unread `comment_added` notification for that assignee in the same transaction. No notification is created when the author is the assignee or the card is unassigned (approved, UD-08, NOTIF-003-AC09 and AC10).
- **COMMENT-001-AC08** The notification created by a comment contains no comment text (approved, UD-08, NOTIF-003-AC16).

### COMMENT-002 List comments
`GET /api/cards/{id}/comments` MUST return a card's comments to the board's members.

**Acceptance criteria**
- **COMMENT-002-AC01** A member receives HTTP 200 and `data` contains the card's comments ordered by `created_at` ascending (A-05).
- **COMMENT-002-AC02** A request with no token returns HTTP 401.
- **COMMENT-002-AC03** A non-member of the card's board receives HTTP 404.
- **COMMENT-002-AC04** A card ID that does not exist returns HTTP 404.
- **COMMENT-002-AC05** A soft-deleted card returns HTTP 404 and no comments (approved, A-15).

### COMMENT-003 Edit comment (owner only)
`PATCH /api/comments/{id}` MUST allow only the comment owner to edit a comment. Ownership applies equally to Board Administrators and Board Members: an administrator has no override on another user's comment (approved, UD-05).

**Acceptance criteria**
- **COMMENT-003-AC01** The owner sending non-empty `content` receives HTTP 200 and `data` contains the new content.
- **COMMENT-003-AC02** An authenticated user who is a member of the board but not the comment owner receives HTTP 403 and the content is unchanged.
- **COMMENT-003-AC03** A Board Administrator who is not the comment owner receives HTTP 403 and the content is unchanged.
- **COMMENT-003-AC04** A request with no token returns HTTP 401.
- **COMMENT-003-AC05** The owner sending empty or missing `content` receives HTTP 400 and the content is unchanged.
- **COMMENT-003-AC06** A user who is not a member of the comment's board receives HTTP 404.
- **COMMENT-003-AC07** The owner of a comment whose card is soft-deleted receives HTTP 404 and the content is unchanged (approved, A-15).
- **COMMENT-003-AC08** A Board Administrator or a Board Member who is not the comment owner and sends empty, missing, or valid `content` receives HTTP 403, and the content and `updated_at` are unchanged (approved, UD-05).
- **COMMENT-003-AC09** An owner receives HTTP 200 when editing their own comment, whether the owner is a Board Administrator or a Board Member.

### COMMENT-004 Delete comment (owner only)
`DELETE /api/comments/{id}` MUST allow only the comment owner to delete a comment. Ownership applies equally to Board Administrators and Board Members: an administrator has no override on another user's comment (approved, UD-05).

**Acceptance criteria**
- **COMMENT-004-AC01** The owner receives HTTP 200 with `data` exactly `{ "id": "<the deleted comment's ID>" }` (approved, UD-19), and the comment is absent from `GET /api/cards/{id}/comments`.
- **COMMENT-004-AC02** An authenticated board member who is not the comment owner receives HTTP 403 and the comment still exists.
- **COMMENT-004-AC03** A Board Administrator who is not the comment owner receives HTTP 403 and the comment still exists.
- **COMMENT-004-AC04** A request with no token returns HTTP 401.
- **COMMENT-004-AC05** A comment ID that does not exist returns HTTP 404.
- **COMMENT-004-AC06** After the owner deletes a comment, the comment row no longer exists in the database (hard delete, approved, UD-18), and the activity events that reference it remain.
- **COMMENT-004-AC07** The owner of a comment whose card is soft-deleted receives HTTP 404 and the comment still exists (approved, A-15).
- **COMMENT-004-AC08** An owner receives HTTP 200 when deleting their own comment, whether the owner is a Board Administrator or a Board Member.

### 3.6 Notifications (NOTIF)

### NOTIF-001 List notifications
`GET /api/notifications` MUST return the authenticated user's notifications, paginated with the `page` and `per_page` query parameters. Default and maximum `per_page` values are unresolved (UD-09).

**Acceptance criteria**
- **NOTIF-001-AC01** The response is HTTP 200 and contains only notifications addressed to the authenticated user, newest first (A-05).
- **NOTIF-001-AC02** Given 5 notifications, `per_page=2&page=1` returns 2 items and `per_page=2&page=3` returns 1 item.
- **NOTIF-001-AC03** Given 5 notifications, `per_page=2&page=4` returns HTTP 200 and an empty list.
- **NOTIF-001-AC04** A `page` or `per_page` value that is 0, negative, or not an integer returns HTTP 400.
- **NOTIF-001-AC05** A request with no token returns HTTP 401.
- **NOTIF-001-AC06** Each item has exactly these keys: `id` (UUID string), `type`, `message` (string), `board_id` (UUID string), `card_id` (UUID string), `actor` (an object with `id`, a UUID string, and `name`), `is_read` (boolean), and `created_at` (a UTC ISO 8601 timestamp). `type` is `card_assigned` or `comment_added` (approved, UD-08).
- **NOTIF-001-AC07** Items are ordered by `created_at` descending, and items with equal `created_at` are ordered by `id` descending, so the order is the same on every request (approved, UD-08).
- **NOTIF-001-AC08** No item contains comment text, an email address, or a password hash, and `message` is built only from the actor's name and the card title (approved, UD-08).
- **NOTIF-001-AC09** A notification stays in the response after its card or column is soft-deleted and after its comment is deleted, and the response needs no live card to be built (approved, UD-08).

### NOTIF-002 Mark notification as read
`PATCH /api/notifications/{id}/read` MUST mark a notification as read for its recipient. A notification belongs to exactly one recipient and only that recipient may read or mark it (approved, UD-08).

**Acceptance criteria**
- **NOTIF-002-AC01** The recipient receives HTTP 200, and the notification is read in a following `GET /api/notifications`.
- **NOTIF-002-AC02** Marking an already-read notification returns HTTP 200 and leaves it read.
- **NOTIF-002-AC03** A user who is not the recipient receives HTTP 404 and the notification is unchanged.
- **NOTIF-002-AC04** A notification ID that does not exist returns HTTP 404.
- **NOTIF-002-AC05** A request with no token returns HTTP 401.
- **NOTIF-002-AC06** The recipient receives HTTP 200 when marking a notification whose card or column was soft-deleted or whose comment was deleted, and the notification is read afterward (approved, UD-08).
- **NOTIF-002-AC07** A user who is not the recipient receives the same HTTP 404 status and body as for a notification ID that does not exist, including when both users belong to the same board (approved, UD-08).
- **NOTIF-002-AC08** Marking a notification as read changes only its read state: its `type`, `message`, `board_id`, `card_id`, `actor`, and `created_at` are unchanged.

### NOTIF-003 Notification creation
The system MUST create a notification only for these events (approved, UD-08): a card is assigned to a board member other than the requester (`card_assigned`), a card is reassigned to a different board member other than the requester (`card_assigned`), and a comment is created on an assigned card by someone other than its assignee (`comment_added`). The recipient is the new assignee in the first two cases and the card's assignee in the third. A user is never notified about their own actions. The notification is created in the same database transaction as the originating action, only for a recipient who is a member of the card's board, and never contains comment text.

The events that do not notify are: card creation, card unassignment, assigning a card to yourself, repeating an unchanged `assignee_id`, card moves and reordering, card title changes, card deletion, column creation, renaming, reordering, completion changes, and deletion, board changes and membership additions, and comment edits and deletions.

**Acceptance criteria**
- **NOTIF-003-AC01** When a board member assigns an unassigned card to a different board member through `PATCH /api/cards/{id}`, exactly one unread `card_assigned` notification is created for the new assignee, with the requester as `actor`, and the notification is visible in the new assignee's `GET /api/notifications` (approved, UD-08).
- **NOTIF-003-AC02** A user who is not a member of the relevant board never receives a notification for events on that board: assigning a card to a non-member returns HTTP 400 and creates no notification, a comment notifies only the card's assignee, and a non-member's `GET /api/notifications` contains no notification for that board (approved, UD-08).
- **NOTIF-003-AC03** When a card assigned to B is reassigned to C by someone other than C, exactly one `card_assigned` notification is created for C and none for B. B's earlier notifications remain unchanged.
- **NOTIF-003-AC04** When a user assigns a card to themselves, the assignee changes and no notification is created for anyone.
- **NOTIF-003-AC05** When a card is unassigned with `assignee_id: null`, no notification is created, and the former assignee's earlier notifications remain unchanged.
- **NOTIF-003-AC06** When a card is assigned to B, unassigned, and then assigned to B again by someone other than B, B receives a second `card_assigned` notification. A card reassigned from B to C and back to B by someone other than B also notifies B again. No uniqueness rule prevents these repeated notifications.
- **NOTIF-003-AC07** When `assignee_id` equals the stored assignee, no notification is created. Sending the same assignment twice in a row creates exactly one notification in total.
- **NOTIF-003-AC08** When two identical assignment requests for the same card and assignee run concurrently, exactly one notification is created and the assignee changes once. The service serializes them with a database row lock and a comparison with the stored state.
- **NOTIF-003-AC09** When a board member other than the assignee creates a comment on an assigned card, exactly one unread `comment_added` notification is created for the assignee, with the comment author as `actor`.
- **NOTIF-003-AC10** No notification is created when the comment author is the card's assignee, or when the card has no assignee.
- **NOTIF-003-AC11** None of these actions creates a notification: card creation, card move, card reorder, card title change, card deletion, column creation, renaming, reordering, completion change, or deletion, board rename, board deletion, member addition, and comment edit or deletion.
- **NOTIF-003-AC12** If a failure is forced after the card's assignee was updated and before the notification is stored, or after the notification is stored and before the commit, the assignee is unchanged and no notification exists afterward.
- **NOTIF-003-AC13** If a failure is forced after the comment is stored and before the notification is stored, or after the notification is stored and before the commit, no comment and no notification exist afterward.
- **NOTIF-003-AC14** A request rejected with HTTP 400, 401, 403, 404, or 409 creates no notification, including a mixed request that changes `assignee_id` and also contains an invalid field.
- **NOTIF-003-AC15** The recipient of a notification is a member of the notification's board at the time of creation, and the service refuses to create a notification for a user who is not.
- **NOTIF-003-AC16** The `message` of a `comment_added` notification does not contain the comment text, and no notification field or message contains an email address.
- **NOTIF-003-AC17** After the card is soft-deleted, after its column is soft-deleted, or after the comment is deleted, the notification remains in the recipient's `GET /api/notifications` and can be marked as read.
- **NOTIF-003-AC18** After `DELETE /api/boards/{id}`, no notification that refers to that board or its cards remains, for any recipient, and notifications of other boards are unchanged (BOARD-005-AC04).
- **NOTIF-003-AC19** Creating a notification creates no activity event, and no activity-event count changes (approved, UD-13).

### 3.7 Board analytics (ANALYTICS)

### ANALYTICS-001 Analytics endpoint access
`GET /api/boards/{id}/analytics` MUST return the board's analytics for the current UTC reporting week to the board's members. It reports only the current week, supports no custom date ranges, and accepts no query parameters (approved, UD-14). It adds no endpoint. The response uses the standard `{ "data": ... }` envelope and has this shape:

```json
{ "data": {
  "window": { "start": "2025-01-13T00:00:00Z", "end": "2025-01-20T00:00:00Z" },
  "cards_per_column": [ { "column_id": "<uuid>", "name": "To Do", "card_count": 3 } ],
  "completed_this_week": 2,
  "member_activity": [ { "user_id": "<uuid>", "name": "Ana", "activity_count": 5 } ]
} }
```

**Acceptance criteria**
- **ANALYTICS-001-AC01** A member receives HTTP 200, and `data` has exactly the keys `window`, `cards_per_column`, `completed_this_week`, and `member_activity` inside the `{ "data": ... }` envelope.
- **ANALYTICS-001-AC02** A non-member receives HTTP 404.
- **ANALYTICS-001-AC03** A request with no token returns HTTP 401.
- **ANALYTICS-001-AC04** `window` has exactly the keys `start` and `end`. Both are UTC ISO 8601 timestamps in the form `YYYY-MM-DDTHH:MM:SSZ`. `start` is a Monday at 00:00:00 UTC, `end` is exactly 7 days after `start`, and the server's current UTC time satisfies `start <= now < end`.
- **ANALYTICS-001-AC05** Each `cards_per_column` entry has exactly the keys `column_id` (a UUID string), `name`, and `card_count` (an integer of at least 0), and the entries are ordered by ascending column `order`.
- **ANALYTICS-001-AC06** `completed_this_week` is an integer of at least 0.
- **ANALYTICS-001-AC07** Each `member_activity` entry has exactly the keys `user_id` (a UUID string), `name`, and `activity_count` (an integer of at least 0). The entries are ordered by `activity_count` descending, then `name` ascending, then `user_id` ascending. No entry contains an email address or any other private profile field.
- **ANALYTICS-001-AC08** For a board that has no columns, `cards_per_column` is `[]`, `completed_this_week` is 0, and `member_activity` has one entry for each current board member with `activity_count` 0 when no qualifying events exist. No key is omitted and no value is null.
- **ANALYTICS-001-AC09** A member who sends any query parameter (for example `week`, `start`, `end`, or an unknown name) receives HTTP 400 with an `error` message and no analytics data. A non-member who sends a query parameter receives HTTP 404, and a request with no token receives HTTP 401 (Section 2.4).

### ANALYTICS-002 Total cards per column
The analytics MUST include the number of cards in each column.

**Acceptance criteria**
- **ANALYTICS-002-AC01** For a board with a column holding 3 cards and a column holding 0 cards, the response reports 3 and 0 for those columns.
- **ANALYTICS-002-AC02** Cards with a non-null `deleted_at` are not counted.
- **ANALYTICS-002-AC03** Soft-deleted columns are absent from the per-column result, and cards that were soft-deleted with their column are not counted anywhere (approved, UD-18 and UD-23).
- **ANALYTICS-002-AC04** After a column holding 3 cards is deleted, the response lists one column fewer and the total number of counted cards drops by 3.
- **ANALYTICS-002-AC05** `cards_per_column` lists every non-soft-deleted column of the board in ascending `order`, with `card_count` equal to the number of its non-soft-deleted cards, and a column without cards appears with `card_count` 0. The counts are a snapshot of the current state and do not depend on the reporting window.

### ANALYTICS-003 Cards completed this week
The analytics MUST include `completed_this_week`: the number of non-soft-deleted cards in non-soft-deleted done columns whose current `completed_at` lies inside the reporting window (`window_start <= completed_at < window_end`, UTC; approved, UD-14). Each card counts at most once. The count uses the current `completed_at` only and does not reconstruct completions from activity events, and no completion history is stored. For a non-deleted card in a non-deleted column, `completed_at` is non-null if and only if the column is marked done (UD-12, A-13). A card in a column that was newly marked done counts as completed this week, even if the card was created months earlier. A card completed twice counts once, with its latest `completed_at`.

In the criteria below the server clock is fixed at `2025-01-15T12:00:00Z` (a Wednesday) unless stated otherwise, so the window is `2025-01-13T00:00:00Z` (inclusive) to `2025-01-20T00:00:00Z` (exclusive).

**Acceptance criteria**
- **ANALYTICS-003-AC01** Given 2 cards in a done column with `completed_at` `2025-01-14T09:00:00Z` and `2025-01-15T08:00:00Z`, and 1 card in the same column with `completed_at` `2025-01-10T09:00:00Z`, `completed_this_week` is 2.
- **ANALYTICS-003-AC02** A card with `completed_at` `2025-01-10T09:00:00Z` that is still in a done column is not counted.
- **ANALYTICS-003-AC03** A card completed on `2025-01-14T09:00:00Z` and then moved to an active column has a null `completed_at` and is not counted.
- **ANALYTICS-003-AC04** A card completed this week and then soft-deleted keeps its `completed_at` and is not counted.
- **ANALYTICS-003-AC05** After a done column holding cards completed this week is soft-deleted, none of its cards is counted.
- **ANALYTICS-003-AC06** A card with `completed_at` `2025-01-13T00:00:00Z` is counted, and a card with `completed_at` `2025-01-12T23:59:59.999999Z` is not (start inclusive).
- **ANALYTICS-003-AC07** With the clock fixed at `2025-01-19T23:59:59.900000Z`, the window ends at `2025-01-20T00:00:00Z`, and a card with `completed_at` `2025-01-19T23:59:59.500000Z` is counted (Sunday fractional-second inclusion).
- **ANALYTICS-003-AC08** With the clock fixed at `2025-01-20T00:00:00Z`, the window is `2025-01-20T00:00:00Z` to `2025-01-27T00:00:00Z`, the card of AC07 is no longer counted, and a card with `completed_at` `2025-01-20T00:00:00Z` is counted (week rollover and end exclusive).
- **ANALYTICS-003-AC09** After any sequence of the endpoints in Section 3.0, every non-deleted card in a non-deleted column has a non-null `completed_at` if and only if its column is marked done.
- **ANALYTICS-003-AC10** A card that is completed, moved to an active column, and completed again is counted once and has the later `completed_at`. When the first completion was before the window and the second is inside it, the card is counted this week.
- **ANALYTICS-003-AC11** A card moved from one done column to another keeps its `completed_at`: a card completed before the window is still not counted, and a card completed inside the window is counted once.
- **ANALYTICS-003-AC12** When an administrator marks a column done, its 3 existing non-deleted cards, which were created weeks earlier, are counted as completed this week and `completed_this_week` rises by 3. When the column is marked active again, `completed_this_week` falls by 3.
- **ANALYTICS-003-AC13** `completed_this_week` is the same before and after all activity-event rows of the board are removed in a test, because it does not depend on events.

### ANALYTICS-004 Member activity
The analytics MUST include member activity. Activity MUST be taken from the activity-event records (ANALYTICS-006) and not inferred from current data. A member's `activity_count` is the number of that member's activity events of the three approved types (`card_created`, `card_moved`, `comment_created`; approved, UD-13) for this board whose event time lies inside the same reporting window as `completed_this_week` (`window_start <= event time < window_end`, UTC; approved, UD-14 and A-14). Each event counts once. The response has one entry for each current board member, and a current member with no qualifying events has `activity_count` 0. A member who joined during the week keeps all their qualifying events of that week, without proration. Former members get no entry. Events whose card, column, or comment was later soft-deleted or deleted still count. There is no per-type breakdown. The criteria use the clock and window of ANALYTICS-003 (fixed at `2025-01-15T12:00:00Z`) unless stated otherwise.

**Acceptance criteria**
- **ANALYTICS-004-AC01** The response includes one activity entry for each current member of the board, and a current member with no recorded events has an activity count of 0.
- **ANALYTICS-004-AC02** When the event time is inside the reporting window, creating a card, moving a card to another column, and creating a comment each increase the acting member's activity count by 1 in the next analytics response.
- **ANALYTICS-004-AC03** An event with time `2025-01-12T23:59:59.999999Z` (before the window) is not counted, and an event with time `2025-01-13T00:00:00Z` is counted (start inclusive).
- **ANALYTICS-004-AC04** Events performed on another board are not counted for this board.
- **ANALYTICS-004-AC05** `completed_this_week` and every `activity_count` are computed with the single `window` returned in the same response, which comes from one reading of the server clock (approved, A-14 and UD-14). An event and a card completion with the same timestamp are both inside or both outside that window.
- **ANALYTICS-004-AC06** After a card, or the column that holds it, is soft-deleted, the activity counts of the board's members are unchanged, because the events of the deleted card and column still count (approved, UD-13 and A-13).
- **ANALYTICS-004-AC07** With the clock fixed at `2025-01-19T23:59:59.900000Z`, an event with time `2025-01-19T23:59:59.500000Z` is counted. With the clock fixed at `2025-01-20T00:00:00Z`, the window is `2025-01-20T00:00:00Z` to `2025-01-27T00:00:00Z` and that event is no longer counted (end exclusive and rollover).
- **ANALYTICS-004-AC08** Three card-moved events by one member inside the window give that member an `activity_count` of 3, whether they involve one card or three cards.
- **ANALYTICS-004-AC09** A card assignment, a comment edit or deletion, a done-column toggle, a card deletion, and a column deletion leave every member's `activity_count` unchanged.
- **ANALYTICS-004-AC10** A user added to the board on Wednesday appears in `member_activity`, and every qualifying event of that user inside the window is counted without proration.
- **ANALYTICS-004-AC11** A user who has no current membership row for the board (the row is removed directly in the test, because no endpoint removes members) has no entry in `member_activity`, and no private data of that user appears in the response.

### ANALYTICS-005 Implementation constraint
Analytics MUST be calculated with SQLAlchemy joins in the service layer.

**Acceptance criteria**
- **ANALYTICS-005-AC01** The route handler for `GET /api/boards/{id}/analytics` contains no query construction and delegates to a service-layer function.
- **ANALYTICS-005-AC02** A test that records the SQL emitted during an analytics request finds at least one statement containing `JOIN`.
- **ANALYTICS-005-AC03** Recording the SQL for each of the three metrics separately (cards per column, cards completed this week, member activity) finds a `JOIN` in the statement for each metric.
- **ANALYTICS-005-AC04** The service layer computes the reporting window once per request from the current UTC time, uses that window for both `completed_this_week` and `member_activity`, and reads the time from a clock that tests can fix. Tests never depend on the real current date.

### ANALYTICS-006 Activity-event recording
The service layer MUST record an append-only activity event, in the same database transaction as the action, for each card creation, each card movement to another column, and each comment creation (approved, UD-13). The event type names below are working names. Events MUST survive the soft-deletion of their column or card and the deletion of their comment. They are removed only when their board is hard-deleted (approved, UD-18). Further approved behavior is in A-13 and A-14.

**Acceptance criteria**
- **ANALYTICS-006-AC01** A successful `POST /api/columns/{id}/cards` records exactly one card-created event with the board, the acting user, the card, and the event time.
- **ANALYTICS-006-AC02** A successful `PATCH /api/cards/{id}/position` that changes the card's column records exactly one card-moved event that includes the source column and the destination column. A request that keeps the card in the same column records no event.
- **ANALYTICS-006-AC03** A successful `POST /api/cards/{id}/comments` records exactly one comment-created event with the board, the acting user, the card, and the event time.
- **ANALYTICS-006-AC04** A request rejected with HTTP 400, 401, 403, or 404 records no event.
- **ANALYTICS-006-AC05** The API has no endpoint that updates or deletes an activity event, and deleting a card or a comment leaves its events in the table.
- **ANALYTICS-006-AC06** Every event row has a non-null board, acting user, event type, and event time. A card-moved event also has non-null source and destination columns.
- **ANALYTICS-006-AC07** After a card is soft-deleted and after a comment is deleted, the events that reference them remain readable in the activity-event table and still count toward the acting member's activity.
- **ANALYTICS-006-AC08** A successful `PATCH /api/comments/{id}` and a successful `DELETE /api/comments/{id}` each record no activity event, and the acting member's activity count is unchanged (approved, A-14).
- **ANALYTICS-006-AC09** After a column is soft-deleted together with its cards, every activity event that references the column or its cards still exists with unchanged values and remains readable. A successful `DELETE /api/columns/{id}` records no new event.
- **ANALYTICS-006-AC10** Hard-deleting a board removes that board's activity events and no event of another board (approved, UD-18).
- **ANALYTICS-006-AC11** Every activity event's time is a UTC timestamp equal to the time of the request that created it, taken from the same clock reading as the action's other timestamps (`created_at`, `updated_at`, and `completed_at` where they change), so that window boundaries are deterministic under a fixed clock (approved, UD-14).

### 3.8 User profile (USER)

### USER-001 Get current user
`GET /api/users/me` MUST return the authenticated user's profile without the password.

**Acceptance criteria**
- **USER-001-AC01** The response is HTTP 200 and `data` contains the user's `id`, `name`, and `email`.
- **USER-001-AC02** No key in `data` contains the text `password`, and no password hash value appears in the response body.
- **USER-001-AC03** A request with no token returns HTTP 401.

### USER-002 Update current user
`PATCH /api/users/me` MUST allow updating `name` and `email` only. It MUST NOT allow updating the password.

**Acceptance criteria**
- **USER-002-AC01** A valid `name` and `email` return HTTP 200, `data` contains the new values, and a following `GET /api/users/me` returns them.
- **USER-002-AC02** A request body that includes `password` returns HTTP 400 (A-06), and the user can still log in with the old password and cannot log in with the submitted one.
- **USER-002-AC03** An email that is not syntactically valid returns HTTP 400 and the stored email is unchanged.
- **USER-002-AC04** An email already used by another user returns HTTP 409 and the stored email is unchanged.
- **USER-002-AC05** The response body contains no `password` key and no password hash.
- **USER-002-AC06** A request with no token returns HTTP 401.

### 3.9 API behavior (API)

### API-001 Success response envelope
Every successful JSON response MUST use the `{ "data": ... }` envelope and the status conventions of Section 2.3 (approved, UD-19). The reorder endpoint has its own approved response (COLUMN-004). The card position endpoint has its own approved response (CARD-005). The endpoint-specific response contract that is still pending (the notification list pagination of UD-09) is an exception to criteria AC04 and AC06 below until that decision is made, and a more specific approved rule always overrides a general one here.

**Acceptance criteria**
- **API-001-AC01** For every endpoint in Section 3.0, a successful response body is a JSON object with a top-level `data` key and no `error` key.
- **API-001-AC02** Every successful request returns HTTP 200 for a GET, a PATCH, and a DELETE, and also for login, notification mark-as-read, and the health check. It never returns HTTP 204.
- **API-001-AC03** `POST /api/auth/register`, `POST /api/boards`, `POST /api/boards/{id}/columns`, `POST /api/columns/{id}/cards`, `POST /api/cards/{id}/comments`, and `POST /api/boards/{id}/members` each return HTTP 201 on success, and `data` is the created resource, which contains its `id` (for the member extension, the added user's `id`).
- **API-001-AC04** Every successful PATCH other than `PATCH /api/boards/{id}/columns/reorder` (whose array response is defined by COLUMN-004) returns HTTP 200 and a `data` object that contains the resource's `id` and the new value of every field the request changed. Every key that `data` shares with a following GET representation of the same resource has the same value there.
- **API-001-AC05** Every successful `DELETE /api/boards/{id}`, `DELETE /api/columns/{id}`, `DELETE /api/cards/{id}`, and `DELETE /api/comments/{id}` returns HTTP 200 and `data` is exactly `{ "id": "<the ID of the deleted resource>" }`. A repeated delete of a deleted board, of a soft-deleted column or card, or of a deleted comment still returns the HTTP 404 required by the criteria of that resource.
- **API-001-AC06** `GET /api/boards`, `GET /api/cards?assignee=me`, and `GET /api/cards/{id}/comments` return `data` as a JSON array, and `[]` when there are no results, never null and never omitted. `GET /api/notifications` is excluded until UD-09 defines its pagination contract.
- **API-001-AC07** Every API response that has a body, whether success or error, has the header `Content-Type: application/json`.
- **API-001-AC08** No successful response body contains a password, a password hash, or a JWT, except the `access_token` in the login response.

### API-002 Error response envelope
Every error response MUST use the `{ "error": "..." }` envelope.

**Acceptance criteria**
- **API-002-AC01** Responses with status 400, 401, 403, and 404 each have a body that is a JSON object with a top-level `error` string and no `data` key.
- **API-002-AC02** A request to a route that does not exist returns HTTP 404 with a JSON `error` body, not an HTML page.
- **API-002-AC03** An unhandled exception returns HTTP 500 with a JSON `error` body that does not contain a stack trace or file path.
- **API-002-AC04** Responses with status 405, 409, 415, and 500, like those with 400, 401, 403, and 404, have a body that is a JSON object with a top-level `error` string and no `data` key. For every error status the `error` value is a non-empty string, including validation failures (approved, UD-19).
- **API-002-AC05** The `error` text of an HTTP 500 response is a generic message that is the same for every kind of unhandled exception, and it contains no stack trace, file path, SQL statement, token, exception class name, or other internal detail (approved, UD-19).

### API-003 Health check
`GET /api/health` MUST report that the API is running, with HTTP 200 and `{ "data": { "status": "ok" } }` (approved, UD-19). It performs no database check and returns no dependency diagnostics, version information, or environment details.

**Acceptance criteria**
- **API-003-AC01** A request with no token returns HTTP 200, and the body is exactly `{ "data": { "status": "ok" } }`.
- **API-003-AC02** The endpoint is reachable on the deployed Render URL over HTTPS.
- **API-003-AC03** A request to the endpoint executes no database query, and the body contains no key other than `status`.

### API-004 Cross-origin access
The API MUST accept direct browser requests from the deployed Vercel frontend origin and reject other origins. With the approved cookie architecture (UD-03), authenticated requests reach Flask only from the Next.js server and never from browser code. Direct browser requests are limited to `GET /api/health` (API-005-AC08). Flask MUST NOT allow credentialed cross-origin requests.

**Acceptance criteria**
- **API-004-AC01** A preflight request from the configured frontend origin receives a response whose `Access-Control-Allow-Origin` equals that origin.
- **API-004-AC02** A preflight request from any other origin receives no `Access-Control-Allow-Origin` header.
- **API-004-AC03** The allowed origin is read from an environment variable listed in the backend `.env.example`.
- **API-004-AC04** No response from the API includes `Access-Control-Allow-Credentials: true`.
- **API-004-AC05** A preflight response does not list `Authorization` in `Access-Control-Allow-Headers`.

## 4. Frontend Requirements

### 4.1 Server and Client Components
Next.js App Router components are Server Components by default. The assignment requires the `/` Dashboard page and the `/boards/[id]` Board Detail page to be Server Components, and requires interactive forms, modals, drag-and-drop, and notification controls to be Client Components. A file that uses React state, effects, context, event handlers, or browser APIs MUST be a Client Component.

**Authentication architecture (approved, UD-03).** The JWT is stored only in an HttpOnly cookie, and browser JavaScript never sees it. A Next.js server-side session layer reads the cookie and forwards the JWT to Flask in the `Authorization: Bearer` header:
- Server Components fetch authenticated data on the Next.js server through `apiClient.ts` in server-side mode, using `API_BASE_URL`.
- Client Components send authenticated requests (mutations, polling) to a same-origin Next.js proxy, which attaches the JWT from the cookie and forwards the request to Flask (FRONT-023).
- Direct browser requests to Flask through `NEXT_PUBLIC_API_BASE_URL` are limited to `GET /api/health`.
- Login and logout requests from the browser go to Next.js route handlers on the same origin. The login route handler is the only code that receives the JWT from Flask and sets the cookie. Registration needs no JWT and goes through the same proxy.
- Expired or invalid sessions redirect to `/login`.

```text
Server Component page --(API_BASE_URL, Bearer JWT from cookie)--> Flask
Client Component ------(same-origin, cookie only)--> Next.js proxy --(Bearer JWT)--> Flask
Browser ---------------(NEXT_PUBLIC_API_BASE_URL, no JWT, GET /api/health only)--> Flask
```

| Module | Type |
|---|---|
| Root layout | Server Component. It reads the session, loads the current user on the server when a session exists, and renders a Client Component that mounts `AuthContext` (initialized with that user) and the toast container. |
| `/` Dashboard page | Server Component (required by the assignment). It fetches the board list on the server and renders `BoardCard` components and a Client Component board-creation form. |
| `/boards/[id]` Board Detail page | Server Component (required by the assignment). It fetches the board on the server and renders Client Components for interaction. |
| `/register`, `/login` page files | Server Components that render Client Component forms (A-12). |
| `/my-tasks`, `/profile` page files | Server Components that fetch data on the server and render Client Components for interaction (A-12). |
| Forms: registration, login, board creation, add column, profile, `AddCardForm` | Client Components. |
| Modals: `BaseModal`, `CardDetailModal` | Client Components. |
| Drag-and-drop: the board view container and `useDragAndDrop` | Client Components and a client-only hook. |
| Notification controls: `NotificationBell`, `useNotifications` | Client Component and a client-only hook. |
| `CommentList`, `ColumnHeader`, card search input, `BaseButton` | Client Components. |
| `BoardCard`, `BaseBadge` | No client-only features. They MAY be rendered from Server or Client Components. |
| `AuthContext`, `useErrorHandler`, `toast.ts` | Client-only modules. |
| `apiClient.ts`, `errors.ts` | Plain modules with no React imports. They run on the server and in the browser. |
| Session layer and proxy (FRONT-023) | Server-only modules and route handlers. |

### 4.2 Pages

### FRONT-001 Register page (`/register`)
The `/register` page MUST let a visitor create an account.

**Acceptance criteria**
- **FRONT-001-AC01** The page renders name, email, and password inputs and a submit control.
- **FRONT-001-AC02** Submitting with an empty field shows a message next to that field and sends no request.
- **FRONT-001-AC03** A 201 response navigates to `/login` (approved, UD-04) and shows a success toast.
- **FRONT-001-AC04** A 409 response shows the `error` message from the response and keeps the user on `/register`.
- **FRONT-001-AC05** The page contains a link to `/login`.
- **FRONT-001-AC06** The registration request is sent to the same-origin Next.js proxy and not directly to Flask.

### FRONT-002 Login page (`/login`)
The `/login` page MUST let a registered user sign in.

**Acceptance criteria**
- **FRONT-002-AC01** Valid credentials call `AuthContext.login()`, which establishes the session cookie (FRONT-023) and sets `currentUser`, and then navigate to `/` (A-08).
- **FRONT-002-AC02** A 401 response shows a visible error message and the URL remains `/login`.
- **FRONT-002-AC03** Submitting with an empty email or password shows a message next to that field and sends no request.
- **FRONT-002-AC04** The page contains a link to `/register`.

### FRONT-003 Route protection
Protected pages MUST NOT be visible to unauthenticated users.

**Acceptance criteria**
- **FRONT-003-AC01** An unauthenticated visit to `/`, `/boards/[id]`, `/my-tasks`, or `/profile` is redirected to `/login` by the server, before any page content is rendered.
- **FRONT-003-AC02** The server response to an unauthenticated visit contains no protected content (board names, card titles, profile data), and none appears in the DOM at any time.
- **FRONT-003-AC03** After logout, a visit to any protected page is redirected to `/login`.

### FRONT-004 Logout
An authenticated user MUST be able to log out.

**Acceptance criteria**
- **FRONT-004-AC01** A logout control is visible on every protected page.
- **FRONT-004-AC02** Activating the logout control calls `AuthContext.logout()`, which causes the server to expire the session cookie (a `Set-Cookie` with a past expiry) and clears `currentUser`, then navigates to `/login`.
- **FRONT-004-AC03** After logout and a page reload, the user is still unauthenticated.

### FRONT-005 Dashboard (`/`)
The `/` page MUST be a Server Component that lists the user's boards using `BoardCard`, and it MUST include a Client Component form for creating a board.

**Acceptance criteria**
- **FRONT-005-AC01** The page shows each board returned by `GET /api/boards` as a `BoardCard` with a link to `/boards/[id]` for that board.
- **FRONT-005-AC02** Submitting a non-empty board name in the Client Component form calls `POST /api/boards` through the same-origin proxy, and the new board appears in the list without a full page reload.
- **FRONT-005-AC03** When the user has no boards, the page shows an empty-state message and the create-board control.
- **FRONT-005-AC04** While the server-side board request is pending, the route shows a loading UI that contains an element with `role="status"`.
- **FRONT-005-AC05** If the server-side board request fails with a non-401 error, the route shows an error message containing the `error` text from the response. If the board-creation request fails, an error toast shows the `error` message.
- **FRONT-005-AC06** The page file for `/` has no `"use client"` directive and is a Server Component.
- **FRONT-005-AC07** The board list is fetched on the Next.js server with the JWT forwarded from the session cookie, and the JWT string does not appear in the page HTML.

### FRONT-006 Board page (`/boards/[id]`)
The `/boards/[id]` page MUST be a Server Component that fetches and displays a board's columns and cards, and it MUST render Client Components for editing, drag-and-drop, search, and modals. Mutations from Client Components go through the same-origin proxy.

**Acceptance criteria**
- **FRONT-006-AC01** Columns appear in ascending `order`, and each column's cards appear in ascending `order`.
- **FRONT-006-AC02** A 404 response shows a "board not found" message and no board data.
- **FRONT-006-AC03** Submitting a column name creates a column through `POST /api/boards/{id}/columns`, and the column appears after the existing columns.
- **FRONT-006-AC04** Submitting a card title in a column's `AddCardForm` creates a card through `POST /api/columns/{id}/cards`, and the card appears in that column.
- **FRONT-006-AC05** Activating a card opens `CardDetailModal` for that card.
- **FRONT-006-AC06** Renaming a column through its `ColumnHeader` calls `PATCH /api/columns/{id}` for any board member, and deleting a column, which only a Board Administrator can do (approved, UD-05), calls `DELETE /api/columns/{id}` after a confirmation step.
- **FRONT-006-AC07** The page file for `/boards/[id]` has no `"use client"` directive and is a Server Component.
- **FRONT-006-AC08** The board data is fetched on the Next.js server with the JWT forwarded from the session cookie, and the JWT string does not appear in the page HTML.
- **FRONT-006-AC09** For a Board Administrator, the column-delete confirmation states that the column's cards will be deleted with it. After a successful `DELETE /api/columns/{id}`, the column and all its cards disappear from the page without a reload.
- **FRONT-006-AC10** When `DELETE /api/columns/{id}` fails, the column and its cards stay visible and an error toast shows the `error` message.
- **FRONT-006-AC11** The board page passes the `members` from the `GET /api/boards/{id}` response to `CardDetailModal` and sends no other request to obtain them (approved, UD-08).
- **FRONT-006-AC12** When the page is opened from a notification for a card that is not in the board data, it shows the message "This card is no longer available" and a way back to the board, shows no error toast, and does not fail to render.

### FRONT-007 Board analytics view
`/boards/[id]` MUST display the analytics returned by `GET /api/boards/{id}/analytics` (A-10) for the current UTC reporting week (approved, UD-14). The page remains a Server Component, and the analytics panel is refreshed from the browser through the same-origin proxy (FRONT-023). The view has no timezone setting and no date-range control.

**Acceptance criteria**
- **FRONT-007-AC01** The view shows the card count for each column labeled with the column name, the number of cards completed this week, and member activity.
- **FRONT-007-AC02** If the analytics request fails, the analytics panel shows an error message instead of numbers, and the rest of the board remains visible.
- **FRONT-007-AC03** The panel labels the reporting period using `window.start` and `window.end` from the response and treats `window.end` as exclusive, so the last displayed day is the day before `window.end`. For `2025-01-13T00:00:00Z` to `2025-01-20T00:00:00Z` it shows "Week of Jan 13–19, 2025 (UTC)". A week that crosses a month shows "Week of Jan 27–Feb 2, 2025 (UTC)", and one that crosses a year shows "Week of Dec 30, 2024–Jan 5, 2025 (UTC)". The dates are computed in UTC and do not change when the browser's time zone is set to Asia/Jakarta or America/Los_Angeles.
- **FRONT-007-AC04** A count of zero is displayed as "0" for `completed_this_week`, for every `card_count`, and for every `activity_count`. No count is blank or omitted.
- **FRONT-007-AC05** For a board with no columns, the panel shows the message "This board has no columns yet" in place of the per-column counts, and still shows the reporting period, `completed_this_week` as 0, and the member activity entries.
- **FRONT-007-AC06** Member activity is shown in the order returned by the API, without sorting in the browser, and each entry shows the member's `name` and `activity_count`. No email address is shown.
- **FRONT-007-AC07** The analytics view contains no time zone selector, no date input, and no week selector.
- **FRONT-007-AC08** After a successful card creation, card move, or card deletion, and after a successful Done/Active toggle (FRONT-025-AC15), the panel requests `GET /api/boards/{id}/analytics` again and shows the new response. After a failed mutation it makes no analytics request.

### FRONT-008 Card search with debounce
Card search on `/boards/[id]` MUST filter the card titles of the board data already loaded from `GET /api/boards/{id}`, in the browser, and MUST debounce the search input by 300 ms. The scope is the current board only (approved, UD-10). There is no search API endpoint and the search sends no API request (approved, UD-11). The matching rule is A-11.

**Acceptance criteria**
- **FRONT-008-AC01** With fake timers, after typing three characters with 100 ms between keystrokes, the displayed cards are unchanged 299 ms after the last keystroke and filtered at 300 ms.
- **FRONT-008-AC02** The filter uses the final input value, and no filter pass runs for an intermediate value.
- **FRONT-008-AC03** A keystroke before 300 ms elapses restarts the 300 ms wait.
- **FRONT-008-AC04** When the component unmounts during the wait, no filter pass runs and no React warning is logged.
- **FRONT-008-AC05** After the debounce, only cards whose title contains the search term (ignoring letter case) remain visible, and all other cards are hidden.
- **FRONT-008-AC06** Clearing the input, or entering only whitespace, restores every card. Columns stay visible when none of their cards match.
- **FRONT-008-AC07** Typing and filtering sends zero requests to the API or the proxy.
- **FRONT-008-AC08** When no card matches, a message states that no cards match.

### FRONT-009 My Tasks page (`/my-tasks`)
The `/my-tasks` page MUST show the cards assigned to the current user, grouped by board name.

**Acceptance criteria**
- **FRONT-009-AC01** On the server, the page requests `GET /api/cards?assignee=me` with the JWT forwarded from the session cookie.
- **FRONT-009-AC02** Cards are shown under one heading per board name, and cards from the same board appear under the same heading.
- **FRONT-009-AC03** When the response contains no cards, the page shows an empty-state message.
- **FRONT-009-AC04** While the server-side request is pending, the route shows a loading UI that contains an element with `role="status"`.

### FRONT-010 Profile page (`/profile`)
The `/profile` page MUST show and edit the user's name and email and MUST NOT offer a password change.

**Acceptance criteria**
- **FRONT-010-AC01** The page shows the `name` and `email` from `GET /api/users/me`.
- **FRONT-010-AC02** Submitting edited values calls `AuthContext.updateProfile()`, which sends `PATCH /api/users/me` with a body that contains only `name` and `email`, then shows a success toast.
- **FRONT-010-AC03** The page contains no input of type `password`.
- **FRONT-010-AC04** A 400 or 409 response shows the `error` message and keeps the values the user typed.

### 4.3 Components

### FRONT-011 CardDetailModal
`CardDetailModal` MUST show and edit one card, and MUST include the card's comments. It MUST also let any board member assign or unassign the card through an assignee dropdown that lists the board's members, using `assignee_id` and `PATCH /api/cards/{id}` (approved, UD-08). It receives the board's members from the board data, which `GET /api/boards/{id}` returns, and sends no additional request to obtain them. Card creation stays title-only, so `AddCardForm` has no assignment control.

**Acceptance criteria**
- **FRONT-011-AC01** The modal shows the card's title and assignee, and contains `CommentList`.
- **FRONT-011-AC02** Saving an edited title calls `PATCH /api/cards/{id}` and the board shows the new title.
- **FRONT-011-AC03** Deleting the card after confirmation calls `DELETE /api/cards/{id}`, closes the modal, and removes the card from the board.
- **FRONT-011-AC04** The modal is built on `BaseModal` and closes with the close control and the Escape key.
- **FRONT-011-AC05** The modal displays the current assignee's name, found by matching `assignee_id` to the board's `members`, or the text "Unassigned" when `assignee_id` is null.
- **FRONT-011-AC06** The assignee dropdown has an accessible name that includes "Assignee", contains one option per board member showing only the member's `name`, contains an "Unassigned" option, and has the current assignee selected. The dropdown is present for Board Administrators and Board Members alike and shows no email addresses.
- **FRONT-011-AC07** Choosing a member sends `PATCH /api/cards/{id}` through the same-origin proxy with a body whose only field is `assignee_id` set to that member's UUID. Choosing "Unassigned" sends a body whose only field is `assignee_id` set to null. Choosing the current value sends no request.
- **FRONT-011-AC08** After a successful request, the modal and the card on the board show the new assignee, or "Unassigned", without a page reload.
- **FRONT-011-AC09** When the request fails with a non-2xx status or a network error, the dropdown and the displayed assignee return to the previous assignee, and an error toast is shown (approved, UD-08).
- **FRONT-011-AC10** While the request is pending, the dropdown is disabled, and a second change sends no second request.
- **FRONT-011-AC11** The dropdown can be focused with the Tab key, its options can be changed with the arrow keys, and a selection can be committed with the keyboard alone. The focused control has a visible focus indicator.
- **FRONT-011-AC12** At a 360 px wide viewport, the modal and the assignee dropdown fit the viewport with no horizontal scrolling, and the dropdown is at least 44 px high.
- **FRONT-011-AC13** The modal contains no control that creates a card, and `AddCardForm` contains no assignee control, because card creation is title-only (approved, UD-08).

### FRONT-012 CommentList
`CommentList` MUST display a card's comments and let the user add, edit, and delete their own comments.

**Acceptance criteria**
- **FRONT-012-AC01** Each comment shows its author and content, in the order returned by the API.
- **FRONT-012-AC02** Edit and delete controls appear only on comments owned by the current user.
- **FRONT-012-AC03** Submitting an empty or whitespace-only comment sends no request and shows a message.
- **FRONT-012-AC04** A valid comment calls `POST /api/cards/{id}/comments`, and the new comment appears in the list.
- **FRONT-012-AC05** A 403 response to an edit or delete shows an error toast and leaves the list unchanged.
- **FRONT-012-AC06** When the card has no comments, the list shows an empty-state message.

### FRONT-013 BaseButton
`BaseButton` MUST be the shared button component.

**Acceptance criteria**
- **FRONT-013-AC01** It renders its children and calls `onClick` when activated.
- **FRONT-013-AC02** When `disabled`, it has the `disabled` attribute and does not call `onClick`.
- **FRONT-013-AC03** In a loading state, it is disabled, shows a loading indicator, and has `aria-busy="true"`.

### FRONT-014 BaseBadge
`BaseBadge` MUST be the shared badge component.

**Acceptance criteria**
- **FRONT-014-AC01** It renders its children as visible text.
- **FRONT-014-AC02** It applies a `className` passed by the caller to its root element.

### FRONT-015 BaseModal
`BaseModal` MUST be the shared modal dialog component.

**Acceptance criteria**
- **FRONT-015-AC01** When closed, it renders no dialog. When open, it renders its children inside an element with `role="dialog"` and `aria-modal="true"`.
- **FRONT-015-AC02** Pressing Escape calls `onClose`.
- **FRONT-015-AC03** Clicking the backdrop calls `onClose`, and clicking inside the dialog does not.
- **FRONT-015-AC04** On open, keyboard focus moves into the dialog. On close, focus returns to the element that opened it.

### FRONT-016 NotificationBell
`NotificationBell` MUST display the unread notification count, and it MUST let the recipient read, open, and mark as read the notifications returned by `GET /api/notifications` (approved, UD-08). It is a Client Component and uses `useNotifications` for fetching and polling. How the unread count is derived across pages is defined by UD-09, which is unresolved; the criteria below use fewer notifications than one page.

**Acceptance criteria**
- **FRONT-016-AC01** When the unread count from `useNotifications` is greater than 0, the bell shows that number. When it is 0, no number is shown.
- **FRONT-016-AC02** The bell's accessible name includes the unread count.
- **FRONT-016-AC03** Activating an unread notification calls `PATCH /api/notifications/{id}/read` and reduces the displayed count by 1. Activating an already-read notification sends no request and leaves the count unchanged.
- **FRONT-016-AC04** The bell is present on every protected page and absent from `/login` and `/register`.
- **FRONT-016-AC05** Opening the bell shows a list of the notifications returned by `GET /api/notifications` in the order returned. Each item shows its `message`, a readable label for its `type` ("Assignment" for `card_assigned` and "Comment" for `comment_added`), and its timestamp. The timestamp is rendered in a `time` element whose `datetime` attribute is the UTC value of `created_at`.
- **FRONT-016-AC06** Read and unread items are distinguished by more than color: an unread item has a visible "Unread" text label and an accessible name that includes "Unread", and a read item has neither.
- **FRONT-016-AC07** Each unread item has a "Mark as read" control that calls `PATCH /api/notifications/{id}/read`, turns the item into a read item, and reduces the displayed count by 1, without navigating.
- **FRONT-016-AC08** Activating an item navigates to `/boards/{board_id}` of the notification and opens the notification's card in `CardDetailModal` when the card is present in the board data. The item is also marked as read.
- **FRONT-016-AC09** When the notification's card is no longer available because it was soft-deleted, activating the item still marks it as read and opens the board page, which shows the friendly message "This card is no longer available" (FRONT-006-AC12) and no error toast.
- **FRONT-016-AC10** An item displays only its `message`, type label, and timestamp. No item shows comment text, an email address, or any other field.
- **FRONT-016-AC11** When loading notifications or marking one as read fails, the bell shows the generic message "Notifications could not be updated" and no HTTP status, URL, stack trace, or server message, and it keeps the previously displayed notifications and count.
- **FRONT-016-AC12** With fake timers, an authenticated bell shows a new unread notification and the increased count after the poll at 30,000 ms, and the count and list stop updating after the user logs out.
- **FRONT-016-AC13** The bell button, the item list, each item, and each "Mark as read" control can be reached and activated with the keyboard (Tab, Enter, and Space), and the Escape key closes the list and returns focus to the bell button.
- **FRONT-016-AC14** At a 360 px wide viewport, the open list fits the viewport with no horizontal scrolling, and each activatable control is at least 44 px high.

### FRONT-024 BoardCard.tsx
`BoardCard.tsx` MUST be the dashboard tile that represents one board. It is a Server Component with no interactive behavior.

**Acceptance criteria**
- **FRONT-024-AC01** The file exports a TypeScript interface `BoardCardProps` that declares at least `id: string` and `name: string`, and `tsc --noEmit` with `strict` enabled passes with no `any` in the props.
- **FRONT-024-AC02** The component renders the board name inside a link whose `href` is `/boards/` followed by the board `id`.
- **FRONT-024-AC03** The file has no `"use client"` directive and uses no React hooks or event handler props, and rendering it inside a Server Component succeeds.
- **FRONT-024-AC04** Styling uses Tailwind utility classes, and the component sets no inline `style` attribute.
- **FRONT-024-AC05** The file contains no raw `<button>` element. Any button it renders is a `BaseButton`.
- **FRONT-024-AC06** The link has an accessible name that includes the board name.

### FRONT-025 ColumnHeader.tsx
`ColumnHeader.tsx` MUST show a column's name and card count and provide a rename control to every board member. It MUST provide the delete control and the Done/Active toggle only to a Board Administrator, and it MUST NOT offer either to Board Members (approved, UD-05). It is a Client Component.

**Acceptance criteria**
- **FRONT-025-AC01** The file exports a TypeScript interface `ColumnHeaderProps` that declares `columnId: string`, `name: string`, `cardCount: number`, `onRename` with a typed signature, and `onDelete` with a typed signature, `isDone: boolean`, `isAdministrator: boolean`, and `onToggleDone` with a typed signature, and `tsc --noEmit` with `strict` enabled passes with no `any` in the props.
- **FRONT-025-AC02** The component renders the column name and shows the card count in a `BaseBadge`.
- **FRONT-025-AC03** Activating the rename control shows a text input prefilled with the current name. Submitting a non-empty, changed name calls `onRename` once with the column ID and the new name. Pressing Escape closes the input and does not call `onRename`.
- **FRONT-025-AC04** Submitting an empty or whitespace-only name does not call `onRename` and shows a message.
- **FRONT-025-AC05** Activating the delete control asks for confirmation. Confirming calls `onDelete` once with the column ID. Cancelling does not call `onDelete`.
- **FRONT-025-AC06** The file begins with a `"use client"` directive.
- **FRONT-025-AC07** Styling uses Tailwind utility classes. Every button is a `BaseButton`, and the file contains no raw `<button>` element.
- **FRONT-025-AC08** The rename and delete controls have accessible names that include the column name.
- **FRONT-025-AC09** When `isAdministrator` is true, the header renders a toggle control whose accessible name includes the column name and whose `aria-pressed` value equals `isDone`. The header shows the text "Done" when `isDone` is true and "Active" when it is false.
- **FRONT-025-AC10** When `isAdministrator` is false, the toggle control is not present in the DOM. The board view sets `isAdministrator` from the `role` returned by `GET /api/boards/{id}` (BOARD-003-AC06).
- **FRONT-025-AC11** Activating the toggle calls `onToggleDone` once with the column ID and the opposite of `isDone`, and the board view sends `PATCH /api/columns/{id}` with a body whose `is_done` equals that value.
- **FRONT-025-AC12** After the request succeeds, the header shows the new state: the "Done" or "Active" text and `aria-pressed` match the new `is_done`, without a page reload.
- **FRONT-025-AC13** When the request fails with a non-2xx status or a network error, an error toast is shown and the header shows the previous state again.
- **FRONT-025-AC14** While the request is pending, the toggle is a `BaseButton` in its loading state, and a second activation sends no second request.
- **FRONT-025-AC15** After a successful toggle, the board analytics are refreshed: a new request for `GET /api/boards/{id}/analytics` is made, directly or by refreshing the server-rendered data, and the analytics panel shows the new response. After a failed toggle, no analytics request is made.
- **FRONT-025-AC16** When `isAdministrator` is true, the delete control is present. When `isAdministrator` is false, the delete control is not present in the DOM, and the rename control is still present and works.
- **FRONT-025-AC17** When `DELETE /api/columns/{id}` or the toggle request fails with HTTP 403, an error toast shows the `error` message and the column, its cards, and its Done/Active state stay as they were.

### FRONT-026 AddCardForm.tsx
`AddCardForm.tsx` MUST let a user add a card to one column. It is a Client Component.

**Acceptance criteria**
- **FRONT-026-AC01** The file exports a TypeScript interface `AddCardFormProps` that declares `columnId: string` and a typed `onCardCreated` callback, and `tsc --noEmit` with `strict` enabled passes with no `any` in the props.
- **FRONT-026-AC02** Submitting a non-empty title sends `POST /api/columns/{id}/cards` for that column through `apiClient.ts`. On success the form calls `onCardCreated` with the created card and clears the input.
- **FRONT-026-AC03** Submitting an empty or whitespace-only title sends no request and shows a message.
- **FRONT-026-AC04** While the request is pending, the submit `BaseButton` is in its loading state and the input is disabled, and a second submission sends no second request.
- **FRONT-026-AC05** When the request fails, an error is shown through `useErrorHandler` and the input keeps the typed text.
- **FRONT-026-AC06** The file begins with a `"use client"` directive.
- **FRONT-026-AC07** Styling uses Tailwind utility classes. The submit control is a `BaseButton`, and the file contains no raw `<button>` element.
- **FRONT-026-AC08** The title input has a label that provides its accessible name.
- **FRONT-026-AC09** The form has no assignee control, and the request body it sends contains only `title` (approved, UD-08).

### 4.4 State, hooks, and utilities

### FRONT-017 useNotifications
`useNotifications` MUST poll `GET /api/notifications` every 30 seconds. It runs in the browser, so its requests go through the same-origin proxy (FRONT-023).

**Acceptance criteria**
- **FRONT-017-AC01** With fake timers, the hook makes 1 request on mount, still 1 request at 29,999 ms, and 2 requests at 30,000 ms.
- **FRONT-017-AC02** After the component unmounts, no further requests are made.
- **FRONT-017-AC03** The hook makes no request while the user is unauthenticated.
- **FRONT-017-AC04** The hook returns the unread count and a function that calls `PATCH /api/notifications/{id}/read`.
- **FRONT-017-AC05** When a poll fails, the failure is reported through `useErrorHandler` with the generic message "Notifications could not be updated" instead of the server's `error` text (FRONT-016-AC11), and the next poll still occurs 30 seconds later.
- **FRONT-017-AC06** Repeated poll failures show at most one error indication until a poll succeeds, so a failing API does not stack an error toast every 30 seconds. The indication contains no HTTP status, URL, or stack trace (approved, UD-08).

### FRONT-018 AuthContext
`AuthContext` MUST hold the authentication state for Client Components. It MUST expose `currentUser`, a `session` value, `login()`, `logout()`, and `updateProfile()`. With the approved HttpOnly cookie architecture (UD-03), `session` is a secure representation that contains no JWT: it holds only an authenticated flag and the session expiry time. Its initial `currentUser` comes from the server (Section 4.1, root layout).

**Acceptance criteria**
- **FRONT-018-AC01** The context exposes `currentUser`, `session`, `login`, `logout`, and `updateProfile`.
- **FRONT-018-AC02** After `login()` succeeds, `currentUser` equals the returned profile and `session` is authenticated. After `logout()`, `currentUser` is null and `session` is not authenticated.
- **FRONT-018-AC03** After a full page reload with an unexpired session cookie, `currentUser` is populated again from the server-provided initial value, without a login prompt.
- **FRONT-018-AC04** A session whose expiry time has passed is treated as unauthenticated: `currentUser` is null and protected pages redirect to `/login`.
- **FRONT-018-AC05** The module is a Client Component.
- **FRONT-018-AC06** `updateProfile({ name, email })` sends `PATCH /api/users/me` with a body that contains only `name` and `email`.
- **FRONT-018-AC07** After `updateProfile()` succeeds, `currentUser.name` and `currentUser.email` equal the values in the response `data`, without a page reload.
- **FRONT-018-AC08** When `updateProfile()` fails with HTTP 400 or 409, `currentUser` is unchanged and the call rejects with the API error.
- **FRONT-018-AC09** The JWT string does not appear in the `AuthContext` value, in `document.cookie`, in `localStorage`, or in `sessionStorage`.

### FRONT-019 useDragAndDrop
`useDragAndDrop` MUST move cards and columns by drag-and-drop with optimistic updates and rollback.

**Acceptance criteria**
- **FRONT-019-AC01** When a card is dropped on another column, the card appears in the target column before the API response arrives.
- **FRONT-019-AC02** The drop calls `PATCH /api/cards/{id}/position` with the target `column_id` and a positive float `order`.
- **FRONT-019-AC03** Whenever a distinct positive float exists strictly between the `order` values of the two neighboring cards, the `order` sent is strictly between them (the midpoint). When dropped before the first card it is positive and less than the first card's `order`, and when dropped after the last card it is greater than the last card's `order`, whenever such a value exists. When dropped into an empty column it is positive. FRONT-019-AC14 covers the case in which no such value exists.
- **FRONT-019-AC04** If the API call fails with any non-2xx status or a network error, the card returns to its previous column and its previous place in that column, and an error toast is shown.
- **FRONT-019-AC05** Dropping a card at its original location sends no request.
- **FRONT-019-AC06** Dragging a column calls `PATCH /api/boards/{id}/columns/reorder` with positive float `order` values in the body defined by COLUMN-004, and a failed call restores the previous column order and shows an error toast.
- **FRONT-019-AC07** While a search filter hides some cards, a card dropped in a column gets an `order` computed from its neighbors among all cards in that column, including hidden ones.
- **FRONT-019-AC08** An ordinary column drag sends one request whose `columns` list has exactly one entry: the moved column's `id` and its new `order`. That `order` is strictly between the `order` values of the two neighboring columns, less than the first column's `order` (and positive) when dropped first, and greater than the last column's `order` when dropped last. Dropping a column at its original place sends no request.
- **FRONT-019-AC09** After a successful column reorder, the displayed columns are replaced by the `data` array of the response, in the order returned, so the page shows the server's authoritative `order` values.
- **FRONT-019-AC10** When the request fails with HTTP 400 or 409, the previous column order is restored, an error toast is shown, and the frontend refetches the latest board state with `GET /api/boards/{id}` (through the server-rendered data or the proxy) and shows it.
- **FRONT-019-AC11** When no distinct float lies strictly between the `order` values of the two neighboring columns (the midpoint equals one of them), the frontend sends one request that lists every active column it has loaded exactly once, with distinct positive `order` values that give the intended final order (for example 1024.0, 2048.0, and 3072.0). The request uses the same endpoint and body, with no flag.
- **FRONT-019-AC12** An ordinary drag, whose neighbors have a distinct midpoint, never sends a normalization request, and no minimum gap threshold is applied.
- **FRONT-019-AC13** When the normalization request fails with HTTP 400 or 409, no partial result is shown: the previous column order is restored, an error toast is shown, and the frontend refetches the latest board state.
- **FRONT-019-AC14** When no distinct positive float exists strictly between the `order` values of the neighbors of a dropped card (the computed midpoint equals a neighbor's `order`, or no positive value is smaller than the first card's `order`), the frontend sends the `order` of the neighbor that must follow the dropped card, so that the service layer resolves the tie and rebalances (approved, UD-06). The request is the same `PATCH /api/cards/{id}/position` with the same body shape.
- **FRONT-019-AC15** An ordinary card drop, whose neighbors have a distinct midpoint, sends the midpoint and nothing else. The frontend applies no minimum-gap threshold, sends no separate rebalance request, and sends no `rebalanced` field.
- **FRONT-019-AC16** After a successful card move, the card's displayed `order` is the `order` in the response. When `rebalanced` is true, the frontend refetches the latest board state and replaces the `order` of all displayed cards, with no partial result shown.

### FRONT-020 useErrorHandler
`useErrorHandler` MUST turn errors into user-visible messages.

**Acceptance criteria**
- **FRONT-020-AC01** Given an API error carrying an `error` message, the handler shows an error toast with that message.
- **FRONT-020-AC02** Given a network failure, the handler shows an error toast stating that the server could not be reached.
- **FRONT-020-AC03** Given an unknown error, the handler shows a generic error toast and does not throw.
- **FRONT-020-AC04** No displayed message contains a stack trace.

### FRONT-021 Server and Client Component boundaries
The frontend MUST follow the component types in Section 4.1. The `/` and `/boards/[id]` pages MUST be Server Components. Interactive forms, modals, drag-and-drop, and notification controls MUST be Client Components.

**Acceptance criteria**
- **FRONT-021-AC01** `next build` completes with no error about hooks or browser APIs used in a Server Component.
- **FRONT-021-AC02** The root layout file has no `"use client"` directive.
- **FRONT-021-AC03** The page files for `/` and `/boards/[id]` contain no `"use client"` directive, and the files for `BoardCard` and `BaseBadge` contain no React hooks or event handlers.
- **FRONT-021-AC04** The files for `BaseModal`, `CardDetailModal`, `AddCardForm`, `ColumnHeader`, `CommentList`, `NotificationBell`, the board view container that uses `useDragAndDrop`, and every form component begin with a `"use client"` directive.

### FRONT-022 Authenticated data fetching
Server Components MUST fetch authenticated data on the Next.js server with the JWT read from the HttpOnly session cookie. Client Components MUST send authenticated requests through the same-origin proxy (FRONT-023). Browser JavaScript MUST NOT read, store, or send the JWT.

**Acceptance criteria**
- **FRONT-022-AC01** Each request from the Next.js server to Flask on behalf of a user carries `Authorization: Bearer <token>` taken from the session cookie (A-07). Each request from browser code to the proxy carries the session cookie and no `Authorization` header.
- **FRONT-022-AC02** While a Server Component page's data request is pending, the route shows a loading UI that contains an element with `role="status"`.
- **FRONT-022-AC03** A 401 response from Flask during server rendering clears the session cookie and redirects to `/login`. A 401 response to a proxied client request clears the session cookie and navigates to `/login`.
- **FRONT-022-AC04** While a client-side mutation is pending, the `BaseButton` that triggered it is in its loading state, and a second activation sends no second request.

### FRONT-023 Cookie session and server-side proxy
The Next.js server MUST keep the JWT in an HttpOnly cookie, read it only through a server-only session module, and forward it to Flask in the `Authorization: Bearer` header. Browser JavaScript, `AuthContext`, and Client Component props MUST NOT receive the raw JWT. This requirement implements the approved decision UD-03. The token lifetime (UD-01) and refresh strategy (UD-02) are unresolved. The cookie lifetime follows whatever token lifetime is approved.

**Acceptance criteria**
- **FRONT-023-AC01** After a successful login through the session login route handler, the response sets exactly one session cookie with these attributes: `HttpOnly`; `Secure` in production (it MAY be omitted only for local development over `http://localhost`); `SameSite=Lax`; `Path=/`; no `Domain` attribute, so the cookie is host-only; and a `Max-Age` equal to the remaining lifetime of the JWT, so the cookie expires no later than the JWT `exp` time.
- **FRONT-023-AC02** The login response body returned to the browser contains the user profile and does not contain the JWT string.
- **FRONT-023-AC03** `document.cookie` does not list the session cookie, and the JWT string does not appear in any response body, page HTML, React Server Component payload, `localStorage`, or `sessionStorage`.
- **FRONT-023-AC04** For an authenticated proxy request, the Next.js server calls Flask with `Authorization: Bearer <token>` taken from the cookie, and the browser request itself carries no `Authorization` header.
- **FRONT-023-AC05** A proxy request with no session cookie returns HTTP 401 with an `error` body and is not forwarded to Flask. The exceptions are `POST /api/auth/register` and `GET /api/health`, which are forwarded without an `Authorization` header.
- **FRONT-023-AC06** When Flask returns HTTP 401 to a proxied request, the proxy expires the session cookie and returns HTTP 401.
- **FRONT-023-AC07** The proxy forwards only to paths under `/api` on the host in `API_BASE_URL`, and a request for any other path or host is rejected with HTTP 404 and not forwarded.
- **FRONT-023-AC08** Every POST, PATCH, or DELETE request to the proxy and to the session login and logout route handlers must carry an `Origin` header equal to the application's own origin. A request with a different or missing `Origin` returns HTTP 403 and is not forwarded or processed (CSRF protection).
- **FRONT-023-AC09** Importing the server-side session module into a Client Component causes `next build` to fail.
- **FRONT-023-AC10** The logout route expires the session cookie, and a following protected request is rejected with HTTP 401 or a redirect to `/login`.
- **FRONT-023-AC11** The generic proxy does not forward `POST /api/auth/login`. A browser request for it through the proxy returns HTTP 404. Login is handled only by the session login route handler, so no response sent to the browser contains the JWT.
- **FRONT-023-AC12** A request for a protected page whose cookie holds a JWT with an `exp` time in the past, or a JWT that Flask rejects with HTTP 401, is redirected to `/login`, and the response expires the stale session cookie.
- **FRONT-023-AC13** The proxy discards any `Authorization` header and any `Cookie` header sent by the browser, and calls Flask with only the `Authorization: Bearer` header built from the session cookie.
- **FRONT-023-AC14** A POST, PATCH, or DELETE request to the proxy whose `Content-Type` is not `application/json` returns HTTP 415 and is not forwarded.
- **FRONT-023-AC15** Page files and Client Components contain no direct read of the session cookie. Server Components obtain authentication only through the server-only session module.

### 4.5 API client and utilities

### API-005 apiClient.ts
`apiClient.ts` MUST be the single module through which the frontend calls the API. It MUST support server-side use (Server Components and the Next.js session layer) and client-side use (Client Components). Server-side calls go directly to Flask. Authenticated client-side calls go to the same-origin Next.js proxy (FRONT-023). Direct browser calls to Flask are limited to `GET /api/health`. The raw JWT is never available to `apiClient.ts` in the browser.

**Acceptance criteria**
- **API-005-AC01** Server-side calls use the `API_BASE_URL` environment variable. Direct browser calls use the `NEXT_PUBLIC_API_BASE_URL` environment variable. Both are listed in the frontend `.env.example`.
- **API-005-AC02** In server-side mode, when the session cookie holds a JWT, each request to Flask includes `Authorization: Bearer <token>`. In client-side mode, an authenticated request is sent to the same-origin proxy with the session cookie, and no `Authorization` header is set by browser code.
- **API-005-AC03** For a 2xx response, the call resolves with the value of the `data` key.
- **API-005-AC04** For a non-2xx response, the call rejects with an error from `errors.ts` carrying the HTTP status and the `error` message.
- **API-005-AC05** A 401 response to a request other than login, in client-side mode, clears `currentUser` in `AuthContext` and navigates to `/login`. In server-side mode, it triggers a server redirect to `/login`.
- **API-005-AC06** A 401 response to the login request does not navigate and rejects with the `error` message.
- **API-005-AC07** When the network request fails, the call rejects with the network error type from `errors.ts`.
- **API-005-AC08** Direct browser mode (`NEXT_PUBLIC_API_BASE_URL`) is used only for `GET /api/health`. A test finds that no other endpoint is requested in this mode.
- **API-005-AC09** Server-side and client-side modes expose the same call signature and both resolve with the `data` value.
- **API-005-AC10** A successful DELETE call resolves with an object whose `id` equals the deleted resource's ID, and the client never treats an empty body or an HTTP 204 as a successful delete (approved, UD-19).

### API-006 errors.ts
`errors.ts` MUST define the frontend error types.

**Acceptance criteria**
- **API-006-AC01** The module exports an API error type carrying `status` and `message`, and a network error type.
- **API-006-AC02** The statuses 400, 401, 403, 404, and 500 and above map to distinct error kinds that callers can distinguish.
- **API-006-AC03** Given a response body `{ "error": "X" }`, the error message is `X`. Given a body without an `error` string, the message is a fixed fallback string.

### API-007 toast.ts
`toast.ts` MUST wrap react-hot-toast for the application.

**Acceptance criteria**
- **API-007-AC01** The module exports a success function and an error function that display the given message.
- **API-007-AC02** The toast container is mounted exactly once, in the root layout.
- **API-007-AC03** Calling the error function with a message renders that message text in the document.

## 5. Testing Requirements

### TEST-001 Backend test suite
The backend MUST have a pytest suite that covers every endpoint in Section 3.0.

**Acceptance criteria**
- **TEST-001-AC01** Running `pytest` in the backend exits with code 0.
- **TEST-001-AC02** A test compares the Flask URL map with the endpoint list in Section 3.0 (the 26 mandatory endpoints and the approved membership extension). It fails if a listed endpoint is missing or has no test, or if the map contains any other route under `/api`.
- **TEST-001-AC03** The test configuration uses a database separate from the production Supabase database.
- **TEST-001-AC04** A parametrized contract test covers each of the 27 endpoints (the 26 mandatory endpoints and the approved extension) and asserts the success status of Section 2.3, the `{ "data": ... }` envelope with no `error` key, the `Content-Type: application/json` header, and the `data` type (an object, or an array for the three list endpoints of API-001-AC06). It asserts the exact bodies of the login response (`{ "access_token": ... }`), the health response (`{ "status": "ok" }`), and the four delete responses (`{ "id": ... }`, with a repeated delete returning 404 and no HTTP 204). The three pending contracts of API-001 are excluded.
- **TEST-001-AC05** Tests assert the error envelope for each of the statuses 400, 401, 403, 404, 405, 409, 415, and 500: the body is a JSON object with a non-empty `error` string and no `data` key. They trigger 405 with an unsupported method, 415 with an unsupported content type, and 500 through a failing route that exists only in the test configuration, and assert that the 500 message is generic and contains no stack trace, SQL, token, or exception class name (API-002-AC04, AC05).

### TEST-002 Comment response tests
The backend suite MUST test the comment status codes.

**Acceptance criteria**
- **TEST-002-AC01** A test asserts HTTP 201 for creating a valid comment.
- **TEST-002-AC02** A test asserts HTTP 400 for creating a comment with missing content.
- **TEST-002-AC03** A test asserts HTTP 401 for a comment request with no token.
- **TEST-002-AC04** A test asserts HTTP 403 when a non-owner edits a comment and when a non-owner deletes a comment.

### TEST-003 Authorization tests
The backend suite MUST test authentication and board-scoped authorization.

**Acceptance criteria**
- **TEST-003-AC01** A parametrized test asserts HTTP 401 with no token for every protected endpoint.
- **TEST-003-AC02** A test asserts HTTP 401 for an expired token.
- **TEST-003-AC03** A parametrized test asserts HTTP 404 for a non-member on every board-scoped endpoint.
- **TEST-003-AC04** A parametrized test asserts HTTP 403 for a non-administrator member, with a valid body, on each of the five administrator-only operations in Section 2.1, and asserts that the target rows are unchanged (approved, UD-05).
- **TEST-003-AC05** A parametrized test asserts HTTP 403 for a non-administrator member on each of the five administrator-only operations when the body is invalid, empty, unchanged, or mixed with allowed fields. It includes an `is_done` value that is invalid, an `is_done` value equal to the stored value, `name` together with `is_done`, an empty board name, and a member-add body with a missing `email` or an extra `role` field. It asserts that no field changed.
- **TEST-003-AC06** A test asserts that Flask returns HTTP 401 when the JWT is supplied only in a cookie.
- **TEST-003-AC07** A test asserts that `GET /api/boards/{id}` reports the role `administrator` for the board creator and `member` for a user added through `POST /api/boards/{id}/members`.
- **TEST-003-AC08** A parametrized test asserts that a Board Administrator succeeds at each of the five administrator-only operations (HTTP 200, or 201 for member add) and that each effect is visible afterward.
- **TEST-003-AC09** A parametrized test with a user who is an administrator of board A and a member of board B asserts success on board A and HTTP 403 with no change on board B for each of the five operations.
- **TEST-003-AC10** A parametrized test asserts that, for each of the five administrator-only operations and each member-allowed operation, the status and body returned to a non-member are identical to those returned for a resource ID that does not exist.
- **TEST-003-AC11** A parametrized test asserts that a Board Member who is not an administrator succeeds at each member-allowed operation listed in BOARD-006-AC04.
- **TEST-003-AC12** A parametrized test over the actor roles administrator and member asserts that a non-owner receives HTTP 403 when editing or deleting another user's comment, and that an owner receives HTTP 200, with the comment unchanged after each 403.
- **TEST-003-AC13** A parametrized test asserts that a rejected mutation (HTTP 400, 403, 404, or 409) on each mutating endpoint leaves a before-and-after snapshot of all rows, including `updated_at`, unchanged and creates no activity event or notification.
- **TEST-003-AC14** Tests assert the check order in Section 2.4: no token with an invalid body returns 401, a non-member with an administrator-only request returns 404, a member with an administrator-only request and an invalid body returns 403, an administrator with an invalid body returns 400, a duplicate member returns 409, and an unparseable JSON body returns 400 for any caller.
- **TEST-003-AC15** Tests assert the member-list privacy rules in BOARD-003-AC08 to AC11: a member sees the complete `members` list, each entry has exactly `id` and `name`, no email or hash appears anywhere in the response, a user of another board is never listed, a non-member receives the uniform 404 without member data, the previously required fields are still present, and the URL map has no separate member-list route.

### TEST-004 Position and analytics tests
The backend suite MUST test FLOAT positioning and analytics.

**Acceptance criteria**
- **TEST-004-AC01** Tests cover the valid and invalid cases in CARD-006-AC01, CARD-006-AC02, and CARD-006-AC03 against `CardPositionSchema`.
- **TEST-004-AC02** A test asserts the Card position column type is `Float`.
- **TEST-004-AC03** A test asserts that the analytics service emits SQL containing `JOIN`.
- **TEST-004-AC04** Tests cover the `completed_at` rules in CARD-002-AC06, CARD-005-AC07 to AC11, and COLUMN-002-AC08 and AC09, the `is_done` rules in COLUMN-002-AC05 to AC07, and the column model in COLUMN-005-AC01 to AC03.
- **TEST-004-AC05** Tests cover the activity events in ANALYTICS-006-AC01 to AC08 and AC11.
- **TEST-004-AC06** Tests cover BOARD-007-AC01 to AC10.
- **TEST-004-AC07** Tests cover the `is_done` rules in COLUMN-002-AC11 to AC14: an unchanged or repeated `is_done` leaves every card's `completed_at` unchanged and creates no event or notification, a changed value applies the completion rules in one transaction, and a forced failure leaves the column and its cards unchanged.
- **TEST-004-AC08** The analytics tests use a frozen server clock and never the real current date. A test asserts the window for these fixed instants: `2025-01-15T12:00:00Z` (a Wednesday), `2025-01-13T00:00:00Z` (a Monday at the start of the week), `2025-01-19T23:59:59.999999Z` (the last instant of a week), and `2025-01-20T00:00:00Z` (the next week). A test run with the process time zone set to `Asia/Jakarta` produces the same windows (ANALYTICS-001-AC04, ANALYTICS-005-AC04).
- **TEST-004-AC09** Tests cover the completed-card count in ANALYTICS-003-AC01 to AC13: counting, the Monday start inclusion, the next-Monday exclusion, Sunday fractional-second inclusion, week rollover, reopened and recompleted cards, done-to-done moves, done-column toggling, soft-deleted card and column exclusion, the `completed_at` invariant after a sequence of operations, and independence from activity events.
- **TEST-004-AC10** Tests cover member activity in ANALYTICS-004-AC01 to AC11: boundary inclusion and exclusion, rollover, three distinct moves counting as three, zero counts for current members, inclusion of events of soft-deleted cards, columns, and comments, exclusion of events of other boards, exclusion of non-qualifying actions, members who joined mid-week, and users without a current membership.
- **TEST-004-AC11** Tests cover the response contract in ANALYTICS-001-AC01 to AC09: the exact keys and value types, the UTC `Z` timestamp format, the ordering of `cards_per_column` and of `member_activity` including ties on `activity_count` and `name`, explicit empty arrays and zero counts for an empty board, the absence of email addresses, HTTP 400 for any query parameter, and the 401 and 404 precedence.
- **TEST-004-AC12** A test seeds a board with cards in done and active columns, soft-deleted cards, a soft-deleted column, and events of several members and of another board, and asserts the full analytics response (the `window`, every `card_count`, `completed_this_week`, and every `activity_count`) against hand-computed expected values under a frozen clock.
- **TEST-004-AC13** Tests cover a partial column reorder in COLUMN-004-AC10, AC11, and AC13: a single moved column, two columns at once, an exchange of two `order` values, and the exact preservation of unlisted columns. They also cover a full normalization request that lists every active column once (COLUMN-004-AC26).
- **TEST-004-AC14** Tests cover the invalid requests in COLUMN-004-AC02, AC03, AC06, AC07, and AC08 with no change to any column: `order` values of 0, negative, boolean, string, null, `NaN`, `Infinity`, `1e400`, and `1e-400`, nonexistent, foreign-board, and soft-deleted column IDs with identical response bodies, malformed bodies and extra keys, invalid UUIDs, and duplicate IDs.
- **TEST-004-AC15** Tests cover duplicate `order` values within a request (COLUMN-004-AC09, HTTP 400) and a collision with an unlisted active column (COLUMN-004-AC12, HTTP 409), and assert that no column changes in either case.
- **TEST-004-AC16** A test forces a failure after some columns were updated and asserts that no column has a changed `order` afterward, and a test records the SQL to assert that the board row is locked with `FOR UPDATE` before the active columns are read (COLUMN-004-AC14, AC15).
- **TEST-004-AC17** Tests run on separate database connections: two reorders that collide return one 200 and one 409, two reorders that do not collide both succeed, and a reorder that runs against a concurrent column creation or deletion never leaves duplicate `order` values or a changed `order` on a soft-deleted column (COLUMN-004-AC16, AC17, COLUMN-001-AC05, COLUMN-003-AC15).
- **TEST-004-AC18** A test asserts that a no-op reorder returns HTTP 200 with the complete array, issues no column `UPDATE`, and leaves every `updated_at` unchanged. A test asserts that only a changed column gets a new `updated_at` (COLUMN-004-AC20, AC21).
- **TEST-004-AC19** Tests assert the response contract of COLUMN-004-AC18 and AC19 and the `order` mapping of COLUMN-004-AC25, CARD-001-AC11, and COLUMN-005-AC07: no response of the reorder, board, column creation, card creation, or card position endpoints contains a `position` key, and each contains `order` equal to the stored `position` value.
- **TEST-004-AC20** Tests assert that a reorder creates no activity event and no notification, that an administrator and a member both succeed, and that the check order of COLUMN-004-AC24 holds (COLUMN-004-AC22 to AC24).
- **TEST-004-AC21** Tests cover the deterministic card rebalancing of CARD-005-AC14 to AC17: a move without a tie keeps the submitted `order` and `rebalanced` false, a tie places the moved card immediately before the tied card and renumbers the column to 1024.0, 2048.0, 3072.0 in the final sequence, ties with soft-deleted cards, with cards of other columns, and with the moved card itself are not ties, and soft-deleted cards keep their `order`.
- **TEST-004-AC22** Tests assert the response contract of CARD-005-AC21 to AC23: `data` has the moved card's `id`, `column_id`, the authoritative `order`, and a boolean `rebalanced`, with no `position` key, the `order` equals the following board response, `rebalanced` is false for an ordinary move and a no-op, and a no-op writes nothing.
- **TEST-004-AC23** A test forces a failure after some cards were renumbered and asserts that no card has a changed `order`, `column_id`, or `completed_at` and that no event exists (CARD-005-AC18). A rejected request changes no card's `order` (CARD-005-AC26).
- **TEST-004-AC24** Tests run on separate database connections: two moves into the same column with the same `order` are serialized, both succeed, exactly one rebalances, and the final `order` values are pairwise distinct. A card creation concurrent with a move into the same column never produces duplicate `order` values, and a move concurrent with the soft-deletion of its destination column never leaves an active card in a deleted column (CARD-005-AC19, AC20, CARD-002-AC10).
- **TEST-004-AC25** Tests assert that rebalancing records no activity event beyond the one card-moved event of a move to another column, creates no notification, leaves the `completed_at`, `assignee_id`, and `column_id` of the renumbered cards unchanged, and sets a new `updated_at` only on cards whose `order` changed (CARD-005-AC24, AC25).
- **TEST-004-AC26** Tests assert the `CardPositionSchema` rules of CARD-006-AC04 and AC05: booleans, null, numeric strings, `NaN`, `Infinity`, `1e400`, `1e-400`, and unknown keys such as `position` and `rebalanced` are rejected.

### TEST-005 Frontend component tests
The frontend MUST have React Testing Library tests for its components and hooks.

**Acceptance criteria**
- **TEST-005-AC01** Running the frontend test command exits with code 0.
- **TEST-005-AC02** A test file exists for each of `CardDetailModal`, `CommentList`, `BaseButton`, `BaseBadge`, `BaseModal`, `NotificationBell`, `BoardCard`, `ColumnHeader`, and `AddCardForm`.
- **TEST-005-AC03** A test with fake timers verifies the 300 ms debounce boundaries in FRONT-008-AC01.
- **TEST-005-AC04** A test with fake timers verifies the 30,000 ms polling boundaries in FRONT-017-AC01.
- **TEST-005-AC05** A test verifies that `useDragAndDrop` rolls back a card move when the API call fails.
- **TEST-005-AC06** Tests cover the session layer and the proxy route handlers in FRONT-023-AC01 to AC08, AC11, AC13, and AC14, using a mocked Flask API.
- **TEST-005-AC07** Tests cover `AuthContext.updateProfile()` in FRONT-018-AC06 to AC08.
- **TEST-005-AC08** Tests cover the Done/Active toggle and the delete control in FRONT-025-AC09 to AC17: visibility by role, the request body, the success state, rollback on failure, the analytics refresh, and a 403 response.
- **TEST-005-AC09** Tests cover the assignee dropdown in FRONT-011-AC05 to AC13: the displayed assignee, the member options and the "Unassigned" option, the request body for an assignment and an unassignment, the success state, restoring the previous assignee with an error toast on failure, the pending state, keyboard operation, and the absence of assignment controls in `AddCardForm`.
- **TEST-005-AC10** Tests cover `NotificationBell` in FRONT-016-AC05 to AC14 and `useNotifications` in FRONT-017-AC06: the item content, the read and unread distinction, marking as read, navigation to the board, the "This card is no longer available" state, the absence of comment text, a generic error message, polling with fake timers, and keyboard operation.
- **TEST-005-AC11** Tests cover the analytics panel in FRONT-007-AC03 to AC08: the week label computed in UTC for a week inside a month, across a month, and across a year, run with the process time zone set to `Asia/Jakarta` and `America/Los_Angeles`, zero counts displayed as 0, the empty-board message, the order of members as returned, the absence of time zone and range controls, and the refresh after card and Done/Active mutations.

### TEST-006 Playwright suite rules
Playwright end-to-end tests MUST run against the deployed Vercel frontend.

**Acceptance criteria**
- **TEST-006-AC01** The Playwright base URL is read from an environment variable, and the test run fails with a clear error if it is unset.
- **TEST-006-AC02** A search of the Playwright test directory finds zero occurrences of `waitForTimeout`.
- **TEST-006-AC03** Tests wait only through Playwright auto-waiting locators and web-first assertions, or on network responses.
- **TEST-006-AC04** The E2E account email and password are read from environment variables, and the repository contains no E2E credentials.
- **TEST-006-AC05** Every board and card created by a test has a name that contains a unique run identifier.
- **TEST-006-AC06** After the run, whether it passes or fails, no board whose name contains the run identifier remains in the E2E account.
- **TEST-006-AC07** Tests read and modify only data they created, and never touch other users' data.

### TEST-007 Playwright authentication scenarios
Playwright MUST cover four authentication scenarios.

**Acceptance criteria**
- **TEST-007-AC01** Successful login: submitting the E2E account's valid credentials on `/login` navigates to `/`.
- **TEST-007-AC02** Invalid credentials: submitting a wrong password shows a visible error message and the URL remains `/login`.
- **TEST-007-AC03** Unauthenticated redirect: visiting a protected page with no session navigates to `/login`.
- **TEST-007-AC04** Post-logout redirect: after logging in and logging out, visiting a protected page navigates to `/login`.
- **TEST-007-AC05** Cookie protection: after login, the browser context reports the session cookie with `httpOnly` true, and `document.cookie`, `localStorage`, and `sessionStorage` do not contain the JWT.

### TEST-008 Playwright Kanban journey
Playwright MUST cover the approved eight-step Kanban journey in a single test.

**Acceptance criteria**
- **TEST-008-AC01** Step 1: the test logs in as the E2E account and reaches `/`.
- **TEST-008-AC02** Step 2: the test creates a uniquely named board, and the board appears on `/`.
- **TEST-008-AC03** Step 3: the test adds two columns, and the board page shows them in the order they were added.
- **TEST-008-AC04** Step 4: the test creates a uniquely named card in the first column, and it appears there.
- **TEST-008-AC05** Step 5: the test opens the card, and `CardDetailModal` shows the card's title.
- **TEST-008-AC06** Step 6: the test drags the card to the second column, and the card appears in the second column.
- **TEST-008-AC07** Step 7: after the drag, the board data from the API shows the card in the second column with a positive float `order`.
- **TEST-008-AC08** Step 8: after a page reload, the card is still shown in the second column.

### TEST-009 Playwright responsive tests
Playwright MUST verify layouts at mobile and desktop widths.

**Acceptance criteria**
- **TEST-009-AC01** Playwright projects run the layout checks at a 360 px wide viewport and at a 1920 px wide viewport.
- **TEST-009-AC02** At both widths, on each page in Section 4.2, the document's scroll width does not exceed its client width.

### TEST-010 Deletion and retention tests
The backend pytest suite MUST cover soft deletion of columns and cards, preservation of card foreign keys, hard deletion of boards, activity-event retention (approved, UD-18 and UD-23), and the administrator-only authorization of column and board deletion (approved, UD-05). These tests run against PostgreSQL.

**Acceptance criteria**
- **TEST-010-AC01** A test, acting as a Board Administrator, deletes a column that holds 3 non-deleted cards and asserts HTTP 200, a non-null `deleted_at` on the column and on all 3 cards, and identical `deleted_at` values (COLUMN-003-AC03, AC04).
- **TEST-010-AC02** A test asserts that, after the deletion, all card rows and the column row still exist and every card keeps its `column_id` (COLUMN-003-AC06), and that the database has a non-null foreign key from the card's `column_id` to the column (CARD-001-AC09).
- **TEST-010-AC03** A test forces a failure between marking the column and marking its cards and asserts that the column and all its cards are unchanged (COLUMN-003-AC07).
- **TEST-010-AC04** A test deletes a column that holds one previously soft-deleted card and asserts that the card keeps its original `deleted_at` (COLUMN-003-AC05).
- **TEST-010-AC05** A test creates a card-created event, a card-moved event, and a comment-created event, then soft-deletes the column and its cards, then deletes the comment. It asserts that every event row still exists with unchanged values and that the members' activity counts are unchanged (ANALYTICS-006-AC09, ANALYTICS-004-AC06).
- **TEST-010-AC06** A test asserts that the board response, the analytics response, and `GET /api/cards?assignee=me` exclude soft-deleted columns and cards (BOARD-003-AC07, ANALYTICS-002-AC03, CARD-007-AC06).
- **TEST-010-AC07** A parametrized test asserts HTTP 404 and no change for these operations on a soft-deleted resource: `PATCH` and `DELETE /api/columns/{id}`, `POST /api/columns/{id}/cards`, `PATCH` and `DELETE /api/cards/{id}`, `PATCH /api/cards/{id}/position`, and the four comment endpoints of a soft-deleted card.
- **TEST-010-AC08** A test hard-deletes a board that holds every kind of dependent row, including soft-deleted columns and cards, comments, notifications, memberships, and activity events. It asserts HTTP 200, zero remaining dependent rows, and that another board and all users are untouched (BOARD-005-AC04 to AC07).
- **TEST-010-AC09** A test runs a sequence of creates, moves, column deletions, and card deletions and then asserts that no card with a null `deleted_at` references a column with a non-null `deleted_at` (CARD-001-AC10).
- **TEST-010-AC10** A test asserts that the Flask URL map contains no restore or undelete route (COLUMN-003-AC12).
- **TEST-010-AC11** A test sends `DELETE /api/columns/{id}` as a Board Member who is not an administrator and asserts HTTP 403 and that the column, every card of the column, and all their `deleted_at`, `updated_at`, and `column_id` values are unchanged and no activity event exists (COLUMN-003-AC13).
- **TEST-010-AC12** A test asserts that a Board Member's `DELETE /api/columns/{id}` on an already soft-deleted column returns HTTP 404 and not 403, and that no `deleted_at` value changes (COLUMN-003-AC09, Section 2.4).
- **TEST-010-AC13** A test with a user who is an administrator of another board and a member of the column's board asserts HTTP 403 and no change (COLUMN-003-AC14).
- **TEST-010-AC14** A test sends `DELETE /api/boards/{id}` as a Board Member who is not an administrator and asserts HTTP 403 and that the board and every dependent row, including soft-deleted columns and cards, are unchanged (BOARD-005-AC03).

### TEST-011 Notification tests
The backend pytest suite MUST cover notification creation, the events that do not notify, duplicate prevention, transactional behavior, recipient-only access, retention, and removal with the board (approved, UD-08). These tests run against PostgreSQL.

**Acceptance criteria**
- **TEST-011-AC01** A parametrized test asserts the event matrix of NOTIF-003-AC01 to AC11: initial assignment, reassignment to the new assignee only, self-assignment, unassignment, assignment after unassignment, an unchanged `assignee_id`, a comment by a non-assignee, a comment by the assignee, a comment on an unassigned card, and every non-event listed in NOTIF-003-AC11. Each case asserts the exact notifications created, including their `type`, recipient, and `actor`.
- **TEST-011-AC02** A test sends two identical assignment requests concurrently on separate database connections and asserts exactly one notification and one assignee change (NOTIF-003-AC08).
- **TEST-011-AC03** Tests force a failure at each step of an assignment and of a comment creation, before and after the notification is stored, and assert that neither the originating change nor a notification exists afterward (NOTIF-003-AC12, AC13). They also assert that a rejected request (400, 401, 403, 404, 409) creates no notification (NOTIF-003-AC14).
- **TEST-011-AC04** Tests assert recipient-only access: user B never sees user A's notifications in `GET /api/notifications`, and B's `PATCH /api/notifications/{id}/read` for A's notification returns the same 404 as for an unknown ID and leaves it unread, including when A and B share a board (NOTIF-001-AC01, NOTIF-002-AC03, NOTIF-002-AC07).
- **TEST-011-AC05** Tests assert that notifications remain listed and can be marked as read after the card is soft-deleted, after its column is soft-deleted, and after the comment is deleted (NOTIF-003-AC17, NOTIF-002-AC06, CARD-004-AC09).
- **TEST-011-AC06** A test deletes a board that has notifications for several recipients and asserts that none remain for that board or its cards and that notifications of another board are unchanged (NOTIF-003-AC18).
- **TEST-011-AC07** Tests assert the item contract of NOTIF-001-AC06 to AC08, including key names and types, the descending order with equal `created_at` values ordered by `id` descending, and that no message contains comment text or an email address.
- **TEST-011-AC08** A test assigns B, unassigns, assigns B again, and then reassigns to C and back to B, and asserts that B has the expected number of notifications. A schema introspection asserts that the notification table has no unique constraint that would prevent these repeats (NOTIF-003-AC06).
- **TEST-011-AC09** A test asserts that creating notifications creates no activity event and that a notification is created only for a recipient who is a member of the board (NOTIF-003-AC15, AC19).

## 6. Non-Functional Requirements

### NFR-001 Password protection
Passwords MUST be stored hashed.

**Acceptance criteria**
- **NFR-001-AC01** After registration, the stored password value is not equal to the submitted password.
- **NFR-001-AC02** After registration and login requests, the application log output does not contain the submitted password.

### NFR-002 Secret handling
Secrets MUST NOT be stored in source control.

**Acceptance criteria**
- **NFR-002-AC01** A secret scan of tracked files reports zero findings.
- **NFR-002-AC02** Both the backend and the frontend `.env` files are ignored by git, which `git check-ignore` confirms.
- **NFR-002-AC03** Production secrets are set only in the Render and Vercel environment settings, and the README states this.
- **NFR-002-AC04** No environment variable whose name begins with `NEXT_PUBLIC_` holds a secret, and the frontend `.env.example` labels each such variable as public.

### NFR-003 Input handling
Inputs MUST be validated and queries MUST be parameterized.

**Acceptance criteria**
- **NFR-003-AC01** Each endpoint that accepts a request body validates it with a Marshmallow schema.
- **NFR-003-AC02** A board name containing `'; DROP TABLE users;--` is stored and returned as literal text, and the `users` table remains intact.
- **NFR-003-AC03** Backend code builds no SQL by string concatenation or formatting with request values.

### NFR-004 Transport security
Deployed services MUST use HTTPS.

**Acceptance criteria**
- **NFR-004-AC01** The documented Vercel and Render URLs begin with `https://`.
- **NFR-004-AC02** The `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL` values in the deployed configuration begin with `https://`.
- **NFR-004-AC03** In production, the session cookie is sent with the `Secure` and `HttpOnly` attributes.

### NFR-005 Read latency
**Project target** (not an existing measured result): the 95th percentile (p95) response time for standard read requests MUST be under 500 ms.

**Acceptance criteria**
- **NFR-005-AC01** After one warm-up request per endpoint, a run of at least 100 sequential requests to each of `GET /api/boards`, `GET /api/boards/{id}`, `GET /api/cards?assignee=me`, `GET /api/notifications`, `GET /api/cards/{id}/comments`, and `GET /api/boards/{id}/analytics` on the deployed Render API yields a p95 under 500 ms for each.
- **NFR-005-AC02** The measurement procedure and the dataset size used are recorded in the README.

### NFR-006 Client request rates
The frontend MUST limit the rate of search filtering and the rate of notification polling. Search is client-side and sends no request (FRONT-008).

**Acceptance criteria**
- **NFR-006-AC01** Typing a 5-character search term with 100 ms between keystrokes causes exactly 1 filter pass and sends zero requests to the API or the proxy.
- **NFR-006-AC02** While a protected page stays open for 90 seconds, `GET /api/notifications` is requested 4 times, once on load and once every 30 seconds.

### NFR-007 Responsive design
The application MUST be usable at viewport widths from 360 px to 1920 px.

**Acceptance criteria**
- **NFR-007-AC01** At widths of 360, 768, 1280, and 1920 px, no page in Section 4.2 has a horizontal page scroll bar.
- **NFR-007-AC02** At 360 px, every column and card on `/boards/[id]` can be reached by scrolling inside the board area, and no card text is clipped.
- **NFR-007-AC03** At 360 px, all interactive controls on `/login` can be activated without zooming, and no control overlaps another.

### NFR-008 Deployment architecture
The system MUST be deployed with a Supabase PostgreSQL database, a Render Flask API, and a Vercel frontend.

**Acceptance criteria**
- **NFR-008-AC01** The Next.js frontend is served from a Vercel URL over HTTPS.
- **NFR-008-AC02** `GET /api/health` on the Render URL returns HTTP 200.
- **NFR-008-AC03** The backend `DATABASE_URL` points to a Supabase PostgreSQL host.
- **NFR-008-AC04** In the deployed configuration, `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL` point to the Render service. A server-side request from the Vercel deployment to `GET /api/boards` with a valid JWT succeeds, and a direct browser request from the Vercel origin to `GET /api/health` succeeds.

### NFR-009 Database migrations
Database schema changes MUST be made with Flask-Migrate.

**Acceptance criteria**
- **NFR-009-AC01** `flask db upgrade` on an empty PostgreSQL database completes without error and reaches the latest revision.
- **NFR-009-AC02** After upgrading, generating a new migration produces no schema differences.

### NFR-010 Environment configuration
Each deployable MUST have an `.env.example` file that documents its configuration.

**Acceptance criteria**
- **NFR-010-AC01** A backend `.env.example` is committed and lists every environment variable the backend reads, with placeholder values only.
- **NFR-010-AC02** A frontend `.env.example` is committed and lists every environment variable the frontend reads, including `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL`, with placeholder values only.
- **NFR-010-AC03** The backend fails at startup with a message naming the variable when a required variable is unset.

### NFR-011 AI workflow documentation and guidelines
The AI-assisted development workflow MUST be documented. The project MUST contain at least five before-and-after refinement rounds in `specs/CHANGELOG.md` and at least three documented guideline violations in `evidence/ai-reviews/violation-report.md`. It MUST also contain three steering guideline files and a measured with-guideline versus without-guideline comparison. These artifacts do not exist yet and are created during the project.

**Acceptance criteria**
- **NFR-011-AC01** `specs/CHANGELOG.md` records at least five refinement rounds. Each round has a "Before" entry that quotes or summarizes the artifact state before refinement and an "After" entry for the state after refinement.
- **NFR-011-AC02** `evidence/ai-reviews/violation-report.md` documents at least three guideline violations found in AI output.
- **NFR-011-AC03** Every AI-generated change has a recorded human review before acceptance.
- **NFR-011-AC04** Each violation entry in `evidence/ai-reviews/violation-report.md` contains four labeled fields: the guideline violated, the offending code or evidence, the correction, and the verification of the correction.
- **NFR-011-AC05** The files `guidelines/frontend.md`, `guidelines/backend.md`, and `guidelines/database.md` exist.
- **NFR-011-AC06** Every guideline in each of the three files has three labeled parts: Rule, Rationale, and Concrete Example.
- **NFR-011-AC07** A comparison document in `evidence/ai-reviews/` covers at least one identical task generated without the guidelines and with the guidelines. For each run it reports the number of guideline violations found in review and the number of tests passing on the first run, and it states the difference between the runs.

## 7. Requirements Traceability Matrix

Every acceptance criterion maps to a planned Flask route, Next.js page or component, or a named cross-cutting artifact. Exact file paths are set in `design.md`.

| Requirement ID | Acceptance Criterion ID | Planned Flask Route or Next.js Page/Component |
|---|---|---|
| AUTH-001 | AUTH-001-AC01 | POST /api/auth/register |
| AUTH-001 | AUTH-001-AC02 | POST /api/auth/register |
| AUTH-001 | AUTH-001-AC03 | POST /api/auth/register |
| AUTH-001 | AUTH-001-AC04 | POST /api/auth/register |
| AUTH-001 | AUTH-001-AC05 | POST /api/auth/register |
| AUTH-002 | AUTH-002-AC01 | POST /api/auth/login |
| AUTH-002 | AUTH-002-AC02 | POST /api/auth/login |
| AUTH-002 | AUTH-002-AC03 | POST /api/auth/login |
| AUTH-002 | AUTH-002-AC04 | POST /api/auth/login |
| AUTH-002 | AUTH-002-AC05 | POST /api/auth/login (response schema) |
| AUTH-003 | AUTH-003-AC01 | Flask-JWT-Extended configuration (token expiry setting) |
| AUTH-003 | AUTH-003-AC02 | Flask-JWT-Extended error handlers |
| AUTH-003 | AUTH-003-AC03 | Flask-JWT-Extended error handlers |
| AUTH-003 | AUTH-003-AC04 | Flask-JWT-Extended error handlers |
| AUTH-003 | AUTH-003-AC05 | Backend configuration and backend `.env.example` |
| AUTH-003 | AUTH-003-AC06 | Flask-JWT-Extended configuration (token location setting) |
| AUTH-004 | AUTH-004-AC01 | Flask-JWT-Extended `jwt_required` on all protected routes |
| AUTH-004 | AUTH-004-AC02 | Auth and health routes (no JWT requirement) |
| BOARD-001 | BOARD-001-AC01 | POST /api/boards |
| BOARD-001 | BOARD-001-AC02 | POST /api/boards |
| BOARD-001 | BOARD-001-AC03 | POST /api/boards (membership creation) |
| BOARD-001 | BOARD-001-AC04 | POST /api/boards (administrator role assignment) |
| BOARD-002 | BOARD-002-AC01 | GET /api/boards |
| BOARD-002 | BOARD-002-AC02 | GET /api/boards |
| BOARD-002 | BOARD-002-AC03 | GET /api/boards |
| BOARD-003 | BOARD-003-AC01 | GET /api/boards/{id} |
| BOARD-003 | BOARD-003-AC02 | GET /api/boards/{id} |
| BOARD-003 | BOARD-003-AC03 | GET /api/boards/{id} |
| BOARD-003 | BOARD-003-AC04 | GET /api/boards/{id} |
| BOARD-003 | BOARD-003-AC05 | GET /api/boards/{id} |
| BOARD-003 | BOARD-003-AC06 | GET /api/boards/{id} |
| BOARD-003 | BOARD-003-AC07 | GET /api/boards/{id} |
| BOARD-003 | BOARD-003-AC08 | GET /api/boards/{id} |
| BOARD-003 | BOARD-003-AC09 | GET /api/boards/{id} (member schema) |
| BOARD-003 | BOARD-003-AC10 | GET /api/boards/{id} |
| BOARD-003 | BOARD-003-AC11 | GET /api/boards/{id} |
| BOARD-003 | BOARD-003-AC12 | GET /api/boards/{id} and POST /api/boards/{id}/members |
| BOARD-004 | BOARD-004-AC01 | PATCH /api/boards/{id} |
| BOARD-004 | BOARD-004-AC02 | PATCH /api/boards/{id} |
| BOARD-004 | BOARD-004-AC03 | PATCH /api/boards/{id} |
| BOARD-004 | BOARD-004-AC04 | PATCH /api/boards/{id} (administrator check) |
| BOARD-005 | BOARD-005-AC01 | DELETE /api/boards/{id} |
| BOARD-005 | BOARD-005-AC02 | DELETE /api/boards/{id} |
| BOARD-005 | BOARD-005-AC03 | DELETE /api/boards/{id} (administrator check) |
| BOARD-005 | BOARD-005-AC04 | DELETE /api/boards/{id} (service layer deletion strategy) |
| BOARD-005 | BOARD-005-AC05 | DELETE /api/boards/{id} (service layer deletion strategy) |
| BOARD-005 | BOARD-005-AC06 | DELETE /api/boards/{id} (transaction boundary) |
| BOARD-005 | BOARD-005-AC07 | DELETE /api/boards/{id} (board isolation) |
| BOARD-005 | BOARD-005-AC08 | Flask-Migrate migration scripts and DELETE /api/boards/{id} |
| BOARD-006 | BOARD-006-AC01 | Shared board-authorization helper (service layer) |
| BOARD-006 | BOARD-006-AC02 | Shared board-authorization helper (service layer) |
| BOARD-006 | BOARD-006-AC03 | Administrator-only authorization decorator or helper |
| BOARD-006 | BOARD-006-AC04 | Shared board-authorization helper (service layer) |
| BOARD-006 | BOARD-006-AC05 | Shared board-authorization helper (service layer) |
| BOARD-006 | BOARD-006-AC06 | Shared board-authorization helper (service layer) |
| BOARD-006 | BOARD-006-AC07 | Shared board-authorization helper and service layer transactions |
| BOARD-007 | BOARD-007-AC01 | POST /api/boards/{id}/members |
| BOARD-007 | BOARD-007-AC02 | POST /api/boards/{id}/members (administrator check) |
| BOARD-007 | BOARD-007-AC03 | POST /api/boards/{id}/members (board isolation) |
| BOARD-007 | BOARD-007-AC04 | POST /api/boards/{id}/members |
| BOARD-007 | BOARD-007-AC05 | POST /api/boards/{id}/members |
| BOARD-007 | BOARD-007-AC06 | POST /api/boards/{id}/members (Marshmallow schema) |
| BOARD-007 | BOARD-007-AC07 | POST /api/boards/{id}/members |
| BOARD-007 | BOARD-007-AC08 | POST /api/boards/{id}/members (board isolation) |
| BOARD-007 | BOARD-007-AC09 | POST /api/boards/{id}/members (role assignment) |
| BOARD-007 | BOARD-007-AC10 | Flask URL map (route registration) |
| COLUMN-001 | COLUMN-001-AC01 | POST /api/boards/{id}/columns |
| COLUMN-001 | COLUMN-001-AC02 | POST /api/boards/{id}/columns |
| COLUMN-001 | COLUMN-001-AC03 | POST /api/boards/{id}/columns |
| COLUMN-001 | COLUMN-001-AC04 | POST /api/boards/{id}/columns |
| COLUMN-001 | COLUMN-001-AC05 | POST /api/boards/{id}/columns (board row lock) |
| COLUMN-002 | COLUMN-002-AC01 | PATCH /api/columns/{id} |
| COLUMN-002 | COLUMN-002-AC02 | PATCH /api/columns/{id} |
| COLUMN-002 | COLUMN-002-AC03 | PATCH /api/columns/{id} |
| COLUMN-002 | COLUMN-002-AC04 | PATCH /api/columns/{id} |
| COLUMN-002 | COLUMN-002-AC05 | PATCH /api/columns/{id} |
| COLUMN-002 | COLUMN-002-AC06 | PATCH /api/columns/{id} (administrator check) |
| COLUMN-002 | COLUMN-002-AC07 | PATCH /api/columns/{id} (Marshmallow schema) |
| COLUMN-002 | COLUMN-002-AC08 | PATCH /api/columns/{id} (service layer) |
| COLUMN-002 | COLUMN-002-AC09 | PATCH /api/columns/{id} (service layer) |
| COLUMN-002 | COLUMN-002-AC10 | PATCH /api/columns/{id} (soft-delete guard) |
| COLUMN-002 | COLUMN-002-AC11 | PATCH /api/columns/{id} (administrator check) |
| COLUMN-002 | COLUMN-002-AC12 | PATCH /api/columns/{id} (service layer) |
| COLUMN-002 | COLUMN-002-AC13 | PATCH /api/columns/{id} (service layer) |
| COLUMN-002 | COLUMN-002-AC14 | PATCH /api/columns/{id} (transaction boundary) |
| COLUMN-003 | COLUMN-003-AC01 | DELETE /api/columns/{id} |
| COLUMN-003 | COLUMN-003-AC02 | DELETE /api/columns/{id} |
| COLUMN-003 | COLUMN-003-AC03 | DELETE /api/columns/{id} (service layer) |
| COLUMN-003 | COLUMN-003-AC04 | DELETE /api/columns/{id} (service layer) |
| COLUMN-003 | COLUMN-003-AC05 | DELETE /api/columns/{id} (service layer) |
| COLUMN-003 | COLUMN-003-AC06 | DELETE /api/columns/{id} (foreign key preservation) |
| COLUMN-003 | COLUMN-003-AC07 | DELETE /api/columns/{id} (transaction boundary) |
| COLUMN-003 | COLUMN-003-AC08 | GET /api/boards/{id} and GET /api/cards?assignee=me (soft-delete filtering) |
| COLUMN-003 | COLUMN-003-AC09 | DELETE /api/columns/{id} |
| COLUMN-003 | COLUMN-003-AC10 | PATCH /api/columns/{id}, POST /api/columns/{id}/cards, and card routes (soft-delete guard) |
| COLUMN-003 | COLUMN-003-AC11 | DELETE /api/columns/{id} (service layer) |
| COLUMN-003 | COLUMN-003-AC12 | Flask URL map (route registration) |
| COLUMN-003 | COLUMN-003-AC13 | DELETE /api/columns/{id} (administrator check) |
| COLUMN-003 | COLUMN-003-AC14 | DELETE /api/columns/{id} (administrator check per board) |
| COLUMN-003 | COLUMN-003-AC15 | DELETE /api/columns/{id} (board row lock) |
| COLUMN-004 | COLUMN-004-AC01 | PATCH /api/boards/{id}/columns/reorder |
| COLUMN-004 | COLUMN-004-AC02 | PATCH /api/boards/{id}/columns/reorder |
| COLUMN-004 | COLUMN-004-AC03 | PATCH /api/boards/{id}/columns/reorder |
| COLUMN-004 | COLUMN-004-AC04 | PATCH /api/boards/{id}/columns/reorder |
| COLUMN-004 | COLUMN-004-AC05 | Column model (SQLAlchemy) |
| COLUMN-004 | COLUMN-004-AC06 | PATCH /api/boards/{id}/columns/reorder (soft-delete guard) |
| COLUMN-004 | COLUMN-004-AC07 | PATCH /api/boards/{id}/columns/reorder (Marshmallow schema) |
| COLUMN-004 | COLUMN-004-AC08 | PATCH /api/boards/{id}/columns/reorder (Marshmallow schema) |
| COLUMN-004 | COLUMN-004-AC09 | PATCH /api/boards/{id}/columns/reorder (Marshmallow schema) |
| COLUMN-004 | COLUMN-004-AC10 | PATCH /api/boards/{id}/columns/reorder (service layer) |
| COLUMN-004 | COLUMN-004-AC11 | PATCH /api/boards/{id}/columns/reorder (service layer) |
| COLUMN-004 | COLUMN-004-AC12 | PATCH /api/boards/{id}/columns/reorder (final-state validation) |
| COLUMN-004 | COLUMN-004-AC13 | PATCH /api/boards/{id}/columns/reorder (final-state validation) |
| COLUMN-004 | COLUMN-004-AC14 | PATCH /api/boards/{id}/columns/reorder (transaction boundary) |
| COLUMN-004 | COLUMN-004-AC15 | PATCH /api/boards/{id}/columns/reorder (board row lock) |
| COLUMN-004 | COLUMN-004-AC16 | PATCH /api/boards/{id}/columns/reorder (board row lock) |
| COLUMN-004 | COLUMN-004-AC17 | PATCH /api/boards/{id}/columns/reorder, POST /api/boards/{id}/columns, and DELETE /api/columns/{id} (board row lock) |
| COLUMN-004 | COLUMN-004-AC18 | PATCH /api/boards/{id}/columns/reorder (response schema) |
| COLUMN-004 | COLUMN-004-AC19 | PATCH /api/boards/{id}/columns/reorder (response schema) |
| COLUMN-004 | COLUMN-004-AC20 | PATCH /api/boards/{id}/columns/reorder (no-op) |
| COLUMN-004 | COLUMN-004-AC21 | PATCH /api/boards/{id}/columns/reorder (service layer) |
| COLUMN-004 | COLUMN-004-AC22 | PATCH /api/boards/{id}/columns/reorder (service layer) |
| COLUMN-004 | COLUMN-004-AC23 | PATCH /api/boards/{id}/columns/reorder (authorization) |
| COLUMN-004 | COLUMN-004-AC24 | PATCH /api/boards/{id}/columns/reorder (authorization order) |
| COLUMN-004 | COLUMN-004-AC25 | PATCH /api/boards/{id}/columns/reorder (position-to-order mapping) |
| COLUMN-004 | COLUMN-004-AC26 | PATCH /api/boards/{id}/columns/reorder (service layer) |
| COLUMN-004 | COLUMN-004-AC27 | PATCH /api/boards/{id}/columns/reorder (final-state validation) |
| COLUMN-005 | COLUMN-005-AC01 | Column model (SQLAlchemy) |
| COLUMN-005 | COLUMN-005-AC02 | POST /api/boards/{id}/columns |
| COLUMN-005 | COLUMN-005-AC03 | Flask-Migrate migration scripts |
| COLUMN-005 | COLUMN-005-AC04 | Column model (SQLAlchemy) |
| COLUMN-005 | COLUMN-005-AC05 | Flask-Migrate migration scripts |
| COLUMN-005 | COLUMN-005-AC06 | GET /api/boards/{id} and POST /api/boards/{id}/columns (soft-delete filtering) |
| COLUMN-005 | COLUMN-005-AC07 | Column schema (position-to-order mapping) |
| CARD-001 | CARD-001-AC01 | Card model (SQLAlchemy) |
| CARD-001 | CARD-001-AC02 | Card model (SQLAlchemy) |
| CARD-001 | CARD-001-AC03 | Card model (SQLAlchemy) |
| CARD-001 | CARD-001-AC04 | Card model (SQLAlchemy) |
| CARD-001 | CARD-001-AC05 | Card model (SQLAlchemy) |
| CARD-001 | CARD-001-AC06 | Flask-Migrate migration scripts |
| CARD-001 | CARD-001-AC07 | Card model (SQLAlchemy) |
| CARD-001 | CARD-001-AC08 | Card model (SQLAlchemy) |
| CARD-001 | CARD-001-AC09 | Card model and Flask-Migrate migration scripts |
| CARD-001 | CARD-001-AC10 | Card and column service layer (soft-delete invariant) |
| CARD-001 | CARD-001-AC11 | Card schema (position-to-order mapping) |
| CARD-002 | CARD-002-AC01 | POST /api/columns/{id}/cards |
| CARD-002 | CARD-002-AC02 | POST /api/columns/{id}/cards |
| CARD-002 | CARD-002-AC03 | POST /api/columns/{id}/cards |
| CARD-002 | CARD-002-AC04 | POST /api/columns/{id}/cards |
| CARD-002 | CARD-002-AC05 | POST /api/columns/{id}/cards |
| CARD-002 | CARD-002-AC06 | POST /api/columns/{id}/cards (service layer) |
| CARD-002 | CARD-002-AC07 | POST /api/columns/{id}/cards (soft-delete guard) |
| CARD-002 | CARD-002-AC08 | POST /api/columns/{id}/cards (Marshmallow schema) |
| CARD-002 | CARD-002-AC09 | POST /api/columns/{id}/cards |
| CARD-002 | CARD-002-AC10 | POST /api/columns/{id}/cards (column row lock) |
| CARD-003 | CARD-003-AC01 | PATCH /api/cards/{id} |
| CARD-003 | CARD-003-AC02 | PATCH /api/cards/{id} |
| CARD-003 | CARD-003-AC03 | PATCH /api/cards/{id} |
| CARD-003 | CARD-003-AC04 | PATCH /api/cards/{id} |
| CARD-003 | CARD-003-AC05 | PATCH /api/cards/{id} (Marshmallow schema) |
| CARD-003 | CARD-003-AC06 | PATCH /api/cards/{id} |
| CARD-003 | CARD-003-AC07 | PATCH /api/cards/{id} (soft-delete guard) |
| CARD-003 | CARD-003-AC08 | PATCH /api/cards/{id} (service layer) |
| CARD-003 | CARD-003-AC09 | PATCH /api/cards/{id} (service layer) |
| CARD-003 | CARD-003-AC10 | PATCH /api/cards/{id} (service layer) |
| CARD-003 | CARD-003-AC11 | PATCH /api/cards/{id} (Marshmallow schema) |
| CARD-003 | CARD-003-AC12 | PATCH /api/cards/{id}, GET /api/boards/{id}, and POST /api/columns/{id}/cards (card schema) |
| CARD-004 | CARD-004-AC01 | DELETE /api/cards/{id} |
| CARD-004 | CARD-004-AC02 | DELETE /api/cards/{id} |
| CARD-004 | CARD-004-AC03 | GET /api/cards?assignee=me |
| CARD-004 | CARD-004-AC04 | DELETE /api/cards/{id} |
| CARD-004 | CARD-004-AC05 | DELETE /api/cards/{id} (service layer) |
| CARD-004 | CARD-004-AC06 | DELETE /api/cards/{id} (soft-delete guard) |
| CARD-004 | CARD-004-AC07 | DELETE /api/cards/{id} and card and comment routes (soft-delete guard) |
| CARD-004 | CARD-004-AC08 | DELETE /api/cards/{id} (service layer) |
| CARD-004 | CARD-004-AC09 | DELETE /api/cards/{id} (notification retention) |
| CARD-005 | CARD-005-AC01 | PATCH /api/cards/{id}/position |
| CARD-005 | CARD-005-AC02 | PATCH /api/cards/{id}/position |
| CARD-005 | CARD-005-AC03 | PATCH /api/cards/{id}/position |
| CARD-005 | CARD-005-AC04 | PATCH /api/cards/{id}/position |
| CARD-005 | CARD-005-AC05 | PATCH /api/cards/{id}/position |
| CARD-005 | CARD-005-AC06 | PATCH /api/cards/{id}/position |
| CARD-005 | CARD-005-AC07 | PATCH /api/cards/{id}/position (service layer) |
| CARD-005 | CARD-005-AC08 | PATCH /api/cards/{id}/position (service layer) |
| CARD-005 | CARD-005-AC09 | PATCH /api/cards/{id}/position (service layer) |
| CARD-005 | CARD-005-AC10 | PATCH /api/cards/{id}/position (service layer) |
| CARD-005 | CARD-005-AC11 | PATCH /api/cards/{id}/position (service layer) |
| CARD-005 | CARD-005-AC12 | PATCH /api/cards/{id}/position (soft-delete guard) |
| CARD-005 | CARD-005-AC13 | PATCH /api/cards/{id}/position (soft-delete guard) |
| CARD-005 | CARD-005-AC14 | PATCH /api/cards/{id}/position (service layer) |
| CARD-005 | CARD-005-AC15 | PATCH /api/cards/{id}/position (rebalancing) |
| CARD-005 | CARD-005-AC16 | PATCH /api/cards/{id}/position (rebalancing) |
| CARD-005 | CARD-005-AC17 | PATCH /api/cards/{id}/position (rebalancing) |
| CARD-005 | CARD-005-AC18 | PATCH /api/cards/{id}/position (transaction boundary) |
| CARD-005 | CARD-005-AC19 | PATCH /api/cards/{id}/position (column row lock) |
| CARD-005 | CARD-005-AC20 | PATCH /api/cards/{id}/position and DELETE /api/columns/{id} (column row lock) |
| CARD-005 | CARD-005-AC21 | PATCH /api/cards/{id}/position (response schema) |
| CARD-005 | CARD-005-AC22 | PATCH /api/cards/{id}/position (response schema) |
| CARD-005 | CARD-005-AC23 | PATCH /api/cards/{id}/position (no-op) |
| CARD-005 | CARD-005-AC24 | PATCH /api/cards/{id}/position (rebalancing) |
| CARD-005 | CARD-005-AC25 | PATCH /api/cards/{id}/position (rebalancing) |
| CARD-005 | CARD-005-AC26 | PATCH /api/cards/{id}/position and POST /api/columns/{id}/cards (final-state invariant) |
| CARD-006 | CARD-006-AC01 | CardPositionSchema (Marshmallow) |
| CARD-006 | CARD-006-AC02 | CardPositionSchema (Marshmallow) |
| CARD-006 | CARD-006-AC03 | CardPositionSchema (Marshmallow) |
| CARD-006 | CARD-006-AC04 | CardPositionSchema (Marshmallow) |
| CARD-006 | CARD-006-AC05 | CardPositionSchema (Marshmallow) |
| CARD-007 | CARD-007-AC01 | GET /api/cards?assignee=me |
| CARD-007 | CARD-007-AC02 | GET /api/cards?assignee=me |
| CARD-007 | CARD-007-AC03 | GET /api/cards?assignee=me |
| CARD-007 | CARD-007-AC04 | GET /api/cards?assignee=me |
| CARD-007 | CARD-007-AC05 | GET /api/cards?assignee=me |
| CARD-007 | CARD-007-AC06 | GET /api/cards?assignee=me (soft-delete filtering) |
| COMMENT-001 | COMMENT-001-AC01 | POST /api/cards/{id}/comments |
| COMMENT-001 | COMMENT-001-AC02 | POST /api/cards/{id}/comments |
| COMMENT-001 | COMMENT-001-AC03 | POST /api/cards/{id}/comments |
| COMMENT-001 | COMMENT-001-AC04 | POST /api/cards/{id}/comments |
| COMMENT-001 | COMMENT-001-AC05 | POST /api/cards/{id}/comments |
| COMMENT-001 | COMMENT-001-AC06 | POST /api/cards/{id}/comments (soft-delete guard) |
| COMMENT-001 | COMMENT-001-AC07 | POST /api/cards/{id}/comments (notification creation) |
| COMMENT-001 | COMMENT-001-AC08 | POST /api/cards/{id}/comments (notification creation) |
| COMMENT-002 | COMMENT-002-AC01 | GET /api/cards/{id}/comments |
| COMMENT-002 | COMMENT-002-AC02 | GET /api/cards/{id}/comments |
| COMMENT-002 | COMMENT-002-AC03 | GET /api/cards/{id}/comments |
| COMMENT-002 | COMMENT-002-AC04 | GET /api/cards/{id}/comments |
| COMMENT-002 | COMMENT-002-AC05 | GET /api/cards/{id}/comments (soft-delete guard) |
| COMMENT-003 | COMMENT-003-AC01 | PATCH /api/comments/{id} |
| COMMENT-003 | COMMENT-003-AC02 | PATCH /api/comments/{id} (ownership check) |
| COMMENT-003 | COMMENT-003-AC03 | PATCH /api/comments/{id} (ownership check) |
| COMMENT-003 | COMMENT-003-AC04 | PATCH /api/comments/{id} |
| COMMENT-003 | COMMENT-003-AC05 | PATCH /api/comments/{id} |
| COMMENT-003 | COMMENT-003-AC06 | PATCH /api/comments/{id} |
| COMMENT-003 | COMMENT-003-AC07 | PATCH /api/comments/{id} (soft-delete guard) |
| COMMENT-003 | COMMENT-003-AC08 | PATCH /api/comments/{id} (ownership check) |
| COMMENT-003 | COMMENT-003-AC09 | PATCH /api/comments/{id} (ownership check) |
| COMMENT-004 | COMMENT-004-AC01 | DELETE /api/comments/{id} |
| COMMENT-004 | COMMENT-004-AC02 | DELETE /api/comments/{id} (ownership check) |
| COMMENT-004 | COMMENT-004-AC03 | DELETE /api/comments/{id} (ownership check) |
| COMMENT-004 | COMMENT-004-AC04 | DELETE /api/comments/{id} |
| COMMENT-004 | COMMENT-004-AC05 | DELETE /api/comments/{id} |
| COMMENT-004 | COMMENT-004-AC06 | DELETE /api/comments/{id} (service layer) |
| COMMENT-004 | COMMENT-004-AC07 | DELETE /api/comments/{id} (soft-delete guard) |
| COMMENT-004 | COMMENT-004-AC08 | DELETE /api/comments/{id} (ownership check) |
| NOTIF-001 | NOTIF-001-AC01 | GET /api/notifications |
| NOTIF-001 | NOTIF-001-AC02 | GET /api/notifications |
| NOTIF-001 | NOTIF-001-AC03 | GET /api/notifications |
| NOTIF-001 | NOTIF-001-AC04 | GET /api/notifications |
| NOTIF-001 | NOTIF-001-AC05 | GET /api/notifications |
| NOTIF-001 | NOTIF-001-AC06 | GET /api/notifications (notification schema) |
| NOTIF-001 | NOTIF-001-AC07 | GET /api/notifications |
| NOTIF-001 | NOTIF-001-AC08 | GET /api/notifications (notification schema) |
| NOTIF-001 | NOTIF-001-AC09 | GET /api/notifications |
| NOTIF-002 | NOTIF-002-AC01 | PATCH /api/notifications/{id}/read |
| NOTIF-002 | NOTIF-002-AC02 | PATCH /api/notifications/{id}/read |
| NOTIF-002 | NOTIF-002-AC03 | PATCH /api/notifications/{id}/read |
| NOTIF-002 | NOTIF-002-AC04 | PATCH /api/notifications/{id}/read |
| NOTIF-002 | NOTIF-002-AC05 | PATCH /api/notifications/{id}/read |
| NOTIF-002 | NOTIF-002-AC06 | PATCH /api/notifications/{id}/read |
| NOTIF-002 | NOTIF-002-AC07 | PATCH /api/notifications/{id}/read |
| NOTIF-002 | NOTIF-002-AC08 | PATCH /api/notifications/{id}/read |
| NOTIF-003 | NOTIF-003-AC01 | Notification service (service layer) |
| NOTIF-003 | NOTIF-003-AC02 | Notification service (service layer) |
| NOTIF-003 | NOTIF-003-AC03 | Notification service (service layer) |
| NOTIF-003 | NOTIF-003-AC04 | Notification service (service layer) |
| NOTIF-003 | NOTIF-003-AC05 | Notification service (service layer) |
| NOTIF-003 | NOTIF-003-AC06 | Notification service (service layer) |
| NOTIF-003 | NOTIF-003-AC07 | Notification service (service layer) |
| NOTIF-003 | NOTIF-003-AC08 | Notification service (database locking and state comparison) |
| NOTIF-003 | NOTIF-003-AC09 | Notification service (service layer) |
| NOTIF-003 | NOTIF-003-AC10 | Notification service (service layer) |
| NOTIF-003 | NOTIF-003-AC11 | Notification service (service layer) |
| NOTIF-003 | NOTIF-003-AC12 | Notification service (transaction boundary) |
| NOTIF-003 | NOTIF-003-AC13 | Notification service (transaction boundary) |
| NOTIF-003 | NOTIF-003-AC14 | Notification service (transaction boundary) |
| NOTIF-003 | NOTIF-003-AC15 | Notification service (recipient check) |
| NOTIF-003 | NOTIF-003-AC16 | Notification service (message builder) |
| NOTIF-003 | NOTIF-003-AC17 | Notification service (retention) |
| NOTIF-003 | NOTIF-003-AC18 | DELETE /api/boards/{id} (service layer deletion strategy) |
| NOTIF-003 | NOTIF-003-AC19 | Notification service (service layer) |
| ANALYTICS-001 | ANALYTICS-001-AC01 | GET /api/boards/{id}/analytics |
| ANALYTICS-001 | ANALYTICS-001-AC02 | GET /api/boards/{id}/analytics |
| ANALYTICS-001 | ANALYTICS-001-AC03 | GET /api/boards/{id}/analytics |
| ANALYTICS-001 | ANALYTICS-001-AC04 | GET /api/boards/{id}/analytics (response schema) |
| ANALYTICS-001 | ANALYTICS-001-AC05 | GET /api/boards/{id}/analytics (response schema) |
| ANALYTICS-001 | ANALYTICS-001-AC06 | GET /api/boards/{id}/analytics (response schema) |
| ANALYTICS-001 | ANALYTICS-001-AC07 | GET /api/boards/{id}/analytics (response schema) |
| ANALYTICS-001 | ANALYTICS-001-AC08 | GET /api/boards/{id}/analytics (response schema) |
| ANALYTICS-001 | ANALYTICS-001-AC09 | GET /api/boards/{id}/analytics (query validation) |
| ANALYTICS-002 | ANALYTICS-002-AC01 | Analytics service (service layer) |
| ANALYTICS-002 | ANALYTICS-002-AC02 | Analytics service (service layer) |
| ANALYTICS-002 | ANALYTICS-002-AC03 | Analytics service (service layer) |
| ANALYTICS-002 | ANALYTICS-002-AC04 | Analytics service (service layer) |
| ANALYTICS-002 | ANALYTICS-002-AC05 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC01 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC02 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC03 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC04 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC05 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC06 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC07 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC08 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC09 | Card and column service layer (completion invariant) |
| ANALYTICS-003 | ANALYTICS-003-AC10 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC11 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC12 | Analytics service (service layer) |
| ANALYTICS-003 | ANALYTICS-003-AC13 | Analytics service (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC01 | Analytics service (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC02 | Activity recording (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC03 | Analytics service (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC04 | Analytics service (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC05 | Analytics service (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC06 | Analytics service (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC07 | Analytics service (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC08 | Analytics service (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC09 | Analytics service (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC10 | Analytics service (service layer) |
| ANALYTICS-004 | ANALYTICS-004-AC11 | Analytics service (service layer) |
| ANALYTICS-005 | ANALYTICS-005-AC01 | Analytics service module and route handler |
| ANALYTICS-005 | ANALYTICS-005-AC02 | Analytics service (SQLAlchemy join queries) |
| ANALYTICS-005 | ANALYTICS-005-AC03 | Analytics service (SQLAlchemy join queries) |
| ANALYTICS-005 | ANALYTICS-005-AC04 | Analytics service (window computation and clock) |
| ANALYTICS-006 | ANALYTICS-006-AC01 | POST /api/columns/{id}/cards (activity recording in service layer) |
| ANALYTICS-006 | ANALYTICS-006-AC02 | PATCH /api/cards/{id}/position (activity recording in service layer) |
| ANALYTICS-006 | ANALYTICS-006-AC03 | POST /api/cards/{id}/comments (activity recording in service layer) |
| ANALYTICS-006 | ANALYTICS-006-AC04 | Activity recording (service layer transaction) |
| ANALYTICS-006 | ANALYTICS-006-AC05 | Activity-event table (append-only) and Flask URL map |
| ANALYTICS-006 | ANALYTICS-006-AC06 | Activity-event table (SQLAlchemy model and Flask-Migrate migration) |
| ANALYTICS-006 | ANALYTICS-006-AC07 | Activity-event table (no cascade delete) and Analytics service |
| ANALYTICS-006 | ANALYTICS-006-AC08 | PATCH /api/comments/{id} and DELETE /api/comments/{id} (no activity recording) |
| ANALYTICS-006 | ANALYTICS-006-AC09 | Activity-event table (retention) and DELETE /api/columns/{id} |
| ANALYTICS-006 | ANALYTICS-006-AC10 | DELETE /api/boards/{id} (service layer deletion strategy) |
| ANALYTICS-006 | ANALYTICS-006-AC11 | Activity recording (service layer) and clock |
| USER-001 | USER-001-AC01 | GET /api/users/me |
| USER-001 | USER-001-AC02 | GET /api/users/me |
| USER-001 | USER-001-AC03 | GET /api/users/me |
| USER-002 | USER-002-AC01 | PATCH /api/users/me |
| USER-002 | USER-002-AC02 | PATCH /api/users/me (Marshmallow schema) |
| USER-002 | USER-002-AC03 | PATCH /api/users/me |
| USER-002 | USER-002-AC04 | PATCH /api/users/me |
| USER-002 | USER-002-AC05 | PATCH /api/users/me |
| USER-002 | USER-002-AC06 | PATCH /api/users/me |
| API-001 | API-001-AC01 | Flask response helper (shared success serializer) |
| API-001 | API-001-AC02 | Flask response helper (shared success serializer) |
| API-001 | API-001-AC03 | Flask response helper (shared success serializer) |
| API-001 | API-001-AC04 | Flask response helper (shared success serializer) |
| API-001 | API-001-AC05 | Flask response helper (shared success serializer) |
| API-001 | API-001-AC06 | Flask response helper (shared success serializer) |
| API-001 | API-001-AC07 | Flask response helper and error handlers |
| API-001 | API-001-AC08 | Flask response helper (shared success serializer) |
| API-002 | API-002-AC01 | Flask error handlers |
| API-002 | API-002-AC02 | Flask error handlers (404) |
| API-002 | API-002-AC03 | Flask error handlers (500) |
| API-002 | API-002-AC04 | Flask error handlers |
| API-002 | API-002-AC05 | Flask error handlers (500) |
| API-003 | API-003-AC01 | GET /api/health |
| API-003 | API-003-AC02 | GET /api/health (deployed on Render) |
| API-003 | API-003-AC03 | GET /api/health |
| API-004 | API-004-AC01 | Flask CORS configuration |
| API-004 | API-004-AC02 | Flask CORS configuration |
| API-004 | API-004-AC03 | Backend `.env.example` and Flask CORS configuration |
| API-004 | API-004-AC04 | Flask CORS configuration |
| API-004 | API-004-AC05 | Flask CORS configuration |
| FRONT-001 | FRONT-001-AC01 | Page /register |
| FRONT-001 | FRONT-001-AC02 | Page /register |
| FRONT-001 | FRONT-001-AC03 | Page /register |
| FRONT-001 | FRONT-001-AC04 | Page /register |
| FRONT-001 | FRONT-001-AC05 | Page /register |
| FRONT-001 | FRONT-001-AC06 | Page /register (Client Component form) and Next.js proxy |
| FRONT-002 | FRONT-002-AC01 | Page /login (Client Component form) and AuthContext |
| FRONT-002 | FRONT-002-AC02 | Page /login |
| FRONT-002 | FRONT-002-AC03 | Page /login |
| FRONT-002 | FRONT-002-AC04 | Page /login |
| FRONT-003 | FRONT-003-AC01 | Next.js server-side route protection (session check) |
| FRONT-003 | FRONT-003-AC02 | Next.js server-side route protection (session check) |
| FRONT-003 | FRONT-003-AC03 | Next.js server-side route protection (session check) |
| FRONT-004 | FRONT-004-AC01 | Authenticated layout header |
| FRONT-004 | FRONT-004-AC02 | AuthContext (logout) and session logout route |
| FRONT-004 | FRONT-004-AC03 | AuthContext (logout) |
| FRONT-005 | FRONT-005-AC01 | Page / and BoardCard.tsx |
| FRONT-005 | FRONT-005-AC02 | Page / (board-creation Client Component form) |
| FRONT-005 | FRONT-005-AC03 | Page / |
| FRONT-005 | FRONT-005-AC04 | Page / (loading UI) |
| FRONT-005 | FRONT-005-AC05 | Page / (error UI and board-creation form) |
| FRONT-005 | FRONT-005-AC06 | Page / |
| FRONT-005 | FRONT-005-AC07 | Page / and apiClient.ts (server-side mode) |
| FRONT-006 | FRONT-006-AC01 | Page /boards/[id] |
| FRONT-006 | FRONT-006-AC02 | Page /boards/[id] |
| FRONT-006 | FRONT-006-AC03 | Page /boards/[id] |
| FRONT-006 | FRONT-006-AC04 | Page /boards/[id] and AddCardForm.tsx |
| FRONT-006 | FRONT-006-AC05 | Page /boards/[id] |
| FRONT-006 | FRONT-006-AC06 | Page /boards/[id] and ColumnHeader.tsx |
| FRONT-006 | FRONT-006-AC07 | Page /boards/[id] |
| FRONT-006 | FRONT-006-AC08 | Page /boards/[id] and apiClient.ts (server-side mode) |
| FRONT-006 | FRONT-006-AC09 | Page /boards/[id] and ColumnHeader.tsx |
| FRONT-006 | FRONT-006-AC10 | Page /boards/[id] and ColumnHeader.tsx |
| FRONT-006 | FRONT-006-AC11 | Page /boards/[id] (board view container) |
| FRONT-006 | FRONT-006-AC12 | Page /boards/[id] (board view container) |
| FRONT-007 | FRONT-007-AC01 | Page /boards/[id] (analytics panel) |
| FRONT-007 | FRONT-007-AC02 | Page /boards/[id] (analytics panel) |
| FRONT-007 | FRONT-007-AC03 | Page /boards/[id] (analytics panel) |
| FRONT-007 | FRONT-007-AC04 | Page /boards/[id] (analytics panel) |
| FRONT-007 | FRONT-007-AC05 | Page /boards/[id] (analytics panel) |
| FRONT-007 | FRONT-007-AC06 | Page /boards/[id] (analytics panel) |
| FRONT-007 | FRONT-007-AC07 | Page /boards/[id] (analytics panel) |
| FRONT-007 | FRONT-007-AC08 | Page /boards/[id] (analytics panel) |
| FRONT-008 | FRONT-008-AC01 | Card search filter (Client Component on /boards/[id]) |
| FRONT-008 | FRONT-008-AC02 | Card search filter (Client Component on /boards/[id]) |
| FRONT-008 | FRONT-008-AC03 | Card search filter (Client Component on /boards/[id]) |
| FRONT-008 | FRONT-008-AC04 | Card search filter (Client Component on /boards/[id]) |
| FRONT-008 | FRONT-008-AC05 | Card search filter (Client Component on /boards/[id]) |
| FRONT-008 | FRONT-008-AC06 | Card search filter (Client Component on /boards/[id]) |
| FRONT-008 | FRONT-008-AC07 | Card search filter (Client Component on /boards/[id]) |
| FRONT-008 | FRONT-008-AC08 | Card search filter (Client Component on /boards/[id]) |
| FRONT-009 | FRONT-009-AC01 | Page /my-tasks and apiClient.ts (server-side mode) |
| FRONT-009 | FRONT-009-AC02 | Page /my-tasks |
| FRONT-009 | FRONT-009-AC03 | Page /my-tasks |
| FRONT-009 | FRONT-009-AC04 | Page /my-tasks (loading UI) |
| FRONT-010 | FRONT-010-AC01 | Page /profile |
| FRONT-010 | FRONT-010-AC02 | Page /profile (Client Component form) and AuthContext |
| FRONT-010 | FRONT-010-AC03 | Page /profile |
| FRONT-010 | FRONT-010-AC04 | Page /profile |
| FRONT-011 | FRONT-011-AC01 | CardDetailModal |
| FRONT-011 | FRONT-011-AC02 | CardDetailModal |
| FRONT-011 | FRONT-011-AC03 | CardDetailModal |
| FRONT-011 | FRONT-011-AC04 | CardDetailModal |
| FRONT-011 | FRONT-011-AC05 | CardDetailModal |
| FRONT-011 | FRONT-011-AC06 | CardDetailModal |
| FRONT-011 | FRONT-011-AC07 | CardDetailModal |
| FRONT-011 | FRONT-011-AC08 | CardDetailModal and Page /boards/[id] (board view container) |
| FRONT-011 | FRONT-011-AC09 | CardDetailModal |
| FRONT-011 | FRONT-011-AC10 | CardDetailModal |
| FRONT-011 | FRONT-011-AC11 | CardDetailModal |
| FRONT-011 | FRONT-011-AC12 | CardDetailModal |
| FRONT-011 | FRONT-011-AC13 | CardDetailModal and AddCardForm.tsx |
| FRONT-012 | FRONT-012-AC01 | CommentList |
| FRONT-012 | FRONT-012-AC02 | CommentList |
| FRONT-012 | FRONT-012-AC03 | CommentList |
| FRONT-012 | FRONT-012-AC04 | CommentList |
| FRONT-012 | FRONT-012-AC05 | CommentList |
| FRONT-012 | FRONT-012-AC06 | CommentList |
| FRONT-013 | FRONT-013-AC01 | BaseButton |
| FRONT-013 | FRONT-013-AC02 | BaseButton |
| FRONT-013 | FRONT-013-AC03 | BaseButton |
| FRONT-014 | FRONT-014-AC01 | BaseBadge |
| FRONT-014 | FRONT-014-AC02 | BaseBadge |
| FRONT-015 | FRONT-015-AC01 | BaseModal |
| FRONT-015 | FRONT-015-AC02 | BaseModal |
| FRONT-015 | FRONT-015-AC03 | BaseModal |
| FRONT-015 | FRONT-015-AC04 | BaseModal |
| FRONT-016 | FRONT-016-AC01 | NotificationBell |
| FRONT-016 | FRONT-016-AC02 | NotificationBell |
| FRONT-016 | FRONT-016-AC03 | NotificationBell |
| FRONT-016 | FRONT-016-AC04 | Authenticated layout header |
| FRONT-016 | FRONT-016-AC05 | NotificationBell |
| FRONT-016 | FRONT-016-AC06 | NotificationBell |
| FRONT-016 | FRONT-016-AC07 | NotificationBell |
| FRONT-016 | FRONT-016-AC08 | NotificationBell and Page /boards/[id] |
| FRONT-016 | FRONT-016-AC09 | NotificationBell and Page /boards/[id] |
| FRONT-016 | FRONT-016-AC10 | NotificationBell |
| FRONT-016 | FRONT-016-AC11 | NotificationBell |
| FRONT-016 | FRONT-016-AC12 | NotificationBell and useNotifications |
| FRONT-016 | FRONT-016-AC13 | NotificationBell |
| FRONT-016 | FRONT-016-AC14 | NotificationBell |
| FRONT-024 | FRONT-024-AC01 | BoardCard.tsx |
| FRONT-024 | FRONT-024-AC02 | BoardCard.tsx |
| FRONT-024 | FRONT-024-AC03 | BoardCard.tsx |
| FRONT-024 | FRONT-024-AC04 | BoardCard.tsx |
| FRONT-024 | FRONT-024-AC05 | BoardCard.tsx |
| FRONT-024 | FRONT-024-AC06 | BoardCard.tsx |
| FRONT-025 | FRONT-025-AC01 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC02 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC03 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC04 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC05 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC06 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC07 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC08 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC09 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC10 | ColumnHeader.tsx and Page /boards/[id] (board view container) |
| FRONT-025 | FRONT-025-AC11 | ColumnHeader.tsx and Page /boards/[id] (board view container) |
| FRONT-025 | FRONT-025-AC12 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC13 | ColumnHeader.tsx and Page /boards/[id] (board view container) |
| FRONT-025 | FRONT-025-AC14 | ColumnHeader.tsx |
| FRONT-025 | FRONT-025-AC15 | Page /boards/[id] (analytics panel) |
| FRONT-025 | FRONT-025-AC16 | ColumnHeader.tsx and Page /boards/[id] (board view container) |
| FRONT-025 | FRONT-025-AC17 | ColumnHeader.tsx and Page /boards/[id] (board view container) |
| FRONT-026 | FRONT-026-AC01 | AddCardForm.tsx |
| FRONT-026 | FRONT-026-AC02 | AddCardForm.tsx |
| FRONT-026 | FRONT-026-AC03 | AddCardForm.tsx |
| FRONT-026 | FRONT-026-AC04 | AddCardForm.tsx |
| FRONT-026 | FRONT-026-AC05 | AddCardForm.tsx |
| FRONT-026 | FRONT-026-AC06 | AddCardForm.tsx |
| FRONT-026 | FRONT-026-AC07 | AddCardForm.tsx |
| FRONT-026 | FRONT-026-AC08 | AddCardForm.tsx |
| FRONT-026 | FRONT-026-AC09 | AddCardForm.tsx |
| FRONT-017 | FRONT-017-AC01 | useNotifications |
| FRONT-017 | FRONT-017-AC02 | useNotifications |
| FRONT-017 | FRONT-017-AC03 | useNotifications |
| FRONT-017 | FRONT-017-AC04 | useNotifications |
| FRONT-017 | FRONT-017-AC05 | useNotifications |
| FRONT-017 | FRONT-017-AC06 | useNotifications and useErrorHandler |
| FRONT-018 | FRONT-018-AC01 | AuthContext |
| FRONT-018 | FRONT-018-AC02 | AuthContext |
| FRONT-018 | FRONT-018-AC03 | AuthContext (initialized from root layout) |
| FRONT-018 | FRONT-018-AC04 | AuthContext and Next.js server-side route protection |
| FRONT-018 | FRONT-018-AC05 | AuthContext |
| FRONT-018 | FRONT-018-AC06 | AuthContext (updateProfile) |
| FRONT-018 | FRONT-018-AC07 | AuthContext (updateProfile) |
| FRONT-018 | FRONT-018-AC08 | AuthContext (updateProfile) |
| FRONT-018 | FRONT-018-AC09 | AuthContext and session layer (FRONT-023) |
| FRONT-019 | FRONT-019-AC01 | useDragAndDrop |
| FRONT-019 | FRONT-019-AC02 | useDragAndDrop |
| FRONT-019 | FRONT-019-AC03 | useDragAndDrop |
| FRONT-019 | FRONT-019-AC04 | useDragAndDrop |
| FRONT-019 | FRONT-019-AC05 | useDragAndDrop |
| FRONT-019 | FRONT-019-AC06 | useDragAndDrop |
| FRONT-019 | FRONT-019-AC07 | useDragAndDrop |
| FRONT-019 | FRONT-019-AC08 | useDragAndDrop (column reorder) |
| FRONT-019 | FRONT-019-AC09 | useDragAndDrop (column reorder) |
| FRONT-019 | FRONT-019-AC10 | useDragAndDrop (column reorder) |
| FRONT-019 | FRONT-019-AC11 | useDragAndDrop (column normalization) |
| FRONT-019 | FRONT-019-AC12 | useDragAndDrop (column normalization) |
| FRONT-019 | FRONT-019-AC13 | useDragAndDrop (column normalization) |
| FRONT-019 | FRONT-019-AC14 | useDragAndDrop (card rebalancing) |
| FRONT-019 | FRONT-019-AC15 | useDragAndDrop (card rebalancing) |
| FRONT-019 | FRONT-019-AC16 | useDragAndDrop (card rebalancing) |
| FRONT-020 | FRONT-020-AC01 | useErrorHandler |
| FRONT-020 | FRONT-020-AC02 | useErrorHandler |
| FRONT-020 | FRONT-020-AC03 | useErrorHandler |
| FRONT-020 | FRONT-020-AC04 | useErrorHandler |
| FRONT-021 | FRONT-021-AC01 | Next.js build configuration |
| FRONT-021 | FRONT-021-AC02 | Root layout |
| FRONT-021 | FRONT-021-AC03 | Page /, Page /boards/[id], BoardCard.tsx, BaseBadge |
| FRONT-021 | FRONT-021-AC04 | BaseModal, CardDetailModal, AddCardForm.tsx, ColumnHeader.tsx, CommentList, NotificationBell, board view container |
| FRONT-022 | FRONT-022-AC01 | apiClient.ts (server-side and client-side modes) |
| FRONT-022 | FRONT-022-AC02 | Protected pages (loading UI) |
| FRONT-022 | FRONT-022-AC03 | apiClient.ts, session layer, and AuthContext |
| FRONT-022 | FRONT-022-AC04 | BaseButton and Client Component forms |
| FRONT-023 | FRONT-023-AC01 | Session login route handler (Next.js server) |
| FRONT-023 | FRONT-023-AC02 | Session login route handler (Next.js server) |
| FRONT-023 | FRONT-023-AC03 | Session layer (Next.js server) |
| FRONT-023 | FRONT-023-AC04 | Next.js proxy route handler |
| FRONT-023 | FRONT-023-AC05 | Next.js proxy route handler |
| FRONT-023 | FRONT-023-AC06 | Next.js proxy route handler |
| FRONT-023 | FRONT-023-AC07 | Next.js proxy route handler (path allow-list) |
| FRONT-023 | FRONT-023-AC08 | Next.js proxy route handler (origin check) |
| FRONT-023 | FRONT-023-AC09 | Session module (server-only) |
| FRONT-023 | FRONT-023-AC10 | Session logout route handler (Next.js server) |
| FRONT-023 | FRONT-023-AC11 | Next.js proxy route handler (path allow-list) and session login route handler |
| FRONT-023 | FRONT-023-AC12 | Next.js server-side route protection and session module |
| FRONT-023 | FRONT-023-AC13 | Next.js proxy route handler |
| FRONT-023 | FRONT-023-AC14 | Next.js proxy route handler (CSRF protection) |
| FRONT-023 | FRONT-023-AC15 | Session module (server-only) and ESLint restricted-import rule |
| API-005 | API-005-AC01 | apiClient.ts and frontend `.env.example` |
| API-005 | API-005-AC02 | apiClient.ts |
| API-005 | API-005-AC03 | apiClient.ts |
| API-005 | API-005-AC04 | apiClient.ts |
| API-005 | API-005-AC05 | apiClient.ts and AuthContext |
| API-005 | API-005-AC06 | apiClient.ts |
| API-005 | API-005-AC07 | apiClient.ts |
| API-005 | API-005-AC08 | apiClient.ts |
| API-005 | API-005-AC09 | apiClient.ts |
| API-005 | API-005-AC10 | apiClient.ts |
| API-006 | API-006-AC01 | errors.ts |
| API-006 | API-006-AC02 | errors.ts |
| API-006 | API-006-AC03 | errors.ts |
| API-007 | API-007-AC01 | toast.ts |
| API-007 | API-007-AC02 | Root layout and toast.ts |
| API-007 | API-007-AC03 | toast.ts |
| TEST-001 | TEST-001-AC01 | Backend pytest suite |
| TEST-001 | TEST-001-AC02 | Backend pytest suite (endpoint coverage test) |
| TEST-001 | TEST-001-AC03 | Backend test configuration (pytest fixtures) |
| TEST-001 | TEST-001-AC04 | Backend pytest suite (response contract) |
| TEST-001 | TEST-001-AC05 | Backend pytest suite (error envelope) |
| TEST-002 | TEST-002-AC01 | Backend pytest suite (comments) |
| TEST-002 | TEST-002-AC02 | Backend pytest suite (comments) |
| TEST-002 | TEST-002-AC03 | Backend pytest suite (comments) |
| TEST-002 | TEST-002-AC04 | Backend pytest suite (comments) |
| TEST-003 | TEST-003-AC01 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC02 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC03 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC04 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC05 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC06 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC07 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC08 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC09 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC10 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC11 | Backend pytest suite (authorization) |
| TEST-003 | TEST-003-AC12 | Backend pytest suite (comment ownership) |
| TEST-003 | TEST-003-AC13 | Backend pytest suite (atomicity) |
| TEST-003 | TEST-003-AC14 | Backend pytest suite (authorization check order) |
| TEST-003 | TEST-003-AC15 | Backend pytest suite (board-member list privacy) |
| TEST-004 | TEST-004-AC01 | Backend pytest suite (card position) |
| TEST-004 | TEST-004-AC02 | Backend pytest suite (card model) |
| TEST-004 | TEST-004-AC03 | Backend pytest suite (analytics) |
| TEST-004 | TEST-004-AC04 | Backend pytest suite (completion timestamps) |
| TEST-004 | TEST-004-AC05 | Backend pytest suite (activity events) |
| TEST-004 | TEST-004-AC06 | Backend pytest suite (membership extension) |
| TEST-004 | TEST-004-AC07 | Backend pytest suite (is_done idempotency) |
| TEST-004 | TEST-004-AC08 | Backend pytest suite (analytics window and clock) |
| TEST-004 | TEST-004-AC09 | Backend pytest suite (completed-this-week analytics) |
| TEST-004 | TEST-004-AC10 | Backend pytest suite (member activity analytics) |
| TEST-004 | TEST-004-AC11 | Backend pytest suite (analytics response contract) |
| TEST-004 | TEST-004-AC12 | Backend pytest suite (analytics end-to-end data set) |
| TEST-004 | TEST-004-AC13 | Backend pytest suite (column reorder) |
| TEST-004 | TEST-004-AC14 | Backend pytest suite (column reorder validation) |
| TEST-004 | TEST-004-AC15 | Backend pytest suite (column reorder collisions) |
| TEST-004 | TEST-004-AC16 | Backend pytest suite (column reorder transaction and lock) |
| TEST-004 | TEST-004-AC17 | Backend pytest suite (column reorder concurrency) |
| TEST-004 | TEST-004-AC18 | Backend pytest suite (column reorder no-op and timestamps) |
| TEST-004 | TEST-004-AC19 | Backend pytest suite (public order mapping) |
| TEST-004 | TEST-004-AC20 | Backend pytest suite (column reorder authorization and side effects) |
| TEST-004 | TEST-004-AC21 | Backend pytest suite (card rebalancing) |
| TEST-004 | TEST-004-AC22 | Backend pytest suite (card position response) |
| TEST-004 | TEST-004-AC23 | Backend pytest suite (card rebalancing transaction) |
| TEST-004 | TEST-004-AC24 | Backend pytest suite (card rebalancing concurrency) |
| TEST-004 | TEST-004-AC25 | Backend pytest suite (card rebalancing side effects) |
| TEST-004 | TEST-004-AC26 | Backend pytest suite (card position schema) |
| TEST-005 | TEST-005-AC01 | Frontend test suite (React Testing Library) |
| TEST-005 | TEST-005-AC02 | Frontend test suite (React Testing Library) |
| TEST-005 | TEST-005-AC03 | Frontend test suite (card search) |
| TEST-005 | TEST-005-AC04 | Frontend test suite (useNotifications) |
| TEST-005 | TEST-005-AC05 | Frontend test suite (useDragAndDrop) |
| TEST-005 | TEST-005-AC06 | Frontend test suite (session layer and proxy route handlers) |
| TEST-005 | TEST-005-AC07 | Frontend test suite (AuthContext) |
| TEST-005 | TEST-005-AC08 | Frontend test suite (ColumnHeader and board view) |
| TEST-005 | TEST-005-AC09 | Frontend test suite (CardDetailModal and AddCardForm) |
| TEST-005 | TEST-005-AC10 | Frontend test suite (NotificationBell and useNotifications) |
| TEST-005 | TEST-005-AC11 | Frontend test suite (analytics panel) |
| TEST-006 | TEST-006-AC01 | Playwright configuration |
| TEST-006 | TEST-006-AC02 | Playwright test suite |
| TEST-006 | TEST-006-AC03 | Playwright test suite |
| TEST-006 | TEST-006-AC04 | Playwright configuration and E2E `.env.example` entries |
| TEST-006 | TEST-006-AC05 | Playwright test helpers |
| TEST-006 | TEST-006-AC06 | Playwright global teardown |
| TEST-006 | TEST-006-AC07 | Playwright test helpers |
| TEST-007 | TEST-007-AC01 | Playwright spec (authentication) |
| TEST-007 | TEST-007-AC02 | Playwright spec (authentication) |
| TEST-007 | TEST-007-AC03 | Playwright spec (authentication) |
| TEST-007 | TEST-007-AC04 | Playwright spec (authentication) |
| TEST-007 | TEST-007-AC05 | Playwright spec (authentication) |
| TEST-008 | TEST-008-AC01 | Playwright spec (Kanban journey) |
| TEST-008 | TEST-008-AC02 | Playwright spec (Kanban journey) |
| TEST-008 | TEST-008-AC03 | Playwright spec (Kanban journey) |
| TEST-008 | TEST-008-AC04 | Playwright spec (Kanban journey) |
| TEST-008 | TEST-008-AC05 | Playwright spec (Kanban journey) |
| TEST-008 | TEST-008-AC06 | Playwright spec (Kanban journey) |
| TEST-008 | TEST-008-AC07 | Playwright spec (Kanban journey) |
| TEST-008 | TEST-008-AC08 | Playwright spec (Kanban journey) |
| TEST-009 | TEST-009-AC01 | Playwright configuration (viewport projects) |
| TEST-009 | TEST-009-AC02 | Playwright spec (responsive layout) |
| TEST-010 | TEST-010-AC01 | Backend pytest suite (column deletion) |
| TEST-010 | TEST-010-AC02 | Backend pytest suite (foreign key preservation) |
| TEST-010 | TEST-010-AC03 | Backend pytest suite (column deletion transaction) |
| TEST-010 | TEST-010-AC04 | Backend pytest suite (column deletion) |
| TEST-010 | TEST-010-AC05 | Backend pytest suite (activity-event retention) |
| TEST-010 | TEST-010-AC06 | Backend pytest suite (soft-delete filtering) |
| TEST-010 | TEST-010-AC07 | Backend pytest suite (soft-delete guard) |
| TEST-010 | TEST-010-AC08 | Backend pytest suite (board hard delete) |
| TEST-010 | TEST-010-AC09 | Backend pytest suite (soft-delete invariant) |
| TEST-010 | TEST-010-AC10 | Backend pytest suite (endpoint coverage test) |
| TEST-010 | TEST-010-AC11 | Backend pytest suite (column deletion authorization) |
| TEST-010 | TEST-010-AC12 | Backend pytest suite (column deletion authorization) |
| TEST-010 | TEST-010-AC13 | Backend pytest suite (column deletion authorization) |
| TEST-010 | TEST-010-AC14 | Backend pytest suite (board deletion authorization) |
| TEST-011 | TEST-011-AC01 | Backend pytest suite (notification event matrix) |
| TEST-011 | TEST-011-AC02 | Backend pytest suite (notification concurrency) |
| TEST-011 | TEST-011-AC03 | Backend pytest suite (notification transaction) |
| TEST-011 | TEST-011-AC04 | Backend pytest suite (notification privacy) |
| TEST-011 | TEST-011-AC05 | Backend pytest suite (notification retention) |
| TEST-011 | TEST-011-AC06 | Backend pytest suite (notification board deletion) |
| TEST-011 | TEST-011-AC07 | Backend pytest suite (notification contract) |
| TEST-011 | TEST-011-AC08 | Backend pytest suite (notification repeat assignments) |
| TEST-011 | TEST-011-AC09 | Backend pytest suite (notification recipient check) |
| NFR-001 | NFR-001-AC01 | User model and password hashing (service layer) |
| NFR-001 | NFR-001-AC02 | Flask logging configuration |
| NFR-002 | NFR-002-AC01 | Repository (secret scan procedure in README) |
| NFR-002 | NFR-002-AC02 | Repository `.gitignore` |
| NFR-002 | NFR-002-AC03 | README (deployment section) |
| NFR-002 | NFR-002-AC04 | Frontend `.env.example` |
| NFR-003 | NFR-003-AC01 | Marshmallow schemas (backend) |
| NFR-003 | NFR-003-AC02 | POST /api/boards |
| NFR-003 | NFR-003-AC03 | Backend data access (SQLAlchemy) |
| NFR-004 | NFR-004-AC01 | README (deployment section) |
| NFR-004 | NFR-004-AC02 | Vercel environment configuration |
| NFR-004 | NFR-004-AC03 | Session login route handler (Next.js server) |
| NFR-005 | NFR-005-AC01 | Render-hosted Flask API (measurement procedure in README) |
| NFR-005 | NFR-005-AC02 | README (performance section) |
| NFR-006 | NFR-006-AC01 | Card search filter (Client Component on /boards/[id]) |
| NFR-006 | NFR-006-AC02 | useNotifications |
| NFR-007 | NFR-007-AC01 | Tailwind CSS layout (all pages) |
| NFR-007 | NFR-007-AC02 | Page /boards/[id] |
| NFR-007 | NFR-007-AC03 | Page /login |
| NFR-008 | NFR-008-AC01 | Vercel deployment |
| NFR-008 | NFR-008-AC02 | Render deployment (GET /api/health) |
| NFR-008 | NFR-008-AC03 | Render environment configuration |
| NFR-008 | NFR-008-AC04 | Vercel environment configuration and Flask CORS configuration |
| NFR-009 | NFR-009-AC01 | Flask-Migrate migration scripts |
| NFR-009 | NFR-009-AC02 | Flask-Migrate migration scripts |
| NFR-010 | NFR-010-AC01 | Backend `.env.example` |
| NFR-010 | NFR-010-AC02 | Frontend `.env.example` |
| NFR-010 | NFR-010-AC03 | Backend configuration |
| NFR-011 | NFR-011-AC01 | specs/CHANGELOG.md |
| NFR-011 | NFR-011-AC02 | evidence/ai-reviews/violation-report.md |
| NFR-011 | NFR-011-AC03 | evidence/ai-reviews/violation-report.md and specs/CHANGELOG.md |
| NFR-011 | NFR-011-AC04 | evidence/ai-reviews/violation-report.md |
| NFR-011 | NFR-011-AC05 | guidelines/frontend.md, guidelines/backend.md, guidelines/database.md |
| NFR-011 | NFR-011-AC06 | guidelines/frontend.md, guidelines/backend.md, guidelines/database.md |
| NFR-011 | NFR-011-AC07 | evidence/ai-reviews/ (guideline comparison document) |

## 8. Design Decisions

This section records design decisions. Section 8.1 lists unresolved decisions. Every entry there is **[Proposed, not approved]**. A proposal is a suggestion for discussion and is not a requirement. Section 8.2 lists the **Approved Decisions**. They were settled by human review and are requirements. Entries UD-01 to UD-17 come from the Open Questions in `PROJECT_BRIEF.md` (Question 6, on per-board roles, is resolved by the board-specific authorization constraint and is no longer open). Entries UD-18 to UD-24 were found while writing and reviewing this document. UD-18, UD-19, and UD-23 are approved and are listed in Section 8.2 with their original IDs.

### 8.1 Unresolved decisions

### UD-01 Access token lifetime
- **Proposal:** 60 minutes.
- **Rationale:** Short enough to limit exposure of a stolen token, long enough that a user is not logged out during a session.
- **Affects:** AUTH-003, FRONT-018, FRONT-023.

### UD-02 Refresh strategy
- **Proposal:** No refresh token. An expired session returns the user to `/login`.
- **Rationale:** Simplest option that meets the expiry requirement. A refresh token adds storage and revocation work.
- **Affects:** AUTH-003, API-005.

### UD-07 Additional card fields
- **Proposal:** Add an optional `description` text field and an optional `due_date`. Completion tracking is covered separately by UD-12.
- **Rationale:** These are common Trello-like fields, but only title and assignee are required today.
- **Affects:** CARD-003, FRONT-011.

### UD-09 Pagination defaults and unread count
- **Proposal:** Default `per_page` 20, maximum 100. The notification list response includes the user's total unread count alongside the page of items.
- **Rationale:** `NotificationBell` must show an unread count that covers all pages, not only the first page.
- **Affects:** NOTIF-001, FRONT-016, FRONT-017.

### UD-15 Coverage targets
- **Proposal:** At least 80% line coverage for backend services and routes, and for frontend components and hooks.
- **Rationale:** A common, measurable threshold that is achievable for a project of this size.
- **Affects:** TEST-001, TEST-005.

### UD-16 Environments
- **Proposal:** Two environments, local development and production. Playwright runs only against the deployed production Vercel URL using the dedicated E2E account.
- **Rationale:** Matches the approved deployment targets and avoids setting up a third hosted stack. Note that a Render service on a free plan can respond slowly after being idle, which affects NFR-005 measurements.
- **Affects:** NFR-005, NFR-008, TEST-006.

### UD-17 CI/CD
- **Proposal:** A GitHub Actions workflow runs pytest and the frontend tests on each pull request. Playwright runs after deployment.
- **Rationale:** Runs the fast tests before merge and the deployed-URL tests only once a deployment exists.
- **Affects:** TEST-001, TEST-005, TEST-006.

### UD-21 Password policy
- **Proposal:** Minimum length of 8 characters, with no other composition rules.
- **Rationale:** Length contributes more to strength than composition rules, and a single rule is easy to test.
- **Affects:** AUTH-001.

### UD-22 E2E account provisioning
- **Proposal:** Create the dedicated E2E account once through `POST /api/auth/register`, and store its credentials only as environment variables in CI and local configuration.
- **Rationale:** It uses an existing endpoint and keeps credentials out of the repository.
- **Affects:** TEST-006, TEST-007, TEST-008.

### 8.2 Approved Decisions

These decisions were approved by the human reviewer. They are requirements, not proposals. The derived assumptions A-01 to A-10 in Section 1.4 remain to be confirmed.

### UD-03 Authentication architecture [Approved]
- **Decision:**
  - The JWT is held only in an HttpOnly cookie that a Next.js server-side session layer sets.
  - Server Components read authentication through a server-only session module and call Flask directly with `API_BASE_URL`.
  - Browser-side authenticated requests go to a same-origin Next.js proxy. The proxy forwards the JWT to Flask in the `Authorization: Bearer` header.
  - The raw JWT is never exposed through `AuthContext` or browser JavaScript.
  - Cookie settings: `HttpOnly`; `Secure` in production; `SameSite=Lax`; `Path=/`; no `Domain` attribute; `Max-Age` equal to the remaining JWT lifetime.
  - CSRF protection for cookie-authenticated state-changing requests: `SameSite=Lax`, a required matching `Origin` header, and a required JSON content type.
  - Expired or invalid sessions redirect to `/login`.
  - Direct browser calls through `NEXT_PUBLIC_API_BASE_URL` are limited to `GET /api/health`. Flask accepts the JWT only from the `Authorization` header and allows no credentialed CORS.
- **Rationale:** Browser JavaScript, including injected script, cannot read the token. The `/` and `/boards/[id]` pages can be Server Components that fetch authenticated data. The browser never calls Flask with credentials. The costs are an extra proxy hop for client requests and the CSRF checks above.
- **Governs:** AUTH-003, FRONT-003, FRONT-004, FRONT-018, FRONT-021, FRONT-022, FRONT-023, API-004, API-005, NFR-004, NFR-008.
- **Still open:** The token lifetime (UD-01) and the refresh strategy (UD-02).

### UD-04 Registration and board creation [Approved]
- **Decision:** Successful registration redirects to `/login`. The creator of a board becomes that board's Board Administrator. Membership beyond the creator is managed through the approved extension endpoint (UD-24).
- **Rationale:** A new board needs an administrator, and registration should not create a session without a login step.
- **Governs:** FRONT-001, BOARD-001, BOARD-007.
- **Still open:** The password policy (UD-21).

### UD-05 Administrator-only operations and authorization order [Approved]
- **Decision:**
  - Exactly five operations are administrator-only: `PATCH /api/boards/{id}` (rename board), `DELETE /api/boards/{id}` (delete board), `POST /api/boards/{id}/members` (add member), `PATCH /api/columns/{id}` when the body contains `is_done` (change completion status), and `DELETE /api/columns/{id}` (soft-delete the column and its active cards).
  - Board members and administrators may both view boards, columns, cards, comments, and analytics, create and rename columns, reorder columns, create, edit, move, reorder, and delete cards, and create comments.
  - Any authenticated user may create a board and becomes its administrator.
  - Comment ownership applies equally to administrators and members. Users may edit or delete only their own comments, and administrators have no override.
  - Permissions are board-specific. Being an administrator of board A grants nothing on board B.
  - Authorization checks run in this order: 401 for missing or invalid authentication, uniform 404 for a missing resource or a non-member, 403 for a member without permission, then 400 or 409 for validation or conflict. The full rules, including the framework-level parsing exception, are in Section 2.4.
  - A non-administrator whose PATCH body contains `is_done` receives 403 before field validation, even when the value is invalid or unchanged. A mixed body of `name` and `is_done` from a non-administrator is rejected as a whole with 403 and no change.
  - When an administrator sends an `is_done` value equal to the column's stored value, the completion-state update is a no-op: no `completed_at` is reset, and no activity event or notification is created. Unrelated fields are applied only when they are present and valid. When the value changes, the completion timestamp rules of UD-12 and A-13 apply in one transaction.
- **Rationale:** Board-level and destructive column operations are the narrowest meaning of "management". Column and card work is routine for all members. The comment rule comes from the assignment. A fixed check order and a no-op for an unchanged `is_done` keep unauthorized users from learning anything about validation and keep repeated requests from rewriting completion times.
- **Governs:** Sections 2.1 and 2.4, BOARD-004, BOARD-005, BOARD-006, BOARD-007, COLUMN-002, COLUMN-003, COMMENT-003, COMMENT-004, FRONT-006, FRONT-025, TEST-003, TEST-004, TEST-005, TEST-010.
- **Note:** Column reorder (`PATCH /api/boards/{id}/columns/reorder`) is not in the administrator-only list, so every board member may use it.

### UD-08 Notification events and recipients [Approved]
- **Decision:**
  - **Triggers.** A notification is created when a card is assigned to another board member (`card_assigned`), when a card is reassigned to a different board member (`card_assigned`, new assignee only), and when a comment is created on an assigned card by someone other than its assignee (`comment_added`, recipient is the assignee). Users are never notified about their own actions. A new assignment after an unassignment creates a new notification unless it is a self-assignment. A reassignment from B to C notifies C only.
  - **Exclusions.** No notification for card creation, card unassignment, self-assignment, an unchanged `assignee_id`, card moves and reordering, card title changes, card deletion, column creation, renaming, reordering, completion changes, or deletion, board changes or membership additions, or comment edits and deletions.
  - **Assignment API.** Card creation is title-only and rejects `assignee_id` with HTTP 400. `PATCH /api/cards/{id}` is the only way to assign or unassign an existing card: `assignee_id` is a UUID string to assign or `null` to unassign, and omitting it leaves the assignment unchanged. A nonexistent user and a user who is not a member of the card's board return the same HTTP 400 body. An unchanged `assignee_id` creates no notification and no activity event and does not change `updated_at` by itself.
  - **Persistence and security.** A notification belongs to exactly one recipient and is accessible only to that recipient, and another user receives 404 when reading or marking it. It is created in the same transaction as the originating assignment or comment, only for a valid board-member recipient, and never contains comment text. It remains available (readable and markable) after its card or comment is deleted, and is removed only when its board is hard-deleted. Notifications for earlier assignments are kept after unassignment or reassignment. Failed or rejected operations create none. Concurrent identical assignment requests are serialized with database locking and a comparison with the stored state, and no uniqueness constraint blocks legitimate repeated assignments.
  - **Response contract.** Each item has `id`, `type`, `message`, `board_id`, `card_id`, `actor` (`id` and `name`), `is_read`, and `created_at`, with UUID identifiers and UTC ISO 8601 timestamps, ordered newest first with `id` descending as the tie-breaker. The existing envelope and pagination parameters are unchanged. Messages contain no comment text and no private user data.
  - **Board members for assignment.** `GET /api/boards/{id}` also returns `members` as a list of `{ id, name }` for the board's members only. It exposes no email address or other profile field, keeps every previously required field (including the requester's role), and is the only source of the member list: no additional member-list endpoint is allowed.
  - **Frontend.** `CardDetailModal` has an assignee dropdown with the board's members and an "Unassigned" option, updates the visible card after success, and restores the previous assignee with an error after failure. `AddCardForm` has no assignment control. `NotificationBell` shows the unread count, polls every 30 seconds while authenticated, shows each notification's message, type, and timestamp, distinguishes read from unread, lets the recipient mark notifications as read, navigates to the card when it is available, shows "This card is no longer available" when it is not, never shows comment text, and handles API errors without exposing sensitive details.
- **Rationale:** These are the events that directly concern one user, which keeps notifications relevant and the first version small. Persisting notifications independently of cards keeps the recipient's history and unread count stable. The locking rule prevents duplicate notifications without blocking valid repeated assignments.
- **Governs:** A-04, BOARD-003, CARD-002, CARD-003, CARD-004, COMMENT-001, COLUMN-003, NOTIF-001, NOTIF-002, NOTIF-003, FRONT-006, FRONT-011, FRONT-016, FRONT-017, FRONT-026, TEST-003, TEST-005, TEST-011, Section 2.3.
- **Still open:** The default and maximum `per_page` and the way the unread count is derived across pages (UD-09). The URL mechanism that opens a specific card from a notification link is left to `design.md`.

### UD-10 Search fields and scope [Approved]
- **Decision:** Card search filters card titles within the current board, in the browser, using the board data already loaded from `GET /api/boards/{id}`.
- **Rationale:** The narrowest scope that gives a usable search. It needs no cross-board authorization logic and no new request.
- **Governs:** FRONT-008, NFR-006.

### UD-11 Search API contract [Approved]
- **Decision:** There is no search API endpoint. Searching sends no API request. The 300 ms debounce still applies, and it limits how often the filter runs.
- **Rationale:** The board data is already in the browser, so filtering needs no round trip.
- **Governs:** FRONT-008, NFR-006.

### UD-12 Done columns and completion timestamps [Approved]
- **Decision:**
  - A Board Administrator can mark a column as a done (completed) column through `PATCH /api/columns/{id}`.
  - A card stores a nullable `completed_at` timestamp.
  - Moving a card from a non-done column into a done column sets `completed_at` to the time of the move.
  - Moving a card from a done column into a non-done column sets `completed_at` to null.
  - When a card leaves a done column and enters a done column again, `completed_at` is overwritten with the time of the later entry.
  - `completed_at` represents only the card's current completion state. Earlier timestamps are cleared or overwritten by later transitions, no completion history is stored, and historical completion counts cannot be reconstructed reliably from the activity events, because the three approved event types do not record whether a column was done at the time. The activity events remain available for the separately approved activity reporting (UD-13).
  - "Cards completed this week" counts non-deleted cards in non-deleted done columns whose current `completed_at` falls inside the reporting window of the approved UD-14, each card at most once.
- **Rationale:** A card's current column alone cannot show when the card was completed. A stored timestamp written at the moment of the move gives a reliable completion time and handles reopened cards.
- **Governs:** COLUMN-002, CARD-001, CARD-002, CARD-005, BOARD-003, ANALYTICS-003.
- **Still open:** Nothing. The reporting window is approved in UD-14, the treatment of cards in a deleted column in UD-23, and the remaining completion-timestamp rules in A-13.

### UD-13 Member activity events [Approved]
- **Decision:**
  - The service layer appends one row to an auditable activity-event table for each card creation, each card movement to another column, and each comment creation.
  - Each row stores the board, the acting user, the event type, the card, and the event time. A movement row also stores the source and destination columns.
  - A member's activity is the count of that member's events for the board inside the reporting window of the approved UD-14. A current member with no qualifying events has a count of 0.
  - Analytics are calculated with SQLAlchemy joins in the service layer.
- **Rationale:** Current data cannot show who did what and when. An append-only log written at the time of each action gives a reliable count and keeps boards separate.
- **Governs:** ANALYTICS-004, ANALYTICS-005, ANALYTICS-006.
- **Still open:** Nothing. The reporting window is approved in UD-14, and further rules are in the approved A-13 and A-14.

### UD-14 Analytics reporting window [Approved]
- **Decision:**
  - **Window.** The reporting week starts on Monday at 00:00:00 UTC and ends at the following Monday at 00:00:00 UTC. The interval is half-open: `window_start <= timestamp < window_end`. Sunday 23:59:59 is not used as the end boundary.
  - **Time zone and range.** Reporting uses UTC and no user or board time zone setting exists. The analytics API reports the current UTC calendar week only and supports no custom date ranges. Any query parameter on `GET /api/boards/{id}/analytics` returns HTTP 400. No new endpoint is added.
  - **Shared window.** `completed_this_week` and member activity use the same window, and the response states it explicitly as `window.start` and `window.end`.
  - **Response.** `data` contains `window` (`start`, `end`, in ISO 8601 UTC with `Z`), `cards_per_column` (entries with `column_id`, `name`, and `card_count`, ordered by column position), `completed_this_week` (an integer), and `member_activity` (entries with `user_id`, `name`, and `activity_count`, ordered by `activity_count` descending, then `name` ascending, then `user_id` ascending). Empty arrays and zero counts are returned explicitly and never omitted or null. No email address or other private profile field is exposed.
  - **Completed this week.** The number of non-soft-deleted cards in non-soft-deleted done columns whose current `completed_at` is inside the window, each card at most once. The count uses the current `completed_at`, not a reconstruction from activity events, and no completion history is stored. For a non-deleted card in a non-deleted column, `completed_at` is non-null if and only if the column is done. A card in a column newly marked done counts as completed this week even if it was created months earlier, and a card completed twice counts once with its latest `completed_at`. The lifecycle of UD-12 and A-13 is unchanged.
  - **Member activity.** A member's `activity_count` is the number of their `card_created`, `card_moved`, and `comment_created` events for the board whose event time is inside the window. Each event counts once, three moves count as three, other boards are excluded, and events of cards, columns, or comments that were later soft-deleted or deleted are included. Actions that create no approved event type are not counted, and there is no per-type breakdown. The response has one entry for each current board member (0 when no qualifying events), counts a member who joined during the week for all their qualifying events of that week without proration, and has no entry for former members.
- **Rationale:** A fixed UTC week with a half-open interval is deterministic and has no gap or overlap at the boundaries. Reporting only the current week avoids promising history that `completed_at` cannot provide, because it is cleared or overwritten by later transitions. Counting soft-deleted resources' events keeps member activity an audit of what members did, while the completed count describes the board's current state.
- **Governs:** ANALYTICS-001 to ANALYTICS-006, FRONT-007, FRONT-025, NFR-005, TEST-004, TEST-005, UD-12, UD-13, A-14, Section 2.3.

### UD-18 Soft-delete scope [Approved]
- **Decision:**
  - Boards are hard-deleted.
  - Columns are soft-deleted using a nullable UTC `deleted_at` timestamp.
  - Cards are soft-deleted using their `deleted_at` timestamp.
  - Comments are hard-deleted when explicitly deleted.
  - Normal board, card, and analytics queries exclude soft-deleted columns and cards.
  - Mutations that target a soft-deleted column or card do not operate on it and return HTTP 404.
  - Hard-deleting a board removes its dependent columns, cards (including soft-deleted ones), comments, notifications, memberships, and activity events, using an explicitly defined deletion order or foreign-key strategy that never leaves orphan rows or raises a foreign-key error.
  - Existing activity events survive the soft-deletion of columns and cards and the deletion of comments.
  - No restore or undelete endpoint is required.
- **Rationale:** Soft deletion keeps the card-to-column foreign key and the activity history intact. A board is a self-contained tree, so deleting it removes everything below it.
- **Governs:** BOARD-003, BOARD-005, COLUMN-003, COLUMN-005, CARD-001, CARD-004, COMMENT-004, ANALYTICS-002, ANALYTICS-003, ANALYTICS-006, TEST-010.

### UD-19 Status-code and response-body conventions [Approved]
- **Decision:**
  - **Envelopes.** All successful responses use `{ "data": ... }` and all error responses use `{ "error": "<non-empty message>" }`. A success response has no `error` key, an error response has no `data` key, and JSON responses use `Content-Type: application/json`. The authorization and validation precedence of UD-05 and Section 2.4 is unchanged.
  - **Statuses.** 200 for successful GET, PATCH, and DELETE, login, notification mark-as-read, and the health check. 201 for successful registration, board creation, column creation, card creation, comment creation, and board-member addition. 400 for request validation failures, including the already approved special cases. 401 for a missing, invalid, or expired JWT and for invalid or unknown login credentials. 403 for a board member attempting an administrator-only operation and for a non-owner editing or deleting another user's comment. 404 for missing resources, inaccessible boards and resources (uniform for non-members), soft-deleted cards and columns, notifications of other users, and an unregistered email in member addition. 409 for a duplicate registration email, a duplicate profile email, and duplicate board membership. 405 and 415 keep the framework-level exception of Section 2.4 and use the error envelope. 500 for an unhandled server error with a generic message that exposes no stack trace, SQL statement, token, or internal exception detail. A more specific approved rule overrides a general one.
  - **Success bodies.** A successful POST that creates a resource returns the created resource. A successful PATCH returns the complete updated public resource. A successful DELETE returns HTTP 200 with `{ "data": { "id": "<uuid>" } }` and never HTTP 204, for boards, columns, cards, and comments, and a repeated delete still returns the 404 that the existing criteria require. A GET that lists resources returns an array, and `[]` when empty, except where a specialized contract is approved or still pending. No success body exposes a password, a password hash, or internal-only data, and the only token ever returned is the login `access_token`.
  - **Login.** `POST /api/auth/login` returns HTTP 200 with `{ "data": { "access_token": "<jwt>" } }`. It adds no refresh token and no authentication endpoint, the Next.js server consumes it, and the raw JWT is never exposed to the browser. The Next.js server may derive the session expiry from the JWT `exp` claim, and the session interface may expose a non-sensitive `expires_at` value.
  - **Health.** `GET /api/health` returns HTTP 200 with `{ "data": { "status": "ok" } }` and performs no database check.
  - **Deferred.** The notification pagination shape (UD-09), the token lifetime (UD-01), the refresh policy (UD-02), the password-length policy (UD-21), are not decided here. The reorder response and the naming of position versus order were decided afterward in UD-20, and the card position rebalancing and its response in UD-06.
- **Rationale:** One envelope, one status per kind of outcome, and one delete shape let the API client, the tests, and the Next.js proxy treat every endpoint the same way. Returning the resource ID on delete keeps the `{ "data": ... }` envelope valid without HTTP 204 and gives the client the ID to remove from its state.
- **Governs:** Section 2.3, API-001, API-002, API-003, API-005, AUTH-002, BOARD-005, COLUMN-003, CARD-004, COMMENT-004, TEST-001.

### UD-20 Column reorder contract and position/order naming [Approved]
- **Decision:**
  - **Endpoint.** `PATCH /api/boards/{id}/columns/reorder` reorders columns using positive FLOAT `order` values. No new endpoint is introduced. Any authenticated board member may reorder columns, and the five administrator-only operations of UD-05 are unchanged.
  - **Request.** A JSON object with exactly the key `columns`, a non-empty array whose entries have exactly `id` (a valid UUID) and `order` (a positive, finite JSON number). Partial lists are allowed and may update one or more columns. Each column ID appears at most once, and duplicate `order` values within a request are invalid. Booleans, strings, null, `NaN`, `Infinity`, zero, and negative values are rejected, and unknown fields are rejected (A-06). No maximum `order` is imposed, and values that cannot be stored as finite positive floats are rejected with HTTP 400. A nonexistent, foreign-board, or soft-deleted column ID returns the same generic HTTP 400 body.
  - **Validation and writes.** The service takes a row lock on the board, re-reads the active columns, applies the submitted values in memory, keeps the stored values of unlisted columns, and validates that all final `order` values are positive, finite, and pairwise distinct. A collision with an unlisted active column returns HTTP 409 and duplicates inside the request return HTTP 400. Nothing changes on a failure. Accepted changes are written atomically in one transaction. Unlisted columns are never renumbered silently. Column creation and deletion take the same board lock.
  - **Concurrency.** Concurrent requests are serialized by the board lock, and the later one validates against the state that the earlier one committed, so a collision returns 409 and a valid request may succeed. Stale clients are not always detected, and no version field, ETag, or endpoint is added.
  - **Response.** HTTP 200 with `data` as an array of all active columns of the board in ascending `order`, each with at least `id`, `name`, `order`, and `is_done`, and no soft-deleted column. It contains no `rebalanced` flag and keeps the UD-19 envelope. The reorder response exemption of UD-19 is removed, and the notification pagination exemption of UD-09 stays.
  - **No-op and timestamps.** A request whose values all equal the stored values returns HTTP 200 with the complete array and writes nothing. `updated_at` changes only for columns whose `order` changed. A reorder creates no activity event or notification.
  - **Normalization.** A normal drag sends only the moved column with a value between its neighbors. When no distinct midpoint exists, the frontend may send every active column it loaded, once each, through the same endpoint, with no flag and no minimum-gap threshold. The payload cannot distinguish this from a partial request that lists every column, so the server detects only deleted or soft-deleted listed columns (HTTP 400) and collisions with unlisted columns (HTTP 409). A column added by another user in the meantime is not detected, and the frontend refetches the board after any 400 or 409. Card positions are handled separately by the approved UD-06.
  - **Naming.** The database column and the SQLAlchemy model attribute are `position`, and the API JSON field is `order` in every request and response. The path `/api/cards/{id}/position` is unchanged, and the API schema maps `position` to `order`. "Ascending position" may still describe the internal ordering concept but never a public JSON field.
- **Rationale:** Explicit float values keep the approved FLOAT strategy, allow a single-column write for a normal drag, and let concurrent independent moves merge. Validating the final state under a board lock keeps the active `order` values distinct, which a database unique index cannot do for swaps. One field name in the API avoids two names for the same value, and the model attribute avoids the SQL reserved word `order`.
- **Governs:** Section 2.3, API-001, COLUMN-001, COLUMN-003, COLUMN-004, COLUMN-005, CARD-001, CARD-002, CARD-005, BOARD-003, FRONT-006, FRONT-019, ANALYTICS-001, ANALYTICS-002, TEST-004, TEST-008, A-01, A-04, A-05.

### UD-06 Card position rebalancing [Approved]
- **Decision:**
  - **Storage and naming.** Card positions are positive FLOAT values in the database and the `position` attribute, exposed as `order` in API JSON (UD-20).
  - **Normal moves.** Drag-and-drop uses midpoint `order` values between the neighboring cards.
  - **Trigger.** When no distinct representable midpoint exists, the frontend sends the `order` of the neighbor that must follow the dropped card. The service layer treats an `order` equal to that of another active card in the destination column as a tie. No minimum-gap threshold exists, and a tie is the only trigger.
  - **Rebalancing.** The moved card is placed immediately before the tied card, and the destination column's active cards, including the moved card, receive evenly spaced positive FLOAT values 1024.0, 2048.0, 3072.0, and so on in the final sequence (ascending `order`, then `created_at`, then `id`). Soft-deleted cards are untouched.
  - **Atomicity and concurrency.** Rebalancing happens in the same transaction as the move. The service takes a row lock on the destination column, and card creation takes the same lock.
  - **Response.** `PATCH /api/cards/{id}/position` returns the moved card with its authoritative final `order` and a boolean `rebalanced`. When `rebalanced` is true, the frontend refetches the board.
  - **Side effects.** Rebalancing creates no extra activity event or notification, and authorization, board membership, soft-delete, activity-event, and notification rules are unchanged. No endpoint, table, or page is added.
  - **Columns.** Column normalization is handled through the approved reorder endpoint (UD-20) and is unaffected.
- **Rationale:** Repeated midpoint inserts exhaust float precision, so a rebalance restores gaps without changing the visible order. A tie is detectable exactly and needs no threshold, and the "before the tied card" rule lets the unchanged payload express the intended position. The response flag tells the client when other cards changed.
- **Governs:** CARD-002, CARD-005, CARD-006, FRONT-019, TEST-004, Section 2.3, API-001, UD-19, UD-20.
- **Limitation:** The tie rule places the moved card before the tied card, so a drop after the last card cannot be expressed by a tie. This only matters if the last card's `order` is so large that no greater finite value exists, which cannot happen with values produced by the application.

### UD-23 Cards in a deleted column [Approved]
- **Decision:**
  - Deleting a column soft-deletes the column and all its currently active cards in one database transaction.
  - The column and the affected cards receive the same UTC `deleted_at` timestamp.
  - Cards that were already soft-deleted keep their original `deleted_at`.
  - The `cards.column_id` foreign key is preserved. The column is not hard-deleted and its cards are not cascade-deleted.
  - Existing activity events survive.
- **Rationale:** One transaction and one timestamp keep a column and its cards consistent. A shared timestamp also identifies which cards were removed with the column. Preserving the foreign key avoids orphaned cards and keeps the activity history joinable.
- **Governs:** COLUMN-003, COLUMN-005, CARD-001, CARD-004, ANALYTICS-002, ANALYTICS-006, FRONT-006, TEST-010.

### UD-24 Board membership endpoint [Approved extension]
- **Decision:** Add `POST /api/boards/{id}/members` as one extension endpoint. Only Board Administrators may call it. It accepts the email of an existing registered user and adds that user as a Board Member. It rejects duplicate membership. It preserves board isolation and authorization. It does not change the 26 mandatory endpoints, and no other membership endpoint is added.
- **Rationale:** None of the 26 mandatory endpoints can add a second member to a board. Without it, the Board Member role and the 403 checks for non-administrators cannot be exercised.
- **Governs:** BOARD-007, BOARD-006, TEST-003, TEST-004.
- **Note:** An unregistered email returns 404 (BOARD-007-AC05, A-13). This lets an administrator learn whether an email is registered.

### A-11 Card search matching [Approved]
- **Decision:** Card search matches when the card title contains the search term, ignoring letter case. Leading and trailing whitespace in the term is ignored. The filter runs on board data already loaded in the browser, and the 300 ms debounce is preserved.
- **Governs:** FRONT-008, NFR-006.

### A-12 Page architecture [Approved]
- **Decision:** The `/` Dashboard and `/boards/[id]` Board Detail pages are Server Components. The `/register`, `/login`, `/my-tasks`, and `/profile` page files are Server Components that render Client Components where interaction is needed. Client Components handle forms, modals, drag-and-drop, notifications, and browser interactions. The root layout is a Server Component.
- **Governs:** Section 4.1, FRONT-001, FRONT-002, FRONT-005, FRONT-006, FRONT-009, FRONT-010, FRONT-021.

### A-13 Completion timestamps and activity behavior [Approved]
- **Decision:**
  1. A card created in a done column receives `completed_at` at creation.
  2. Moving a card from an active column into a done column sets `completed_at`.
  3. Moving a card between two done columns preserves `completed_at`.
  4. Moving a card from a done column to an active column clears `completed_at`.
  5. Marking a column as done stamps its existing active (non-deleted) cards with the current completion timestamp.
  6. Unmarking a done column clears `completed_at` for its cards.
  7. Only movement between different columns creates a card-movement activity event. Reordering within a column creates none.
  8. Activity events remain available after their referenced card or comment is deleted.
  9. The column model uses a Boolean `is_done` field.
  10. The membership extension returns HTTP 404 for an email that does not belong to a registered user.
- **Governs:** COLUMN-002, COLUMN-005, CARD-001, CARD-002, CARD-005, ANALYTICS-003, ANALYTICS-006, BOARD-007, FRONT-025.
- **Frontend:** Board Administrators toggle a column between Done and Active from `ColumnHeader` (FRONT-025-AC09 to AC15).

### A-14 Comment events, activity window, duplicate membership, and board role [Approved]
- **Decision:**
  1. Editing or deleting a comment does not create a member activity event.
  2. Member activity uses the reporting window defined by the approved UD-14: the current UTC week from Monday 00:00:00 UTC (inclusive) to the following Monday 00:00:00 UTC (exclusive).
  3. Adding a user who is already a member of the same board returns HTTP 409.
  4. `GET /api/boards/{id}` includes the authenticated requester's board role, which is `administrator` or `member`.
- **Governs:** ANALYTICS-004, ANALYTICS-006, BOARD-003, BOARD-007, FRONT-025, Section 2.3.

### A-15 Consequences of soft deletion [Approved]
- **Decision:**
  1. Soft-deleting a card preserves its comments in the database. The comment endpoints (create, list, edit, delete) return HTTP 404 while the card is soft-deleted.
  2. Soft-deleted cards retain their `completed_at` and assignee values.
  3. A soft-deleted column returns HTTP 404 when it is directly accessed or mutated.
  4. Using a soft-deleted column as the destination of a card move, or including it in a reorder payload, returns HTTP 400.
  5. Deleting a card or a column does not create an activity event.
  6. Cards that were already soft-deleted keep their original `deleted_at` when their column is deleted (this repeats UD-23).
- **Governs:** COLUMN-002, COLUMN-003, COLUMN-004, CARD-002, CARD-004, CARD-005, COMMENT-001, COMMENT-002, COMMENT-003, COMMENT-004, ANALYTICS-006, Section 2.3.

## 9. Requirement Index and Summary

| Category | Name | Requirements | Acceptance criteria |
|---|---|---|---|
| AUTH | Authentication | 4 | 18 |
| BOARD | Board management and membership | 7 | 48 |
| COLUMN | Column management | 5 | 68 |
| CARD | Card management and positioning | 7 | 79 |
| COMMENT | Comments | 4 | 30 |
| NOTIF | Notifications | 3 | 36 |
| ANALYTICS | Board analytics | 6 | 53 |
| USER | User profile | 2 | 9 |
| FRONT | Frontend pages and components | 26 | 191 |
| API | API client and response format | 7 | 37 |
| TEST | Testing | 11 | 106 |
| NFR | Non-functional requirements | 11 | 35 |
| **Total** | | **93** | **710** |

- Mandatory Flask API endpoints covered: 26 of 26.
- Approved extension endpoints covered: 1 of 1 (`POST /api/boards/{id}/members`, BOARD-007, 10 acceptance criteria).
- Next.js pages covered: 6 of 6.
- Approved decisions: 15 (UD-03, UD-04, UD-05, UD-06, UD-08, UD-10, UD-11, UD-12, UD-13, UD-14, UD-18, UD-19, UD-20, UD-23, UD-24) plus 5 approved assumptions (A-11, A-12, A-13, A-14, A-15).
- Unresolved design decisions (all [Proposed, not approved]): 9.
- Acceptance criteria blocked by an unresolved decision: 0. Blocking decisions: none.
