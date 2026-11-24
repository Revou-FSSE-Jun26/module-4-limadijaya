# RevoTask

RevoTask is a Trello-like task management web application. Users organize work on boards that contain columns, and columns contain cards. Cards can be moved between columns, commented on, assigned to board members, and tracked through notifications and weekly board analytics.

**Status: under construction.** The specification, design, guidelines, and task plan are written and approved. Application implementation has only just begun, and no application functionality is implemented yet. This README is a stub that later tasks extend.

## Planned architecture

| Part | Technology | Hosting |
|---|---|---|
| Frontend | Next.js (App Router), React, TypeScript, Tailwind CSS | Vercel |
| Backend API | Python, Flask, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Marshmallow | Render |
| Database | PostgreSQL | Supabase |

## Repository structure

```text
.
├── README.md
├── .gitignore
├── specs/          Requirements, design, tasks, and project brief
├── guidelines/     Frontend, backend, and database development guidelines
├── evidence/       AI-assisted workflow evidence (ai-reviews/)
├── backend/        Flask API (Python project files so far, application code in later tasks)
└── frontend/       Next.js application (placeholder, filled in by later tasks)
```

`backend/` and `frontend/` are independent deployables. `backend/` currently holds only the Python project files (dependency lists, `pytest.ini`, `wsgi.py`, `.env.example`) and the test safety guard. `frontend/` still contains only a `.gitkeep` placeholder file.

## Local development setup

The backend application code does not exist yet. These steps prepare the Python environment and the local test database only. Commands are for Windows PowerShell and run from the repository root.

### 1. Python virtual environment (Python 3.12)

```powershell
py -3.12 -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
```

The environment lives in `backend/.venv` and is ignored by Git. The commands call its interpreter directly, so no activation is needed.

**Certificate errors on Windows.** If pip 24.0 fails with `CERTIFICATE_VERIFY_FAILED` (for example because security software inspects HTTPS traffic with its own certificate), install through the Windows certificate store instead:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install --use-feature=truststore -r backend\requirements-dev.txt
```

This keeps certificate verification switched on. Do not use `--trusted-host`, which switches it off.

### 2. Local PostgreSQL test database

Tests need a PostgreSQL server on your own machine (`localhost`, port `5432`). The project is set up against PostgreSQL 17.4 on Windows. As a PostgreSQL administrator (for example in `psql`), create a dedicated role and an empty database. Choose your own password and never commit it:

```sql
CREATE ROLE revotask_test_user LOGIN PASSWORD '<choose-a-password>'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
CREATE DATABASE revotask_test OWNER revotask_test_user;
REVOKE ALL ON DATABASE revotask_test FROM PUBLIC;
```

The role has no elevated privileges, the database is owned by that role, and its `PUBLIC` privileges are revoked. The database starts with no tables. Tables are created by Flask-Migrate migrations in a later task, not by hand.

### 3. The two database variables

| Variable | Meaning | Used by tests |
|---|---|---|
| `DATABASE_URL` | The application database. In production it is the Supabase session-mode pooler connection string, set only in the Render environment settings. | No |
| `TEST_DATABASE_URL` | The local test database from step 2. | Yes |

Tests never use Supabase. Local testing and production are separate: production data lives in Supabase PostgreSQL, and the tests run only against the PostgreSQL server on your machine.

Set `TEST_DATABASE_URL` in your PowerShell session. The value below is a placeholder, so replace `<password>` with your own password and percent-encode any special characters in it:

```powershell
$env:TEST_DATABASE_URL = "postgresql://revotask_test_user:<password>@localhost:5432/revotask_test"
```

Do not put the real value in a file that Git tracks. The backend does not load `backend/.env` automatically yet, so set the variable in the shell for now. You do not need `DATABASE_URL` to run tests. If it is set, it must not point at the test database.

### Test safety guard

`backend/tests/conftest.py` checks the settings when pytest starts, before any database connection is made. It refuses to run, with an error that never contains a password, host, or URL, when:

- `TEST_DATABASE_URL` is missing, empty, or malformed, or uses a scheme other than `postgresql`.
- The host is not `localhost`, `127.0.0.1`, or `::1`, the port is not `5432`, the database is not `revotask_test`, or the role is not `revotask_test_user`.
- The URL has a query string, a fragment, or an ambiguous layout that could override the destination.
- `DATABASE_URL` equals `TEST_DATABASE_URL` or points at the same database.
- The libpq variables `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGSERVICE`, or `PGSERVICEFILE` are set.

Because the check runs at pytest start, `pytest` fails with a usage error whenever `TEST_DATABASE_URL` is not set. This is intentional: the test session fails closed.

### Running the guard tests

`backend/tests/test_database_guard.py` tests the guard with synthetic credentials. It makes no database connection and changes no data, so it needs no running PostgreSQL server. The guard itself still runs at pytest start, so set `TEST_DATABASE_URL` to a value that satisfies it. A synthetic password is enough for this test file. Run from the repository root:

```powershell
$env:TEST_DATABASE_URL = "postgresql://revotask_test_user:synthetic-password@localhost:5432/revotask_test"
.\backend\.venv\Scripts\python.exe -m pytest -c backend\pytest.ini backend\tests\test_database_guard.py
```

If you later run tests that use the real local database, set `TEST_DATABASE_URL` with the real password instead.

## Documentation

- [Requirements](specs/requirements.md): the authoritative source for behavior and API contracts.
- [Design](specs/design.md): the technical design.
- [Tasks](specs/tasks.md): the implementation task plan.
- [Project brief](specs/PROJECT_BRIEF.md): the original brief. Where it differs from the requirements or the design, the requirements and the design take precedence.
- [Frontend guidelines](guidelines/frontend.md)
- [Backend guidelines](guidelines/backend.md)
- [Database guidelines](guidelines/database.md)

## Secrets and configuration

No secret or real credential is committed to this repository. Production secrets are set only in the Render and Vercel environment settings. Local environment files (`.env`, `.env.local`, and similar) are ignored by Git, and only placeholder `*.example` files are committed.
