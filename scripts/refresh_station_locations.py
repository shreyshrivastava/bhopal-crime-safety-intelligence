"""Read the public map embedded by Bhopal Police; no private map access."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
import requests

URL = 'https://www.google.com/maps/d/kml?mid=1B6Ui99x-DXx_TDO3EGDPPfmtzF4ij6w&forcekml=1'
PAGE = 'https://bhopal.mppolice.gov.in/'

def refresh():
    response = requests.get(URL, timeout=25)
    response.raise_for_status()
    ns = {'k': 'http://www.opengis.net/kml/2.2'}
    records = []
    for place in ET.fromstring(response.content).findall('.//k:Placemark', ns):
        name = place.findtext('k:name', namespaces=ns)
        coord = place.findtext('.//k:Point/k:coordinates', namespaces=ns)
        if not name or not coord: continue
        lon, lat = map(float, coord.strip().split(',')[:2])
        if not (22.8 < lat < 24 and 76.8 < lon < 78): raise ValueError('Unexpected map bounds')
        records.append(dict(name=name, lat=lat, lon=lon,
            jurisdiction='Public facility location — not an incident location',
            phone='See official contact directory', source_url=PAGE,
            contact_url='https://bhopal.mppolice.gov.in/contact/'))
    if not records: raise ValueError('No official map points')
    payload = dict(source_url=PAGE, map_url=URL, retrieved_at=datetime.now(timezone.utc).isoformat(),
        sha256=hashlib.sha256(response.content).hexdigest(), records=records)
    path = Path(__file__).resolve().parents[1]/'data/official/stations.json'
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False)+'\n')
    print(f'Saved {len(records)} public police facilities from the official embedded map')

if __name__ == '__main__': refresh()
