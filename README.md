# RevoTask

RevoTask is a Trello-like task management application for board members and administrators. Users create boards, organize work into columns, create and move cards, collaborate through comments, receive notifications, and review board activity analytics.

## AI-driven workflow

The project follows a specification-first workflow: the brief was refined into requirements, the design maps requirements to routes and pages, the task plan maps implementation to files, and steering guidelines are reviewed before code is accepted. AI-generated output is checked against the guidelines, violations are recorded in `evidence/ai-reviews/`, and focused tests are added at each milestone. Kiro/Kiro CLI are intended for supervised generation and review; Codex is now continuing implementation and verification.

## Implemented features

- Flask API with JWT authentication, board/column/card CRUD, ordering, comments, notifications, analytics, and profile endpoints.
- PostgreSQL SQLAlchemy models and a reversible initial Flask-Migrate revision with explicit constraints and RLS enablement.
- Next.js App Router frontend with register, login, dashboard, board detail, My Tasks, and Profile pages.
- Shared `BaseButton`, `BaseBadge`, and `BaseModal` components; typed API client; authentication context; notification polling; and native HTML5 drag-and-drop hook.
- Automated backend guard/model/foundation tests and frontend lint, Vitest, TypeScript, and production build checks.

## Technologies

Next.js, React, TypeScript, Tailwind CSS, Playwright, Flask, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Marshmallow, PostgreSQL, Gunicorn, and python-dotenv. Kiro, Kiro CLI, and Codex support the AI-assisted development workflow.

## Local setup

### Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:DATABASE_URL = "postgresql://<user>:<password>@<host>:5432/<database>"
$env:JWT_SECRET_KEY = "<local-secret>"
$env:JWT_ACCESS_TOKEN_EXPIRES_SECONDS = "900"
$env:FRONTEND_ORIGIN = "http://localhost:3000"
$env:LOG_LEVEL = "INFO"
$env:FLASK_APP = "wsgi:app"
flask db upgrade
flask run
```

Tests require the separate local PostgreSQL database described in `backend/README` and `TEST_DATABASE_URL`; the guard refuses production or remote destinations.

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:5000/api` for browser requests and `API_BASE_URL` for server requests.

## Verification

```powershell
# backend
cd backend
$env:TEST_DATABASE_URL = "postgresql://revotask_test_user:<password>@localhost:5432/revotask_test"
.\.venv\Scripts\python.exe -m pytest -v

# frontend
cd frontend
npm run lint
npm test
npm run typecheck
npm run build
npx playwright install
npx playwright test
```

The Playwright base URL is supplied with `PLAYWRIGHT_BASE_URL`; no deployment URL is hard-coded. Production deployment and screenshots must be recorded after the owner supplies the hosting accounts, public URLs, and deployment credentials.

## Repository map

- `specs/`: requirements, design, task plan, and changelog.
- `guidelines/`: frontend, backend, and database steering rules.
- `backend/`: Flask API, models, migrations, and tests.
- `frontend/`: Next.js application, shared components, hooks, and tests.
- `evidence/ai-reviews/`: guideline violation and before/after comparison evidence.
