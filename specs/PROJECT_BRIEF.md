# RevoTask Project Brief

## 1. Project Overview and Objectives

RevoTask is a Trello-like task management web application. Users organize work on boards that contain columns, and columns contain cards. Cards can be reordered and moved with drag-and-drop.

### Objectives
- Provide authenticated users with boards, columns, and cards for managing tasks.
- Support drag-and-drop reordering and moving of cards, persisted with positive FLOAT order values.
- Keep users informed through comments and notifications.
- Let users find cards quickly through search and a personal My Tasks view.
- Give board members visibility into progress through board analytics.
- Demonstrate an AI-assisted development workflow using Kiro IDE and Kiro CLI with mandatory human review.

## 2. User Roles

| Role | Description |
|---|---|
| Board Member | A user who belongs to a board and works with its content. |
| Board Administrator | A user who manages a board. Holds all Board Member capabilities plus board-level management. |

The exact permission boundary between the two roles is not yet defined. See Open Questions.

## 3. Core Features

### 3.1 JWT Authentication
- The system MUST authenticate users with JSON Web Tokens (JWT).
- Tokens MUST have an expiry.
- Protected endpoints MUST reject requests with a missing, invalid, or expired token with HTTP 401.
- Token lifetime, refresh strategy, and secure token storage are open design decisions.

### 3.2 Boards
- An authenticated user can create, view, update, and delete boards, subject to role permissions.
- A board has Board Members and at least one Board Administrator.

### 3.3 Columns
- A board contains columns.
- Columns can be created, renamed, and deleted, subject to role permissions.

### 3.4 Cards
- A column contains cards.
- Cards can be created, viewed, updated, and deleted.
- Cards can be assigned to a user.
- The Card model MUST store its position with `db.Column(db.Float)`.

### 3.5 Drag-and-Drop with FLOAT Order Values
- Users can reorder cards within a column and move cards between columns by drag-and-drop.
- Card positions MUST be positive float values.
- The Card model MUST define its order field with `db.Column(db.Float)`.
- The API MUST reject non-positive position values.
- Rebalancing of float values is an open design decision.

### 3.6 Comments
- Users can add comments to a card.
- Comments are visible to users who can view the card.
- Only the comment owner may edit or delete their own comments.
- An authenticated non-owner attempting to edit or delete a comment MUST receive HTTP 403 Forbidden.
- An unauthenticated request to a protected comment endpoint MUST receive HTTP 401 Unauthorized.
- Creating a valid comment MUST return HTTP 201 Created.
- Creating a comment with missing content MUST return HTTP 400 Bad Request.

### 3.7 Notifications
- The frontend MUST poll `GET /api/notifications` every 30 seconds.
- `GET /api/notifications` MUST be paginated using the `page` and `per_page` query parameters.
- `PATCH /api/notifications/<id>/read` marks a notification as read.
- The `NotificationBell` component MUST display the unread notification count.
- Which events create notifications is an open design decision.

### 3.8 Card Search
- Search input MUST use a 300ms debounce before sending a request.
- Searched fields and the API contract are open design decisions.

### 3.9 My Tasks
- My Tasks displays the cards assigned to the current user.
- The frontend fetches them from `GET /api/cards?assignee=me`.
- Cards are grouped by board name.

### 3.10 User Profile
- `GET /api/users/me` returns the current user's profile and MUST NOT include the password.
- `PATCH /api/users/me` permits updating `name` and `email` only.
- `PATCH /api/users/me` MUST NOT permit updating the password.

### 3.11 Board Analytics
The following metrics are required:
- Total cards per column.
- Cards completed this week.
- Member activity.

Metrics MUST be calculated using SQLAlchemy joins in the service layer.

The definitions of "completed", "member activity", and "this week" are open design decisions.

### 3.12 API Response Format
- Successful API responses use the format `{ "data": ... }`.
- Error responses use the format `{ "error": "..." }`.

## 4. Technology Stack

| Layer | Technology |
|---|---|
| Frontend framework | Next.js (App Router), React, TypeScript |
| Styling | Tailwind CSS |
| UI feedback | react-hot-toast |
| Backend | Python, Flask |
| ORM and migrations | SQLAlchemy, Flask-Migrate |
| Authentication | Flask-JWT-Extended |
| Validation and serialization | Marshmallow |
| Database | PostgreSQL on Supabase |
| Backend hosting | Render |
| Frontend hosting | Vercel |
| Backend testing | pytest |
| Frontend component testing | React Testing Library |
| End-to-end testing | Playwright |
| AI development tools | Kiro IDE, Kiro CLI |

## 5. Non-Functional Requirements

| ID | Category | Requirement | Measure |
|---|---|---|---|
| NFR-S1 | Security | Passwords are stored hashed, never in plain text. | No plain-text password exists in the database or logs. |
| NFR-S2 | Security | Protected endpoints require a valid JWT. | Requests with a missing, invalid, or expired token return 401. |
| NFR-S3 | Security | Secrets are kept out of source control. | No secrets are committed to the repository. Secrets are supplied through environment configuration. |
| NFR-P1 | Performance | Project target: p95 API response time for standard read requests is under 500 ms. | This is a target for the project, not an existing measured result. It must be measured and verified. |
| NFR-P2 | Performance | Card search sends at most one request per 300 ms pause in typing. | Verified by a frontend test of the debounce behavior. |
| NFR-P3 | Performance | Notification polling interval is 30 seconds. | Verified by a frontend test of the polling interval. |
| NFR-R1 | Responsive design | The application is usable at viewport widths from 360 px to 1920 px. | Core flows pass in Playwright at 360 px and 1920 px with no horizontal page scroll. |

## 6. Deployment Architecture

| Component | Platform |
|---|---|
| Next.js frontend | Vercel |
| Flask API | Render |
| PostgreSQL database | Supabase |

```text
Browser
   |
   v
Vercel (Next.js frontend)
   |  HTTPS, JWT-authenticated requests to /api/*
   v
Render (Flask API)
   |  SQLAlchemy
   v
Supabase (PostgreSQL)
```

Database schema changes are managed with Flask-Migrate.

Environments, CI/CD, and environment variable management are open design decisions.

## 7. Testing Strategy

| Level | Tool | Scope |
|---|---|---|
| Backend | pytest | API endpoints, authentication, comment ownership and status codes, models, service layer including analytics queries, and positive-FLOAT position validation. |
| Frontend components | React Testing Library | Components and hooks, including the 300ms search debounce and the 30-second notification polling in `NotificationBell`. |
| End to end | Playwright | Authentication scenarios and the Kanban journey below. |

### 7.1 Playwright Rules
- Tests MUST NOT use `waitForTimeout`.
- Tests MUST wait on observable conditions, such as element state, URL changes, or network responses.

### 7.2 Playwright Authentication Scenarios
1. Successful login and redirect.
2. Invalid credentials show an error.
3. An unauthenticated user is redirected to login.
4. Post-logout access to a protected page redirects to login.

### 7.3 Playwright Kanban Journey
The following eight-step journey is approved:
1. Log in.
2. Create a board.
3. Add two columns.
4. Create a card in the first column.
5. Open and inspect the card.
6. Drag the card to the second column.
7. Verify the updated card position.
8. Reload the page and verify that the card remains in the second column.

## 8. AI Development Workflow

- **Kiro IDE** is used for specification and code generation.
- **Kiro CLI** is used for tests and documentation.
- All AI-generated output MUST receive human review before it is accepted.
- Guideline violations MUST be reported in `evidence/ai-reviews/violation-report.md`.
- Refinement rounds MUST be documented in `specs/CHANGELOG.md`.

## 9. Open Questions

### Authentication
1. What is the access token lifetime?
2. Is there a refresh token strategy, and if so, what is it?
3. Where does the frontend store the token (for example, cookie or browser storage)?
4. How do users register, and how are they invited to boards?

### Roles and Permissions
5. What can a Board Administrator do that a Board Member cannot (for example, delete a board, manage members, delete columns)?
6. Can a user be an administrator on one board and a member on another?

### Cards and Ordering
7. Does float order need rebalancing when gaps become too small, and if so, when and how?
8. Which card fields exist besides position and assignee (for example, description, due date, completed status)?

### Notifications
9. Which events create notifications?
10. What are the default and maximum values of `per_page`?

### Search
11. Which fields does card search cover, and is it scoped to one board or all boards?
12. What is the search API contract (route, parameters, response shape)?

### Analytics
13. How is a card determined to be completed?
14. What counts as member activity, and over what time window?
15. How is "this week" defined (calendar week, week start day, time zone)?

### Testing
16. What are the coverage targets for pytest and React Testing Library?

### Deployment
17. Which environments exist (for example, development, staging, production)?
18. What CI/CD pipeline is used?
