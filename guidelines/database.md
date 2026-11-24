# RevoTask Database Guidelines
These guidelines apply to the PostgreSQL database hosted on Supabase, accessed through SQLAlchemy and migrated with Flask-Migrate. They are steering rules for people and AI tools that write or review models, migrations, and queries.
- **Source of truth:** `specs/requirements.md`. If a guideline and the requirements disagree, the requirements win and the guideline must be corrected.
- **Format:** every guideline has an ID (`DB-nn`) and exactly three labeled parts: **Rule**, **Rationale**, and **Concrete Example**. A violation report cites the ID.
- **Wording:** MUST and MUST NOT are mandatory. The check named in a Rule is how a reviewer or a test verifies it.
- **Scope:** the eight approved entities: User, Board, BoardMembership, BoardColumn, Card, Comment, Notification, ActivityEvent. Nothing here adds an entity or a field. Table and column names beyond those listed in the requirements are fixed by `design.md` (approved, DA-02). Service-layer rules live in `guidelines/backend.md`.
---
## 1. Platform and access
### DB-01 Supabase is a PostgreSQL host, and Flask is its only client
**Rule:** Supabase is used only as the managed PostgreSQL server, and the Flask API is the only client. The frontend and the Next.js server MUST NOT use a Supabase client library, the Supabase Data API, Auth, Storage, or Realtime. The Render Flask API connects through the Supabase **session-mode pooler** (DA-16, approved). The connection string comes from the `DATABASE_URL` environment variable and never appears in source, tests, logs, or error bodies. SQLAlchemy uses a small connection pool with `pool_pre_ping`, sized by the environment variables `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`. Both are listed in `backend/.env.example`, and no pool value is hard-coded. Row Level Security MUST be enabled on all eight application tables through a Flask-Migrate revision, never by hand in the Supabase dashboard, and with no policy for browser-facing roles. The Supabase Data API MUST be disabled if that is practical. The database role that Flask uses MUST be verified to read and write all eight tables with RLS enabled, and the exposure of the Flask-Migrate `alembic_version` table is checked in the same verification (DA-17). The connection mode MUST NOT be changed silently: if verification fails, report the failure and request a new human approval. Verification is outstanding and is not done yet (V-02 and V-03): connectivity from Render, `flask db upgrade` through the pooler, the concurrency and row-locking tests against it, the connection limit against the pool size, and the role permissions with RLS enabled. Check: grep for `supabase` client packages and keys in both applications, grep for a literal connection string, a migration test that asserts RLS is enabled and no policy exists on each of the eight tables, and the recorded V-02 and V-03 results before production use.
**Rationale:** All authorization lives in Flask (BE-08). A second access path, such as the Data API or a direct browser connection, would bypass it, and RLS without a browser-facing policy closes that path even if the Data API stays reachable. Session-mode pooling gives each client connection its own database session, so row locks are expected to behave as on a direct connection. That is verified in V-02 and not assumed.
**Concrete Example:**
```python
def _engine_options():
    opts = {"pool_pre_ping": True}
    for env, key in (("DB_POOL_SIZE", "pool_size"), ("DB_MAX_OVERFLOW", "max_overflow")):
        if os.environ.get(env):
            opts[key] = int(os.environ[env])          # small values, set during verification V-02
    return opts

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]   # session-mode pooler string, fails fast when missing
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options()

# migration revision: RLS on every application table, no policies
op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
op.execute("ALTER TABLE boards ENABLE ROW LEVEL SECURITY")   # ...and the other six application tables
```
### DB-02 Production and test databases are separate
**Rule:** Tests run against PostgreSQL, not SQLite, in a database that differs from the production Supabase database (TEST-001-AC03). The test configuration refuses to start when its URL equals the production URL. Check: a startup assertion in the test config, and a CI or local run that begins from an empty database.
**Rationale:** SQLite does not reproduce row locks, UUID types, or timezone-aware timestamps, and tests that write to production destroy real data.
**Concrete Example:**
```python
assert os.environ["TEST_DATABASE_URL"] != os.environ.get("DATABASE_URL"), "tests must not use the production database"
```
---
## 2. Schema conventions
### DB-03 UUID primary keys and foreign keys
**Rule:** Every table has a UUID primary key generated on the server side by the application (CARD-001-AC01), never supplied by the client. Every foreign key column uses the same UUID type as the key it references. Use the PostgreSQL `UUID` type, not a string. Check: a model test that inserts a row with no id and gets a UUID, and a schema test that rejects a client-sent `id`.
**Rationale:** UUIDs avoid guessable ids and let services create ids before insert.
**Concrete Example:**
```python
id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
board_id = db.Column(UUID(as_uuid=True), db.ForeignKey("boards.id"), nullable=False)
```
### DB-04 Timestamps are timezone-aware UTC
**Rule:** Every timestamp column is `DateTime(timezone=True)` and holds UTC. Application code creates timestamps from a timezone-aware UTC clock (`datetime.now(timezone.utc)`), never `datetime.utcnow()` or a naive value. One request that writes several timestamps takes a single clock reading and reuses it (ANALYTICS-005-AC04, ANALYTICS-006-AC11). The clock is injectable for tests. API output is ISO 8601 with an explicit UTC offset. Check: a test that fails if any stored timestamp is naive, and a test with a fixed clock that sees the same value in `created_at`, `completed_at`, and the activity event of one request.
**Rationale:** Weekly analytics windows are UTC-based, and naive timestamps shift with the server timezone.
**Concrete Example:**
```python
created_at = db.Column(db.DateTime(timezone=True), nullable=False)   # set from the request clock
```
### DB-05 `position` is FLOAT in storage and `order` in the API
**Rule:** Column and card ordering is stored in a `position` column declared as `db.Column(db.Float, nullable=False)`. The model attribute and the database column are both `position`. The API field is `order`, mapped only in schemas (BE-12). Initial values use a spacing of `1024.0` (`1024.0, 2048.0, ...`), and new rows go after the current maximum of their parent. A card's position is unique only among live cards of one column, and a column's position only among live columns of one board. These uniqueness rules are enforced by service validation under a row lock, not by a database unique index. A unique index would reject valid swaps in the middle of a statement and would conflict with soft-deleted rows. Check: a migration test asserts the column type is double precision, and no unique index covers `position`.
**Rationale:** FLOAT positions allow a move with one UPDATE. The unique-index ban is needed for the swap and rebalance rules (UD-06, UD-20).
**Concrete Example:**
```python
position = db.Column(db.Float, nullable=False)      # exposed as "order" by the schema, never as "position"
```
### DB-06 Soft delete for columns and cards, hard delete for boards and comments
**Rule:** `BoardColumn` and `Card` have a nullable timestamptz `deleted_at`. Deleting sets it, and no code removes those rows. Deleting a column sets `deleted_at` on the column and on its live cards in one transaction, and `cards.column_id` stays non-null and keeps pointing to the soft-deleted column. `Board` and `Comment` are removed with a real `DELETE`. No other table gets a `deleted_at` column. Every query on columns and cards filters `deleted_at IS NULL` through shared helpers (BE-11). Check: a test that soft-deletes a column and asserts the row still exists with a non-null `deleted_at`, and a test that hard-deletes a comment and asserts the row is gone (UD-18, UD-23).
**Rationale:** Soft deletion keeps activity history and analytics consistent. Hard deletion for boards and comments follows the approved decision.
**Concrete Example:**
```python
deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
```
### DB-07 Required columns and constraints
**Rule:** Declare `NOT NULL` for every field the requirements treat as required. `is_done` on `BoardColumn` is `Boolean`, `nullable=False`, `server_default=false`. `completed_at` on `Card` is a nullable timestamptz. Declare these invariants: a live card in a live done column has a non-null `completed_at`, and a live card in a non-done column has `completed_at` NULL. The service keeps the invariant (BE-13) and a test verifies it with a query. `BoardMembership` is unique on (`user_id`, `board_id`), and its role is limited to `administrator` and `member` (use a CHECK constraint or a PostgreSQL enum). `User.email` is unique. Email addresses are trimmed and lowercased before every lookup and write: registration, login, membership lookup by email (`POST /api/boards/{id}/members`), and profile update (DA-06). The plain unique constraint on `User.email` then applies to the normalized value. Text length limits are not declared (DA-07): do not add per-field length limits. Check: the migration declares each constraint, a test inserts a duplicate membership and expects an integrity error, and a test registers `A@Example.com` and then `a@example.com` and expects 409, while login with `  A@EXAMPLE.COM ` succeeds for the first account.
**Rationale:** The database must reject invalid data even if a service has a bug (NFR-004).
**Concrete Example:**
```python
is_done = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
email = db.Column(db.Text, nullable=False, unique=True)   # stored as normalize_email(value) = value.strip().lower() (DA-06)
__table_args__ = (db.UniqueConstraint("user_id", "board_id", name="uq_membership_user_board"),)
```
---
## 3. Relationships and deletion
### DB-08 Board hard-delete strategy is PostgreSQL ON DELETE CASCADE
**Rule:** Deleting a board MUST remove all data that belongs to it: memberships, columns (including soft-deleted ones), cards (including soft-deleted ones), comments, activity events, and notifications (BOARD-005-AC04). The approved strategy is PostgreSQL `ON DELETE CASCADE` (DA-14), declared in the Flask-Migrate migration on `board_memberships.board_id`, `columns.board_id`, `cards.column_id`, `comments.card_id`, `notifications.board_id`, and `activity_events.board_id` (BOARD-005-AC08). Do not rely on an implicit ORM default. The delete runs in one atomic transaction that takes the board row lock first, and a failure leaves the board and all its dependent rows unchanged (BOARD-005-AC06). Columns and cards are never hard-deleted by any other operation: they stay soft-deleted (DB-06) and are removed only by this cascade. A mandatory PostgreSQL integration test (V-04, not yet run) builds a board with soft-deleted columns and cards, comments, notifications, memberships, and events, deletes the board, and asserts zero rows for that board id in every table, no change to `users`, and no change to another board. If that test fails, do NOT switch to ordered service deletes automatically: report the failure and request a new human approval. Check: that integration test, run on a database built by `flask db upgrade`.
**Rationale:** Without an explicit strategy, a delete either fails on a foreign key or leaves orphan rows, and a service that deletes table by table can leave a partial result.
**Concrete Example:**
```python
# migration: board-owned data is removed by the database when the board row is deleted
sa.ForeignKeyConstraint(["board_id"], ["boards.id"], ondelete="CASCADE")      # memberships, columns, notifications, activity_events
sa.ForeignKeyConstraint(["column_id"], ["columns.id"], ondelete="CASCADE")    # cards
sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="CASCADE")        # comments
```
### DB-09 ActivityEvent is append-only and survives its subjects
**Rule:** `ActivityEvent` rows are inserted and never updated or deleted by application code. They MUST survive the soft-delete of a card or column and the hard-delete of a comment (ANALYTICS-006-AC07, AC09). `activity_events.comment_id` is a plain UUID column with no foreign-key constraint (DA-14), so a comment hard-delete never touches an event. `activity_events.card_id`, `from_column_id`, and `to_column_id` are foreign keys with the default NO ACTION and no cascade of their own, so a foreign key from an event to a card, column, or comment MUST NOT use `ON DELETE CASCADE`. Only `activity_events.board_id` carries `ON DELETE CASCADE`: board-scoped events and notifications are removed when the board is hard-deleted (DB-08, DB-10), and at no other time. Only the three approved event types exist (`card_created`, `card_moved`, and `comment_created`), enforced by a CHECK constraint, and a `card_moved` row has both its source and destination column. This rule adds no entity and no other foreign-key behavior. Check: a test that deletes a comment, deletes a card, and deletes a column, and asserts the related events remain and analytics still counts them as specified; a test that deleting the board removes its events; and a test that the CHECK rejects any other event type.
**Rationale:** Analytics and the member activity count depend on the history staying intact, and a foreign key on `comment_id` would either block the comment delete or tie the event to it.
**Concrete Example:**
```python
board_id = db.Column(UUID(as_uuid=True), db.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)   # the only cascade
card_id = db.Column(UUID(as_uuid=True), db.ForeignKey("cards.id"), nullable=False)                          # NO ACTION, no cascade
comment_id = db.Column(UUID(as_uuid=True), nullable=True)   # plain UUID, no foreign key: a comment delete must keep the event
```
### DB-10 Notification belongs to a user and a board
**Rule:** `Notification` carries the recipient user id and a board id, and is removed when its board is deleted. There is no unique constraint that blocks repeated notifications of the same type for the same card and user (UD-08). The read state is a Boolean `is_read`, `nullable=False`, default false, because the API item exposes `is_read` as a boolean (NOTIF-001-AC06). Do not store the read state as a `read_at` timestamp or add a read-time column. The pagination shape, default page size, and unread count are undecided (UD-09), so models and indexes MUST NOT assume them. Check: a test inserts two identical-looking notifications and both persist, a new notification has `is_read` false, marking it read changes only `is_read`, and a board delete removes the notifications.
**Rationale:** Re-assignment after unassignment is a valid new event.
**Concrete Example:**
```python
user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
board_id = db.Column(UUID(as_uuid=True), db.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
is_read = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
```
---
## 4. Indexes and queries
### DB-11 Index what the requirements query
**Rule:** Add indexes for foreign keys used in joins and filters, and add partial indexes for live rows. At minimum: `cards(column_id, position) WHERE deleted_at IS NULL`, `columns(board_id, position) WHERE deleted_at IS NULL`, `cards(assignee_id) WHERE deleted_at IS NULL` for My Tasks, `memberships(user_id)` and `memberships(board_id)`, `comments(card_id, created_at)`, `notifications(user_id, created_at)`, and `activity_events(board_id, created_at)` for the analytics window. Each index is created in a migration. Do not add an index without a query that uses it. Check: a migration review and an `EXPLAIN` note in the pull request for any new query on a large table.
**Rationale:** These are the access paths of the board page, My Tasks, notifications, and analytics.
**Concrete Example:**
```python
db.Index("ix_cards_column_live", "column_id", "position", postgresql_where=db.text("deleted_at IS NULL"))
```
### DB-12 Query rules
**Rule:** Use SQLAlchemy expressions or bound parameters only. Never build SQL from strings (NFR-003). Load a board with its columns and cards using a fixed number of queries (JOIN or `selectinload`), not one query per column or card. Analytics counts use one grouped query with JOINs. Do not return password hashes from any query that feeds an API response. Check: SQL-capture tests assert statement counts for the board view and analytics, and grep finds no string-built SQL.
**Rationale:** N+1 queries and string-built SQL are the two common causes of slow and unsafe data access.
**Concrete Example:**
```python
cards = (Card.query.filter(Card.column_id.in_(column_ids), Card.deleted_at.is_(None))
         .order_by(Card.position, Card.created_at, Card.id).all())
```
---
## 5. Transactions and concurrency
### DB-13 Transactions and isolation
**Rule:** Every multi-statement write runs in one transaction with one commit and a rollback on any exception (BE-16). Do not change the default isolation level to work around a race: use explicit row locks (DB-14). A session MUST NOT stay open across a request boundary, and each request gets its own session. Check: tests that raise at the last step and assert no row changed.
**Rationale:** Atomicity keeps card moves, events, and notifications consistent (NFR-004).
**Concrete Example:**
```python
try:
    db.session.add_all([card, event]); db.session.commit()
except Exception:
    db.session.rollback(); raise
```
### DB-14 Row locks use `SELECT ... FOR UPDATE` in a fixed order
**Rule:** The approved locks (DA-11) are: the board row for column create, column reorder, column delete, and board delete (UD-20); the column row for a change of `is_done` and, after the board row, for column delete; the destination column row for card move and card creation (UD-06); the card row, followed by a comparison of current and requested state, for card update including assignment (NOTIF-003-AC08), for card move, and for card delete; and the card row `FOR SHARE` for comment creation. The default READ COMMITTED isolation level stays, and explicit row locks, not a stricter isolation level, resolve the races. When one request needs several locks, take them in this order: board, columns by ascending id, cards by ascending id (a guideline-level rule that prevents deadlocks). After locking, re-read the row and re-check `deleted_at`. Check: SQL-capture tests for `FOR UPDATE`, and concurrency tests that use two separate connections.
**Rationale:** FLOAT positions, rebalancing, and completion timestamps are read-modify-write operations that race without locks.
**Concrete Example:**
```python
board = db.session.execute(select(Board).where(Board.id == board_id).with_for_update()).scalar_one_or_none()
```
---
## 6. Migrations
### DB-15 Flask-Migrate is the only way the schema changes
**Rule:** Every schema change is a Flask-Migrate migration committed with the model change. Nobody edits the Supabase schema by hand or through the Supabase dashboard. `flask db upgrade` MUST succeed on an empty database (NFR-009), and `flask db migrate` run afterwards MUST detect no differences. Hand-edit autogenerated migrations to add partial indexes, CHECK constraints, `ondelete` settings, and the Row Level Security statements (DA-17), and review them before committing. A migration that adds a NOT NULL column to existing data supplies a default: `is_done` defaults to false, and `deleted_at` defaults to NULL for existing rows. Do not edit a migration that has already been applied elsewhere. Add a new one. Check: a CI or local test runs `upgrade` on an empty database and then asserts that autogenerate produces an empty diff.
**Rationale:** Reproducible schema history lets any environment rebuild the database, and manual changes cause drift.
**Concrete Example:**
```python
def upgrade():
    op.add_column("columns", sa.Column("is_done", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("cards", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
```
### DB-16 Migrations are reversible and safe
**Rule:** Each migration has a working `downgrade()`, or a comment that explains why it cannot be reversed. Take a backup before running a migration that drops or rewrites data. A migration MUST NOT delete production rows as a side effect. Test each new migration with `upgrade`, `downgrade`, and `upgrade` again on a test database. Check: the migration test runs the cycle.
**Rationale:** A failed deploy must be recoverable without data loss.
**Concrete Example:**
```python
def downgrade():
    op.drop_column("cards", "completed_at")
    op.drop_column("columns", "is_done")
```
---
## 7. Scope guard
### DB-17 No invented entities, tables, or decisions
**Rule:** The schema contains only the eight approved entities and their approved fields. Do not add tables or columns for features that the requirements do not list: no refresh-token table, no extra card fields (UD-07), no soft-delete flag on boards or comments, and no notification preference table. Do not resolve UD-01, UD-02, UD-07, UD-09, UD-15, UD-16, UD-17, UD-21, or UD-22 through the schema. The items that were open (pooler or direct connection, RLS, event foreign-key behavior, email case, length limits) are decided by the approved DA-16, DA-17, DA-14, DA-06, and DA-07, so do not reopen them through the schema. Check: reviewers compare every new table and column to the requirements, and the migration test lists the table names.
**Rationale:** The requirements are the contract.
**Concrete Example:** A migration that adds `cards.priority` is rejected until UD-07 is approved and the requirements list the field.

---
## Reviewer checklist
Not a guideline. A reviewer confirms:
- No Supabase client library is used, `DATABASE_URL` is the session-mode pooler string read from the environment, the pool uses `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`, and RLS is enabled on all eight tables by a migration with no browser-facing policy (DB-01).
- Emails are trimmed and lowercased on every lookup and write (DB-07).
- Primary keys are UUIDs, timestamps are timezone-aware UTC, and `position` is `Float` with no unique index (DB-03, DB-04, DB-05).
- Soft-delete applies only to columns and cards, and every query filters `deleted_at IS NULL` (DB-06).
- Board delete uses `ON DELETE CASCADE` with a passing PostgreSQL integration test and no unapproved fallback, and events outlive their card, column, and comment with `comment_id` as a plain UUID (DB-08, DB-09).
- Indexes match the listed queries (DB-11), and locks follow the fixed order (DB-14).
- The migration runs on an empty database with no autogenerate drift and has a downgrade (DB-15, DB-16).
