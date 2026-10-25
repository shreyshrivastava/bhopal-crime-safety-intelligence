"""Reviewed public publications, never an incident census or synthetic fallback."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from .reviewed_facts import FACTS

ROOT = Path(__file__).resolve().parent / 'official'
SNAPSHOT = ROOT / 'publications.json'
API = 'https://bhopal.mppolice.gov.in/wp-json/wp/v2/posts'
# Editorial summaries of reviewed source publications; no personal data is retained.
REVIEWED = {
    5223: ('Women Safety Concerns', 'Hanumanganj', 'Police report arrests in an investigation concerning trafficking and kidnapping of girls.', 'hanumanganj-girl-protection-2025'),
    5017: ('Violent Assault', 'Shyamla Hills', 'Police report a robbery involving a cyclist being knocked down and assaulted with chilli powder.', 'kilol-robbery-2026-04-10'),
    5406: ('Excise enforcement', 'Khajuri Sadak', 'Police report an illicit liquor seizure and an arrest.', 'khajuri-excise-2026-10-08'),
    5380: ('Property crime', 'Kotwali', 'Police report recovery of stolen gold and jewellery.', 'kotwali-gold-2026-10'),
    5375: ('Excise enforcement', 'TT Nagar', 'Police report enforcement action under the Excise Act.', 'tt-nagar-excise-2026-10'),
    5360: ('Property crime', 'Kolar Road', 'Police publish a further recovery update in a burglary investigation.', 'kolar-burglary-2026-09'),
    5347: ('Property crime', 'Kolar Road', 'Police report arrests and recovery in a burglary investigation.', 'kolar-burglary-2026-09'),
    5340: ('Narcotics enforcement', 'Bhopal Crime Branch', 'Police report a narcotics seizure and arrests.', 'crime-branch-narcotics-2026-09'),
    5337: ('Weapons enforcement', 'Bhopal Crime Branch', 'Police report seizure of weapons and manufacturing equipment.', 'crime-branch-weapons-2026-09'),
    5327: ('Property crime', 'MP Nagar', 'Police report arrests in theft investigations.', 'mp-nagar-theft-2026-09'),
}


def validate_snapshot(payload):
    if not isinstance(payload, dict):
        raise ValueError('Snapshot must be an object')
    if payload.get('schema_version') != 2 or payload.get('data_kind') != 'official_publications':
        raise ValueError('Unsupported snapshot: official publications required')
    retrieved = datetime.fromisoformat(payload['retrieved_at'])
    if retrieved.tzinfo is None or retrieved > datetime.now(timezone.utc):
        raise ValueError('Snapshot retrieval time must be timezone-aware and not in the future')
    rows = payload['records']
    if not isinstance(rows, list):
        raise ValueError('records must be a list')
    seen = set()
    for row in rows:
        post_id = row['source_post_id']
        if post_id not in REVIEWED or post_id in seen:
            raise ValueError('Unknown or duplicate reviewed source ID')
        seen.add(post_id)
        url = urlparse(row['source_url'])
        if url.scheme != 'https' or url.netloc != 'bhopal.mppolice.gov.in' or url.username or url.password:
            raise ValueError('Source must be the official HTTPS police website')
        publication_date = datetime.fromisoformat(row['publication_date']).date()
        if publication_date > datetime.now(timezone.utc).date():
            raise ValueError('Future publication date')
        expected = REVIEWED[post_id]
        if tuple(row[k] for k in ('category', 'reporting_unit', 'summary', 'related_case_group')) != expected:
            raise ValueError('Unreviewed editorial fields')
        if row.get('reviewed_facts') != FACTS[post_id]:
            raise ValueError('Unsupported or unreviewed locality, time or legal facts')
        if row['latitude'] is not None or row['longitude'] is not None or row['incident_date'] != FACTS[post_id]['occurrence']['date']:
            raise ValueError('These sources have no reviewed coordinates or incident dates')
        if set(row) != {'source_post_id', 'source_url', 'publication_date', 'category', 'reporting_unit', 'summary', 'related_case_group', 'latitude', 'longitude', 'incident_date', 'source_sha256', 'reviewed_facts'}:
            raise ValueError('Unexpected fields; do not retain personal details')
        digest = row['source_sha256']
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Missing source response checksum')
    return payload


def load_snapshot(path=SNAPSHOT):
    # An explicit empty state is safer than generating observations on failure.
    try:
        with Path(path).open(encoding='utf-8') as f:
            return validate_snapshot(json.load(f))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {'schema_version': 2, 'data_kind': 'official_publications', 'records': [],
                'retrieved_at': None, 'status': 'unavailable', 'error': str(exc)}


def refresh_snapshot(path=SNAPSHOT, get=None):
    """Explicit maintenance operation. Failures leave the last snapshot untouched."""
    get = get or requests.get
    records = []
    for post_id, (category, unit, summary, group) in REVIEWED.items():
        response = get(f'{API}/{post_id}', timeout=20, allow_redirects=False)
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError('Unexpected source redirect or status')
        post = response.json()
        if post['id'] != post_id or post.get('status') != 'publish':
            raise ValueError('Unexpected source document')
        facts = FACTS[post_id]
        source_text = ' '.join(BeautifulSoup(post['content']['rendered'], 'html.parser').get_text(' ',strip=True).split())
        evidence = [facts['locality_evidence'], facts['legal_evidence'], *facts['occurrence']['evidence']]
        for quote in filter(None, evidence):
            if ' '.join(quote.split()) not in source_text:
                raise ValueError(f'Reviewed evidence changed in official source {post_id}')
        records.append(dict(source_post_id=post_id, source_url=post['link'],
            publication_date=post['date'][:10], category=category, reporting_unit=unit,
            summary=summary, related_case_group=group, latitude=None, longitude=None,
            incident_date=facts['occurrence']['date'], reviewed_facts=facts, source_sha256=hashlib.sha256(response.content).hexdigest()))
    payload = validate_snapshot(dict(schema_version=2, data_kind='official_publications',
        retrieved_at=datetime.now(timezone.utc).isoformat(), status='snapshot', records=records))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, path)
    return payload
