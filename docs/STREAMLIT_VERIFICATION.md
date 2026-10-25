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
