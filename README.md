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
├── backend/        Flask API (placeholder, filled in by later tasks)
└── frontend/       Next.js application (placeholder, filled in by later tasks)
```

`backend/` and `frontend/` are independent deployables. They currently contain only a `.gitkeep` placeholder file.

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
