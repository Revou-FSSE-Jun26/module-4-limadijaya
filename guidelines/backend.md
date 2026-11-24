# RevoTask Backend Guidelines
These guidelines apply to the Flask API (Flask, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Marshmallow, pytest). They are steering rules for people and AI tools that write or review backend code.
- **Source of truth:** `specs/requirements.md`. If a guideline and the requirements disagree, the requirements win and the guideline must be corrected.
- **Format:** every guideline has an ID (`BE-nn`) and exactly three labeled parts: **Rule**, **Rationale**, and **Concrete Example**. A violation report cites the ID.
- **Wording:** MUST and MUST NOT are mandatory. The check named in a Rule is how a reviewer or a test verifies it.
- **Scope:** the 26 mandatory endpoints plus the one approved extension (`POST /api/boards/{id}/members`). Nothing here adds an endpoint, entity, or feature. Database rules live in `guidelines/database.md`.
---
## 1. Structure and layering
### BE-01 Application factory, config from the environment
**Rule:** The app is built by `create_app(config=None)`. Extensions (`db`, `migrate`, `jwt`) are created at module level without an app and bound with `init_app` inside the factory. All settings come from environment variables read in a config object: `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES_SECONDS` (required, with no default in code because UD-01 is open), `FRONTEND_ORIGIN` (the allowed web origin of the health route), `LOG_LEVEL`, and the optional `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` (the small connection pool of DA-16, with no hard-coded value). A missing required variable stops start-up with a message that names it (NFR-010-AC03). `MAX_CONTENT_LENGTH` is a constant of 1,048,576 bytes and not an environment variable (DA-07). The variable names agree with `design.md` Section 4.1 and `database.md` DB-01, and all of them are listed in `backend/.env.example`. No secret or connection string appears in source, tests, or logs. Tests call `create_app` with a test config. Check: grep finds no literal secret or URL, the test suite builds the app only through the factory, and a test unsets each required variable and asserts the message.
**Rationale:** A factory lets tests run with isolated config, and environment-only secrets satisfy NFR-001 and the deployment rules.
**Concrete Example:**
```python
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]           # fails fast when missing
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options()                  # pool_pre_ping, DB_POOL_SIZE, DB_MAX_OVERFLOW (database.md DB-01)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ["JWT_ACCESS_TOKEN_EXPIRES_SECONDS"]))   # no default: UD-01 is open
    MAX_CONTENT_LENGTH = 1_048_576                                 # DA-07

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
**Rule:** `routes.py` only parses the request (reads the path ids and the raw JSON body, where invalid JSON returns 400 and a wrong content type returns 415), calls one service function with the raw payload, and returns the envelope. `service.py` holds business rules, transactions, and locking, and it runs the checks in the Section 2.4 order: it loads the resource and the membership (404), checks the permission (403), and only then calls the Marshmallow schema `load()` (400) and the conflict checks (409). A route MUST NOT call a schema `load()` for a board-scoped or resource-scoped endpoint before the service has passed the 404 and 403 checks, because a non-member or a member without permission must get 404 or 403 whatever the body contains. Routes that have no resource to authorize (`POST /api/auth/register`, `POST /api/auth/login`, `POST /api/boards`, `PATCH /api/users/me`) may validate in the service as their first step after authentication. `schema.py` holds Marshmallow schemas only. Models hold columns and relationships, not business rules. A route MUST NOT call `db.session.commit()` or build a query. A service MUST NOT import `flask.request`. Check: grep of `routes.py` for `session.`, `query`, and `.load(`; grep of `service.py` for `request`; and, for each resource-scoped endpoint, a test that sends an invalid body as a non-member and expects 404, and as a member without permission (where one exists) and expects 403.
**Rationale:** Services that do not depend on the request object can be tested directly and reused by the transaction and concurrency tests. Validating after authorization keeps the approved order 401, 404, 403, then 400 or 409 (UD-05, Section 2.4, BOARD-006-AC06).
**Concrete Example:**
```python
@cards_bp.patch("/cards/<uuid:card_id>/position")
@jwt_required()
def move_card(card_id):
    raw = request.get_json()                      # invalid JSON -> 400, wrong content type -> 415
    card, rebalanced = card_service.move_card(current_user_id(), card_id, raw)
    return ok({**CardSchema().dump(card), "rebalanced": rebalanced})

# service.py
def move_card(user_id, card_id, raw):
    card, board_id = get_live_card_or_404(card_id)    # 404: missing, soft-deleted, or parent soft-deleted
    require_member(user_id, board_id)                 # 404 for a non-member, same body
    payload = MoveCardSchema().load(raw)              # 400 only after the checks above
    ...
```
---
## 2. Requests, responses, and errors
### BE-04 One response envelope
**Rule:** Every JSON response uses `{"data": ...}` on success and `{"error": "<non-empty string>"}` on failure through shared helpers (`ok`, `fail`). The `error` value is one non-empty string, never an object, and an error body has no `data` key (UD-19, API-002-AC04). Do not add `code`, `message`, or `details` keys. `DELETE` returns `{"data": {"id": "<id>"}}`. Login returns `{"data": {"access_token": "..."}}` and nothing else. Health returns `{"data": {"status": "ok"}}`. No route returns a bare object, list, or string. Check: the contract tests (TEST-001-AC04, AC05) assert the envelope for every endpoint including error paths.
**Rationale:** The frontend `apiClient.ts` depends on one shape (API-002).
**Concrete Example:**
```python
def ok(data, status=200):
    return jsonify({"data": data}), status

def fail(message, status):
    assert isinstance(message, str) and message      # the error value is a non-empty string
    return jsonify({"error": message}), status
```
### BE-05 Central error handlers
**Rule:** Register handlers so the envelope also covers framework errors: Marshmallow `ValidationError` (400, converted to one non-empty string), 401 from JWT callbacks, 404, 405, 413, 415, and unhandled exceptions (500). A request body is limited to 1,048,576 bytes through Flask `MAX_CONTENT_LENGTH` (DA-07). A larger body returns 413 with `{"error": "Request body is too large."}`, and a body of exactly 1,048,576 bytes MUST NOT be rejected only because of its size. The size decision depends only on the body size and not on the resource or the caller's membership (Section 2.4, API-002-AC06). Do not add per-field length limits. The 500 body is a fixed generic message. It MUST NOT include a stack trace, SQL text, a token, or an exception string. The full exception is logged server side without the token or the request body. Invalid JSON returns 400. A missing JSON content type on a body route returns 415. Check: tests that force an exception and assert the body contains none of the exception text (API-002-AC05), and a test that sends a body of 1,048,576 bytes (not rejected for its size) and a body of 1,048,577 bytes (413 with the envelope, `Content-Type: application/json`, no `data` key, and no changed row) (TEST-001-AC06).
**Rationale:** Leaked internals help attackers, and a client's error parser must work for every status.
**Concrete Example:**
```python
@app.errorhandler(RequestEntityTooLarge)
def too_large(exc):
    return fail("Request body is too large.", 413)      # {"error": "Request body is too large."}

@app.errorhandler(Exception)
def unhandled(exc):
    app.logger.exception("unhandled error")          # no token, no body
    return fail("Internal server error.", 500)      # {"error": "Internal server error."}
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
**Rule:** The service that changes state also appends any `ActivityEvent` and any `Notification` in the same transaction. If the change rolls back, the event and notification roll back. Only three activity event types exist: `card_created` (a card is created), `card_moved` (a card moves to a different column, with source and destination columns), and `comment_created` (a comment is created). No other action appends an event: assignment, unassignment, comment edit or delete, card delete, column changes, `is_done` toggles, reordering, and rebalancing append none (ANALYTICS-004-AC09, ANALYTICS-006, A-13, A-14). Notifications are created only for `card_assigned` (a card is assigned or reassigned to a different board member who is not the requester) and `comment_added` (a comment on an assigned card by someone other than the assignee), never for the actor's own action, and creating one appends no activity event (NOTIF-003-AC19). Assignment uses `assignee_id`: `null` unassigns, the assignee must be a member of the board, and card creation rejects `assignee_id`. An assignment to the stored assignee creates no notification (compare under the card row lock, NOTIF-003-AC08). Repeated valid assignments to different states may create repeated notifications (UD-08). Marking a notification read affects only the owner's notification, and another user's notification returns 404. Check: tests for rollback, no-op assignment, self-assignment, non-member assignee, and a test that an assignment leaves the activity-event count unchanged.
**Rationale:** Events and notifications that do not match committed data corrupt analytics and the bell count, and an event type outside the approved three would change the member activity counts.
**Concrete Example:**
```python
with db.session.begin_nested():
    card = lock_card(card_id)
    if card.assignee_id != new_assignee_id:
        card.assignee_id = new_assignee_id
        # assignment appends NO ActivityEvent; only a notification, and only for another member
        if new_assignee_id and new_assignee_id != user_id:
            db.session.add(Notification(user_id=new_assignee_id, actor_id=user_id, board_id=card.board_id,
                                        card_id=card.id, type="card_assigned", message=message, created_at=now))

# card creation appends the event instead
db.session.add(ActivityEvent(board_id=board_id, actor_id=user_id, card_id=card.id, type="card_created", created_at=now))
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
**Rule:** A service function that writes opens one transaction and commits once at the end. Any exception rolls the whole transaction back. No route commits, and no service commits halfway and then continues writing. Validation and authorization errors raise before any write. A failed multi-step operation (column delete with its cards, board hard-delete, move with rebalance, assignment with its notification) MUST leave no partial state. Check: tests that inject a failure at the last step and assert nothing changed.
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
**Rule:** Use `SELECT ... FOR UPDATE` (`with_for_update()`) and, where stated, `FOR SHARE` (`with_for_update(read=True)`) for exactly these approved locks (DA-11): the board row for column reorder, column create, column delete, and board delete (UD-20); the column row for a change of `is_done` and, after the board row, for column delete; the destination column row for card move and card creation (UD-06); the card row, then a state comparison, for card update including assignment (NOTIF-003-AC08), for card move, and for card delete; and the card row `FOR SHARE` for comment creation. When a request needs several locks, take them in this order: board row, then column rows by ascending id, then card rows by ascending id. After taking a lock, re-read the row and re-check existence, `deleted_at`, and permissions before writing. Never lock in the reverse order. Never hold a lock across a network call. The default READ COMMITTED isolation level stays, and no stricter isolation level replaces the locks. Do not add a lock that is not listed here without a new approval. Check: SQL-capture tests that assert the lock clauses and their order, and concurrency tests on separate connections (two simultaneous moves into one column, reorder against column create and column delete, a move against the delete of its destination column, two simultaneous assignments), repeated in a stability run (V-05, outstanding).
**Rationale:** A fixed order prevents deadlocks, and the re-read prevents acting on stale state. The order itself is a guideline-level rule. The requirements mandate the board, destination column, and assignment locks, and DA-11 approves the others.
**Concrete Example:**
```python
column = (Column.query.filter_by(id=dest_id).with_for_update().one_or_none())
if column is None or column.deleted_at is not None:
    raise NotFound()
# comment creation: FOR SHARE on the card, so its assignee and deleted_at cannot change mid-transaction
card = db.session.execute(select(Card).where(Card.id == card_id).with_for_update(read=True)).scalar_one_or_none()
```
---
## 6. Security and logging
### BE-18 Passwords, secrets, and injection
**Rule:** Passwords are hashed with Werkzeug `generate_password_hash` using scrypt with explicit parameters written in one module (`security.py`) (DA-05). `scrypt:32768:8:1` is a provisional development configuration only. The final parameters are set after the V-01 security, latency, and memory verification on Render, which is outstanding and must pass before production deployment, and any change needs human approval. The encoded hash, which carries its salt and parameters, is stored in `users.password_hash` and is never returned, logged, or placed in an error, and a plaintext password is never logged. Login failure returns one generic message for an unknown email and a wrong password, and for an unknown email login verifies the submitted password against a fixed dummy hash so that the response time is similar. Email addresses are trimmed and lowercased before every lookup and write (DA-06). All queries use the SQLAlchemy expression API or bound parameters. String-built SQL (f-strings, `%`, `+`, `text()` with interpolated values) is forbidden. The password policy (UD-21) is undecided: code MUST NOT invent one beyond "present and non-empty". Check: grep for string-built SQL, a test that no response or log line contains a hash or a plaintext password, an identical-response test for unknown email versus wrong password, and a test that the stored hash starts with the explicit scrypt parameters.
**Rationale:** NFR-001 and NFR-003. An explicit, provisional parameter string keeps the cost visible and replaceable in one place until it has been measured on the real instance.
**Concrete Example:**
```python
SCRYPT_METHOD = "scrypt:32768:8:1"      # provisional development configuration (DA-05); final value only after V-01

def hash_password(password):
    return generate_password_hash(password, method=SCRYPT_METHOD)

user = User.query.filter_by(email=normalize_email(email)).one_or_none()
stored = user.password_hash if user else DUMMY_HASH            # same work for an unknown email
if not check_password_hash(stored, password) or user is None:
    return fail("Invalid email or password.", 401)   # same string for both cases
```
### BE-19 CORS only for the health route
**Rule:** Browsers do not call Flask directly, because the Next.js server proxies every call. The only cross-origin access is `GET /api/health` from the configured web origin (`FRONTEND_ORIGIN`). Use Flask-CORS (DA-12) restricted to that path: `resources={r"/api/health": {...}}`, `origins=[FRONTEND_ORIGIN]`, `methods=["GET"]`, `supports_credentials=False`, and an explicit allowed-headers list that does not contain `Authorization` (the library default for allowed headers is not used). No response carries `Access-Control-Allow-Credentials: true`, and the preflight response does not list `Authorization` (API-004). Any other route MUST NOT send CORS headers. Check: tests that `OPTIONS` and `GET` on every other route carry no `Access-Control-*` header, and tests for API-004-AC01 to AC05 (a preflight from the configured origin is allowed, from another origin it gets no `Access-Control-Allow-Origin`).
**Rationale:** A broad CORS policy would let other sites call authenticated routes from a browser.
**Concrete Example:**
```python
CORS(app, resources={r"/api/health": {
    "origins": [app.config["FRONTEND_ORIGIN"]],
    "methods": ["GET"],
    "allow_headers": ["Content-Type"],       # explicit list, no Authorization
    "supports_credentials": False,
}})

@app.get("/api/health")
def health():
    return ok({"status": "ok"})              # no database query
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
- Every response uses the envelope, `error` is a plain non-empty string, 500 bodies are generic, and a body over 1,048,576 bytes gets 413 with "Request body is too large." (BE-04, BE-05).
- Configuration comes from the environment with the approved variable names, and the JWT lifetime has no default (BE-01).
- Routes pass raw JSON to services, and schemas load only after the 404 and 403 checks (BE-03, BE-09).
- Schemas use `unknown = RAISE`, and numbers are strict (BE-06).
- Check order is 401, 404, 403, then 400/409 (BE-09), and only the five admin-only operations require administrator (BE-10).
- Every column or card query filters `deleted_at IS NULL` (BE-11).
- Writes are atomic, only the approved locks are used in the fixed order under READ COMMITTED, and events and notifications share the transaction (BE-14, BE-16, BE-17).
- Passwords use explicit scrypt parameters (provisional until V-01), emails are normalized, and CORS is limited to the health route (BE-18, BE-19).
- Only `card_created`, `card_moved`, and `comment_created` events exist, and assignment appends none (BE-14).
- New tests include permission, rollback, and concurrency cases (BE-20).
