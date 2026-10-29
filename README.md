# Bhopal Safety Intelligence

An interactive Bhopal safety dashboard built with Streamlit, Leaflet and a Material Active interface. The default app uses reviewed public police publications and published geographic references. It does not generate synthetic incidents or run the demonstration forecasting model.


## What the dashboard shows

- An interactive map with OpenStreetMap, Civic and Satellite basemaps, dark/light themes, and independent police-facility visibility.
- Source-linked locality pins, colored by property, assault and other reported offenses/enforcement actions. Related recovery updates share a pin.
- Women's/girls' safety and vandalism filters that retain missing-data states instead of inventing records.
- A rotatable 3D chart and bars based on **source-named localities and publication counts**. Police units such as Bhopal Crime Branch are kept as reporting metadata, not area nodes. Chart positions are illustrative layout, not geographic coordinates.
- Search, category/locality/date filters, source records, and CSV export with provenance and missing values preserved.
- Occurrence-time evidence distinguishing exact times, reported windows, unspecified times and conflicting chronology.
- Published offense/legal-section evidence in the severity panel. No numeric severity scores are assigned.

The original navigation and controls remain available. AI risk estimates, incident-density heatmaps, safe-corridor claims and neighborhood safety ratings await suitable verified data and validation; the production app does not fill these gaps with simulated values.

## Understand the map before using it

**Pins are approximate locality references, not exact crime-scene GPS coordinates.** The reports do not establish precise incident coordinates. Each popup identifies the reference landmark, its geographic source, the precision limit and the linked official police publication(s).

The snapshot has nine locatable publications represented by eight grouped pins. Two Kolar publications update the same investigation. One additional girls' safety report has no established publishable occurrence locality and remains unpinned. Victim/informant residential addresses and the reporting police station are not substituted for its crime location.

| Map category | Source publications loaded | Coverage |
| --- | ---: | --- |
| Property | 5 | Includes a robbery also tagged assault |
| Assault | 1 | Robbery-with-assault report |
| Women's/girls' safety | 1 | Location not established; no invented pin |
| Vandalism | 0 | No verified record loaded; not evidence of zero crime |
| Other official reports | 4 | Excise, narcotics and weapons enforcement |
| Police facilities / thana layer | 48 facilities | Published stations, special units and headquarters; some lie outside the urban commissionerate |

Map category tags can overlap. Publication counts, grouped reference pins and police-facility counts are different quantities; none is a citywide incident count. Approximate reference points are not used to calculate a crime-density heatmap.

## Sources and provenance

Crime/report content comes from the [Commissionerate of Police Bhopal](https://bhopal.mppolice.gov.in/) through its public publication pages and WordPress endpoint. The snapshot covers publications dated April 16–October 10, 2026; selected events can predate publication.

- [`data/official/publications.json`](data/official/publications.json): source IDs, exact publication URLs, publication dates, related-case groups, response checksums and reviewed facts.
- [`data/reviewed_facts.py`](data/reviewed_facts.py): manually reviewed locality, time and legal-section facts with short source evidence snippets. An explicit refresh checks these snippets against the official article text and stops if the evidence changes.
- [`data/official/stations.json`](data/official/stations.json): 48 public facility points from the public map embedded on the official Bhopal Police homepage, with map URL, retrieval timestamp and checksum. Contact links use the [official directory](https://bhopal.mppolice.gov.in/contact/).
- [`data/official/map_references.json`](data/official/map_references.json): separately reviewed civic/place coordinates, source URLs and precision notes. References come from the [public TCIL/MP Police location list](https://www.tcil.net.in/tender/pdf/25f2357_2.pdf), the indexed [MP Pollution Control Board river report](https://mppcb.mp.gov.in/proc/KALIYASOTE%2023.5.19.pdf), and one reviewed OpenStreetMap locality feature. These are geographic references, not police-published crime GPS coordinates. The river-report binary could not be fetched with current TLS settings; its checksum is explicitly null.

The app does not retain names, private home addresses, vehicle identifiers or raw article bodies in its publication snapshot. Police publications describe reported allegations and enforcement actions, not necessarily convictions. Missing/corrupt snapshots show an unavailable state; failed refreshes preserve the existing snapshot. The old synthetic cache is not used.

## Run locally

Requires Python 3.10 or later. Local verification was performed with Python 3.14; the existing Dockerfile uses Python 3.12.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py \
  --server.address 127.0.0.1 \
  --server.port 8507 \
  --server.headless true \
  --browser.gatherUsageStats false
```

Open [the local dashboard](http://127.0.0.1:8507/). Checked-in snapshots load without police API credentials. Browser map tiles, fonts and the existing UI libraries require internet access.

Generate the standalone HTML export:

```bash
.venv/bin/python scripts/export_official_html.py
```

This writes `index.html` from the same official-data dashboard. The app does not overwrite that file during requests.

## Refresh official snapshots

A GitHub Actions workflow checks the official public source daily at **12:00 a.m. IST** (18:30 UTC), with a manual **Run workflow** option. Scheduling is best effort; GitHub may delay a run. The dashboard shows the last successful refresh and warns when it is over 48 hours old.

The job revalidates reviewed publications, checks the public index for unreviewed posts, runs source-validation tests and exports the dashboard before publishing the snapshot. Network or evidence-validation failures preserve the deployed snapshot. Unreviewed posts retain only public IDs, dates and source links; they are listed under Data Sources and excluded from crime counts, maps and model input. They require source review before import.

Run the same update locally, or refresh individual snapshots manually:

```bash
.venv/bin/python scripts/scheduled_refresh.py
```

```bash
.venv/bin/python scripts/refresh_official_data.py
.venv/bin/python scripts/refresh_station_locations.py
.venv/bin/python scripts/export_official_html.py
```

Publication refresh fetches only the ten explicitly reviewed public post IDs. Add a new record only after reviewing its source, locality evidence, occurrence-time meaning and category. Never infer an occurrence time from a publication timestamp, a crime location from a police-station coordinate, or a severity score from missing data.

`build_reviewed_map_references.py` is a maintenance transcription script; it uses the reviewed source PDF and geocoding review cache described in the [migration plan](docs/REAL_DATA_MIGRATION.md). It is not required to run the app. Do not automatically geocode victim addresses or accept the first place-search match.

## Test locally

```bash
.venv/bin/python -m unittest discover -s tests -v
```

With the local app running on port 8507, run the browser checks:

```bash
.venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python tests/browser_official_data.py
```

**Validation:** 21 automated tests passed, plus browser checks at 1400 × 900 and 390 × 844. Checks cover source validation, changed-source rejection, missing-data behavior, model isolation, 3D locality semantics, map categories, real facility toggles, occurrence-time filters, basemaps, theme controls, navigation and CSV exports. Both viewports had no JavaScript page errors or horizontal page overflow.

See the [local test report](docs/LOCAL_TEST_RESULTS.md), [browser results](artifacts/browser-results.json) and [unit-test log](artifacts/unit-tests.txt). Screenshots and downloaded source-review material remain local and are excluded from Git.

## Architecture and development

| Component | Purpose |
| --- | --- |
| `app.py` | Default Streamlit host for official data |
| `dashboard.py` | Connects reviewed facts and geographic references to the existing dashboard shell |
| `ui_builder.py` | Original Material Active HTML/CSS/Leaflet shell |
| `static/official-dashboard.js` | Official-record rendering, source filters, locality pins and evidence panels |
| `data/official_sources.py` | Snapshot validation and reviewed publication refresh |
| `data/reviewed_facts.py` | Reviewed source facts and map-category tags |
| `data/official/` | Checked-in publication, facility and geographic-reference snapshots |
| `data/update_monitor.py` | Public-index discovery and safe scheduled refresh |
| `.github/workflows/refresh-official-data.yml` | Daily midnight IST update, validation and snapshot publication |
| `scripts/` | Refresh and HTML export commands |
| `tests/` | Automated source/data checks and browser verification |

Preserve the existing interface, search, navigation, responsive layout and CSV export when changing data connections. Keep publication dates, occurrence dates, reporting police units, source localities and reference coordinates separate. Check desktop and mobile screenshots after frontend changes. Do not reintroduce simulated data fallbacks, unsupported live-feed badges, named unverified person profiles or fixed accuracy claims.

## Synthetic training/demo experiments

The previous generated-data interface is isolated behind an explicit separate entrypoint:

```bash
.venv/bin/python -m streamlit run demo_app.py --server.port 8508
```



