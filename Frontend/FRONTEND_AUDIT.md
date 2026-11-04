# Frontend Audit Report — ProcureMind AI

Generated: 2026-11-04

## Summary

1. **14 routes** registered; 3 are scaffold placeholders, 1 WhatsApp link is a dead/empty href.
2. Only **2 pages connect to live backend** (LoginPage → /auth/*, DataManagementPage → /users, /items). Everything else runs on **mock/hardcoded data**.
3. **68 backend endpoint contracts** exist in contracts.py (all return 501). The frontend calls **zero** of them.
4. The chat page exists and works in **mock mode** (default). In live mode it calls `/agents/chat` (implemented) and `/conversations/*` (501 placeholders).
5. `fraudDetectionService.js` and `procurementStore.js` persist demo state in **localStorage** — acceptable for demo but a data-leak vector if real data ever flows through them.
6. A legacy string `"life-purpose-auth-session"` is the sessionStorage key for auth tokens.
7. The landing page has an empty WhatsApp link (`https://wa.me/` with no phone number).
8. No lint, test, or type-check scripts exist in package.json. README claims TypeScript but no tsconfig or .tsx files exist.

---

## Table A — Pages and Routes

| Route | File | Classification | Auth required | Sidebar link | Owner |
|---|---|---|---|---|---|
| `/` | App.jsx:55 (LandingPage inline) | REAL PAGE | No | No | unknown |
| `/login` | src/pages/LoginPage.jsx | REAL PAGE | No | No | unknown |
| `/dashboard` | src/components/dashboard/DashboardOverview.jsx | REAL PAGE | No | Yes | unknown |
| `/dashboard/api` | src/pages/BackendApiPage.jsx | REAL PAGE | No | Yes | unknown |
| `/dashboard/data` | src/pages/DataManagementPage.jsx | REAL PAGE | **Yes** | Yes | unknown |
| `/dashboard/chat` | src/pages/ChatPage.jsx | REAL PAGE | No | Yes | unknown |
| `/dashboard/purchase-orders` | src/pages/ProcurementPages.jsx | REAL PAGE | No | Yes | unknown |
| `/dashboard/suppliers` | src/pages/ProcurementPages.jsx | REAL PAGE | No | Yes | unknown |
| `/dashboard/invoices` | src/pages/ProcurementPages.jsx | REAL PAGE | No | Yes | unknown |
| `/negotiation` | src/pages/NegotiationPage.jsx | REAL PAGE | No | Yes | unknown |
| `/fraud-detection` | src/pages/FraudDetectionPage.jsx | REAL PAGE | No | Yes | unknown |
| `/dashboard/audit-logs` | src/components/dashboard/DashboardScaffoldPage.jsx | SCAFFOLD | No | Yes | unknown |
| `/dashboard/settings` | src/components/dashboard/DashboardScaffoldPage.jsx | SCAFFOLD | No | Yes | unknown |
| `/dashboard/:section` (catch-all) | src/components/dashboard/DashboardScaffoldPage.jsx | SCAFFOLD | No | No | unknown |
| `*` (fallback) | App.jsx:56 → LandingPage | REDIRECT | No | No | unknown |

**Dead links:**
- WhatsApp link `https://wa.me/` (no phone number) — App.jsx:55

---

## Table B — Wiring Matrix

| Page / Service | Data Source | Needed Backend Endpoint | Status | Evidence |
|---|---|---|---|---|
| **LoginPage** | LIVE API | POST /auth/login | CONNECTED | LoginPage.jsx:21, api.js:159 |
| **LoginPage** | LIVE API | POST /auth/refresh | CONNECTED | api.js:117 |
| **LoginPage** | LIVE API | POST /auth/logout | CONNECTED | api.js:164 |
| **AuthenticatedRoute** | LIVE API | GET /auth/me | CONNECTED | AuthenticatedRoute.jsx:18, api.js:172 |
| **DataManagementPage** | LIVE API | GET /auth/me | CONNECTED | DataManagementPage.jsx:36 |
| **DataManagementPage** | LIVE API | PATCH /auth/me | CONNECTED | api.js:173 |
| **DataManagementPage** | LIVE API | GET/POST /items/ | CONNECTED | api.js:177-178 |
| **DataManagementPage** | LIVE API | PATCH/DELETE /items/{id} | CONNECTED | api.js:179-180 |
| **DataManagementPage** | LIVE API | GET /users/ | CONNECTED | api.js:174 |
| **DataManagementPage** | LIVE API | GET/PATCH /users/{id} | CONNECTED | api.js:175-176 |
| **BackendApiPage** | LIVE API | GET /health, /ready | CONNECTED | BackendApiPage.jsx:42, api.js:157-158 |
| **DashboardOverview** | MOCK CONSTANT | (none — all from mockData.js + procurementStore) | MOCK | DashboardOverview.jsx:6-8 |
| **ProcurementPages** | MOCK CONSTANT | GET /purchase-orders, /vendors, /invoices, /contracts | MOCK | ProcurementPages.jsx:25-28, procurementStore.js |
| **NegotiationPage** | MOCK CONSTANT | POST /negotiations, /negotiations/{id}/options, /negotiations/{id}/drafts | MOCK | NegotiationPage.jsx:13, negotiationService.js |
| **FraudDetectionPage** | MOCK + LOCALSTORAGE | POST /fraud/scans, GET /fraud/alerts, PATCH /fraud/alerts/{id} | MOCK | FraudDetectionPage.jsx:9, fraudDetectionService.js:6,14 |
| **ChatPage (mock mode)** | MOCK CONSTANT | POST /conversations, POST /conversations/{id}/messages | MOCK | chatService.js:212-270 |
| **ChatPage (live mode)** | LIVE API | POST /agents/chat | CONNECTED | api.js:182-185, chatService.js:89 |
| **ChatPage (live mode)** | LIVE API | POST /conversations, GET /conversations/{id}/messages | BACKEND-501 | api.js:187-190, contracts.py:9-26 |
| **ChatPage (live mode)** | LIVE API | POST /messages/{id}/feedback | BACKEND-501 | api.js:191, contracts.py:28-33 |
| **ChatPage (live mode)** | LIVE API | POST /approvals/{id}/approve, /reject | BACKEND-501 | api.js:193-194 |
| **DashboardScaffoldPage** | NONE | — | SCAFFOLD | DashboardScaffoldPage.jsx:18 |

---

## Table C — Backend Endpoints With No Frontend Usage (all return 501)

| Endpoint | Frontend calls it? |
|---|---|
| GET /conversations | api.js:187 export exists, **never called** by any page |
| GET /runs/{id} | No |
| GET /runs/{id}/events | No |
| POST /runs/{id}/cancel | No |
| GET /runs/{id}/tool-calls | No |
| GET /approvals | api.js:192 export exists, **never called** by any page |
| GET /approvals/{id} | No |
| POST /approvals | No |
| GET /purchase-orders | No |
| POST /purchase-orders | No |
| GET /purchase-orders/{id} | No |
| GET /purchase-orders/{id}/versions | No |
| POST /purchase-orders/{id}/send | No |
| POST /purchase-orders/{id}/confirmations | No |
| POST /purchase-orders/{id}/follow-ups | No |
| POST /purchase-orders/{id}/cancel | No |
| POST /purchase-orders/{id}/notify-stakeholders | No |
| GET /change-requests | No |
| POST /change-requests | No |
| GET /change-requests/{id} | No |
| POST /change-requests/{id}/accept | No |
| POST /change-requests/{id}/analyze | No |
| POST /change-requests/{id}/reject | No |
| GET /purchase-orders/{id}/communications | No |
| POST /communications/draft | No |
| POST /communications/{id}/send | No |
| PATCH /communications/{id} | No |
| GET /vendors | No |
| POST /vendors | No |
| GET /vendors/{id} | No |
| GET /vendors/{id}/contacts | No |
| GET /vendors/{id}/performance | No |
| GET /vendors/{id}/bank-accounts | No |
| POST /vendors/{id}/bank-accounts/change-requests | No |
| POST /vendors/{id}/bank-accounts/change-requests/{request_id}/verify | No |
| GET /contracts | No |
| GET /contracts/search | No |
| GET /contracts/{id} | No |
| GET /purchase-history | No |
| GET /price-history | No |
| POST /negotiations | No |
| GET /negotiations/{id} | No |
| GET /negotiations/{id}/context | No |
| GET /negotiations/{id}/options | No |
| POST /negotiations/{id}/options | No |
| POST /negotiations/{id}/options/{opt_id}/select | No |
| POST /negotiations/{id}/drafts | No |
| GET /negotiations/{id}/drafts | No |
| PATCH /negotiations/{id}/drafts/{draft_id} | No |
| POST /negotiations/{id}/drafts/{draft_id}/send | No |
| POST /negotiations/{id}/outcome | No |
| POST /fraud/scans | No |
| GET /fraud/alerts | No |
| GET /fraud/alerts/{id} | No |
| PATCH /fraud/alerts/{id} | No |
| POST /fraud/alerts/{id}/explain | No |
| POST /fraud/alerts/{id}/hold-payment | No |
| GET /fraud/rules | No |
| POST /fraud/rules | No |
| PATCH /fraud/rules | No |
| GET /fraud/dashboard | No |
| GET /invoices | No |
| POST /invoices | No |
| GET /invoices/{id} | No |
| GET /audit-logs | No |
| GET /notifications | No |
| POST /notifications | No |
| GET /settings/policies | No |
| PATCH /settings/policies | No |
| GET /usage | No |
| POST /webhooks/inbound-email | No (server-only, correct) |

**Total: 68 placeholder endpoints in contracts.py. Frontend calls 0 of them (excluding chat endpoints covered above).**

---

## Findings

### F1 — Auth Flow

| Aspect | Status | Evidence |
|---|---|---|
| Login | CONNECTED (POST /auth/login) | LoginPage.jsx:21 |
| Logout | CONNECTED (POST /auth/logout) | api.js:164 (used in DataManagementPage) |
| Token refresh | CONNECTED (automatic on 401) | api.js:47-51 |
| Registration | NOT AVAILABLE (by design) | LoginPage.jsx:54 |
| Forgot password | NOT AVAILABLE | — |
| Session storage | sessionStorage under key `life-purpose-auth-session` | api.js:3 |
| Protected routes | Only `/dashboard/data` is behind AuthenticatedRoute | App.jsx:56 |
| 401 handling | Refresh then throw; ChatPage redirects to /login | api.js:47, ChatPage.jsx:39 |
| 403 handling | NOT HANDLED — no special case anywhere | — |
| Redirect after login | Goes to `state.from` or `/dashboard/data` | LoginPage.jsx:15 |

### F2 — Interaction Gaps

| Issue | File:Line |
|---|---|
| WhatsApp link has empty href (`https://wa.me/` with no phone number) | App.jsx:55 |
| Global search input in topbar captures text but only filters DashboardOverview agent activities — does nothing on most pages | DashboardLayout.jsx:35, DashboardOverview.jsx:29 |
| Notification popover is hardcoded with 2 static items, no dismiss, no backend | DashboardLayout.jsx:35 |
| Workspace switcher ("Acme Corporation") is visual-only, no onClick handler | DashboardLayout.jsx:30 |
| Profile popover sign-out only appears if user is signed in; otherwise profile section is decorative | DashboardLayout.jsx:35 |
| ApprovalGate buttons are permanently disabled (both mock and live) | src/components/chat/ApprovalGate.jsx:22-32 |
| `getConversations` and `getApprovals` exported from api.js but never called | api.js:187,192 |
| Keyboard shortcut hint `⌘ K` shown but no handler | DashboardLayout.jsx:35 |

### F3 — Security Hygiene

| Issue | Severity | File:Line |
|---|---|---|
| Auth tokens in sessionStorage (accessible to XSS) | Medium (by design, documented in README) | api.js:12,39 |
| localStorage used for fraud demo alerts | Low (demo data only) | fraudDetectionService.js:6,14 |
| localStorage used for procurement store (zustand persist) | Low (demo data only) | procurementStore.js:38 |
| No dangerouslySetInnerHTML found | OK | — |
| No secrets/keys in src/ or dist/ | OK | — |
| No AGENT_API_KEY, INTERNAL_API_KEY, or X-API-Key in frontend | OK | — |

### F4 — Leftovers

| Issue | File:Line |
|---|---|
| Session key uses legacy project name `life-purpose-auth-session` | api.js:3 |
| README.md line 3 mentions "TypeScript" but project is pure .jsx, no tsconfig | Frontend/README.md:3 |
| WhatsApp link placeholder with no phone number | App.jsx:55 |
| `Cell` imported from recharts in App.jsx but appears unused in visible code (Vite tree-shakes it, no build warning) | App.jsx:5 |

---

## Chat Feature Status (Check 7)

- `src/pages/ChatPage.jsx` — **EXISTS**, 208 lines
- `src/services/chatService.js` — **EXISTS**, 311 lines
- `src/components/chat/` — **7 components**: ContextBar, MessageList, Composer, VerifiedResultCard, RiskFindings, ToolTrace, ApprovalGate
- `.env.example` shows `VITE_CHAT_MODE=live`; default fallback in code is `'mock'` (chatService.js:274)
- Mock mode: 4 scenarios (negotiation draft, fraud review_required, no_flags, model_unavailable error)
- Live mode: calls `POST /agents/chat` (implemented in backend) and manages conversations in-memory (Map) since `/conversations` endpoints return 501
- Approval buttons permanently disabled (no approval_id in agent response)
- `CHAT_INTEGRATION.md` documents assumed shapes and 10 gaps for backend teammate

---

## Build Health (Check 8)

| Check | Result |
|---|---|
| `npm run build` | **PASS** — 0 errors, 1 pre-existing warning (chunk > 500KB) |
| `npm run lint` | NOT RUN — no `lint` script in package.json |
| `npm run test` | NOT RUN — no `test` script in package.json |
| Secrets in dist/ | **CLEAN** — grep for AGENT_API_KEY, INTERNAL_API_KEY, X-API-Key returns nothing |

---

## Prioritized Backlog

### P0 — Blocks the demo

| # | Issue | Size | Who |
|---|---|---|---|
| P0-1 | No procurement pages are connected to real backend data (PO, suppliers, invoices all mock) — if the demo needs live data, this blocks everything | L | frontend + backend teammate |
| P0-2 | Negotiation page is 100% mock — no call to /agents/run or /negotiations/* | L | frontend + backend teammate |
| P0-3 | Fraud detection page is 100% mock — no call to /agents/run or /fraud/* | L | frontend + backend teammate |

### P1 — Should fix

| # | Issue | Size | Who |
|---|---|---|---|
| P1-1 | Chat `/conversations` endpoints return 501; live mode works around this with in-memory Map but loses history on refresh | M | backend teammate |
| P1-2 | Chat approval buttons always disabled (agent response has no `approval_id`; backend approval workflow not implemented) | M | backend teammate |
| P1-3 | Session key `life-purpose-auth-session` is a leftover from a different project name | S | frontend |
| P1-4 | WhatsApp link has empty href `https://wa.me/` — either add a number or remove | S | frontend |
| P1-5 | `getConversations` and `getApprovals` exported but never used — dead code or missing UI | S | frontend |
| P1-6 | Keyboard shortcut `⌘ K` hint displayed but no handler attached | S | frontend |
| P1-7 | 403 status not handled anywhere in the frontend | S | frontend |

### P2 — Nice to have

| # | Issue | Size | Who |
|---|---|---|---|
| P2-1 | Add lint (eslint) and test scripts to package.json | S | frontend |
| P2-2 | README mentions TypeScript but no TS config exists — update README | S | frontend |
| P2-3 | Code-split large chunk (955KB) with dynamic imports for NegotiationPage, FraudDetectionPage, ChatPage | M | frontend |
| P2-4 | Notification popover and workspace switcher are cosmetic — consider removing or wiring | M | frontend |
| P2-5 | Global search only filters one page (DashboardOverview agent activities) | M | frontend |

---

## Open Questions (max 5)

1. Is the demo expected to work with only mock data, or do you need at least one page connected to live backend procurement data?
2. Should the `life-purpose-auth-session` key be renamed to `procuremind-auth-session`, or is backward compatibility needed?
3. Is the WhatsApp link intentional (planned feature) or leftover boilerplate to remove?
4. Should NegotiationPage and FraudDetectionPage eventually call `/agents/run` directly, or only through the chat interface?
5. Are the `/runs/*` endpoints (events, cancel, tool-calls) needed by the frontend, or is tool_trace embedded in messages sufficient?

---

## NOT VERIFIED List

| Item | Reason |
|---|---|
| Runtime behavior of ChatPage in live mode against real backend | No backend running; code-read only |
| 401 → refresh → redirect flow end-to-end | Would require running backend + expired token |
| `Cell`, `Pie`, `PieChart` import usage in App.jsx Analytics() | Long line truncated in read_file; likely used inside the truncated Analytics function but could not confirm line-by-line |
| Actual visual rendering of all pages at 360px breakpoint | Would require browser; CSS-only review done |
| Profile popover sign-out behavior when session is null | Code review suggests it shows "Not signed in" but popover rendering was truncated |
