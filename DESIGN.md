# Bhopal Safety Intelligence — Style Reference

**Direction: civic instrument.** This is a dashboard application, not a website. A calm public record, not a threat console. Apple's Human Interface Guidelines supply the clarity, system type, materials and restraint. Claude's design language supplies warm paper neutrals, a single clay accent and a serif voice for moments of reading.

**Anchor:** the dot-lattice sphere in Analytics. It is the only 3D data view.

Implementation: tokens and components in `static/design-system.css`, motion and 3D in `static/design-motion.js`. `dashboard.py` injects both. Regenerate `index.html` with `scripts/export_official_html.py`.

## Tokens — Colors

Values are RGB triples on `:root` (light) and `html.dark` (dark), used as `rgb(var(--token) / alpha)`. Tailwind's Material role names are mapped onto them in `dashboard.py`, so utility classes follow the theme.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--canvas` | 247 245 240 | 20 19 17 | Page background |
| `--surface` | 255 255 255 | 29 27 24 | Primary cards |
| `--surface-2` | 241 238 231 | 38 36 32 | Nested wells, inputs, inactive chips |
| `--surface-3` | 231 227 218 | 50 47 42 | Hover and pressed fills |
| `--ink` | 31 29 25 | 242 239 232 | Primary text |
| `--ink-2` | 94 89 79 | 184 178 167 | Secondary text |
| `--ink-3` | 111 106 95 | 154 148 136 | Captions; never below 11px |
| `--hairline` | 31 29 25 | 242 239 232 | Borders, at 12% alpha |
| `--accent` | 180 83 47 | 224 138 99 | Selected state, links, the one primary action |
| `--on-accent` | 255 255 255 | 31 18 9 | Text on accent fills |
| `--positive` | 30 120 84 | 102 200 155 | Verified or healthy status |
| `--danger` | 196 51 43 | 196 51 43 | Dial 112 only |

Map category colors (property, assault, women's safety, vandalism, facility) are data colors. Do not reuse them for interface chrome.

## Tokens — Typography

- Text: `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif` (`--font-text`).
- Numbers in tables, stats and metadata use `font-variant-numeric: tabular-nums`. Do not use a monospace font for prose or labels.
- Icons remain Material Symbols.

| Style | Size / line | Weight |
|---|---|---|
| View title | 18px / 1.25 | 600 |
| KPI value | 24px / 1.15 | 600 tabular |
| Panel title | 13px / 1.3 | 600 |
| Body | 13px / 1.45 | 400 |
| Caption | 12px / 1.45 | 400 |

## Tokens — Spacing & Shapes

- Spacing steps: 4, 8, 12, 16, 24, 32, 48.
- Radii: `--r-card` 12px, `--r-well` 8px, full for chips and buttons.
- Borders: 1px hairline at 12% alpha. A card has a border or a shadow at rest, never a colored glow.
- Shadow: `--shadow-1` for cards; `--shadow-float` for floating layers such as tooltips and popups.
- Material: the sticky header uses blur(20px) over 72% canvas. Blur is for layers above content only.

## Motion

| Token | Value | Use |
|---|---|---|
| `--ease-spring` | cubic-bezier(.22, 1, .36, 1) | Entrances, bars, panes |
| `--t-fast` | 160ms | Hover, press |
| `--t-slow` | 620ms | Scroll reveal |

- Views crossfade when switched. KPI values animate when filters change them.
- KPI and analytics cards tilt at most 2.5° under a fine pointer.
- Controls compress to 97% while pressed.
- The sphere has inertia after a drag and stops rendering when off screen.
- Under `prefers-reduced-motion`: no tilt, count-up or spin. The sphere renders one still frame and remains draggable.
- Never apply transforms to the map or its ancestors while it is interactive.

## Components

- **Rail:** 208px left navigation on desktop, six-item bottom bar on phones. Views without data are marked "No data".
- **Top bar:** view title, search, active area, Dial 112, theme.
- **KPI strip:** exactly four cards, each with a value and one line of context, reading the same selection as the map.
- **Publication feed:** newest first, with Show on map and the official source.
- **Status bar:** one visible line of source freshness at the bottom of the shell.
- **Card:** `--surface`, hairline, `--r-card`. Nested content uses `--surface-2` without its own shadow.
- **Filter chip:** full radius and a minimum 32px height (44px on touch). The checkbox renders as a dot; selected chips use an accent tint. Keep the native input for keyboard and assistive technology.
- **Primary button:** `--accent` fill. One per view.
- **Emergency link:** `--danger` solid, no glow. Always visible in the header.
- **Bars:** 8px track, accent fill, animated width.
- **Focus:** 2px accent outline at 2px offset on every interactive element.

## Layout

- At 1024px and wider the shell fills one viewport: rail, then top bar, KPI strip, workspace and status bar. Only panels scroll, never the page.
- Overview workspace: filters 264px, map fills the remainder, feed 296px.
- Selecting a category or locality in any panel filters the map, KPIs, charts and records together.
- Below 1024px the content stacks and scrolls: a swipeable KPI row, filters toggle, map, report types, then a three-item feed that links to Records.
- On phones, filters open as a sheet above the tab bar so the map keeps its place. Records become labeled cards. Long legal evidence starts collapsed.
- Every phone control is at least 44px tall, and form fields use 16px text so iOS does not zoom on focus. Coverage caveats are never clipped.
- Breakpoints follow Tailwind: 640, 768, 1024, 1280. No horizontal page scroll at 390px.
- Page zoom must stay enabled.
- The map's full-screen button expands the map within the page. Native fullscreen is blocked in the Streamlit embed and on iPhones.
- Under Streamlit, `app.py` reserves a 40px bottom strip with the "Built with Streamlit" mark. Keep its right 170px clear for the Community Cloud badge, and never overlap it or hide the badge.

## Do's and Don'ts

- Do label coverage limits next to the figures they qualify.
- Do use "publications" for counts. A publication count is not an incident count.
- Do use the accent for selection and action only.
- Don't show AI, accuracy or risk claims without validated data behind them.
- Don't plot or imply incident coordinates. Sphere positions are layout only and must say so.
- Don't add gradients, neon glows, or a second accent.
- Don't animate anything that does not explain state, hierarchy or direct manipulation.

## Agent Prompt Guide

Read this file before changing UI. Change `static/design-system.css` and the token map in `dashboard.py` rather than adding one-off colors in `ui_builder.py`. Keep every value traceable to a token. Check light and dark mode, 390px width, keyboard focus and reduced motion. Regenerate `index.html` and run `tests/browser_official_data.py`.

## Open questions

- `ui_builder.py` still carries its legacy Material classes; the design system overrides them at the CSS layer. A full markup migration would remove the need for `!important`.
- The Hotspots and AI Risk views stay in navigation with a "No data" tag. Decide whether to remove them until data exists.
- Theme defaults to dark unless the visitor chose otherwise. HIG practice is to follow the system setting.
- Add a compiled Tailwind build. The CDN build is not intended for production.
