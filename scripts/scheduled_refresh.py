"""Refresh validated publications and discover public posts awaiting review."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.update_monitor import refresh_all

if __name__ == '__main__':
    report = refresh_all()
    print(f"Official source checked at {report['checked_at']}; "
          f"{report['indexed_publications']} indexed, {len(report['pending_review'])} awaiting review.")
