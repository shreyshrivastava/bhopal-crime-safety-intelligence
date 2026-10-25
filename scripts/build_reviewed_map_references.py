"""Rebuild reviewed locality references from explicitly transcribed published coordinates.
These are civic/place reference points, never incident GPS coordinates.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def build():
    base='https://www.tcil.net.in/tender/pdf/25f2357_2.pdf'
    binary=ROOT/'tmp/pdfs/tcil-georeferences.pdf'
    sha=hashlib.sha256(binary.read_bytes()).hexdigest() if binary.exists() else None
    points={}
    def add(locality,name,lat,lon,page,note):
        points[locality]=dict(reference_name=name,latitude=lat,longitude=lon,precision='locality_reference',source_url=base+'#page='+str(page),source_page=page,source_sha256=sha,basis=note)
    add('Khajuri Sadak','Khajuri By Pass',23.247939,77.259659,102,'Wider Khajuri civic reference; not the reported mosque or precise enforcement location.')
    add('Lalwani Gali, KN Market','Sarafa Chowk / Kotwali market reference',23.258916,77.401975,99,'Broader Kotwali market reference; Lalwani Gali itself has not been precisely geocoded.')
    add('Mata Mandir','Mata Mandir',23.224633,77.402288,96,'Published Mata Mandir landmark; the report names Mata Mandir 56 ki line, not this precise point.')
    add('MP Nagar Zone 1','Pragati Choraha / MP Nagar reference',23.229155,77.43438,98,'Broad MP Nagar reference; not the precise metro-bridge enforcement site.')
    add('MP Nagar Zone 2','Zone-2 Sargam Talkies reference',23.227918,77.436287,103,'Published Zone-2 reference; not the private location of the selected theft.')
    add('Near Kilol Park','Angithi Chouraha / Shyamla Hills reference',23.247661,77.396654,99,'Wider Kilol Park / Shyamla Hills road-area reference; not the precise robbery point.')
    points['Danish Kunj']=dict(reference_name='Road bridge near Danish Kunj Phase-5',latitude=23.17290,longitude=77.43183,precision='locality_reference',
        source_url='https://mppcb.mp.gov.in/proc/KALIYASOTE%2023.5.19.pdf',source_page=None,source_sha256=None,
        source_section='IV. River quality in the stretch, sampling location 2 (printed page 12)',
        verification='Coordinates transcribed from indexed official report; PDF binary could not be fetched with current TLS settings.',
        basis='Published bridge reference near Danish Kunj; not the private burglary location.')
    cache=ROOT/'tmp/geocoding_candidates.json'
    ftr=json.loads(cache.read_text())['Budhwara Bhopal']['features'][0]
    prop=ftr['properties'];lon,lat=ftr['geometry']['coordinates']
    assert prop['name']=='Budhwara' and prop['city']=='Bhopal'
    osm_type={'N':'node','W':'way','R':'relation'}[prop['osm_type']]
    points['Budhwara, Talaiya']=dict(reference_name='Budhwara locality (OpenStreetMap)',latitude=lat,longitude=lon,precision='locality_reference',
        source_url=f"https://www.openstreetmap.org/{osm_type}/{prop['osm_id']}",source_page=None,
        source_sha256=hashlib.sha256(json.dumps(ftr,sort_keys=True).encode()).hexdigest(),
        basis='OSM residential-locality reference reviewed through Photon; not the precise reported shop location.')
    target=ROOT/'data/official/map_references.json'
    target.write_text(json.dumps(dict(schema_version=1,reviewed_at=datetime.now(timezone.utc).isoformat(),coordinate_kind='locality_reference_not_incident',records=points),indent=2,ensure_ascii=False)+'\n')
    print('Saved',len(points),'reviewed locality reference points')

if __name__=='__main__':build()
