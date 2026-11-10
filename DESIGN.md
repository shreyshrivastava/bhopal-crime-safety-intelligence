# Bhopal Safety Intelligence style reference

This is a dashboard application. The map fills the screen and every panel floats over it as glass, similar to Apple Maps. The layout borrows common dashboard patterns seen on shadcn/ui and 21st.dev; no code was copied from them.


Implementation: tokens and components in `static/design-system.css`, motion and 3D in `static/design-motion.js`. `dashboard.py` injects both. Regenerate `index.html` with `scripts/export_official_html.py`.

## Colors

Values are RGB triples on `:root` (light) and `html.dark` (dark), used as `rgb(var(--token) / alpha)`. Tailwind's Material role names are mapped onto them in `dashboard.py`, so utility classes follow the theme.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--canvas` | 242 242 247 | 16 14 15 | Behind the map while it loads |
| `--glass` | white at 76% | 26 22 24 at 58% | Every floating panel |
| `--glass-edge` | white | white | Panel rim, at 16% and 20% alpha |
| `--ink` | 29 29 31 | 245 245 247 | Primary text |
| `--ink-2` | 82 82 88 | 190 190 196 | Secondary text on glass |
| `--hairline` | 29 29 31 | 245 245 247 | Dividers and control fills, at 6 to 14% alpha |
| `--accent` | 190 24 44 | 255 118 118 | Selected state, links, the one primary action |
| `--on-accent` | 255 255 255 | 42 5 8 | Text on accent fills |
| `--warning` | 170 90 0 | 255 179 64 | Stale data |
| `--danger` | 215 40 38 | 215 40 38 | Dial 112 only |

Red is the only interface color: selected states, links, KPI tints and primary actions (`--cta`). Do not use blue in interface elements. The map stays untinted, and map markers keep their own colors.

Map category colors (property, assault, women's safety, vandalism, facility) are data colors. Use them wherever a report category appears, including charts, chips and feed dots.

## Typography

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

## Spacing and shapes

- Spacing steps: 4, 8, 12, 16, 24, 32, 48.
- Radii: `--r-card` 20px, `--r-well` 12px, full for chips and buttons.
- Borders: 1px hairline at 12% alpha. A card has a border or a shadow at rest, never a colored glow.
- Shadow: `--shadow-1` for cards; `--shadow-float` for floating layers such as tooltips and popups.
- Glass recipe: `--glass` with blur(28px) saturate(180%), a 1px rim and a top inner highlight. Use it for layers above the map only. Nested controls use hairline fills without blur. Glass turns nearly opaque when transparency is reduced or blur is unsupported.

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

- **Rail:** floating 84px glass rail with icon over label on desktop, floating six-item tab bar on phones. Views without data are marked "No data".
- **Top bar:** view title, search, active area, Dial 112, theme.
- **KPI strip:** exactly four cards, each with a value and one line of context, reading the same selection as the map.
- **Publication feed:** newest first, with Show on map and the official source.
- **Status bar:** one visible line of source freshness at the bottom of the shell.
- **Card:** `--surface`, hairline, `--r-card`. Nested content uses `--surface-2` without its own shadow.
- **Filter chip:** full radius and a minimum 32px height (44px on touch). The checkbox renders as a dot; selected chips use an accent tint. Keep the native input for keyboard and assistive technology.
- **Primary button:** `--accent` fill. One per view.
- **Emergency link:** `--danger` solid, no glow. Always visible in the header.
- **Map legend:** lists every category with its live count, including categories with nothing to plot. Reports without a location are named under the map, never given a guessed pin.
- **Bars:** 8px track, accent fill, animated width.
- **Focus:** 2px accent outline at 2px offset on every interactive element.

## Layout

- At 1024px and wider the map fills the viewport. An 84px glass rail floats left, with top bar, KPI strip, filters 272px, feed 304px and status bar floating over the map. Only panels scroll.
- Map fits use padding measured from the panels, so markers stay in the clear area.
- Other views float one glass sheet over the map.
- Map popups pan and cap their height to stay inside the clear area.
- Selecting a category or locality in any panel filters the map, KPIs, charts and records together.
- Below 1024px the map stays fixed behind the page. Glass cards scroll over it, with a floating tab bar: a swipeable KPI row, filters toggle, map tools, then legend, report types and a three-item feed that links to Records.
- On phones, filters open as a sheet above the tab bar so the map keeps its place. Records become labeled cards. Long legal evidence starts collapsed.
- Every phone control is at least 44px tall, and form fields use 16px text so iOS does not zoom on focus. Coverage caveats are never clipped.
- Breakpoints follow Tailwind: 640, 768, 1024, 1280. No horizontal page scroll at 390px.
- Page zoom must stay enabled.
- The map's full-screen button hides the panels. Native fullscreen is blocked in the Streamlit embed and on iPhones.
- Under Streamlit, `app.py` reserves a 40px bottom strip with the "Built with Streamlit" mark. Keep its right 170px clear for the Community Cloud badge, and never overlap it or hide the badge.

## Rules

- Do label coverage limits next to the figures they qualify.
- Do use "publications" for counts. A publication count is not an incident count.
- Do use color to identify a category, a KPI or a view.
- Don't show AI, accuracy or risk claims without validated data behind them.
- Don't plot or imply incident coordinates. Sphere positions are layout only and must say so.
- Don't add neon glows. Don't put glass on glass with blur. Text sits on tints, never on saturated color.
- Animate only to show a change of state or respond to a drag or click.

## Agent Prompt Guide

Read this file before changing UI. Change `static/design-system.css` and the token map in `dashboard.py` rather than adding one-off colors in `ui_builder.py`. Keep every value traceable to a token. Check light and dark mode, 390px width, keyboard focus and reduced motion. Regenerate `index.html` and run `tests/browser_official_data.py`.

## Open questions

- `ui_builder.py` still carries its legacy Material classes; the design system overrides them at the CSS layer. A full markup migration would remove the need for `!important`.
- The Hotspots and AI Risk views stay in navigation with a "No data" tag. Decide whether to remove them until data exists.
- Theme defaults to dark unless the visitor chose otherwise. HIG practice is to follow the system setting.
- Add a compiled Tailwind build. The CDN build is not intended for production.
