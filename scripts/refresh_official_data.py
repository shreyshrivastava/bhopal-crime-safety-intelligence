"""Fetch only the explicitly reviewed official publications; no API key needed."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.official_sources import refresh_snapshot

if __name__ == '__main__':
    result = refresh_snapshot()
    print(f"Saved {len(result['records'])} official publications at {result['retrieved_at']}")
