import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.official_sources import load_snapshot
from dashboard import generate_dashboard

if __name__ == '__main__':
    target = Path(__file__).resolve().parents[1] / 'index.html'
    target.write_text(generate_dashboard(load_snapshot()), encoding='utf-8')
    print(target)
