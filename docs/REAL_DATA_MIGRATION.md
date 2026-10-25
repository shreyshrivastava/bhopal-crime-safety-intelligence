# Replace generated incidents with official data

The local production entrypoint now displays ten reviewed Bhopal Police publications. This is the first data migration stage, not a complete incident dataset. No deployment has been performed. The original Material Active interface and Leaflet map remain the production interface. Real public police-facility locations populate the station layer; synthetic models remain separate in `demo_app.py`.

## Findings that determine the plan

| Evidence | Finding | Implementation path |
| --- | --- | --- |
| `app.py` at the original main revision calls `generate_crime_dataset(520)` on each daily cache cycle | The displayed incident records and apparent daily updates are generated | Production now reads a checked-in official snapshot; fetch time and publication dates are displayed separately |
| Original `data/live_fetcher.py` generates a benchmark when a feed fails | A source failure could silently return generated observations | Replace that fallback; invalid or missing snapshots display data unavailable, failed refreshes preserve the previous snapshot |
| `ai/risk_model.py` augments sector summaries before randomly splitting them; its target is computed from the same features | Related synthetic samples can enter both partitions; this does not test future crime prediction | Disable this model in production; require explicit synthetic demo opt-in |
| `ui_builder.py` claims “80% accurate” | A fixed performance statement is not a measured real-world result | Remove that claim; production publishes no forecast accuracy |
| Original `data/public_records.py` contains named profiles with generic source URLs | Those URLs do not verify the specific profiles | Clear the registry until individual records are verified |
| Public Bhopal Police WordPress endpoint returns dated publications | Real public data can be fetched without private police-system access | Use HTTPS public GET requests for an explicit list of reviewed post IDs |

## Stage 1: official publications — implemented locally

Use [Bhopal Police](https://bhopal.mppolice.gov.in/) and its public WordPress publication endpoint. The snapshot contains post IDs 5223, 5017, 5406, 5380, 5375, 5360, 5347, 5340, 5337 and 5327. Each row links to its exact official page.

- Ten publications, April 16–October 10, 2026. IDs 5347 and 5360 are related reports about the Kolar Road burglary investigation. Other publications may also cover multiple cases: neither ten publications nor nine editorial groups is an incident count.
- Neutral short summaries are manually curated. Personal names, home addresses, vehicle identifiers and raw article bodies are excluded from the stored dataset.
- Store source ID, HTTPS URL, publication date, reporting unit, category, related-case group, retrieval time and response SHA-256. The hash records the fetched response; it is not a digital signature or independent verification of police claims.
- Keep incident coordinates null. Populate selected-event dates and times only from reviewed source evidence. Reporting unit names are not incident locations. No numeric severity, outcome, hour or precise incident location is filled in by the old normalizer.
- The default app retains the original Leaflet map, three basemaps, dark/light theme, five navigation panes, filters, CSV export, and 3D chart. The map shows 48 real public police facilities from the map embedded by Bhopal Police. The 3D chart and categorical bars show publication counts by reporting unit, not crime prevalence. Incident-based overlays await verified locations; their controls and tabs remain present with coverage explanations.
- No automatic collection job or live-feed claim. Refreshes are explicit, limited to the reviewed list. The UI recommends refreshing snapshots older than seven days. The app does not use the old synthetic cache.

## Stage 2: add official aggregate statistics

Use [MP SCRB Crime in MP](https://scrb.mppolice.gov.in/crime_in_mp.php) and the [NCRB Crime in India 2023 catalog](https://www.data.gov.in/catalog/crime-india-2023). The SCRB index links official annual reports including 2021; this is a verified source candidate, not an imported dataset in this change.

1. Download selected public official reports or catalog exports. Preserve the source URL, reporting year, original file checksum, table number, page and extraction date.
2. Extract Bhopal reporting-unit rows into a separate aggregate schema: year, reporting geography, unit definition, offense head, legal classification, count and source evidence.
3. Independently verify extracted numbers against the original table. Confirm totals and subcategories; avoid summing overlapping categories.
4. Reconcile Bhopal Urban/Rural and historical North/South definitions before comparing years. The [official commissionerate website](https://bhopal.mppolice.gov.in/) describes its December 2021 reorganization. Do not join changing reporting units by name alone.
5. Display historical aggregate charts separately from publication records. Never expand annual counts into individual incidents or distribute them across neighborhoods.
6. Preserve IPC/BNS definitions and document breaks in category comparability. Do not imply all legal offense categories are interchangeable.

Acceptance: every displayed statistic reconciles to a cited official table; missing years remain missing; charts clearly state geography, year and coverage. Public catalog availability does not establish that granular records exist.

## Stage 3: restore the incident map when the data supports it

Proceed only if a public official source supplies appropriate incident-level data. Do not bypass authentication or scrape restricted systems. A complete public geocoded Bhopal incident feed has not been established in this investigation.

The separate incident schema needs a stable case/event key, occurrence-date precision, publicly usable coarse location, offense category and source evidence. Distinguish press updates from unique incidents and publication dates from occurrence dates. Validate coordinates, dates, duplicates, missingness and district coverage before drawing points. Prefer public coarse locations; omit sensitive details.

Reconnect existing Leaflet filtering, CSV export and proximity functions only to verified incident locations. Show missing-location counts. Leave heatmaps and rankings unavailable when coverage is sparse or selected by press publication practices. Police-station proximity alone does not measure safety; current corridor labels also need independent official evidence.

Acceptance: every plotted point has location evidence and stated precision, no inferred coordinates, no fictional corridor or safety labels, and the raw incident count matches the deduplicated source records.

## Stage 4: train and evaluate a useful model

Keep synthetic training experiments separate from the official production snapshot. The ten publications are unsuitable for forecasting city crime.

Define a measurable target first, such as next-period recorded incident counts per stable reporting unit. Obtain a sufficiently long series of comparable official observations; let learning curves and uncertainty determine sufficiency. Form features strictly from earlier periods. Use forward chronological validation, a final untouched future holdout and grouping by case/reporting unit where applicable. Augment only the training partition if augmentation is justified; never augment holdout observations.

Compare against last-period and seasonal baselines, report MAE and error by area and time, and show prediction intervals with measured coverage. Do not translate R² to “percent accurate,” infer guilt, or train a model merely to reproduce a hand-computed risk formula. Model approval requires evidence it improves over baselines on future observations; until then show unavailable.

## Run locally

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/refresh_official_data.py
.venv/bin/python scripts/export_official_html.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8507 --server.headless true
```

For browser checks in another terminal:

```bash
.venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python tests/browser_official_data.py
```

The publication and facility snapshots load locally. The original map fetches public map tiles and its existing CDN assets when the browser opens. Only explicit refresh commands fetch new police records. Refreshes use ten HTTPS GET requests with timeouts. A failed fetch leaves the checked-in snapshot unchanged. A future publication is not automatically reviewed or included: read it and add a neutral reviewed summary to `REVIEWED` before refreshing. Review source changes before shipping a refreshed snapshot.

The legacy synthetic UI is opt-in:

```bash
.venv/bin/python -m streamlit run demo_app.py --server.port 8508
```

## Deployment gate

First review the locally tested publication view and its explicit limitations. Run unit and desktop/mobile browser checks, inspect screenshots, verify source links and CSV exports, and check source freshness. Deployment of the source-record view is possible separately from incident mapping and forecasting; those features remain unavailable until stages 3–4 pass their data and evaluation gates.

The current work is on local branch `real-official-data`; no push, merge or deployment is part of the local validation. The checked-in `index.html` is regenerated from official data. `demo_app.py` cannot overwrite it. Rollback can restore the prior application, but it must be labeled synthetic before public use.

## Restore all existing controls with real data

`dashboard.py` adapts official records into the original `ui_builder.py` shell. It does not call the incident generator or AI engines. `static/official-dashboard.js` retains the original map, filtering and navigation handlers while replacing data-specific renderers. Missing incident values remain null and never become map points.

The official homepage embeds a public Google My Maps map. `scripts/refresh_station_locations.py` reads its public KML export and stores source URL, map URL, retrieval timestamp and SHA-256 in `data/official/stations.json`. Its 48 points include stations, special units and headquarters, including facilities outside the urban commissionerate; they are labeled public police facilities. Their coordinates do not represent crimes. Contacts link to the official directory rather than unverified telephone numbers.

The correction restores visual functionality without reintroducing unsupported safe-corridor claims, assigned severity, or fabricated predictions. Time-of-day and severity filters remain visible with an explanation that these fields are absent in the source snapshot. Category, reporting-unit, publication-date and search filters work on the actual records.

## Locality, time and map correction

Reporting police units and reported localities are separate fields. The 3D chart now uses eight source-named localities, including MP Nagar Zone 1 and Budhwara/Talaiya for the Crime Branch publications. Crime Branch remains an attributed reporting unit in the records, never an area node. Node positions are diagram layout, not geographic coordinates; production decorative random particles were removed.

`data/reviewed_facts.py` records short evidence snippets for locality, occurrence/action time, and reported legal sections. Explicit refresh checks each snippet against the original official article body. A mismatch stops the refresh and preserves the previous snapshot. Schema version 2 rejects unreviewed changes to those fields.

The selected cylinder-theft event in publication 5327 is reported at 19:30 IST on September 10, 2026. Publication 5347 bounds a burglary between September 10 at 11:30 and September 11 at 00:30; an interval is not an exact time. The recovery update 5360 does not restate that interval and remains time-unknown. Publication 5380 has conflicting chronology; noon refers to a shop arrival, so it is not used as a theft timestamp. The time panel includes exact, window, unspecified and conflicting evidence. It counts publications, not unique incidents.

No source publishes a numeric 1–5 severity rating. The severity panel therefore displays the reported offenses/legal sections and source links. No offense is silently assigned a score. Source code/chronology inconsistencies remain flagged.

### Map pin precision

Nine locatable publications link to eight grouped locality-reference pins; one additional women’s/girls’ safety publication has no established occurrence locality and is not pinned. Two Kolar publications share a pin because they update the same investigation. These are **not exact crime-scene coordinates**, and neither pin counts nor reference-point clustering measure incident density. The published landmark coordinates are stored only in `map_reference`, separately from the still-null incident latitude/longitude fields. Popups explain the reference landmark, geographic source, precision limit, selected event, and linked police publications. The records table can navigate to the approximate locality.

Six reference points come from the [public TCIL/MP Police geographic location list](https://www.tcil.net.in/tender/pdf/25f2357_2.pdf), PDF pages 96, 98, 99, 102 and 103. They are wider locality references, not a claim that the reported crime occurred at that landmark. Those table pages were extracted and visually inspected. A bridge reference near Danish Kunj comes from the indexed [MP Pollution Control Board river report](https://mppcb.mp.gov.in/proc/KALIYASOTE%2023.5.19.pdf), section IV, sampling site 2; the binary could not be fetched with current TLS settings, so its checksum is explicitly null. Budhwara uses a reviewed OpenStreetMap locality feature retrieved via Photon, with the OSM object URL retained. Candidate geocoder results that matched unrelated places were rejected.

Map controls distinguish property, assault, women's safety, vandalism, other official reports and police facilities. Publication 5017 supplies a reviewed robbery-with-assault record from April 2026 and is tagged property plus assault. One women’s/girls’ safety publication is loaded but remains unlocated. Vandalism has no verified incident records loaded; its filter shows zero loaded, not zero crimes in Bhopal. The women's-safety campaign publication examined during research was not turned into an incident. Default coverage is all loaded publication dates, so the older assault report is not silently hidden.

Heatmap mode preserves the reference pins and explains that a crime-density heatmap needs appropriate incident coordinates. It never treats civic reference landmarks as exact event GPS, generates Gaussian points, or invents missing category examples. Geographic metadata and precision notes are included in CSV separately from occurrence time and incident coordinates.

Publication 5223 adds a source-verified girls’ trafficking/kidnapping investigation. Its selected disappearance date is January 10, 2025, while publication is July 17, 2026. The report does not establish a publishable crime location. Victim/informant residential information is excluded, not converted into a geographic pin. The chart excludes this record from locality nodes while the records, time and legal-evidence panels retain it. Default coverage is all publication dates; time filters distinguish one exact-time report, one window report, seven unspecified-time reports, and one conflicting chronology.
