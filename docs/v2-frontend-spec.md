# Vitals Console — Frontend Engineering Specification

Implementation-ready. Consumes the backend defined in
[v2-engineering-spec.md](v2-engineering-spec.md) §8.3. No design decisions remain.

**Rule for the implementing agent:** if this document and your instinct disagree,
this document wins. If something genuinely is not covered, choose the option most
consistent with §2 (tokens) and §3 (motion), and note it in `DECISIONS.md`.

---

## 0. Stack — locked, and one override

### 0.1 The override

Backend spec **D5/D12** locked "stdlib `http.server`, f-string HTML, no build
step." That is incompatible with the quality bar requested here. **D5 is
superseded by this document.** The *intent* of D5 is preserved exactly:

- **No new runtime dependency.** The Python process still serves everything.
- **No CDN, no external fetch.** Fonts, icons, and JS are all self-hosted.
- **The build step is dev-time only.** Compiled assets are committed to
  `vitals/console/static/` and shipped in the wheel and the Docker image. A user
  running `pip install vitals && vitals run` never sees Node.

### 0.2 Required backend addition (the only one)

The Python console server must serve the SPA:

- `GET /` and **any non-`/api/*`, non-`/assets/*` path** → return
  `vitals/console/static/index.html` with `200` (SPA history fallback).
- `GET /assets/*` → serve from `vitals/console/static/assets/` with
  `Cache-Control: public, max-age=31536000, immutable`.
- `index.html` → `Cache-Control: no-cache`.

Without the fallback, `/v/:id`, `/scopes`, and `/about` 404 on hard refresh.

### 0.3 Locked stack

| Concern | Choice | Why (one line) |
|---|---|---|
| Framework | **React 18 + TypeScript (strict)** | Boring, ubiquitous, and the agent will not fight it. |
| Build | **Vite 5**, output `vitals/console/static/`, base `/` | Fast, zero-config, emits hashed assets. |
| Styling | **CSS Custom Properties + CSS Modules** | Tokens as CSS vars are directly auditable against §2. Utility dialects hide whether the spec was followed. |
| Routing | **React Router v6** (`createBrowserRouter`) | Deep-linkable drawer at `/v/:id` requires real routing. |
| Data | **TanStack Query v5** | Polling, stale-while-revalidate, and backoff are exactly the problem it solves. |
| Animation | **Motion for React** (`motion` package) | Exit animations for drawer/toast are impractical with CSS alone. |
| Icons | **lucide-react** | Tree-shakeable, consistent 1.5px stroke, matches the aesthetic. |
| Charts | **Hand-authored SVG. No chart library.** | Two chart forms only (§9). A library costs 50–150 KB for something fully controlled. |
| Fonts | **Self-hosted Inter var + JetBrains Mono**, woff2, `font-display: swap` | No CDN; works offline and under strict CSP. |
| Testing | **Vitest + React Testing Library**; **Playwright** for two smoke flows | Enough to protect the demo without becoming a test project. |
| Formatting | **Biome** (lint + format) | One tool, no ESLint/Prettier config negotiation. |

**Budget: ≤ 250 KB gzipped JS, ≤ 30 KB CSS, LCP < 1.0s on localhost.** Enforced
in CI (§16.4).

### 0.4 What the frontend must never do

- Never call an endpoint not listed in §10.1.
- Never compute a verdict, a sigma, or a state. **The backend is the only source
  of judgment.** The frontend formats `Verdict` fields; it never derives them.
- Never render `Verdict.sentence` reworded. When the sentence is shown, it is
  shown verbatim.
- Never invent a color, radius, duration, or spacing value outside §2/§3.

---

## 1. Product framing for the UI

The backend emits four states. The UI's entire job is to make **`STEADY` feel
like proof of work, not absence of work** — because on demo day and on day 300,
`STEADY` is what's on screen 95% of the time.

Three consequences that override generic dashboard instincts:

1. **The health strip is not chrome.** It is the evidence that silence is
   monitored silence. It gets real visual weight (§7.1 Zone 3).
2. **`CHANGED` is amber, never red.** Vitals reports change, not failure. Red is
   reserved exclusively for Vitals' own errors.
3. **Honesty fields are first-class UI.** `falsifier`, `caveats`, and
   `inconclusive_reason` render at the same visual weight as the sigma values —
   never in a collapsed "details" section.

---

## 2. Design system — frozen

All tokens live in `src/styles/tokens.css` as CSS custom properties on `:root`.
**Light theme only.** No `prefers-color-scheme` handling. No purple, anywhere,
ever — including hover tints, chart series, and focus rings.

### 2.1 Color — neutrals

Warm-grey neutral ramp (warmer than pure grey; reads as paper, not steel).

| Token | Hex | Use |
|---|---|---|
| `--color-canvas` | `#FBFBFA` | Page background |
| `--color-surface` | `#FFFFFF` | Cards, drawer, popover, table rows |
| `--color-surface-subtle` | `#F7F7F6` | Table header, feed row hover, inset panels |
| `--color-surface-inset` | `#F1F1EF` | Code blocks, JSON viewer, skeleton base |
| `--color-surface-raised` | `#FFFFFF` | Dropdowns, tooltips (with shadow-lg) |
| `--color-border-subtle` | `#EDEDEA` | Row dividers, internal card rules |
| `--color-border` | `#E2E2DE` | Default card and input border |
| `--color-border-strong` | `#CBCBC5` | Input hover, active dividers |
| `--color-text` | `#18181B` | Primary text, numbers |
| `--color-text-secondary` | `#57575F` | Labels, secondary copy |
| `--color-text-tertiary` | `#8A8A92` | Timestamps, hints, units |
| `--color-text-disabled` | `#B6B6BC` | Disabled labels |
| `--color-overlay` | `rgba(24,24,27,0.32)` | Drawer/modal scrim |

### 2.2 Color — accent

Deep confident blue. Used for interactive affordance only, never for status.

| Token | Hex |
|---|---|
| `--color-accent` | `#1A56DB` |
| `--color-accent-hover` | `#1546B4` |
| `--color-accent-active` | `#113A96` |
| `--color-accent-subtle` | `#EBF1FE` |
| `--color-accent-border` | `#C3D6FB` |
| `--color-accent-text` | `#1546B4` |

### 2.3 Color — status (maps 1:1 to `VerdictState`)

Hues match backend §9; tuned for light-theme contrast. Each state has four roles:
`dot` (solid indicator), `text`, `bg`, `border`.

| State | dot | text | bg | border |
|---|---|---|---|---|
| **STEADY** (success) | `#16A34A` | `#146C33` | `#F971FD`→ **`#F1FDF4`** | `#BBF0CC` |
| **CHANGED** (warning) | `#F59E0B` | `#96590C` | `#FFFAEB` | `#FBE3A6` |
| **INCONCLUSIVE** (info) | `#3B82F6` | `#1D4ED8` | `#EFF5FF` | `#C2D8FC` |
| **WARMING** (neutral) | `#8A8A92` | `#57575F` | `#F5F5F3` | `#E2E2DE` |
| **ERROR** (Vitals fault only) | `#DC2626` | `#A81E1E` | `#FEF2F2` | `#F8CFCF` |

`STEADY` bg is `#F1FDF4`. (The strikethrough above is intentional in the source
table only to make the correction unmissable — implement `#F1FDF4`.)

**Rule:** `--color-error-*` may only style Vitals' own failures — API unreachable,
store error, console degraded. A `CHANGED` verdict is never red.

### 2.4 Color — chart palette

Categorical, colorblind-safe, no purple. Use in this order.

| # | Token | Hex | Reserved meaning |
|---|---|---|---|
| 1 | `--chart-1` | `#1A56DB` | behavior sigma |
| 2 | `--chart-2` | `#0E9F6E` | cost sigma |
| 3 | `--chart-3` | `#F59E0B` | threshold / annotation |
| 4 | `--chart-4` | `#0891B2` | samples (n) |
| 5 | `--chart-5` | `#C2410C` | velocity ratio |
| 6 | `--chart-6` | `#64748B` | baseline / reference |

Grid `#EDEDEA`. Axis text `--color-text-tertiary`. Threshold band fill
`rgba(245,158,11,0.08)`.

### 2.5 Spacing

4px base. **Only these values may appear.**

`--space-0: 0` · `1: 4px` · `2: 8px` · `3: 12px` · `4: 16px` · `5: 20px` ·
`6: 24px` · `8: 32px` · `10: 40px` · `12: 48px` · `16: 64px` · `20: 80px`

### 2.6 Radius

`--radius-sm: 4px` (badges, dots) · `--radius-md: 6px` (buttons, inputs) ·
`--radius-lg: 10px` (cards, drawer) · `--radius-xl: 14px` (hero card) ·
`--radius-full: 9999px` (pills, avatars)

### 2.7 Shadows

Very subtle. Two-layer (contact + ambient). No colored shadows.

| Token | Value |
|---|---|
| `--shadow-xs` | `0 1px 2px rgba(24,24,27,0.04)` |
| `--shadow-sm` | `0 1px 3px rgba(24,24,27,0.06), 0 1px 2px rgba(24,24,27,0.04)` |
| `--shadow-md` | `0 4px 12px rgba(24,24,27,0.07), 0 1px 3px rgba(24,24,27,0.05)` |
| `--shadow-lg` | `0 12px 28px rgba(24,24,27,0.10), 0 2px 6px rgba(24,24,27,0.05)` |
| `--shadow-xl` | `0 24px 56px rgba(24,24,27,0.14), 0 4px 10px rgba(24,24,27,0.06)` |

Cards use `--shadow-xs` at rest, `--shadow-sm` on hover. Drawer `--shadow-xl`.
Dropdown/tooltip `--shadow-lg`.

**Gradients:** exactly two are permitted, both effectively invisible:
(a) hero card background `linear-gradient(180deg,#FFFFFF 0%,#FDFDFC 100%)`;
(b) feed bottom fade-to-canvas, 40px. No others.

### 2.8 Typography

Families: `--font-sans: "Inter var", -apple-system, "Segoe UI", sans-serif` ·
`--font-mono: "JetBrains Mono", ui-monospace, "SF Mono", monospace`.

**All numbers, sigma values, IDs, timestamps, and code use `--font-mono` with
`font-variant-numeric: tabular-nums`.** Non-negotiable — it is what makes a
polling UI stop twitching.

| Token | Size / Line height | Weight | Tracking | Use |
|---|---|---|---|---|
| `--text-display` | 32/40 | 600 | -0.02em | Hero state word (`CHANGED`) |
| `--text-h1` | 24/32 | 600 | -0.015em | Page titles |
| `--text-h2` | 18/26 | 600 | -0.01em | Card titles, section heads |
| `--text-h3` | 15/22 | 600 | -0.005em | Sub-sections, drawer groups |
| `--text-body` | 14/22 | 400 | 0 | Default copy |
| `--text-body-md` | 14/22 | 500 | 0 | Emphasized copy, buttons |
| `--text-sm` | 13/20 | 400 | 0 | Table cells, feed rows |
| `--text-xs` | 12/18 | 500 | 0.005em | Labels, badges, health strip |
| `--text-micro` | 11/16 | 500 | 0.02em | Uppercase eyebrows, axis ticks |
| `--text-mono-lg` | 20/28 | 600 | -0.01em | Sigma values in hero |
| `--text-mono` | 13/20 | 400 | 0 | IDs, JSON, code |
| `--text-mono-sm` | 12/18 | 400 | 0 | Timestamps, trace ids in feed |

Eyebrow labels: `--text-micro`, `text-transform: uppercase`,
`color: --color-text-tertiary`.

### 2.9 Icons

lucide-react, stroke width **1.5**, sizes **14 / 16 / 20 / 24** only.
14 in badges and feed rows · 16 default (buttons, inline) · 20 section headers ·
24 empty-state illustrations. Icons are always `aria-hidden` unless they are the
sole content of a control, which then requires `aria-label`.

Fixed icon assignments (never substitute):
`STEADY`→`CircleCheck` · `CHANGED`→`Activity` · `INCONCLUSIVE`→`CircleHelp` ·
`WARMING`→`LoaderCircle` · error→`TriangleAlert` · caveat→`Info` ·
falsifier→`GitCompareArrows` · release→`Tag` · unattributed→`CircleDashed` ·
runaway→`Flame` · trace→`ExternalLink` · copy→`Copy` · search→`Search` ·
filter→`ListFilter` · close→`X` · expand→`ChevronDown`.

### 2.10 Layout constants

`--layout-max: 1120px` · `--layout-gutter: 24px` (mobile 16px) ·
`--header-height: 56px` · `--drawer-width: 560px` ·
`--focus-ring: 0 0 0 2px #FFFFFF, 0 0 0 4px var(--color-accent)`.

---

## 3. Motion system — frozen

### 3.1 Durations & easing

| Token | Value | Use |
|---|---|---|
| `--dur-instant` | 80ms | Color/opacity on hover |
| `--dur-fast` | 140ms | Buttons, badges, small transforms |
| `--dur-base` | 200ms | Cards, tooltips, tab indicator |
| `--dur-slow` | 300ms | Drawer, modal, route transitions |
| `--dur-slower` | 460ms | Number count-up, chart draw-in |

| Token | Curve | Use |
|---|---|---|
| `--ease-out` | `cubic-bezier(0.22, 1, 0.36, 1)` | **Default.** Anything entering or expanding. |
| `--ease-in` | `cubic-bezier(0.5, 0, 0.75, 0)` | Exits only |
| `--ease-inout` | `cubic-bezier(0.65, 0, 0.35, 1)` | Position changes both directions |
| `--ease-spring` | spring `{stiffness: 380, damping: 32, mass: 0.9}` | Drawer, hero state change, toast |

**Never** use `linear` except for the indeterminate spinner and progress shimmer.

### 3.2 Named animations

| Name | Behavior |
|---|---|
| **Route transition** | Outgoing `opacity 1→0` 100ms `--ease-in`; incoming `opacity 0→1, translateY 6px→0` 200ms `--ease-out`, 60ms delay. No horizontal slide. |
| **Card hover** | `box-shadow xs→sm` + `translateY 0→-1px`, 140ms `--ease-out`. Exit 200ms. |
| **Button press** | `scale 1→0.975`, 80ms. Release springs back over 140ms. |
| **Badge state change** | Old badge `opacity→0, scale→0.94` 100ms; new `opacity 0→1, scale 1.06→1` 180ms `--ease-out`. Crossfade in place — badge never reflows. |
| **Hero state change** | Whole card: border+bg color 300ms `--ease-inout`; state word crossfades per Badge rule; sigma bars re-animate (below); a single 600ms ring pulse (`box-shadow 0 0 0 0 → 0 0 0 8px` of the state color at 12% alpha, fading to 0). Fires **once** per state transition, never on refresh. |
| **Sigma bar fill** | `scaleX 0→value` from left origin, 460ms `--ease-out`, staggered 60ms per bar. Re-animates only when the value changes by ≥0.1σ. |
| **Number count-up** | Sigma and cost numbers tween over 460ms `--ease-out` when they change. Integers ≤999 tween; larger values snap. `n=` counts up. Never tweens on first mount — first paint is the final value. |
| **Feed row enter** | New rows: `opacity 0→1, translateY -8px→0` 200ms `--ease-out`. Existing rows shift down with `layout` animation 200ms. Max 3 stagger steps of 40ms; beyond that, all at once. |
| **Drawer** | Panel `translateX 100%→0` with `--ease-spring`; scrim `opacity 0→1` 200ms. Exit: panel `translateX 0→100%` 240ms `--ease-in`, scrim 180ms. |
| **Modal** | `opacity 0→1, scale 0.97→1, translateY 8px→0` 200ms `--ease-out`. Exit 140ms `--ease-in`, no translate. |
| **Toast** | Enter from bottom-right: `translateY 16px→0, opacity 0→1, scale 0.96→1` `--ease-spring`. Exit `opacity→0, translateX 16px` 160ms. Stacked toasts shift with 200ms layout animation. |
| **Tooltip** | Delay 400ms open / 80ms close. `opacity 0→1, scale 0.96→1, translateY 4px→0` 140ms `--ease-out`. Zero delay when moving between adjacent tooltip triggers within 300ms. |
| **Dropdown/popover** | `opacity 0→1, scale 0.97→1` 140ms `--ease-out`, transform-origin at the trigger edge. Exit 100ms. |
| **Accordion** | `height auto→0` measured, 220ms `--ease-inout`; content `opacity` 140ms, 40ms delay on open. |
| **Tab indicator** | Underline slides via `layoutId`, 220ms `--ease-inout`. |
| **Skeleton shimmer** | Background sweep `translateX -100%→100%`, 1400ms linear, infinite. |
| **Spinner** | `rotate 360deg` 700ms linear infinite. Only appears after 400ms of pending. |
| **Chart draw-in** | Sparkline path `stroke-dashoffset` full→0 over 460ms `--ease-out`, once per mount. Points fade in at 60% of the sweep. |
| **Live pulse** | Health-strip "live" dot: `opacity 1→0.35→1` 2000ms `--ease-inout` infinite. Turns solid grey and stops when polling is paused or failing. |
| **Copy confirm** | Icon swaps `Copy`→`Check` for 1200ms with an 80ms scale pop, then swaps back. |
| **Scroll reveal** | **None.** No scroll-triggered animation anywhere. Content is present when painted. |

### 3.3 Reduced motion

Under `prefers-reduced-motion: reduce`:
- All durations → **0ms** except opacity fades, which clamp to 100ms.
- No transform animation (no slide, scale, spring). Drawer and modal appear
  instantly with a 100ms fade.
- No count-up; numbers snap.
- No shimmer, no live pulse, no chart draw-in, no ring pulse.
- Spinner is replaced by a static `Loading…` label.

Implement via a `useReducedMotion()` hook that gates Motion props, **plus** a
global CSS media query as a backstop. Both, not either.

---

## 4. Information architecture

### 4.1 Routes

| Path | Screen | Data |
|---|---|---|
| `/` | Console | verdicts, scopes, health |
| `/v/:verdictId` | Console **+ Verdict drawer open** | + verdict detail |
| `/scopes` | Scopes | scopes, health |
| `/about` | Blind spots & About | none (static) |
| `*` | Not found | none |

**The verdict drawer is a route, not local state.** `/v/:id` renders the console
underneath with the drawer open, so verdicts are shareable and back/forward work.
Closing the drawer navigates to `/` (or the previous list route) preserving query
params.

### 4.2 URL state (query params — all on `/`)

| Param | Values | Default |
|---|---|---|
| `state` | `steady,changed,inconclusive,warming` (comma-joined multi) | unset = all |
| `service` | service name | unset = all |
| `version` | version string | unset = all |
| `q` | free-text search over sentence, version, verdict_id, trace_id | unset |
| `sort` | `newest` \| `oldest` \| `sigma` | `newest` |
| `paused` | `1` | unset |

URL is the single source of truth for filters. Reading query params happens in
one hook (`useVerdictFilters`); no component reads `useSearchParams` directly.

### 4.3 Navigation

Single top header, 56px, `--color-surface`, `--shadow-xs`, sticky.

- **Left:** wordmark `vitals` (`--text-h2`, mono, `--color-text`) + a small state
  dot reflecting the *most severe live scope state*. Links to `/`.
- **Center:** tabs — `Console` (`/`) · `Scopes` (`/scopes`).
- **Right:** search field (⌘K / Ctrl-K) · pause/resume polling toggle ·
  `About` link (`/about`).

**No sidebar. No breadcrumbs.** The hierarchy is two levels deep; breadcrumbs
would be decoration.

### 4.4 Filtering, sorting, pagination

- **Filtering:** client-side over the fetched verdict list. State filter is a
  segmented multi-select of four chips; service/version are dropdowns populated
  from the fetched data.
- **Sorting:** `newest` (default) · `oldest` · `sigma` (by
  `max(|behavior_sigma|, |cost_sigma|)` desc, nulls last).
- **Pagination: none.** The API returns ≤50 (`limit=50`) and the store retains
  1000. The feed renders all fetched rows with **windowed rendering above 120
  rows** (fixed 44px row height, 8-row overscan). Infinite scroll and page
  controls are both explicitly excluded — the dataset is bounded and recency-
  ordered.

### 4.5 Search (⌘K)

An inline expanding field in the header, **not** a modal palette. Rationale: it
searches one list; a full command palette implies commands, and this UI has none.

- ⌘K / Ctrl-K focuses it; `Esc` clears and blurs.
- Debounce 150ms, writes to `?q=`.
- Matches case-insensitively against `sentence`, `version`, `service_name`,
  `verdict_id`, and exemplar `trace_id`.
- Matched substrings highlight with `--color-accent-subtle` background.
- Shows `N results` in `--text-xs` `--color-text-tertiary` while active.

---

## 5. API integration

### 5.1 Endpoints (the complete set — nothing else exists)

| Key | Endpoint | Poll | Notes |
|---|---|---|---|
| `verdicts` | `GET /api/verdicts?limit=50` | **2s** | Newest first. Drives hero + feed. |
| `verdict` | `GET /api/verdicts/:id` | on demand, `staleTime: Infinity` | Verdicts are immutable once written — never refetch. |
| `scopes` | `GET /api/scopes` | **5s** | Warming progress, live state. |
| `health` | `GET /api/health` | **10s** | Health strip. |

**No mutations exist.** Therefore: **no optimistic updates.** Anything that looks
like a write (pin, dismiss, filter, pause) is local UI state persisted to
`localStorage` — §6.4.

### 5.2 Polling strategy

- `refetchInterval` per the table above; `refetchOnWindowFocus: true`;
  `refetchIntervalInBackground: false`.
- **Pause when `document.hidden`**, resume with an immediate refetch on visibility
  return. A backgrounded demo laptop must not burn requests.
- **Manual pause** (`?paused=1`, header toggle, or `Space` when the feed has
  focus) stops all polling and shows a `Paused` pill in the header. Used when a
  presenter wants the screen to hold still.
- **Never poll while the drawer is open on a verdict detail** — the underlying
  list keeps polling, but the drawer's own query is `staleTime: Infinity`.

### 5.3 Errors and retries

- Retry `3` times with backoff `min(1000 * 2^attempt, 8000)`.
- On the **first** failure: keep showing last-good data; the health-strip live dot
  turns grey and a `Reconnecting…` label appears. **No toast.** Transient blips
  during a demo must not throw UI.
- After **3 consecutive** failed cycles: show a persistent error banner below the
  header (§7.5) with `Retry now`. Data stays visible, dimmed to 60% opacity.
- On recovery: banner exits, one toast `Reconnected`, live dot resumes pulsing.
- `404` on `/api/verdicts/:id` → drawer shows its not-found state (§7.4), does not
  retry.
- All network errors are typed as `{status, message, endpoint}` and surfaced with
  the endpoint name in the banner — a developer tool should say which call failed.

### 5.4 Caching

- `staleTime`: verdicts `1500ms`, scopes `4000ms`, health `8000ms`, verdict
  detail `Infinity`.
- `gcTime`: `5min` for lists, `30min` for verdict details.
- `structuralSharing: true` (default) — critical, it is what keeps unchanged feed
  rows from re-rendering and re-animating on every 2s poll.
- **Seed the detail cache from the list.** When the feed has a verdict, opening
  its drawer renders immediately from `setQueryData` while the full record loads.

### 5.5 Offline

`navigator.onLine === false` → header shows an `Offline` pill, polling suspends,
last-good data remains fully interactive (filters, sort, search, drawer all work
against cache). On `online`, refetch everything immediately. No service worker;
no offline persistence beyond the in-memory query cache.

---

## 6. State management

### 6.1 Server state
TanStack Query only. **No verdict data is ever copied into React state or a
store.** Components read from `useVerdicts()`, `useVerdict(id)`, `useScopes()`,
`useHealth()`.

### 6.2 URL state
Filters, sort, search, pause (§4.2). Owned by `useVerdictFilters()`.

### 6.3 Local component state
Hover, focus, open/closed accordions, copy-confirm timers. Nothing else.

### 6.4 Persisted state (`localStorage`, key prefix `vitals.console.`)

| Key | Value | Purpose |
|---|---|---|
| `vitals.console.density` | `comfortable` \| `compact` | Feed row density |
| `vitals.console.lastSeenVerdictId` | string | Powers the "N new" pill after a pause |
| `vitals.console.sigmaFormat` | `sigma` \| `raw` | Dev escape hatch; default `sigma` |

Reads are wrapped in try/catch with defaults — a locked-down browser must not
break the app.

### 6.5 Derived state (memoized selectors in `src/features/verdicts/selectors.ts`)

`latestVerdict` · `filteredVerdicts` · `sortedVerdicts` · `verdictCounts` (per
state) · `mostSevereScopeState` (for the header dot: CHANGED > INCONCLUSIVE >
WARMING > STEADY) · `hasAnyData`.

**No global store (no Redux/Zustand/Jotai).** With four read-only endpoints and
URL-owned filters, a store would be pure ceremony.

---

## 7. Screens

### 7.1 Console (`/`)

Single column, `max-width: 1120px`, centered, `padding: 32px 24px 80px`.
Three zones, in order, gap `--space-8` (32px).

#### Zone 1 — Hero Verdict Card

The Release Report Card. Renders `latestVerdict`.

Container: `--radius-xl`, 1px border in the state's `border` color, background =
gradient (a) from §2.7 over the state's `bg` color at 40% blend, `--shadow-sm`,
`padding: 28px 32px`.

Internal layout, top to bottom:

1. **Header row** (flex, space-between, align baseline)
   - Left: `StatusDot` (10px) + state word in `--text-display`, in the state's
     `text` color. Beside it, flag chips: `behavior`, `cost`, `runaway` —
     `Badge` size `sm`, only those that are true.
   - Right: `service_name` in `--text-body-md`, then `·`, then `version` in
     `--font-mono`. `--color-text-secondary`.
2. **Subject line** — `--text-sm`, `--color-text-secondary`, `margin-top: 4px`.
   Format: `{subject} · {version} vs {baseline_version}` or `{subject} · {version}`
   when there is no baseline.
3. **Sigma meters** — `margin-top: 24px`, two rows, gap 12px. Each row is a
   3-column grid: label (88px, `--text-xs`, tertiary) · value
   (`--text-mono-lg`, signed, 1 decimal, `+4.2σ`) · bar (flex, 8px tall,
   `--radius-full`, track `--color-surface-inset`).
   - Bar scale: **fixed domain 0→6σ**, clamped, with a 1px threshold tick at 3σ
     in `--chart-3`. Fixed domain matters — a rescaling axis makes two verdicts
     visually incomparable.
   - Fill color: `--chart-1` for behavior, `--chart-2` for cost. When
     `|z| < 1.0`, fill is `--color-text-tertiary` and the trailing label reads
     `flat`.
   - Trailing hint: `normal ±1σ` in `--text-micro`, tertiary.
4. **Attribution line** — `margin-top: 20px`, `--text-sm`. Icon (`Tag` for
   release, `CircleDashed` for unattributed, `Flame` for runaway) + text.
   Release: `onset 14:32:07 — 90s after v2 deployed`.
   Unattributed: `cause unattributed — no release in the last 5m`.
5. **Counts line** — `--text-xs`, tertiary, mono numbers:
   `n=1240 · baseline v1 (n=30)`.
6. **Caveats** (only when non-empty) — `margin-top: 16px`, inset block:
   `--color-surface-subtle`, `--radius-md`, `padding: 10px 12px`, `Info` icon 14,
   `--text-sm`. Comma-joined caveats.
7. **Falsifier** — **always rendered**, same block styling as caveats,
   `GitCompareArrows` icon, `--color-text-secondary`. This is a trust surface; it
   never collapses and never hides.
8. **Evidence** — `margin-top: 24px`, eyebrow `EVIDENCE`, then one `ExemplarRow`
   per exemplar. Worst rows first, **median row always last and always present**.
   Each row: kind chip (`worst` amber-subtle / `median` neutral) · mono trace id
   truncated to 6 chars with copy-on-click · signed sigma · output excerpt
   (single line, `text-overflow: ellipsis`, `--color-text-secondary`) ·
   `ExternalLink` icon that opens the SigNoz trace URL in a new tab.
   Row hover: `--color-surface-subtle`, 80ms. Click anywhere → opens the drawer.
9. **Footer** — `margin-top: 20px`, `border-top: 1px --color-border-subtle`,
   `padding-top: 12px`. Left: relative timestamp (`14s ago`, live-updating every
   second, `title` = absolute ISO). Right: `View full record →` link to `/v/:id`.

**Warming variant:** replaces zones 3–8 with a `ProgressBar` (§8.14),
`collecting reference 340/1000`, `est. 22m`, and the copy *"Vitals is
establishing a healthy baseline. No verdict will be issued until it has one."*
Neutral colors throughout.

**Inconclusive variant:** state word `INCONCLUSIVE`, and the reason renders as a
prominent sentence directly beneath it in `--text-h3`, e.g. *"Your traffic
changed, not your model."* Sigma meters still render, plus a third greyed meter
for `input` if the backend supplied it. The falsifier block stays.

- **Loading:** `HeroCardSkeleton` — exact same geometry, shimmer blocks.
- **Empty (no verdicts yet, backend healthy):** `EmptyState` with `Activity` icon
  24, title *"No verdicts yet"*, body *"Vitals is listening. Send traffic through
  your collector and the first verdict appears here."*, and a mono hint line with
  the receiver port from `/api/health`.
- **Error:** card shows the error variant — `TriangleAlert`, *"Can't reach the
  Vitals API"*, endpoint name, `Retry now` button.

#### Zone 2 — Verdict Feed

Header row: title `Verdicts` (`--text-h2`) + count pill · right side:
`StateFilterChips`, `SortDropdown`, `DensityToggle`.

Filter chips: four `ToggleChip`s (`Steady` `Changed` `Inconclusive` `Warming`),
each with its state dot and a count. Multi-select; all-off means all-on.

Rows: `44px` comfortable / `36px` compact. Columns, left to right:
time (mono-sm, 72px, tertiary) · `StatusDot` (8px) · state word (`--text-xs`
uppercase, state text color, 96px) · sentence (flex, single line, ellipsis,
`--text-sm`) · sigma pair (mono-sm, right-aligned, 104px) · `ChevronDown`
(rotates 180° when expanded, 200ms).

- Row hover: `--color-surface-subtle` background, 80ms; `ChevronDown` fades
  tertiary→secondary.
- **Click expands inline** (accordion, §3.2) showing a compact receipt: subject,
  cause, caveats, falsifier, and up to two exemplars. **Cmd/Ctrl-click or the
  `View full record` link opens the drawer** at `/v/:id`. Rationale: inline
  expansion is for scanning; the drawer is for reading.
- New rows animate in per §3.2. When the feed is scrolled away from the top and
  new verdicts arrive, a floating `N new` pill appears at the top center
  (`--shadow-md`, spring in); clicking scrolls to top and clears it.
- Zebra striping: none. Dividers: 1px `--color-border-subtle` between rows.

- **Loading:** 6 `FeedRowSkeleton`s.
- **Empty (filters exclude everything):** inline `EmptyState`, `ListFilter` icon,
  *"No verdicts match these filters"*, `Clear filters` ghost button.
- **Empty (no data at all):** the feed section is hidden entirely; the hero
  card's empty state carries the message.

#### Zone 3 — Health Strip

Not chrome (§1). Full-width card, `--radius-lg`, `--color-surface`, 1px border,
`padding: 16px 20px`.

Left: `LivePulseDot` + `Live` / `Paused` / `Reconnecting…` / `Offline`.
Center: six `MetricChip`s, `--font-mono` values with `--text-xs` uppercase
labels — `spans received` · `scored` · `skipped` · `scopes` · `verdicts` ·
`emit errors`. Values count up (§3.2). `emit errors` chip turns to the error
palette when `> 0`.
Right: `uptime` and `vitals v{version}`, tertiary.
Footer line: `Known blind spots →` linking to `/about`. Required by backend §20.8.

Skipped-spans chip shows a tooltip: *"Spans that weren't GenAI or couldn't be
mapped. A non-zero value is normal."* — pre-empting the most common false alarm
about Vitals itself.

#### Keyboard (Console)

| Key | Action |
|---|---|
| `⌘K` / `Ctrl-K` | Focus search |
| `/` | Focus search (when not in an input) |
| `j` / `↓` | Next feed row |
| `k` / `↑` | Previous feed row |
| `Enter` | Expand/collapse focused row |
| `o` | Open focused row in drawer |
| `Space` | Toggle polling pause |
| `Esc` | Clear search → clear filters → blur (in that order) |
| `1`–`4` | Toggle state filter chips |
| `?` | Open shortcuts modal |

Focused feed row shows a 2px `--color-accent` left border and
`--color-surface-subtle` background.

#### Responsive (Console)

- **Desktop ≥1280px:** as described, 1120px column.
- **Laptop 1024–1279px:** identical, gutters 24px, container fluid.
- **Tablet 768–1023px:** hero sigma meters stack label-above-bar; feed drops the
  sigma-pair column (moves into the expanded row); filter chips scroll
  horizontally with a fade mask.
- **Mobile <768px:** hero padding `20px 16px`, state word `--text-h1`; feed rows
  become two-line (line 1: time + state + sigma; line 2: sentence); health strip
  chips wrap to a 2-column grid; header tabs collapse to an icon-only segmented
  control; search becomes a full-width row beneath the header when focused;
  **drawer becomes a bottom sheet** (§7.4).

### 7.2 Scopes (`/scopes`)

Answers *"is Vitals watching, and how far along is it?"*

Layout: page title `Scopes` + subtitle *"What Vitals is currently watching."*
Then a responsive grid of `ScopeCard`s — 2 columns ≥1024px, 1 below.

`ScopeCard` (`--radius-lg`, `--shadow-xs`, `padding: 20px`):
- Header: `service_name` (`--text-h3`) + state `Badge`.
- Meta row: `gen_ai.system` · `model` — mono, tertiary, `--text-xs`.
- Body when **warming**: `ProgressBar` with `have/need`, phase label
  (`collecting reference` / `calibrating`), and est. time remaining.
- Body when **live**: a 4-row signal table — `behavior`, `input`, `cost`,
  `length` — each with `μ`, `σ`, and a `calibrated` check. Mono, tabular.
- Footer: versions seen, as `Badge`s; the active one filled, prior ones outline.
- Click → navigates to `/?service={name}` (filters the console to that scope).

Loading: 4 `ScopeCardSkeleton`s. Empty: `EmptyState`, `Search` icon, *"No scopes
yet"*, body *"A scope appears once Vitals sees its first GenAI span."*
Error: same pattern as Console.

Keyboard: `Tab` through cards; `Enter` activates. Responsive: 2→1 column at
1024px; signal table becomes label/value pairs below 768px.

### 7.3 About / Blind Spots (`/about`)

Static, no API. Prose column, `max-width: 720px`.

Sections, in order: **What Vitals claims** · **What Vitals does not claim** ·
**Known blind spots** (the four from the critique: subtle factual degradation,
uniform degradation, baseline poisoning, deploy-during-warming) · **How to read a
verdict** (annotated static example of the sentence grammar) · **Version & build**
(from `/api/health`).

Each blind spot is an `AlertCallout` variant `info` with a title and two-sentence
body. Typography-led, no cards, generous `--space-8` between sections.

This screen exists because "we publish our blind spots" is a product claim, and a
claim without a URL is marketing.

### 7.4 Verdict Drawer (`/v/:verdictId`)

Right-anchored panel, `--drawer-width: 560px`, full height, `--color-surface`,
`--shadow-xl`, `--radius-lg` on the left corners only. Scrim `--color-overlay`.

Header (sticky, 64px, bottom border): `StatusDot` + state word + flag chips ·
right: `Copy JSON` icon button, `X` close.

Body (scrollable, `padding: 24px`), sections separated by 1px rules:

1. **Sentence** — verbatim `Verdict.sentence`, `--font-mono`, `--text-mono`,
   in a `--color-surface-inset` block, `--radius-md`, `padding: 12px`, wrapping.
   Copy button top-right on hover.
2. **Judgment** — definition grid (label left 140px, value right, mono):
   state, subject, cause, flags, runaway.
3. **Evidence** — full-size sigma meters (same component as hero) plus
   `cost_usd_per_req` vs `baseline_cost_usd_per_req` and `velocity_ratio`.
4. **Timing** — `ts_unix` absolute + relative, `onset_ts_unix`,
   `seconds_after_deploy`, `samples`, `baseline_samples`.
5. **Honesty** — `falsifier` and `caveats` as `AlertCallout`s. Always present.
6. **Exemplars** — full `ExemplarCard` list: kind chip, trace id (full, mono,
   copyable), sigma, **full excerpt in a `--color-surface-inset` block** (wrapped,
   not truncated), and an `Open trace in SigNoz` button.
7. **Raw record** — `JsonViewer` (§8.20), collapsed to depth 1 by default.

Footer (sticky): `verdict_id` mono with copy · `Prev` / `Next` buttons that walk
the currently filtered feed order.

- **Open:** §3.2 drawer animation. Focus moves to the header close button. Body
  scroll locked. Focus trapped.
- **Close:** `Esc`, scrim click, `X`, or browser back. Focus returns to the
  originating feed row.
- **Keyboard:** `Esc` close · `j`/`k` prev/next verdict · `c` copy JSON ·
  `Tab` cycles within the trap.
- **Loading:** skeleton mirroring the section geometry; if seeded from the list
  cache (§5.4), sections 1–4 render immediately and only 6–7 skeleton.
- **Not found (404):** `CircleHelp` 24, *"Verdict not found"*, body *"It may have
  been pruned by retention."*, `Back to console` button.
- **Mobile <768px:** becomes a **bottom sheet** — full width, `max-height: 92vh`,
  `--radius-lg` top corners, enters with `translateY 100%→0` `--ease-spring`,
  drag-to-dismiss below 120px threshold, and a 36px grab handle.

### 7.5 Global elements

- **Error banner** — below header, full width, `--color-error-bg`, 1px
  `--color-error-border`, `TriangleAlert` 16, message with endpoint name,
  `Retry now` ghost button. Slides down 200ms `--ease-out`.
- **Shortcuts modal** (`?`) — 480px, two-column key/description list grouped by
  Navigation / Feed / Drawer. Modal animation per §3.2.
- **Toasts** — bottom-right, max 3 stacked, 4s auto-dismiss (errors 8s),
  hover pauses the timer. Only three ever fire: `Reconnected`, `Copied`,
  `Link copied`.
- **404 route** — centered, `CircleHelp` 24, *"Page not found"*,
  `Back to console`.

---

## 8. Component library

Every component lives in `src/components/<Name>/`. Each defines its own `.module.css`.
All accept `className` and forward refs. **No component may hardcode a color,
radius, duration, or spacing literal** — tokens only.

Shared states, unless overridden: `default` · `hover` · `active` · `focus-visible`
(always `--focus-ring`) · `disabled` (`opacity: 0.5`, `cursor: not-allowed`,
no hover) · `loading`.

| # | Component | Variants | Key behavior |
|---|---|---|---|
| 8.1 | **Button** | `primary` (accent fill, white text) · `secondary` (surface, border) · `ghost` (transparent, hover `--color-surface-subtle`) · `danger` (error fill). Sizes `sm` 28px / `md` 32px / `lg` 40px. | Press scale 0.975 (§3.2). `loading` swaps content for spinner at fixed width — the button never resizes. Icon-only requires `aria-label`. |
| 8.2 | **IconButton** | Same variants, square, sizes 28/32/40, radius `md`. | Always has a tooltip and an `aria-label`. |
| 8.3 | **Input** | `default` · `search` (leading icon + clear button) · `error`. Height 32/40. | Border → `--color-border-strong` on hover, `--color-accent` + focus ring on focus. Error shows message below in `--text-xs` error text with `role="alert"`. |
| 8.4 | **Card** | `default` · `interactive` (hover lift) · `inset` (no shadow, subtle bg) | Radius `lg`, border, `--shadow-xs`. Interactive cards are `<button>` or `<a>`, never a div with onClick. |
| 8.5 | **Badge** | `neutral` · `success` · `warning` · `info` · `error` · `accent` · `outline`. Sizes `sm` (18px, `--text-micro`) / `md` (22px, `--text-xs`). | Radius `full`. Optional leading dot (6px) or icon (14). State change crossfades (§3.2). |
| 8.6 | **StatusDot** | Sizes 6/8/10/12. States map to §2.3 `dot` colors. | `pulse` prop adds the live pulse. `role="status"` with an `aria-label` naming the state — the dot is never the only signal. |
| 8.7 | **StateBadge** | Composed: `StatusDot` + uppercase state word + optional count. | The single component that renders a `VerdictState`. Nothing else maps state→color; this is the choke point that guarantees consistency. |
| 8.8 | **SigmaMeter** | `hero` (8px bar, `--text-mono-lg`) · `compact` (6px bar, `--text-mono`) | Fixed 0–6σ domain, 3σ threshold tick, clamp with a `»` glyph past 6σ. Animates per §3.2. `role="meter"` with `aria-valuenow/min/max/text`. |
| 8.9 | **MetricChip** | `default` · `error` | Uppercase micro label above a mono value. Value count-ups. Optional tooltip. |
| 8.10 | **Tooltip** | `top` · `bottom` · `left` · `right` (auto-flip at viewport edge) | 400/80ms delays. Max-width 260px, `--text-xs`, `--color-text` on `--color-surface-raised`, `--shadow-lg`, 6px arrow. Keyboard-focus triggers it. Never contains interactive content. |
| 8.11 | **Dropdown** | `select` (single) · `multi` | Radix-free custom listbox: `role="listbox"`, `aria-activedescendant`, type-ahead, arrow navigation, `Home`/`End`, `Esc` closes and restores focus. Selected item shows a `Check` 14. |
| 8.12 | **ToggleChip** | `off` (surface + border) · `on` (state-tinted bg + border + dot) | 28px, radius `full`. `aria-pressed`. 140ms color transition. |
| 8.13 | **Tabs** | `underline` only | `layoutId` sliding indicator (§3.2). Arrow-key roving tabindex, `role="tablist"`. |
| 8.14 | **ProgressBar** | `determinate` · `indeterminate` | 6px, radius `full`, track `--color-surface-inset`, fill `--color-accent`. Determinate width transitions 300ms `--ease-out`. Indeterminate = 40% bar sweeping 1400ms linear. `role="progressbar"` with values. |
| 8.15 | **Skeleton** | `text` · `block` · `circle` | `--color-surface-inset` with shimmer. Composed into `HeroCardSkeleton`, `FeedRowSkeleton`, `ScopeCardSkeleton`, `DrawerSkeleton`, each mirroring the real geometry so nothing shifts on load. |
| 8.16 | **EmptyState** | `default` · `inline` (compact, no icon circle) | Icon 24 in a 48px `--color-surface-subtle` circle, title `--text-h3`, body `--text-sm` secondary, optional action. Max-width 380px, centered, `padding: 48px 24px`. |
| 8.17 | **AlertCallout** | `info` · `warning` · `error` · `neutral` | Icon 16 + title + body. State-tinted bg and border, radius `md`, `padding: 12px 14px`. Used for caveats, falsifier, blind spots. |
| 8.18 | **Drawer** | `right` (desktop) · `bottom` (mobile) | Focus trap, scroll lock, `Esc` close, scrim click close. `role="dialog"` `aria-modal="true"` `aria-labelledby`. Animations §3.2. |
| 8.19 | **Modal** | `sm` 400 · `md` 480 · `lg` 640 | Same a11y contract as Drawer. Centered, max-height `85vh`, body scrolls. |
| 8.20 | **JsonViewer** | `collapsed` (depth 1) · `expanded` | Mono, syntax-tinted: keys `--color-text`, strings `--chart-2`, numbers `--chart-1`, booleans/null `--chart-5`. Collapsible nodes with `ChevronDown`. Copy-path on row hover. **Read-only, no editing.** Virtualized past 200 rows. |
| 8.21 | **CodeBlock** | `default` · `withCopy` | `--color-surface-inset`, radius `md`, `padding: 12px`, mono, horizontal scroll, no wrap, no syntax highlighting (all our code snippets are one-liners). |
| 8.22 | **Toast** | `success` · `error` · `info` | Bottom-right stack, `--shadow-lg`, radius `md`, 320px. Timer, hover-pause, `X`. `role="status"` (`alert` for errors). |
| 8.23 | **Timeline** | `vertical` only | Used in the drawer's Timing section: dot + connector line + label/value rows. Connector `--color-border`, dots 8px state-colored. |
| 8.24 | **Sparkline** | see §9 | — |
| 8.25 | **CopyButton** | `icon` · `inline` (text + icon) | Copy→Check swap for 1200ms (§3.2). Announces "Copied" to a live region. Falls back to a hidden textarea + `execCommand` when the clipboard API is unavailable. |
| 8.26 | **RelativeTime** | — | Renders `14s ago`, ticks every 1s under 60s then every 60s. `<time dateTime>` with absolute ISO in `title`. Pauses ticking when the tab is hidden. |
| 8.27 | **TruncatedId** | — | First 6 chars of an id + `…`, mono, click-to-copy, full value in tooltip. |
| 8.28 | **KeyHint** | — | Renders a `<kbd>`: 20px, `--color-surface-inset`, 1px border, radius `sm`, `--text-micro` mono. |
| 8.29 | **PageHeader** | — | Title `--text-h1` + optional subtitle + right-slot actions. `margin-bottom: 24px`. |
| 8.30 | **AppHeader** | — | §4.3. Sticky, `z-index: 40`. |

---

## 9. Charts

Two chart forms exist. Both are hand-authored SVG. **No zoom, no pan, no
brushing** — the dataset is ≤50 discrete events, and zoom on sparse event data is
a solved-problem-that-isn't.

### 9.1 SigmaMeter (bar) — §8.8
Covered above. It is a chart in function; treat its spec as binding.

### 9.2 VerdictSparkline

**Where:** Console, between hero card and feed, full width, height 72px.
**Data:** the filtered verdict list, oldest→newest, from `/api/verdicts`.

- **Type:** dual-series line with point markers. Series 1 `behavior_sigma`
  (`--chart-1`), series 2 `cost_sigma` (`--chart-2`). Stroke 1.5px, round caps.
- **Domain:** x = verdict index (evenly spaced — **not** time-scaled; verdict
  cadence is irregular and time-scaling would make the demo's dense moments
  invisible). y = fixed `-1` to `6`, clamped.
- **Threshold:** horizontal dashed line at `3σ` in `--chart-3`, 1px, `4 3` dash,
  with a band fill `rgba(245,158,11,0.08)` from 3 to 6.
- **Null handling:** a null sigma breaks the line (gap), never renders as 0.
- **Markers:** 3px circles at each point, filled with the series color; points
  whose verdict state is `CHANGED` render as 5px with a 2px white ring.
- **Draw-in:** §3.2 chart animation, once per mount only.
- **Hover:** a 1px vertical crosshair in `--color-border-strong` snaps to the
  nearest index; both point markers grow to 6px over 100ms; tooltip
  (`--shadow-lg`, 240px) shows time, state badge, both sigma values, and `n`.
  Pointer tracking is throttled with `requestAnimationFrame`.
- **Click:** opens that verdict's drawer.
- **Legend:** inline above-right, two 8px dashes with labels in `--text-micro`.
  Clicking a legend item toggles that series (opacity 1→0.15, 140ms) — local
  state, not persisted.
- **Empty (<2 verdicts):** the sparkline is not rendered at all; no placeholder.
- **Reduced motion:** no draw-in, no marker growth; crosshair and tooltip still work.
- **A11y:** `role="img"` with an `aria-label` summarizing range and latest values,
  plus a visually-hidden `<table>` of the underlying points.

---

## 10. Responsive

| Breakpoint | Range | Layout |
|---|---|---|
| `mobile` | <768px | Single column, 16px gutters. Two-line feed rows. Bottom-sheet drawer. Icon-only tabs. Health chips in a 2-col grid. Sparkline height 56px. |
| `tablet` | 768–1023px | Single column, 24px gutters, container fluid. Hero meters stack. Feed drops the sigma column. Scopes 1 column. |
| `laptop` | 1024–1279px | Container fluid to 1120px. Full feed columns. Scopes 2 columns. Drawer 480px. |
| `desktop` | ≥1280px | Container fixed 1120px, centered. Drawer 560px. Everything as specified. |

Breakpoints are CSS custom media queries in `src/styles/breakpoints.css`. **No
JS-driven layout switching** except the drawer↔bottom-sheet swap, which uses a
single `useMediaQuery('(max-width: 767px)')` hook.

Touch targets ≥44px on mobile (feed rows are 2-line/56px there). Hover-only
affordances (row hover background, chevron tint) are disabled under
`(hover: none)`; the chevron is always visible instead.

---

## 11. Accessibility

**Target: WCAG 2.1 AA.** Non-negotiable items:

- **Contrast:** every text/background pair in §2 is ≥4.5:1 for body and ≥3:1 for
  ≥18px. Status `text` colors were chosen against their own `bg` tokens and must
  be used as a pair. The 3σ threshold tick and chart series are ≥3:1 against
  `--color-surface`.
- **Never color-only.** Every state is color + icon + text. `StatusDot` always
  carries an `aria-label`. Chart series are distinguished by marker shape as well
  as color (behavior = circle, cost = square).
- **Focus:** `--focus-ring` (white inner + accent outer) on every interactive
  element via `:focus-visible`. Never `outline: none` without a replacement.
  Focus order follows DOM order; no positive `tabindex`.
- **Landmarks:** `<header>`, `<main>`, `<nav>`; the feed is a `<section>` with
  `aria-label="Verdict feed"`.
- **Live regions:** one `aria-live="polite"` region announces new verdicts
  (`"New verdict: CHANGED, behavior, v2 versus v1"`) and one
  `aria-live="assertive"` for connection loss/recovery. **Throttled to one
  announcement per 3 seconds** — a 2s poll would otherwise flood a screen reader.
- **Feed semantics:** `role="list"` / `role="listitem"`; expandable rows are
  `<button aria-expanded>` controlling a region by `aria-controls`.
- **Dialogs:** focus trap, `aria-modal`, labelled by title, focus restored on
  close, background `aria-hidden`.
- **Skip link:** first tab stop, "Skip to content", visually hidden until focused.
- **Reduced motion:** §3.3, implemented twice (hook + media query).
- **Zoom:** usable at 200% with no horizontal scroll at 1280px.
- **Screen-reader text:** a `.visually-hidden` utility for the sparkline data
  table and icon-only control labels.

---

## 12. Folder structure — frozen

```
console/                              # frontend workspace root (repo-level)
  index.html
  vite.config.ts
  tsconfig.json
  biome.json
  package.json
  playwright.config.ts
  public/
    fonts/  InterVariable.woff2  JetBrainsMono-Regular.woff2  JetBrainsMono-Medium.woff2
    favicon.svg
  src/
    main.tsx
    App.tsx
    router.tsx
    styles/
      reset.css  tokens.css  breakpoints.css  typography.css  utilities.css  global.css
    lib/
      api/
        client.ts          # fetch wrapper, typed errors, timeout
        endpoints.ts       # the four URLs, nothing else
        types.ts           # Verdict, Exemplar, Scope, Health, enums
      query/
        queryClient.ts  keys.ts
      format/
        sigma.ts  currency.ts  duration.ts  relativeTime.ts  truncate.ts  number.ts
      utils/
        cn.ts  clamp.ts  storage.ts  throttle.ts  focusTrap.ts  scrollLock.ts
      constants/
        states.ts          # VerdictState -> {label, icon, colorVar, order}
        shortcuts.ts  chart.ts
    hooks/
      useVerdicts.ts  useVerdict.ts  useScopes.ts  useHealth.ts
      useVerdictFilters.ts  usePolling.ts  useVisibility.ts  useOnline.ts
      useReducedMotion.ts  useMediaQuery.ts  useHotkeys.ts  useRovingFocus.ts
      useLocalStorage.ts  useCountUp.ts  useLiveAnnouncer.ts  useCopyToClipboard.ts
    components/                       # one folder each, per §8
      Button/ IconButton/ Input/ Card/ Badge/ StatusDot/ StateBadge/ SigmaMeter/
      MetricChip/ Tooltip/ Dropdown/ ToggleChip/ Tabs/ ProgressBar/ Skeleton/
      EmptyState/ AlertCallout/ Drawer/ Modal/ JsonViewer/ CodeBlock/ Toast/
      Timeline/ Sparkline/ CopyButton/ RelativeTime/ TruncatedId/ KeyHint/
      PageHeader/ AppHeader/
    features/
      verdicts/
        components/
          HeroVerdictCard/ HeroCardSkeleton/ VerdictFeed/ FeedRow/ FeedRowSkeleton/
          FeedFilters/ FeedToolbar/ ExemplarRow/ ExemplarCard/ VerdictSparkline/
          NewVerdictsPill/
        selectors.ts  useFeedKeyboard.ts
      scopes/
        components/ ScopeCard/ ScopeCardSkeleton/ SignalTable/
      health/
        components/ HealthStrip/ LivePulseDot/
      drawer/
        components/ VerdictDrawer/ DrawerHeader/ DrawerSection/ DrawerSkeleton/
                    DrawerNotFound/
      shortcuts/
        components/ ShortcutsModal/
    screens/
      ConsoleScreen/  ScopesScreen/  AboutScreen/  NotFoundScreen/
    providers/
      QueryProvider.tsx  ToastProvider.tsx  MotionProvider.tsx  AnnouncerProvider.tsx
    test/
      setup.ts  fixtures/verdicts.ts  fixtures/scopes.ts  fixtures/health.ts
      msw/handlers.ts  msw/server.ts
  e2e/
    console.spec.ts  drawer.spec.ts
```

Build output goes to `../vitals/console/static/` (configured in `vite.config.ts`)
and **is committed**.

---

## 13. Formatting rules (freeze these — they are where UIs get inconsistent)

| Value | Rule | Example |
|---|---|---|
| Sigma | Always signed, 1 decimal, `σ` suffix. `\|z\| < 1.0` → the word `flat` beside it. | `+4.2σ`, `−0.3σ`, `+0.4σ flat` |
| Sigma sign | Use the **minus sign** `−` (U+2212), not a hyphen. | `−1.2σ` |
| Cost | 4 significant decimals under $1, 2 above. Always `$`. | `$0.0042`, `$1.28` |
| Ratio | 1 decimal + `×`. | `51.0×` |
| Counts | Thousands separator, mono, tabular. | `1,240` |
| Duration | `90s` under 120s; `2m 30s` under 1h; `1h 04m` above. | `90s` |
| Relative time | `now` <5s · `14s ago` · `3m ago` · `2h ago` · then absolute `Jul 23, 14:32`. | |
| Absolute time | `HH:mm:ss` local in the UI; full ISO 8601 in `title` attributes. | `14:32:07` |
| IDs | First 6 chars + `…`, mono, copyable. Full value in tooltip and in the drawer. | `4f2a91…` |
| Version | Verbatim from the API, mono, never prefixed or normalized. | `v2` |
| State word | UPPERCASE in badges and the hero; Sentence case in prose. | `CHANGED` |
| Null sigma | Render `—` in `--color-text-tertiary`. **Never `0.0σ`.** | `—` |
| Excerpt | Collapse whitespace, truncate at 240 chars with `…`, wrap in typographic quotes. | `"Sure! Here's a fun fact…"` |

`Verdict.sentence` is rendered **verbatim**, never re-formatted by these rules —
the backend already formatted it (backend §7).

---

## 14. Error handling summary

| Failure | UI |
|---|---|
| 1st/2nd poll failure | Live dot grey, `Reconnecting…`, last-good data intact, no toast |
| 3rd consecutive failure | Error banner + data dimmed to 60% + `Retry now` |
| Recovery | Banner exits, `Reconnected` toast, dot resumes |
| `404` verdict detail | Drawer not-found state, no retry |
| `5xx` any endpoint | Same as poll failure path, banner names the endpoint |
| Malformed JSON | Treated as a `500`; logged to console with the raw body |
| Missing optional field | Render `—`; **never crash, never `undefined`** |
| `localStorage` unavailable | Silent fallback to defaults |
| Offline | `Offline` pill, polling suspended, cache stays interactive |
| Render crash | Route-level `ErrorBoundary`: `TriangleAlert`, "Something broke in the console", `Reload` button, and the stack in a `CodeBlock` (this is a developer tool — show the stack) |

---

## 15. Testing

- **Unit (Vitest):** every `lib/format` function against the §13 table; selectors;
  `useVerdictFilters` URL round-trip; `states.ts` completeness (every enum value
  has a mapping).
- **Component (RTL):** `StateBadge` renders all four states; `SigmaMeter` clamps
  and sets ARIA values; `Drawer` traps focus and restores it; `FeedRow` expands on
  `Enter`; `EmptyState` variants; reduced-motion gating.
- **Integration (RTL + MSW):** console loads → hero + feed render; poll updates
  prepend a row without remounting existing rows; 3 failures → banner; filters
  update the URL and the list; `⌘K` focuses search.
- **E2E (Playwright), two flows only:**
  `console.spec.ts` — load, assert hero state, filter to `changed`, assert count.
  `drawer.spec.ts` — click a feed row, drawer opens at `/v/:id`, `Esc` closes,
  focus returns to the row, hard-refresh on `/v/:id` renders (proves §0.2).
- **A11y:** `axe-core` on all four routes in CI; zero violations is a merge gate.
- **Visual:** none. Snapshot-testing a UI this young costs more than it catches.

---

## 16. CI gates

1. `biome ci` clean.
2. `tsc --noEmit` clean, `strict: true`.
3. `vitest run` green.
4. **Bundle budget:** JS ≤ 250 KB gz, CSS ≤ 30 KB gz — fail the build past it.
5. `playwright test` green.
6. `axe` zero violations.
7. **Token lint:** a script greps `src/**/*.module.css` for raw hex, `px` radii,
   and `ms` literals outside `tokens.css`; any hit fails. This is what actually
   keeps the design system frozen.

---

## 17. Commit plan — 28 commits

Each commit is independently reviewable and leaves the app running. Milestones are
sequential; an agent may complete one and stop.

### M1 — Foundation (4 commits)

**Objective:** a running Vite app served by the Python console, with the design
system in place and nothing else.

| # | Commit | Files |
|---|---|---|
| 1 | `scaffold vite react typescript console workspace` | `console/` root configs, `index.html`, `main.tsx`, `App.tsx`, build output wired to `vitals/console/static/` |
| 2 | `add design tokens and global styles` | `styles/*` — every token from §2 |
| 3 | `add self-hosted fonts and typography scale` | `public/fonts/`, `typography.css`, `utilities.css` |
| 4 | `add spa history fallback to console server` | `vitals/console/server.py` (§0.2) |

**Acceptance:** `npm run build` emits to `vitals/console/static/`; `vitals run`
serves a styled blank page; `/scopes` renders on hard refresh; token lint passes.

### M2 — API & state layer (3 commits)

**Objective:** typed data flowing, with polling and error semantics, no UI.

| # | Commit | Files |
|---|---|---|
| 5 | `add typed api client and endpoint definitions` | `lib/api/*` |
| 6 | `add query client, keys, and the four data hooks` | `lib/query/*`, `hooks/useVerdicts\|useVerdict\|useScopes\|useHealth` |
| 7 | `add polling, visibility, and online lifecycle hooks` | `hooks/usePolling\|useVisibility\|useOnline`, MSW handlers + fixtures |

**Acceptance:** unit tests prove poll intervals, pause-on-hidden, backoff, and the
3-failure threshold. `staleTime: Infinity` verified for verdict detail.

### M3 — Primitives (5 commits)

**Objective:** the generic component library, verified in isolation.

| # | Commit | Files |
|---|---|---|
| 8 | `add button, icon button, and input primitives` | 8.1–8.3 |
| 9 | `add card, badge, status dot, and state badge` | 8.4–8.7 |
| 10 | `add tooltip, dropdown, toggle chip, and tabs` | 8.10–8.13 |
| 11 | `add skeleton, empty state, alert callout, progress bar` | 8.14–8.17 |
| 12 | `add toast, modal, and drawer with focus management` | 8.18, 8.19, 8.22, `ToastProvider`, `focusTrap`, `scrollLock` |

**Acceptance:** each component renders all variants and states; focus trap and
restore tested; reduced-motion gating tested; zero raw hex in any module CSS.

### M4 — Formatting & display primitives (3 commits)

| # | Commit | Files |
|---|---|---|
| 13 | `add value formatters and number count-up` | `lib/format/*`, `hooks/useCountUp` |
| 14 | `add sigma meter, metric chip, relative time, truncated id` | 8.8, 8.9, 8.26, 8.27 |
| 15 | `add copy button, code block, json viewer, key hint` | 8.20, 8.21, 8.25, 8.28 |

**Acceptance:** every rule in §13 has a passing unit test, including the `−`
minus sign, `—` for null sigma, and `flat` below 1σ.

### M5 — Console screen (6 commits)

**Objective:** the product's main screen, complete.

| # | Commit | Files |
|---|---|---|
| 16 | `add app header, routing, and screen shells` | `router.tsx`, 8.29, 8.30, `screens/*` shells |
| 17 | `add hero verdict card with sigma meters and evidence` | `features/verdicts/components/HeroVerdictCard/`, `ExemplarRow/` |
| 18 | `add hero warming, inconclusive, empty, and error variants` | same + `HeroCardSkeleton/` |
| 19 | `add verdict feed with rows, expansion, and skeletons` | `VerdictFeed/`, `FeedRow/`, `FeedRowSkeleton/` |
| 20 | `add feed filters, sort, search, and url state` | `FeedFilters/`, `FeedToolbar/`, `useVerdictFilters`, `selectors.ts` |
| 21 | `add health strip with live pulse and metric chips` | `features/health/*` |

**Acceptance:** console renders against MSW fixtures for all four states; filters
round-trip through the URL; new verdicts animate in without remounting existing
rows; `STEADY` with an empty feed still shows a live health strip.

### M6 — Drawer & detail (3 commits)

| # | Commit | Files |
|---|---|---|
| 22 | `add verdict drawer route with sections and json viewer` | `features/drawer/*`, route `/v/:id` |
| 23 | `add drawer loading, not-found, prev/next, and cache seeding` | same + `DrawerSkeleton/`, `DrawerNotFound/` |
| 24 | `add mobile bottom sheet variant with drag dismiss` | `Drawer/` bottom variant, `useMediaQuery` |

**Acceptance:** `/v/:id` deep-links and survives refresh; focus returns to the
originating row on close; seeded cache renders sections 1–4 with no skeleton
flash; bottom sheet dismisses past 120px.

### M7 — Chart, scopes, about (3 commits)

| # | Commit | Files |
|---|---|---|
| 25 | `add verdict sparkline with crosshair and legend` | `components/Sparkline/`, `VerdictSparkline/` |
| 26 | `add scopes screen with signal table and progress` | `features/scopes/*`, `ScopesScreen/` |
| 27 | `add about screen with blind spots and shortcuts modal` | `AboutScreen/`, `features/shortcuts/*` |

**Acceptance:** sparkline hides below 2 verdicts, gaps on nulls, crosshair snaps
to nearest index, legend toggles series; scope cards show warming progress; `?`
opens shortcuts.

### M8 — Polish & hardening (1 commit)

| # | Commit | Files |
|---|---|---|
| 28 | `add keyboard shortcuts, live announcer, error boundary, and ci gates` | `useHotkeys`, `useFeedKeyboard`, `AnnouncerProvider`, `ErrorBoundary`, `e2e/*`, bundle + axe + token-lint CI steps |

**Acceptance:** every §7 keyboard shortcut works; announcements throttle to 1 per
3s; route crashes show the boundary with a stack; all seven §16 gates green.

---

## 18. Definition of done

1. All 28 commits landed; all §16 gates green.
2. `vitals run` with no Node installed serves the full console at `:8787`.
3. All four verdict states render correctly from live backend data.
4. The hero card always shows a **median exemplar beside the worst** — the one
   product rule the UI is responsible for enforcing (backend §9, critique C5).
5. `falsifier` and `caveats` are visible without interaction in every state that
   has them.
6. The console is fully usable by keyboard alone, and readable by a screen reader
   without visual context.
7. `prefers-reduced-motion` removes all transform and count-up animation.
8. Killing the backend mid-session degrades to `Reconnecting…` → banner → recovery
   without losing the last-good view.
9. The health strip footer links to `/about`, and `/about` lists the four known
   blind spots.
