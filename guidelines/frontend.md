# RevoTask Frontend Guidelines

These guidelines apply to the Next.js (App Router) and TypeScript application. They are steering rules for people and AI tools that write or review frontend code.

- **Source of truth:** `specs/requirements.md`. If a guideline and the requirements disagree, the requirements win and the guideline must be corrected.
- **Format:** every guideline has an ID (`FE-nn`) and exactly three labeled parts: **Rule**, **Rationale**, and **Concrete Example**. A violation report cites the ID.
- **Wording:** MUST and MUST NOT are mandatory. The check named in a Rule is how a reviewer or a test verifies it.
- **Scope:** the six approved pages, the approved components, and the 26 mandatory endpoints plus the one approved extension. Nothing here adds a page, endpoint, or feature.

---

## 1. Rendering model and boundaries

### FE-01 Server Components by default

**Rule:** A file is a Server Component unless it uses React state, effects, context, event handlers, or browser APIs. The root layout and the page files for `/`, `/boards/[id]`, `/register`, `/login`, `/my-tasks`, and `/profile` MUST NOT start with `"use client"`. The `/` and `/boards/[id]` pages fetch their data on the server. The other four page files are Server Components that render Client Components for the interactive parts. `BoardCard` and `BaseBadge` MUST contain no hooks and no event handlers. Check: `next build` passes, and a test or lint rule asserts which files carry the directive (FRONT-021).

**Rationale:** The assignment requires the dashboard and board pages to be Server Components, and server rendering lets authenticated data be fetched without exposing the JWT (UD-03, A-12).

**Concrete Example:**
```tsx
// app/page.tsx  (no "use client": a Server Component that fetches boards on the server)
export default async function DashboardPage() {
  const boards = await serverApi.get<Board[]>("/api/boards"); // server-side mode, JWT stays on the server
  return (
    <main className="mx-auto max-w-5xl p-4">
      {boards.map((b) => <BoardCard key={b.id} id={b.id} name={b.name} />)}
      <CreateBoardForm /> {/* Client Component */}
    </main>
  );
}
```

### FE-02 Client Components are small, leaf-level, and carry only serializable props

**Rule:** Put `"use client"` on the smallest component that needs interactivity: forms, `BaseModal`, `CardDetailModal`, `AddCardForm`, `ColumnHeader`, `CommentList`, `NotificationBell`, the board view container that uses `useDragAndDrop`, and the `AuthContext` provider. A Server Component MUST pass a Client Component only plain JSON data (strings, numbers, booleans, arrays, objects). It MUST NOT pass the JWT, the session cookie, or a function. Check: FRONT-021-AC04 file-directive test and a review of props for any token-like value.

**Rationale:** A large client boundary ships more code to the browser and makes accidental token exposure more likely.

**Concrete Example:**
```tsx
// app/boards/[id]/page.tsx  (Server Component)
const board = await serverApi.get<BoardDetail>(`/api/boards/${id}`);
return <BoardView board={board} />;   // BoardView is a Client Component and receives JSON only
```

### FE-03 Authenticated data is fetched on the server through the server-only session

**Rule:** Server Components read authentication only through the server-only session module and call Flask through `apiClient.ts` in server-side mode, using `API_BASE_URL`. Every authenticated server-side fetch MUST opt out of caching (`cache: "no-store"` or an equivalent dynamic-rendering setting). A 401 from Flask redirects to `/login` and clears the stale cookie through the expire route. A 404 calls `notFound()` for a board page. Check: FRONT-022 tests and a two-user test that proves one user's data is never served to another.

**Rationale:** Cached per-user responses can leak data across users, and a stale session must not render protected content (FRONT-003, FRONT-022, FRONT-023-AC12).

**Concrete Example:**
```ts
// session.server.ts imports "server-only", so a Client Component import fails `next build`
import "server-only";
import { cookies } from "next/headers";
export async function getToken() { return (await cookies()).get(SESSION_COOKIE_NAME)?.value ?? null; }
```

---

## 2. Authentication and the Next.js BFF

### FE-04 The JWT never reaches browser JavaScript

**Rule:** The JWT lives only in an HttpOnly cookie that the Next.js server sets, with `HttpOnly`, `Secure` in production, `SameSite=Lax`, `Path=/`, no `Domain`, and a `Max-Age` no longer than the JWT's remaining lifetime. The token MUST NOT appear in props, React state, `AuthContext`, `localStorage`, `sessionStorage`, `document.cookie`, response bodies sent to the browser, page HTML, or the RSC payload. No `NEXT_PUBLIC_` variable may hold a secret. Check: TEST-007-AC05, FRONT-023-AC01 to AC03, NFR-002-AC04, and an ESLint restricted-import rule.

**Rationale:** HttpOnly storage keeps an injected script from reading the token (UD-03).

**Concrete Example:**
```ts
// login route handler (server): the response body contains the profile, never the JWT
cookies().set(SESSION_COOKIE_NAME, jwt, {
  httpOnly: true, secure: process.env.NODE_ENV === "production",
  sameSite: "lax", path: "/", maxAge: secondsUntilExp(jwt),
});
return Response.json({ data: { user } });
```

### FE-05 Session handlers and the proxy follow a fixed security checklist

**Rule:** The session login, logout, and expire handlers and the same-origin proxy are server-only route handlers. The exact paths are set in `design.md`. They MUST: (1) forward only to allow-listed `/api` paths on the `API_BASE_URL` host (FRONT-023-AC07); (2) never forward `POST /api/auth/login` through the generic proxy (AC11); (3) discard any `Authorization` and `Cookie` header from the browser and build `Authorization: Bearer` only from the session cookie (AC13); (4) reject POST, PATCH, and DELETE whose `Origin` differs from the application's own origin with 403 (AC08); (5) reject POST, PATCH, and DELETE whose `Content-Type` is not `application/json` with 415 (AC14); (6) return 401 without forwarding when there is no cookie, except for registration and health (AC05); (7) expire the cookie when Flask returns 401 (AC06). The login handler is the only code that receives the JWT from Flask, and it sets `Cache-Control: no-store`. Check: Vitest tests that call the handlers with `Request` objects and a mocked `fetch` (TEST-005-AC06).

**Rationale:** The browser never calls Flask with credentials, so these checks are the CSRF and header-injection defenses (UD-03).

**Concrete Example:**
```ts
export async function POST(req: Request) {
  if (req.headers.get("origin") !== APP_ORIGIN) return jsonError(403, "Forbidden");
  if (!req.headers.get("content-type")?.startsWith("application/json")) return jsonError(415, "Unsupported media type");
  // ...allow-list check, then call Flask with only the Bearer header built from the cookie
}
```

### FE-06 One typed `apiClient.ts` serves server and browser modes

**Rule:** All API calls go through `apiClient.ts`. Server-side mode uses `API_BASE_URL` and a Bearer header from the session. Client-side mode calls the same-origin proxy with the cookie and sets no `Authorization` header. Direct browser calls through `NEXT_PUBLIC_API_BASE_URL` are limited to `GET /api/health`. A 2xx resolves with the `data` value, and any other status rejects with an error from `errors.ts` that carries the status and the `error` message. A successful DELETE resolves with `{ id }` and never treats an empty body or HTTP 204 as success. A 401 outside login clears `currentUser` and navigates to `/login`. Responses are typed with generics, and no call site uses `any`. Check: API-005 tests.

**Rationale:** A single module is the only place that handles the envelope, the error mapping, and the two connection modes (API-005, UD-19).

**Concrete Example:**
```ts
export async function request<T>(method: Method, path: string, opts?: { body?: unknown; signal?: AbortSignal }): Promise<T> {
  const res = await fetchImpl(buildUrl(path), buildInit(method, opts));
  const json = await res.json().catch(() => null);
  if (!res.ok) throw ApiError.from(res.status, json);   // { error: "..." } becomes ApiError.message
  return (json as { data: T }).data;
}
```

### FE-07 Errors are mapped once and shown through `useErrorHandler` and `toast.ts`

**Rule:** `errors.ts` defines an API error type with `status` and `message`, a network error type, and distinct kinds for 400, 401, 403, 404, and 5xx. `useErrorHandler` turns them into toasts: an API error shows its `error` text, a network failure shows that the server could not be reached, and an unknown error shows a generic message. A toast never contains a stack trace, URL, or HTTP status. The notification bell and poller use the fixed generic message of FRONT-016-AC11 instead of the server text. `toast.ts` wraps react-hot-toast, and the toast container is mounted exactly once in the root layout. Check: FRONT-020, API-006, API-007 tests.

**Rationale:** Consistent, non-sensitive error display, and no duplicated error handling in components.

**Concrete Example:**
```tsx
const { handleError } = useErrorHandler();
try { await apiClient.patch<Card>(`/api/cards/${id}`, { title }); }
catch (e) { handleError(e); }   // never write a custom toast per component
```

### FE-08 `AuthContext` exposes the approved interface and nothing secret

**Rule:** `AuthContext` MUST expose `currentUser`, `session` (an authenticated flag and an expiry time, never the JWT), `login()`, `logout()`, and `updateProfile()`. The root layout loads the user on the server and passes it as the initial value. `login()` and `logout()` call the session handlers. `updateProfile({ name, email })` sends `PATCH /api/users/me` with only those two fields and updates `currentUser` from the response. A timer treats the session as ended at its expiry and sends the user to `/login`. No password-change UI exists. Check: FRONT-018 tests.

**Rationale:** Client Components need the user and the session state, but the credential stays on the server (UD-03, USER-002).

**Concrete Example:**
```tsx
const value = { currentUser, session: { isAuthenticated, expiresAt }, login, logout, updateProfile };
// session.expiresAt is a number or ISO string; it is never derived from client-readable token storage
```

---

## 3. TypeScript, styling, and components

### FE-09 Strict TypeScript with exported props interfaces

**Rule:** The project compiles with `strict` TypeScript, and `tsc --noEmit` passes in CI. Every component exports a `ComponentNameProps` interface, and props never use `any`. API response types live in one types module and use the public JSON names (`order`, not `position`). Do not hand-cast response data. Check: FRONT-024-AC01, FRONT-025-AC01, FRONT-026-AC01, and `tsc --noEmit`.

**Rationale:** Typed props and API shapes catch contract drift early and make AI-generated code reviewable.

**Concrete Example:**
```tsx
export interface BoardCardProps { id: string; name: string; }
export function BoardCard({ id, name }: BoardCardProps) { /* ... */ }
```

### FE-10 Tailwind utilities only, with no inline styles

**Rule:** Style with Tailwind CSS utility classes only. A component MUST NOT set the `style` attribute and MUST NOT introduce another styling system (CSS modules, styled-components, or a UI kit) without approval. Build layouts mobile-first. Conditional classes use plain string composition or a small local helper, and no new dependency is added for it. Check: lint or grep for `style=` in components, and FRONT-024-AC04.

**Rationale:** One styling system keeps the UI consistent and reviewable, and the requirements already forbid inline styles for `BoardCard`.

**Concrete Example:**
```tsx
<span className="inline-flex items-center rounded bg-gray-100 px-2 py-0.5 text-sm text-gray-700">{children}</span>
```

### FE-11 Reuse `BaseButton`, `BaseBadge`, and `BaseModal`

**Rule:** Feature components MUST NOT contain a raw `<button>` element. Use `BaseButton`, which renders its children, calls `onClick`, supports `disabled`, and in a loading state is disabled, shows an indicator, and sets `aria-busy="true"`. `BaseBadge` renders its children and applies a caller `className`. `BaseModal` renders nothing when closed and, when open, an element with `role="dialog"` and `aria-modal="true"`. It closes on Escape and on a backdrop click (not on a click inside), moves focus into the dialog, and returns focus to the opener. `CardDetailModal` is built on `BaseModal`. Check: FRONT-013 to FRONT-015 tests and a grep for `<button` outside `BaseButton`.

**Rationale:** Shared primitives give consistent behavior and accessibility, and keep the loading and double-submit rules in one place (FRONT-022-AC04).

**Concrete Example:**
```tsx
<BaseButton type="submit" loading={pending} disabled={!title.trim()}>Add card</BaseButton>
```

### FE-12 Forms, accessibility, and responsive layout

**Rule:** Every input has a label that gives it an accessible name. Every icon-only control has an accessible name that includes the item it acts on (for example the column name). Forms validate required fields on the client (empty and whitespace-only values send no request and show a message), disable submission while pending, and show the server `error` text on failure. The UI MUST NOT enforce password rules, because the password policy is undecided (UD-21). Layouts work from 360 px to 1920 px with no page-level horizontal scroll, and the board area scrolls inside its own container. Interactive controls named in FRONT-011, FRONT-016, and the 360 px login check are at least 44 px high. Check: Playwright viewport tests (TEST-009, NFR-007) and React Testing Library role queries.

**Rationale:** The requirements fix the accessibility and responsive criteria, and the server remains the authority on validation.

**Concrete Example:**
```tsx
<label htmlFor="card-title" className="sr-only">Card title</label>
<input id="card-title" className="w-full rounded border px-3 py-2" value={title} onChange={onChange} />
```

### FE-13 Role-based controls follow the board `role`, and the server still decides

**Rule:** Show the column delete control and the Done/Active toggle only when the board response says `role` is `administrator`. A member still sees rename. Never rely on hiding as security: a 403 shows an error toast and restores the previous state. Do not add UI for board rename, board delete, or member addition, because no approved page offers them. Check: FRONT-025-AC09, AC10, AC16, AC17 tests.

**Rationale:** The UI follows the approved permission table (UD-05), and the backend remains the enforcement point.

**Concrete Example:**
```tsx
<ColumnHeader columnId={c.id} name={c.name} cardCount={n} isDone={c.is_done}
  isAdministrator={board.role === "administrator"} onRename={rename} onDelete={del} onToggleDone={toggle} />
```

---

## 4. Drag-and-drop, search, notifications, analytics

### FE-14 Native HTML5 drag-and-drop with optimistic updates and rollback

**Rule:** `useDragAndDrop` uses the native HTML5 drag-and-drop API (`draggable`, `dragstart`, `dragover`, `drop`, and `dataTransfer` carrying only IDs). Do not add a drag-and-drop library. A drop updates the UI first, then calls the API, and a non-2xx status or network error restores the previous column and place and shows an error toast. Dropping at the original place sends no request. A card drop calls `PATCH /api/cards/{id}/position` with `column_id` and `order`. A column drop calls `PATCH /api/boards/{id}/columns/reorder` with a single entry for the moved column. Native drag-and-drop is the primary desktop interaction, and it MUST NOT be the only way to move a card or reorder a column. Every card and every column on `/boards/[id]` MUST also offer a non-drag alternative with these properties: (1) Keyboard: each card has a real `<button>` (through `BaseButton`) with an accessible name, for example "Move card", that opens a menu or dialog reachable with Tab and operable with Enter, Space, and the arrow keys, where the user picks a destination column and a place (top, bottom, or before or after a named card). Each column header has "Move column left" and "Move column right" buttons. Escape closes the menu and returns focus to its trigger, a visible focus ring is present (Tailwind `focus-visible:` classes), and the result of a move is announced in an `aria-live="polite"` region. (2) Touch: these controls are visible without hover, have a tap target of at least 44 by 44 CSS pixels (Tailwind `min-h-11 min-w-11`), and work at a 360 px width without horizontal page scroll (NFR-007). They MUST NOT depend on `draggable`, drag events, or hover. (3) Same API: the controls feed the same `useDragAndDrop` move logic and call the same endpoints as a drop: `PATCH /api/cards/{id}/position` with `column_id` and `order` for a card, and `PATCH /api/boards/{id}/columns/reorder` with a single entry for the moved column. They use the same optimistic update, rollback, error toast, and no-request-on-no-change behavior. (4) Same ordering: the `order` is computed by the FE-15 functions from the neighbors of the chosen place, stays a FLOAT-compatible JSON number, and is sent under the field name `order`, never `position`. The controls add no endpoint, request field, library, or page. Do not add dnd-kit or any other drag-and-drop or sortable library. Role rules from FE-13 apply equally to the controls. Check: FRONT-019 tests run the same assertions for a drop and for each control (same request, same body, same rollback); a React Testing Library test moves a card and reorders a column using only the keyboard; a Playwright test at a 360 px viewport moves a card and reorders a column with taps and no drag events (TEST-008-AC06 covers the drag journey); a lint or grep check finds no drag-and-drop library in `package.json`.

**Rationale:** Native drag-and-drop does not work with a keyboard or with touch on most mobile browsers, so a drag-only board would block keyboard and phone users and would conflict with the mobile requirement (NFR-007). Sending both paths through one move function and the same approved endpoints keeps one behavior to test and avoids any new API surface. The hook isolates the DOM events so the approved rollback and API behavior stay testable.

**Concrete Example:**
```tsx
<li draggable onDragStart={(e) => e.dataTransfer.setData("text/plain", card.id)} />
<ul onDragOver={(e) => e.preventDefault()} onDrop={onDropCard(column.id)} />

// Non-drag alternative: same hook, same endpoint, same computeCardOrder
<BaseButton
  aria-label={`Move card ${card.title}`}
  className="min-h-11 min-w-11 focus-visible:ring-2"
  onClick={() => setMoveMenuOpen(true)}
/>
// on confirm (destination column + neighbors chosen in the menu):
await moveCard(card.id, { column_id: destId, order: computeCardOrder(prev?.order ?? null, next?.order ?? null) });
```

### FE-15 `order` values are computed by a pure, tested function

**Rule:** Compute the `order` to send in one pure function. For cards, use the midpoint between the two neighbors, an `order` below the first card (positive) or above the last card, and a positive value for an empty column. When no distinct positive float exists between the neighbors, send the `order` of the neighbor that must follow the dropped card, so the server resolves the tie and rebalances (UD-06). Use neighbors from all cards of the column, including cards hidden by a search filter. For columns, send only the moved column. When no distinct midpoint exists, send every active column once with distinct positive values through the same endpoint, with no flag. Apply no minimum-gap threshold, and never send `rebalanced`. After a success, show the response's `order`. If `rebalanced` is true, or a column request returns 400 or 409, refetch the board and replace the displayed `order` values. Check: FRONT-019-AC03, AC07 to AC16 unit tests.

**Rationale:** Predictable values let the server keep distinct, valid orders without extra endpoints (UD-06, UD-20).

**Concrete Example:**
```ts
export function computeCardOrder(prev: number | null, next: number | null): number {
  if (prev === null && next === null) return 1024;                 // empty column
  if (prev === null) { const h = next! / 2; return h > 0 && h < next! ? h : next!; }
  if (next === null) return prev + 1024;                           // after the last card
  const mid = prev + (next - prev) / 2;
  return mid > prev && mid < next ? mid : next;                    // no distinct midpoint: the following card's order
}
```

### FE-16 Card search is a debounced, client-side title filter

**Rule:** Filtering uses the board data already loaded from `GET /api/boards/{id}`. Match a card when its title contains the trimmed term, ignoring letter case. Debounce the input by 300 ms. The filter MUST send no API or proxy request. Clearing the term, or entering only whitespace, restores every card, and columns stay visible when none of their cards match. Check: FRONT-008 and NFR-006-AC01 tests with fake timers.

**Rationale:** The approved design has no search endpoint (UD-10, UD-11), and a debounce limits filtering work.

**Concrete Example:**
```ts
const visible = useMemo(() => filterBoard(board, debouncedTerm), [board, debouncedTerm]);
```

### FE-17 Notifications poll every 30 seconds and never expose comment text

**Rule:** `useNotifications` makes one request on mount and one every 30,000 ms through the proxy, makes none while unauthenticated, stops on unmount and logout, and never overlaps requests. A failing poll shows at most one generic error indication until a poll succeeds. `NotificationBell` shows the unread count, each item's `message`, type label, and timestamp, a read or unread indication that is not color alone, a "Mark as read" control, and keyboard support (Escape closes the list). Activating an item marks it read and opens its board and card, or shows "This card is no longer available" when the card is gone. It renders only the contract fields of NOTIF-001-AC06 and never comment text. Keep the parsing of the `GET /api/notifications` response in one function, because the pagination shape is undecided (UD-09). Check: FRONT-016, FRONT-017, NFR-006-AC02 tests.

**Rationale:** The approved notification behavior (UD-08) is fixed, while the list shape is still open and must stay easy to adapt.

**Concrete Example:**
```ts
useEffect(() => {
  if (!isAuthenticated) return;
  const id = setInterval(() => { if (!inFlight.current) void poll(); }, 30_000);
  void poll();
  return () => clearInterval(id);
}, [isAuthenticated]);
```

### FE-18 The analytics panel shows the UTC week from the API

**Rule:** Label the period from `window.start` and `window.end`, treat `window.end` as exclusive, and compute the dates in UTC so they do not change with the browser time zone (for example "Week of Jan 13–19, 2025 (UTC)"). Show zero as `0`, show "This board has no columns yet" for a board without columns, show members in the order the API returns them, and offer no time zone or range control. Refresh the panel after a successful card creation, move, or deletion and after a Done/Active toggle. Check: FRONT-007, FRONT-025-AC15, TEST-005-AC11 tests run under two non-UTC time zones.

**Rationale:** The reporting window is approved as the current UTC week (UD-14), and the client must not reinterpret it.

**Concrete Example:**
```ts
const last = new Date(Date.parse(window.end) - 1);   // end is exclusive; format with timeZone: "UTC"
```

---

## 5. Configuration, testing, and scope

### FE-19 Configuration and secrets

**Rule:** The frontend reads `API_BASE_URL` on the server and `NEXT_PUBLIC_API_BASE_URL` only for the direct health call. The committed `.env.example` lists every variable the frontend reads with placeholder values, labels each `NEXT_PUBLIC_` variable as public, and the real `.env` files are git-ignored. Deployed values use `https://`. Check: NFR-002, NFR-004, NFR-010-AC02, and a secret scan.

**Rationale:** Secrets must stay out of source control and out of the browser bundle.

**Concrete Example:**
```
# .env.example
API_BASE_URL=https://your-render-service.example   # server only
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.example   # public, used only for GET /api/health
```

### FE-20 Unit and component tests use Vitest and React Testing Library

**Rule:** Use Vitest with a DOM environment and React Testing Library. Every component and hook of the approved list has a test file (`CardDetailModal`, `CommentList`, `BaseButton`, `BaseBadge`, `BaseModal`, `NotificationBell`, `BoardCard`, `ColumnHeader`, `AddCardForm`, plus the hooks). Use fake timers for the 300 ms debounce and the 30-second polling. Query by role and accessible name, not by class or test ID. Test route handlers and the session module as plain functions with `Request` objects and a mocked `fetch`. Do not try to render async Server Components in React Testing Library. Playwright covers them. Coverage thresholds are undecided (UD-15), so do not hard-code a threshold. Check: TEST-005 and the frontend test command exit with code 0.

**Rationale:** Deterministic, behavior-level tests keep the approved criteria verifiable.

**Concrete Example:**
```ts
vi.useFakeTimers();
render(<SearchBox onFilter={onFilter} />);
await user.type(screen.getByRole("searchbox"), "abc");
vi.advanceTimersByTime(299); expect(onFilter).not.toHaveBeenCalled();
vi.advanceTimersByTime(1);   expect(onFilter).toHaveBeenCalledTimes(1);
```

### FE-21 Playwright runs against the deployed Vercel URL with no fixed waits

**Rule:** Playwright tests read the base URL from an environment variable and fail clearly when it is unset. They MUST NOT use `waitForTimeout`. They wait only through auto-waiting locators, web-first assertions, or network responses. The E2E account email and password come from environment variables, and no credential is committed. Every board and card a test creates has a unique run identifier in its name, a teardown removes every board with that identifier even when the run fails (the API calls set an `Origin` header), and a test touches only its own data. Cover the four authentication scenarios, the cookie check, the eight-step Kanban journey in one test, and layouts at 360 px and 1920 px (and 768 and 1280 px for horizontal-scroll checks). Check: a lint rule or CI grep for `waitForTimeout`, TEST-006 to TEST-009.

**Rationale:** Stable end-to-end tests need web-first waiting, isolated data, and no secrets in the repository.

**Concrete Example:**
```ts
await page.getByRole("button", { name: "Create board" }).click();
await expect(page.getByRole("link", { name: boardName })).toBeVisible();   // no waitForTimeout
```

### FE-22 Stay inside the approved scope

**Rule:** Do not add pages beyond `/register`, `/login`, `/`, `/boards/[id]`, `/my-tasks`, and `/profile`. Do not add endpoints, time zone settings, date-range controls, a search API, or a refresh-token flow. Do not decide an open item in code or in a guideline: the token lifetime (UD-01), the refresh policy (UD-02), extra card fields (UD-07), the notification pagination shape (UD-09), coverage thresholds (UD-15), environments (UD-16), CI/CD (UD-17), the password policy (UD-21), and E2E account provisioning (UD-22). When a task seems to need one of them, stop and ask. Check: review against `specs/requirements.md` Section 8.1.

**Rationale:** The requirements record which decisions are approved, and silently deciding the open ones breaks that record.

**Concrete Example:** A request to "add a description field to the card modal" is out of scope until UD-07 is approved. Report it instead of implementing it.

---

## 6. Reviewer checklist

- No `"use client"` on `/`, `/boards/[id]`, the other page files, or the root layout (FE-01).
- No JWT in props, state, storage, HTML, or bodies sent to the browser (FE-04).
- All API calls go through `apiClient.ts`, and responses are unwrapped from `data` (FE-06).
- No `style=`, no raw `<button>`, and no `any` (FE-09, FE-10, FE-11).
- Drag-and-drop uses the native API, rolls back on failure, and uses `order` (FE-14, FE-15).
- Every card and column also has keyboard-operable, touch-sized move controls that call the same endpoints through the same move logic, with no drag library (FE-14).
- No `waitForTimeout` anywhere (FE-21).
- No new page, endpoint, or decision beyond the approved scope (FE-22).
