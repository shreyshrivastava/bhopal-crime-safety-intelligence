# Hosted Streamlit verification

The public [Streamlit demo](https://bhopalcrimesafety.streamlit.app/) was tested after deploying commit `c04f33e` to `main` on October 26, 2026 (IST). It rendered the official-data dashboard rather than the prior 520 synthetic incidents.

Chromium browser checks passed at 1400 × 900 and 390 × 844:

- 10 reviewed publications, 48 police facilities, and 8 approximate locality-reference pins.
- Incident coordinates and numeric severity remain empty; Crime Branch is excluded from area nodes.
- Map tiles, basemap switching, category filters, unlocated women’s safety records and exact-time filtering.
- Five navigation panes, CSV download, occurrence and legal evidence, and 3D spin controls.
- No JavaScript page errors or horizontal overflow in the dashboard.

These checks verify the deployed snapshot and interface, not completeness of police reporting or predictive accuracy. Reference pins do not identify exact incident locations.

Machine-readable browser results:

```json
{
  "url": "https://bhopalcrimesafety.streamlit.app/",
  "checked_at": "2026-10-25T19:10:05.557002+00:00",
  "results": [
    {
      "viewport": "1400x900",
      "publications": 10,
      "police_facilities": 48,
      "approximate_locality_pins": 8,
      "filters": "pass",
      "basemaps": "pass",
      "tabs": "pass",
      "csv": "pass",
      "occurrence_and_legal_evidence": "pass",
      "sphere": "pass",
      "javascript_errors": []
    },
    {
      "viewport": "390x844",
      "publications": 10,
      "police_facilities": 48,
      "approximate_locality_pins": 8,
      "filters": "pass",
      "basemaps": "pass",
      "tabs": "pass",
      "csv": "pass",
      "occurrence_and_legal_evidence": "pass",
      "sphere": "pass",
      "javascript_errors": []
    }
  ]
}
```

## Locality/category spacing and map visibility correction

The compact locality and category cards now sit together, use content-sized heights, and place headings immediately above their bars. Report pins use category-colored teardrop icons and accessible category/locality labels, distinct from square police-facility icons. The initial map fits all eight loaded reference locations; “Show all report pins” restores that view.

Local desktop/mobile browser checks assert that all eight marker elements are visible and inside the initial map bounds, clicking a pin opens its source-linked approximate-location popup, chart headings have less than 40px of space before the bars, and compact cards remain below 500px in height. The existing filter, evidence, navigation, CSV and Streamlit checks also pass. All 17 source/model-isolation tests pass.
