# Local validation — October 26, 2026

Result: the original dashboard, restored with official publications and published police-facility coordinates, passes local validation. This report records local validation before publishing the feature branch; no production deployment or merge was performed. The production Leaflet map runs with real facility coordinates. Incident-location heatmaps and predictive scores remain unavailable pending suitable source data.

## Verified behavior

| Check | Result | Evidence |
| --- | --- | --- |
| Automated tests | 17 passed | `artifacts/unit-tests.txt` |
| Desktop browser | Passed at 1400 × 900 | `artifacts/browser-results.json`, `artifacts/restored-desktop.png` |
| Mobile browser | Passed at 390 × 844 | `artifacts/browser-results.json`, `artifacts/restored-mobile.png` |
| JavaScript and layout | No page errors or horizontal overflow at both viewports | Browser assertions |
| Search and category filters | Passed; property-crime filter gives four publications; reporting-unit and search filters also pass | Browser assertions |
| CSV download | Ten official publications exported and parsed correctly, with blank missing coordinates and severity | `artifacts/dashboard-1400.csv`, `artifacts/dashboard-390.csv` |
| Local Streamlit application | 48 real police-facility markers and ten publication rows rendered in its iframe | Browser assertions and local health endpoint |
| Screenshot review | Both viewports inspected; text, controls and source links visible | Screenshots |
| Missing/corrupt data | Explicit unavailable state, no synthetic generation | Automated tests |
| Failed refresh | Previous snapshot preserved | Automated test with simulated timeout |
| Legacy cache | Cannot reintroduce synthetic records | Automated test |
| Model isolation | Explicit synthetic opt-in required; official publications rejected | Automated test |
| Diff whitespace | Passed | `git diff --check` |

## Scope and limits

The publication snapshot was fetched through ten ordinary public HTTPS GET requests to the official Bhopal Police WordPress endpoint. A separate public KML export of the Google My Maps map embedded by Bhopal Police supplies 48 facility locations, with URL, timestamp and checksum retained. It has ten selected publications dated April 16–October 10, 2026. Two publications update the same known investigation. This is not a complete incident dataset, a crime census, a live feed or an unbiased training sample.

No authenticated police service was used. No login bypass, restricted-data access, exploit, scan or private-system probing was performed. The browser runtime was installed locally to run UI tests.

The original synthetic UI is retained in `demo_app.py`, with an explicit synthetic banner and no ability to overwrite the production `index.html`. It was not the target of the production browser checks. The original model's perturbed random split remains a demo experiment; its scores are not real-world validation.

The restored dashboard retains the original visual interface, Leaflet map, three basemaps, theme controls, filtering, five navigation panes, 3D chart and CSV export. Browser checks verified all of these, including station visibility toggles and empty heatmaps with zero fabricated incident points and eight explicitly approximate locality references. Publication statistics are labeled as publications. The production view intentionally has no invented incident points, severity scores, safe-area rankings, named wanted profiles or forecasting claims. Restoring such features requires the source and evaluation work described in [the migration plan](REAL_DATA_MIGRATION.md). Annual SCRB/NCRB statistics were identified as source candidates, not imported or validated here.

## Reproduce

Run the commands in [the migration plan](REAL_DATA_MIGRATION.md#run-locally). The browser checks require the local app running on port 8507. Screenshots and test logs are local artifacts; PNG files are ignored by the repository's existing ignore rules.

## Additional checks for the locality/time/map corrections

- 17 automated tests pass. Added regressions cover Crime Branch exclusion from 3D area nodes, genuine occurrence times/windows, source conflicts, rejection of invented facts, source-evidence changes preserving the existing snapshot, reference-coordinate separation and no fake category records.
- Desktop and mobile browser checks cover property/assault/other map toggles, unlocated women’s/girls’ safety filtering and zero-loaded vandalism filtering, permanent real police facilities, exact/window/unknown/conflicting time filters, source-linked records, CSV evidence fields, basemaps and theme controls.
- All ten incident latitude/longitude fields remain null. Eight marker groups use separately labeled reference coordinates, with related recovery updates grouped together. Approximate references never enter a crime-density heatmap.
- Reported legal-section evidence is visible in the severity panel; all numeric severity fields remain blank.
- The default time range includes all loaded dates. Publication 5017 is an April report and remains historical.

The final dataset includes ten publications and eight approximate reference pins (two related Kolar updates share a pin and one girls’ safety report is unlocated). Tests check that the girls’ safety record remains available without a fake location and that vandalism is never filled with invented examples. Incident-time and numeric-severity omissions remain distinct from publication metadata and legal-section evidence.
