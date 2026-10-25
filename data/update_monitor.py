"""Public-source discovery metadata; unreviewed posts never enter crime analytics."""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from .official_sources import API, ROOT, REVIEWED, SNAPSHOT, refresh_snapshot

REPORT = ROOT / 'updates.json'


def metadata(post):
    post_id = post['id']
    if type(post_id) is not int or post_id <= 0 or post.get('status') != 'publish':
        raise ValueError('Unexpected publication metadata')
    url = urlparse(post['link'])
    if url.scheme != 'https' or url.netloc != 'bhopal.mppolice.gov.in' or url.username or url.password:
        raise ValueError('Discovery URL must be the official HTTPS source')
    published = datetime.fromisoformat(post['date']).date()
    if published > datetime.now(timezone.utc).date():
        raise ValueError('Future publication')
    return {'source_post_id': post_id, 'publication_date': published.isoformat(), 'source_url': post['link']}


def discover(get=None):
    """Read at most five public index pages; fail rather than claim an incomplete check."""
    get = get or requests.get
    pending = []
    seen = set()
    for page in range(1, 6):
        response = get(API, params={'per_page': 100, 'page': page, 'orderby': 'date',
            'order': 'desc', '_fields': 'id,date,link,status'}, timeout=20, allow_redirects=False)
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError('Unexpected discovery redirect or status')
        posts = response.json()
        if not isinstance(posts, list):
            raise ValueError('Expected public publication index')
        pages = int(response.headers.get('X-WP-TotalPages', '0'))
        if not 1 <= pages <= 5:
            raise ValueError('Publication index size needs review; previous snapshot retained')
        for post in posts:
            row = metadata(post)
            if row['source_post_id'] in seen:
                raise ValueError('Duplicate discovery ID')
            seen.add(row['source_post_id'])
            if row['source_post_id'] not in REVIEWED:
                pending.append(row)
        if page == pages:
            return {'checked_at': datetime.now(timezone.utc).isoformat(),
                'status': 'success', 'indexed_publications': len(seen),
                'pending_review': pending}
    raise ValueError('Incomplete public index')


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, suffix='.tmp', delete=False, encoding='utf-8') as f:
        temporary = Path(f.name)
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def refresh_all(snapshot_path=SNAPSHOT, report_path=REPORT, get=None):
    # Network/validation completes before replacing either production file.
    report = discover(get=get)
    with tempfile.TemporaryDirectory() as directory:
        snapshot = refresh_snapshot(Path(directory) / 'publications.json', get=get)
    write_json(snapshot_path, snapshot)
    write_json(report_path, report)
    return report


def load_report(path=REPORT):
    try:
        report = json.loads(Path(path).read_text())
        checked = datetime.fromisoformat(report['checked_at'])
        if report['status'] != 'success' or checked.tzinfo is None or checked > datetime.now(timezone.utc):
            raise ValueError('Invalid update report')
        for row in report['pending_review']:
            expected = metadata({'id': row['source_post_id'], 'date': row['publication_date'],
                'link': row['source_url'], 'status': 'publish'})
            if row != expected or row['source_post_id'] in REVIEWED:
                raise ValueError('Invalid pending record')
        return report
    except (OSError, ValueError, KeyError, TypeError):
        return None
