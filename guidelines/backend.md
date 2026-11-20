# RevoTask Backend Guidelines
These guidelines apply to the Flask API (Flask, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Marshmallow, pytest). They are steering rules for people and AI tools that write or review backend code.
- **Source of truth:** `specs/requirements.md`. If a guideline and the requirements disagree, the requirements win and the guideline must be corrected.
- **Format:** every guideline has an ID (`BE-nn`) and exactly three labeled parts: **Rule**, **Rationale**, and **Concrete Example**. A violation report cites the ID.
- **Wording:** MUST and MUST NOT are mandatory. The check named in a Rule is how a reviewer or a test verifies it.
- **Scope:** the 26 mandatory endpoints plus the one approved extension (`POST /api/boards/{id}/members`). Nothing here adds an endpoint, entity, or feature. Database rules live in `guidelines/database.md`.
---
## 1. Structure and layering
### BE-01 Application factory, config from the environment
**Rule:** The app is built by `create_app(config=None)`. Extensions (`db`, `migrate`, `jwt`) are created at module level without an app and bound with `init_app` inside the factory. All settings (database URL, JWT secret, allowed web origin for the health route) come from environment variables read in a config object. No secret or connection string appears in source, tests, or logs. Tests call `create_app` with a test config. Check: grep finds no literal secret or URL, and the test suite builds the app only through the factory.
**Rationale:** A factory lets tests run with isolated config, and environment-only secrets satisfy NFR-001 and the deployment rules.
**Concrete Example:**
```python
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)          # Config reads os.environ
    if config:
        app.config.update(config)
    db.init_app(app); migrate.init_app(app, db); jwt.init_app(app)
    register_blueprints(app); register_error_handlers(app)
    return app
```
### BE-02 Eight Blueprints, no more
**Rule:** The API consists of exactly eight Blueprints: `auth`, `users`, `boards`, `columns`, `cards`, `comments`, `notifications`, `analytics`. Each lives in `app/blueprints/<name>/` with `routes.py`, `service.py`, and `schema.py`. Route ownership: `auth` (register, login), `users` (`GET`/`PATCH /api/users/me`), `boards` (board CRUD and `POST /api/boards/{id}/members`), `columns` (create, reorder, update, delete), `cards` (create, update, delete, position, `GET /api/cards?assignee=me`), `comments`, `notifications`, `analytics`. `GET /api/health` is a plain route on the app and is not a ninth Blueprint. Models live in `app/models/`. Check: a test lists `app.blueprints` and asserts the eight names, and the endpoint-coverage test (TEST-001-AC02) asserts every route in the 26+1 list exists.
**Rationale:** A fixed layout keeps one feature in one place and stops endpoint creep (API-001).
**Concrete Example:**
```python
for bp in (auth_bp, users_bp, boards_bp, columns_bp, cards_bp, comments_bp, notifications_bp, analytics_bp):
    app.register_blueprint(bp, url_prefix="/api")
```
### BE-03 Routes, services, models, and schemas have separate jobs
**Rule:** `routes.py` only parses the request, loads and validates input through a schema, calls one service function, and returns the envelope. `service.py` holds business rules, authorization checks, transactions, and locking. `schema.py` holds Marshmallow schemas only. Models hold columns and relationships, not business rules. A route MUST NOT call `db.session.commit()` or build a query. A service MUST NOT import `flask.request`. Check: grep of `routes.py` for `session.` and `query`, and grep of `service.py` for `request`.
**Rationale:** Services that do not depend on the request object can be tested directly and reused by the transaction and concurrency tests.
**Concrete Example:**
```python
@cards_bp.patch("/cards/<uuid:card_id>/position")
@jwt_required()
def move_card(card_id):
    payload = MoveCardSchema().load(request.get_json())
    card, rebalanced = card_service.move_card(current_user_id(), card_id, payload)
    return ok({**CardSchema().dump(card), "rebalanced": rebalanced})
```
---
## 2. Requests, responses, and errors
### BE-04 One response envelope
**Rule:** Every JSON response uses `{"data": ...}` on success and `{"error": {...}}` on failure through shared helpers (`ok`, `fail`). `DELETE` returns `{"data": {"id": "<id>"}}`. Login returns `{"data": {"access_token": "..."}}` and nothing else. Health returns `{"data": {"status": "ok"}}`. No route returns a bare object, list, or string. Check: the contract tests (TEST-001-AC04, AC05) assert the envelope for every endpoint including error paths.
**Rationale:** The frontend `apiClient.ts` depends on one shape (API-002).
**Concrete Example:**
```python
def ok(data, status=200):
    return jsonify({"data": data}), status

def fail(code, message, status, details=None):
    body = {"code": code, "message": message}
    if details: body["details"] = details
    return jsonify({"error": body}), status
```
### BE-05 Central error handlers
**Rule:** Register handlers so the envelope also covers framework errors: Marshmallow `ValidationError` (400), 401 from JWT callbacks, 404, 405, 415, and unhandled exceptions (500). The 500 body is a fixed generic message. It MUST NOT include a stack trace, SQL text, a token, or an exception string. The full exception is logged server side without the token or the request body. Invalid JSON returns 400. A missing JSON content type on a body route returns 415. Check: tests that force an exception and assert the body contains none of the exception text (API-002-AC05).
**Rationale:** Leaked internals help attackers, and a client's error parser must work for every status.
**Concrete Example:**
```python
@app.errorhandler(Exception)
def unhandled(exc):
    app.logger.exception("unhandled error")          # no token, no body
    return fail("internal_error", "Something went wrong.", 500)
```
### BE-06 Marshmallow validates every input strictly
**Rule:** Every route that accepts a body, query string, or path value used as data has a Marshmallow schema defined with `unknown = RAISE`, so an unknown field returns 400 (A-06). Query strings on `GET /api/boards/{id}/analytics` are rejected with 400 when any parameter is present. Numeric fields (`order` and any position value) MUST be real JSON numbers: reject booleans, strings, `null`, `NaN`, `Infinity`, `1e400`, and `1e-400` (CARD-006-AC04, COLUMN-004-AC02). Parse JSON with a hook that rejects `NaN` and `Infinity` constants. Schemas never accept `id`, `created_at`, `deleted_at`, `completed_at`, `board_id`, or role fields from the client unless the requirement names them. Check: parametrized tests per schema for unknown field, wrong type, and each bad number.
**Rationale:** Mass assignment and silent coercion cause integrity and security bugs (NFR-001, NFR-003).
**Concrete Example:**
```python
class MoveCardSchema(Schema):
    class Meta:
        unknown = RAISE
    column_id = fields.UUID(required=True)
    order = StrictNumber(required=True)   # custom field: rejects bool, str, None, NaN, +-Infinity, out-of-range
```
---
## 3. Authentication and authorization
### BE-07 JWT through the Authorization header only
**Rule:** Protected routes use `@jwt_required()` and read the token only from the `Authorization: Bearer` header. Cookies, query strings, and request bodies are never a token source (AUTH-003-AC06). The token carries the user id as the subject and nothing used for authorization. Token lifetime and refresh behavior are undecided (UD-01, UD-02): code MUST NOT hard-code a lifetime outside config and MUST NOT add a refresh endpoint. Missing, malformed, or expired tokens return 401 in the envelope. Check: tests with no header, a bad token, an expired token, and a token in a cookie.
**Rationale:** The Next.js server holds the token in an HttpOnly cookie and forwards it as a header, so Flask has one input path.
**Concrete Example:**
```python
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
token = create_access_token(identity=str(user.id))   # lifetime comes from config, not from this call
```
### BE-08 Authorization comes from the database, never from claims
**Rule:** Board role (`administrator` or `member`) is read from `BoardMembership` on every request. Services load membership through one helper such as `require_board_access(user_id, board_id)`. No code reads a role, membership, or board id from the token or from the request body. Check: a test that changes a user's membership in the database and asserts the next request with the same token sees the new role.
**Rationale:** Roles are per board and can change, so a token cannot hold them (AUTH-003, A-12).
**Concrete Example:**
```python
def require_board_access(user_id, board_id):
    m = BoardMembership.query.filter_by(user_id=user_id, board_id=board_id).first()
    if m is None or m.board is None:
        raise NotFound()          # same body as a missing board
    return m
```
### BE-09 Check order: 401, 404, 403, then 400/409
**Rule:** Every protected route follows Section 2.4 in this order: (1) authentication, 401; (2) resource lookup and membership, 404, with one uniform body for a missing resource, a soft-deleted resource, and a board the user does not belong to; (3) role or ownership, 403; (4) body validation and state conflicts, 400 or 409. Authorization runs before schema validation, so a non-member never learns whether a body was valid. Framework parse errors (invalid JSON, 415, 405, unmatched route) may occur earlier. A route MUST NOT run its schema before authorization has passed. Check: for each endpoint a test sends an invalid body as a non-member and asserts 404, and as a non-admin on an admin-only route and asserts 403.
**Rationale:** The order prevents leaking which boards, cards, or columns exist (UD-05, Section 2.4).
**Concrete Example:**
```python
def update_board(user_id, board_id, data):
    m = require_board_access(user_id, board_id)     # 404 for non-member or missing
    if m.role != "administrator":
        raise Forbidden()                           # 403
    payload = BoardUpdateSchema().load(data)        # 400 only now
```
### BE-10 Five admin-only operations and comment ownership
**Rule:** Only these operations require the `administrator` role: `PATCH /api/boards/{id}`, `DELETE /api/boards/{id}`, `POST /api/boards/{id}/members`, `PATCH /api/columns/{id}` when the body sets `is_done`, and `DELETE /api/columns/{id}`. Every other board operation is open to any member. Editing or deleting a comment requires being its author; a non-author member gets 403, and a non-member gets 404. Each rule lives in one named helper and no route adds its own variation. Setting `is_done` to its current value is idempotent: it returns success without writing and without a new `completed_at` (UD-05). Check: a permissions matrix test with administrator, member, and non-member for all 26+1 endpoints.
**Rationale:** A single approved list stops permission drift (UD-05, COMMENT rules).
**Concrete Example:**
```python
ADMIN_ONLY = {"board.update", "board.delete", "board.add_member", "column.set_done", "column.delete"}

def require_admin(membership):
    if membership.role != "administrator":
        raise Forbidden()
```
---
## 4. Business rules in services
### BE-11 Soft-deleted rows are invisible
**Rule:** Columns and cards are soft-deleted by setting `deleted_at`. Boards and comments are hard-deleted. Every read, count, join, and analytics query on columns and cards MUST filter `deleted_at IS NULL` through shared query helpers, not ad hoc per route. A soft-deleted column or card returns the same 404 body as a missing one. Deleting a column soft-deletes its non-deleted cards in the same transaction. Check: tests that soft-delete a column and then request it, its cards, the board view, My Tasks, search data, and analytics, and assert it is absent everywhere (UD-18, UD-23).
**Rationale:** One forgotten filter shows deleted data or leaks counts.
**Concrete Example:**
```python
def live_cards(column_id):
    return Card.query.filter(Card.column_id == column_id, Card.deleted_at.is_(None))
```
### BE-12 Column ordering, `order`, and rebalancing
**Rule:** The API field is `order`, mapped to the model attribute and DB column `position` (FLOAT). Schemas rename with `data_key`. New items go after the current maximum for their parent. `PATCH /api/cards/{id}/position` places a card in the destination column with the sent `order`. When the sent `order` equals another live card's `order` in that column, place the card before the tied card, then renumber the destination column `1024.0, 2048.0, ...` sorted by `order`, `created_at`, `id`, and return `rebalanced: true`; otherwise return `rebalanced: false`. `PATCH /api/boards/{id}/columns/reorder` takes `{columns: [{id, order}]}` and returns 409 if a listed `order` collides with an unlisted column. Final-state validation happens under the lock, so swaps pass. A request that changes nothing performs no UPDATE. Check: tests for tie, swap, collision, and no-op, with SQL capture for the no-op.
**Rationale:** FLOAT positions avoid renumbering on every move, and a deterministic tie rule keeps clients and server in agreement (UD-06, UD-20).
**Concrete Example:**
```python
class CardSchema(Schema):
    order = fields.Float(attribute="position", data_key="order", dump_only=True)
```
### BE-13 Completion timestamps follow the column
**Rule:** `is_done` on a column controls `completed_at` on its live cards. A card entering a done column gets `completed_at` set to the request clock reading. A card leaving a done column gets `completed_at = NULL`. Setting `is_done` on a column updates `completed_at` for all its live cards in the same transaction. A card in a non-done column never has a `completed_at`. Soft-deleted cards and cards in soft-deleted columns are excluded from analytics. Check: tests for move in, move out, toggle on, toggle off, and a toggle that changes nothing.
**Rationale:** The weekly completion metric depends on this invariant (ANALYTICS-005, ANALYTICS-006).
**Concrete Example:**
```python
card.completed_at = now if dest_column.is_done else None
```
### BE-14 Activity events and notifications are written in the same transaction
**Rule:** The service that changes state also appends the `ActivityEvent` and any `Notification` in the same transaction. If the change rolls back, the event and notification roll back. Notifications are created only for `card_assigned` and `comment_added`, never for the actor's own action. Assignment uses `assignee_id`: `null` unassigns, the assignee must be a member of the board, and card creation rejects `assignee_id`. A re-assignment to the same user creates no event and no notification (compare under the card row lock, NOTIF-003-AC08). Repeated valid assignments to different states may create repeated notifications (UD-08). Marking a notification read affects only the owner's notification, and another user's notification returns 404. Check: tests for rollback, no-op assignment, self-assignment, and non-member assignee.
**Rationale:** Events and notifications that do not match committed data corrupt analytics and the bell count.
**Concrete Example:**
```python
with db.session.begin_nested():
    card = lock_card(card_id)
    if card.assignee_id != new_assignee_id:
        card.assignee_id = new_assignee_id
        db.session.add(ActivityEvent(board_id=card.board_id, card_id=card.id, actor_id=user_id, type="card_assigned", created_at=now))
        if new_assignee_id and new_assignee_id != user_id:
            db.session.add(Notification(user_id=new_assignee_id, board_id=card.board_id, type="card_assigned", card_id=card.id, created_at=now))
```
### BE-15 Analytics is one clock reading and a join
**Rule:** `GET /api/boards/{id}/analytics` computes a current UTC Monday-to-Monday half-open window `[start, end)` from one clock reading. The response has exactly `window`, `cards_per_column`, `completed_this_week`, and `member_activity`. `cards_per_column` and member counts come from a single grouped query with JOINs, not a query per column or user. All queries exclude soft-deleted data. Any query parameter returns 400. The clock is injectable (`app.extensions` or a parameter) so tests can fix it. Check: tests at the boundary instants (Monday 00:00:00 UTC inclusive, next Monday exclusive) and a SQL-capture test that counts statements.
**Rationale:** An N+1 pattern and a double clock read both produce wrong or slow results (ANALYTICS-005, ANALYTICS-006).
**Concrete Example:**
```python
def week_window(now: datetime):
    start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=7)
```
---
## 5. Transactions and concurrency
### BE-16 One request, one atomic transaction
**Rule:** A service function that writes opens one transaction and commits once at the end. Any exception rolls the whole transaction back. No route commits, and no service commits halfway and then continues writing. Validation and authorization errors raise before any write. A failed multi-step operation (column delete with its cards, board hard-delete, move with rebalance, assignment with event and notification) MUST leave no partial state. Check: tests that inject a failure at the last step and assert nothing changed.
**Rationale:** Partial writes cannot be repaired by the client (NFR-004).
**Concrete Example:**
```python
def delete_column(user_id, column_id):
    try:
        ...   # authorization, lock, soft-delete column and cards, append event
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
```
### BE-17 Row locks and lock order
**Rule:** Use `SELECT ... FOR UPDATE` (`with_for_update()`) in these cases: the board row for column reorder, create, and delete (UD-20); the destination column row for card move and card creation (UD-06); the card row, then a state comparison, for assignment (NOTIF-003-AC08). When a request needs several locks, take them in this order: board row, then column rows by ascending id, then card rows by ascending id. After taking a lock, re-read the row and re-check existence, `deleted_at`, and permissions before writing. Never lock in the reverse order. Never hold a lock across a network call. Check: SQL-capture tests that assert `FOR UPDATE` and its order, and concurrency tests on separate connections (two simultaneous moves into one column, reorder against column delete, two simultaneous assignments).
**Rationale:** A fixed order prevents deadlocks, and the re-read prevents acting on stale state. The order itself is a guideline-level rule, and the requirements only mandate the locks listed above.
**Concrete Example:**
```python
column = (Column.query.filter_by(id=dest_id).with_for_update().one_or_none())
if column is None or column.deleted_at is not None:
    raise NotFound()
```
---
## 6. Security and logging
### BE-18 Passwords, secrets, and injection
**Rule:** Passwords are hashed with a vetted library (the algorithm is a design.md decision) and the hash is never returned, logged, or placed in an error. Login failure returns one generic message for an unknown email and a wrong password. All queries use the SQLAlchemy expression API or bound parameters. String-built SQL (f-strings, `%`, `+`, `text()` with interpolated values) is forbidden. Password policy (UD-21) and email case handling are undecided: code MUST NOT invent them beyond what the requirements state. Check: grep for string-built SQL, a test that no response or log line contains a hash, and an identical-response test for unknown email versus wrong password.
**Rationale:** NFR-001 and NFR-003.
**Concrete Example:**
```python
user = User.query.filter_by(email=email).one_or_none()
if user is None or not verify_password(user.password_hash, password):
    return fail("invalid_credentials", "Email or password is incorrect.", 401)
```
### BE-19 CORS only for the health route
**Rule:** Browsers do not call Flask directly, because the Next.js server proxies every call. The only cross-origin access is `GET /api/health` from the configured web origin, without credentials and without allowing the `Authorization` header (API-004). Any other route MUST NOT send CORS headers. The CORS library is a design.md decision. Check: tests that `OPTIONS` and `GET` on other routes carry no `Access-Control-*` header.
**Rationale:** A broad CORS policy would let other sites call authenticated routes from a browser.
**Concrete Example:**
```python
@app.get("/api/health")
def health():
    resp = ok({"status": "ok"})
    # CORS applied here only, for the configured origin, no credentials
    return resp
```
---
## 7. Testing
### BE-20 pytest layout and required tests
**Rule:** Tests run with pytest against PostgreSQL in a separate database from production Supabase (TEST-001-AC03). Required suites: endpoint coverage for all 26+1 routes (TEST-001-AC02); contract tests for envelopes and status codes (AC04, AC05); a permissions matrix (administrator, member, non-member, unauthenticated); validation tests per schema; transaction rollback tests; concurrency tests with separate connections; SQL-capture tests for JOINs, `FOR UPDATE`, and no UPDATE on a no-op; analytics boundary tests with a fixed clock. Each test builds data through factories or fixtures and does not depend on another test's data. Tests never call a real external service. Coverage thresholds are undecided (UD-15) and MUST NOT be invented here. Check: CI or the local `pytest` command passes from an empty database after `flask db upgrade`.
**Rationale:** The requirements name these behaviors as testable, and SQLite would hide row-lock and timezone behavior.
**Concrete Example:**
```python
def test_non_member_gets_404_even_with_invalid_body(client, outsider_token, board):
    r = client.patch(f"/api/boards/{board.id}", json={"bogus": 1}, headers=auth(outsider_token))
    assert r.status_code == 404
    assert r.get_json() == NOT_FOUND_BODY
```
---
## 8. Scope guard
### BE-21 No invented endpoints, entities, or decisions
**Rule:** Do not add routes, Blueprints, tables, fields, or response keys that the requirements do not list. Do not resolve the open decisions: token lifetime (UD-01), refresh policy (UD-02), extra card fields (UD-07), notification pagination and unread count (UD-09), coverage thresholds (UD-15), environments (UD-16), CI/CD (UD-17), password policy (UD-21), and E2E account provisioning (UD-22). When one blocks work, stop and ask. Check: the endpoint-coverage test fails on an extra route, and reviewers compare every new field to the requirements.
**Rationale:** The requirements are the contract, and silent decisions break traceability.
**Concrete Example:** A `POST /api/auth/refresh` route is rejected because UD-02 is unresolved and login returns only `access_token` (UD-19).

---
## Reviewer checklist
Not a guideline. A reviewer confirms:
- The change touches only the eight Blueprints, and routes contain no queries or commits (BE-02, BE-03).
- Every response uses the envelope, and 500 bodies are generic (BE-04, BE-05).
- Schemas use `unknown = RAISE`, and numbers are strict (BE-06).
- Check order is 401, 404, 403, then 400/409 (BE-09), and only the five admin-only operations require administrator (BE-10).
- Every column or card query filters `deleted_at IS NULL` (BE-11).
- Writes are atomic, locks follow the order, and events and notifications share the transaction (BE-14, BE-16, BE-17).
- New tests include permission, rollback, and concurrency cases (BE-20).
