"""Connect official snapshots to the existing Material Active map/dashboard shell."""
import html
import json
import re
from pathlib import Path
from collections import Counter

import pandas as pd
from bs4 import BeautifulSoup
from data.official_sources import load_snapshot
from data.reviewed_facts import MAP_CATEGORIES
from ui_builder import generate_material_active_html

FACILITIES = Path(__file__).resolve().parent/'data/official/stations.json'


def load_facilities():
    try:
        payload = json.loads(FACILITIES.read_text())
        rows = payload['records']
        for row in rows:
            if not (22.8 < row['lat'] < 24 and 76.8 < row['lon'] < 78):
                raise ValueError('Invalid official facility coordinate')
        return rows
    except (OSError, ValueError, KeyError, TypeError):
        return []


def load_map_references():
    try:
        data=json.loads((FACILITIES.parent/'map_references.json').read_text())
        if data.get('coordinate_kind')!='locality_reference_not_incident':return {}
        rows=data['records']
        for row in rows.values():
            if row['precision']!='locality_reference' or not (23 < row['latitude'] < 23.5 and 77.1 < row['longitude'] < 77.7):
                raise ValueError('Invalid reviewed locality reference')
        return rows
    except (OSError,ValueError,TypeError,KeyError):return {}


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c')


def generate_dashboard(payload=None):
    payload = load_snapshot() if payload is None else payload
    rows = payload['records']
    map_references = load_map_references()
    facilities = load_facilities()
    # The legacy engines receive no fabricated incident rows, and none of the AI engines run.
    empty = pd.DataFrame(columns=['neighborhood','category','offense_type','severity'])
    page = generate_material_active_html(empty, pd.DataFrame(),
        refresh_date=payload.get('retrieved_at') or 'Unavailable',
        ingestion_metadata={'status':'Official Bhopal Police publications · historical snapshot' if rows else 'Data unavailable · no synthetic fallback','is_live':False},
        validation_report={'quality_score':100 if rows else 0,'valid_records':len(rows),'dropped_records':0},
        temporal_metrics={}, model_results={'metrics':{'r2':0},'sector_predictions':[], 'feature_importances':{}},
        anomalies=[], hotspots=[], xai_insights={'executive_summary':{'title':'Official source coverage','key_factors':[], 'recommendation':'Coverage is selected; publication counts are not incident counts.','confidence_pct':0}},
        police_stations=facilities, safe_corridors=[])
    records = []
    for r in rows:
        facts = r['reviewed_facts']
        reference = map_references.get(facts['locality'])
        occurrence = facts['occurrence']
        kind = occurrence['kind'] if occurrence['kind'] in ('exact','window','conflicting') else 'unknown'
        records.append(dict(id=f"BHP-PUB-{r['source_post_id']}", lat=None, lon=None,
            neighborhood=facts['locality'] or '', map_reference=reference, map_categories=MAP_CATEGORIES[r['source_post_id']], reporting_unit=r['reporting_unit'],
            category=r['category'], subtype=r['summary'], time_of_day=kind,
            date=r['publication_date'], incident_date=occurrence['date'],
            occurrence_time=occurrence['time'], occurrence_start=occurrence['start'],
            occurrence_end=occurrence['end'], occurrence_label=occurrence['label'],
            legal_basis=facts['legal_basis'] or 'Not specified in this publication',
            source_notes=facts['notes'], severity=None, status='Official publication',
            nearest_ps='', dist_km=None, source_url=r['source_url'], source_sha256=r['source_sha256'],
            related_case_group=r['related_case_group']))
    page = page.replace('const ALL_CRIMES = [];', 'const ALL_CRIMES = '+_json(records)+';')
    # Graph coordinates are layout positions, explicitly not geographic locations.
    units = sorted({r['neighborhood'] for r in records if r['neighborhood']})
    colors = ['#38bdf8','#c084fc','#f43f5e','#34d399','#fbbf24','#fb7185']
    nodes = [dict(name=name,lat=45-i*16,lon=-55+i*24,color=colors[i%6],count=0,dominant='Unknown',avgSev='Unknown') for i,name in enumerate(units)]
    page = re.sub(r'const SPHERE_SECTORS = \[.*?\];', lambda m:'const SPHERE_SECTORS = '+_json(nodes)+';', page, flags=re.S)
    page = re.sub(r'const SPHERE_CHORDS = \[.*?\];', 'const SPHERE_CHORDS = [];', page, flags=re.S)
    page = page.replace('`${found.count} Cases (${pct}% of selection)`','`${found.count} publications (${pct}% of selection)`')
    page = page.replace('`${sec.count} cases`','`${sec.count} publications`')
    page = page.replace('`Avg Severity: Lv ${found.avgSev}/5`', "'Numeric severity is not published; see source evidence below'")
    page = page.replace("document.getElementById('telemetry-node-count').innerText = currentFiltered.length;", "document.getElementById('telemetry-node-count').innerText = currentFiltered.filter(c => Number.isFinite(c.lat) && Number.isFinite(c.lon)).length;")
    particle_start = page.index('  const AMBIENT_PARTICLES =')
    particle_end = page.index('  function initSphericalGraph', particle_start)
    page = page[:particle_start] + '  const AMBIENT_PARTICLES = [];\n' + page[particle_end:]
    page = page.replace('maxClusterRadius: 45,', 'maxClusterRadius: 30, disableClusteringAtZoom: 12,')
    page = page.replace("let currentDateRange = '90';", "let currentDateRange = 'ALL';")
    page = page.replace("const matchCat = currentCategory === 'ALL' || c.category === currentCategory;", "const matchCat = currentCategory === 'ALL' || c.category === currentCategory || c.map_categories.includes(currentCategory.replace('map:', ''));")
    soup = BeautifulSoup(page,'html.parser')
    def fragment(markup): return BeautifulSoup(markup,'html.parser')
    def set_content(node, markup):
        if node:
            node.clear()
            node.append(fragment(markup))
    def text_replace(old,new):
        for text in list(soup.find_all(string=lambda s: s and s.strip()==old)):
            if text.parent.name not in ('script','style'): text.replace_with(new)
    for old,new in {
        '3D City Safety Distribution':'3D Publication Distribution',
        'Interactive 3D view showing crime levels and safety across 9 areas in Bhopal. Drag to rotate the globe.':'Reviewed publications by source-named locality. Police units are excluded. Drag to rotate; positions are chart layout, not geographic coordinates.',
        'Highest Crime Area':'Most represented source locality',
        'Crime Breakdown by Type':'Publication categories','4 IPC Categories':'Reviewed source categories',
        'Area Safety Balance Index':'Coverage limitations', 'Spread score across 9 Bhopal areas':'Selected publications; not a measure of safety',
        'Balanced Distribution':'Not a citywide incident census',
        'Crime Trends & Area Breakdown':'Source Trends & Locality Breakdown',
        'Crime counts by area, time of day, and severity — all charts update automatically when you change filters.':'Counts use reviewed source facts. Exact times, reported windows and unknown times are separate; no numeric severity is assigned.',
        'Crime Records':'Crime Records · Source Reports',
        'Sector / Locality':'Reporting unit','Date':'Published date',
        'Automated 24h rolling cache':'Reviewed official snapshot; explicit refresh',
        '80% Accurate':'Not yet validated',
        '10 PS':f'{len(facilities)} facilities', '3 Routes':'Awaiting source', '9 Areas':'Awaiting data',
        '0 alerts':'Awaiting data','0 areas':'Awaiting data',
        '10 PS • 3 Corridors • 9 AI Halos • 0 Hotspots':f'{len(facilities)} published facilities · incident layers await data',
        'Bhopal Area Safety Ratings':'Locality coverage · risk scores unavailable',
        'Crime Incident Records':'Crime Records · Official Source Reports',
        'Reported crime incidents across Bhopal. Tap any row to see it on the map.':'Reviewed police publications. Open the official source for details; missing incident coordinates are not inferred.',
        'Tap any record to see its exact location on the map':'Source links open the official publication; reporting units are not incident locations.',
        'Quality: 100% Validated':'Schema checked · coverage incomplete',
        'Area':'Source locality', 'Date Range':'Publication date range', 'Time of Day':'Occurrence-time evidence',
        'Safe Corridor':'Unverified corridor layer',
        'Loading crime data...':'Loading official sources and map...',
        'Marker Cluster':'Reported locality pins',
        'Incidents Rendered':'Locality reference pins',

    }.items(): text_replace(old,new)
    graph=soup.find(id='spherical-distribution-card')
    located=sum(bool(r['neighborhood']) for r in records)
    if graph: graph.insert(0,fragment(f'<p id="source-locality-coverage" class="text-xs text-on-surface-variant mb-2">{located} of {len(records)} publications have a source-named locality; {len(records)-located} unlocated publication(s) are excluded from area nodes. Percentages use all selected publications.</p>'))
    # Keep the original five panes and navigation; unsupported analytics explain exactly what is missing.
    for ident,title,detail in [
        ('ai-risk','AI Risk Insights','The real publications are connected. Predictions need a representative historical incident series and forward validation. No production model or accuracy claim is available.'),
        ('hotspots','Crime Hotspots','Cluster and heatmap controls remain on the map. This snapshot has no verified incident coordinates; publication reporting units must not be plotted as incident locations.')]:
        pane=soup.find(id='tab-pane-'+ident)
        set_content(pane, f'<h2 class="text-xl font-bold">{title}</h2><div class="p-5 rounded-2xl bg-surface-container border border-white/10"><b>Awaiting sufficient real incident data</b><p class="text-sm mt-2 text-on-surface-variant">{detail}</p></div>')
    sources=soup.find(id='tab-pane-sources')
    links=''.join(f'<li class="py-2"><a class="text-primary underline" target="_blank" rel="noopener noreferrer" href="{html.escape(r["source_url"],quote=True)}">Publication #{r["source_post_id"]} · {r["publication_date"]} · {html.escape(r["reporting_unit"])}</a></li>' for r in rows)
    set_content(sources,f'''<h2 class="text-xl font-bold">Data Sources &amp; Quality</h2><p>{len(rows)} reviewed official publications are selected historical records, not a complete crime register. Related updates retain case-group IDs in CSV export. Locality, occurrence-time and legal-section facts are checked against the original report text on refresh; source inconsistencies stay flagged. Missing data never means zero crime.</p><p>Snapshot fetched: {html.escape(payload.get('retrieved_at') or 'Unavailable')}</p><p>{len(facilities)} real public police facilities from the map embedded by <a class="text-primary underline" href="https://bhopal.mppolice.gov.in/" target="_blank" rel="noopener">Bhopal Police</a>. Facility markers are not incident locations. Some facilities lie outside the urban commissionerate; this is the scope of the published map.</p><p>Contacts: <a class="text-primary underline" href="https://bhopal.mppolice.gov.in/contact/" target="_blank" rel="noopener">Official directory</a>. Safe-corridor claims have no verified source and are not drawn.</p><ul>{links}</ul>''')
    # Replace the four existing analytical card contents, retaining their layout and shapes.
    charts=soup.find(id='sector-bar-container')
    if charts:
        card=charts.find_parent(class_=lambda v:v and 'rounded-[24px]' in v)
        set_content(card,'<h3 class="font-bold mb-3">Publications by source-named locality</h3><div id="sector-bar-container"></div>')
    for marker,title,detail in [
        ('chart2-day-pct','Time of occurrence · source evidence','Selected event/action times in IST. Publication dates do not determine occurrence times; unknown and conflicting values stay visible.'),
        ('sev-count-2','Incident severity · source evidence','The police reports publish no numeric severity scores. Reported legal sections are shown below as evidence, not converted into a 1–5 rating.'),
        ('modalities-container','Publication categories','')]:
        node=soup.find(id=marker)
        if node:
            card=node.find_parent(class_=lambda v:v and 'rounded-[24px]' in v)
            content_id = {'chart2-day-pct':'occurrence-evidence','sev-count-2':'severity-evidence','modalities-container':'modalities-container'}[marker]
            set_content(card,f'<h3 class="font-bold mb-3">{title}</h3><p class="text-sm text-on-surface-variant">{detail}</p><div id="{content_id}" class="mt-3"></div>')
    # The sector risk table stays in place as a coverage table, with no invented score.
    heading=soup.find(string=lambda s:s and 'Sector Safety' in s)
    if heading: heading.replace_with('Locality coverage · risk scores unavailable')
    risk_table=soup.find(id='tab-pane-analytics').find('table')
    if risk_table:
        set_content(risk_table,'<thead><tr><th class="p-3 text-left">Source locality</th><th class="p-3">Source publications</th><th class="p-3">Risk score</th></tr></thead><tbody id="official-coverage-body"></tbody>')
    table=soup.find(id='records-table-body').find_parent('table')
    set_content(table.find('thead'),'<tr>'+''.join('<th class="py-2 px-3 text-left">'+x+'</th>' for x in ['Publication ID','Published date','Source locality','Reporting police unit','Category','Occurrence / action time (IST)','Reported legal basis','Official source'])+'</tr>')
    notice=fragment('<div id="official-map-coverage" class="px-4 py-3 rounded-2xl bg-surface-container border border-white/10 text-xs">Real police facilities are mapped below. These are not crime locations. Crime/report pins use published locality reference points and link to official evidence. They are approximate area references, not incident GPS. Related reports share one pin. Women’s safety includes an unlocated source report; vandalism has no verified records loaded. Coverage is incomplete.</div>')
    soup.find(id='map-frame-container').insert(0,notice)
    legend=soup.find(id='leaflet-map').find_parent(class_=lambda v:v and 'rounded-[24px]' in v)
    legend.insert(0,fragment('<div id="map-category-controls" class="flex flex-wrap gap-2 text-xs mb-3">'+''.join(f'<label class="px-2 py-1 rounded-full border border-white/10"><input type="checkbox" checked id="map-category-{key}" onchange="toggleMapCategory(\'{key}\',this.checked)"> {label} <span id="map-count-{key}"></span></label>' for key,label in [('property','Property'),('assault','Assault'),('women','Women’s safety'),('vandalism','Vandalism'),('other','Other official reports')])+'</div>'))
    date_select=soup.find(id='date-range-filter-select')
    for option in date_select.find_all('option'):
        option.attrs.pop('selected',None)
        if option.get('value')=='ALL': option['selected']=''
    for ident in ['overlay-corridors-chk','overlay-aizones-chk','overlay-anomalies-chk','overlay-hotspots-chk']:
        node=soup.find(id=ident)
        if node: node.attrs.pop('checked',None)
    for selector in ['#sev-slider']:
        node=soup.select_one(selector)
        if node:
            node['disabled']='';node['title']='The source publishes no numeric severity score; reported legal sections are shown in the severity panel'
    set_content(soup.find(id='sev-slider-val'),'No official score')
    time_button=soup.find(id='time-btn-all')
    if time_button:
        set_content(time_button.parent, ''.join(f'<button type="button" data-time-kind="{key}" id="time-btn-{key.lower()}" onclick="setTimeFilter(\'{key}\')" class="py-1 px-2 rounded-full text-xs">{label}</button>' for key,label in [('ALL','All'),('exact','Exact time'),('window','Window'),('unknown','Not stated'),('conflicting','Conflicting')]))

    search=soup.find(id='global-search-input')
    if search: search['placeholder']='Search publications, localities or categories...'
    # Publication filters use the actual source vocabulary, not the old four generated categories.
    for ident,options in [('cat-filter-select',sorted({r['category'] for r in records})),('zone-filter-select',units)]:
        select=soup.find(id=ident)
        set_content(select,'<option value="ALL">All '+('categories' if ident.startswith('cat') else 'source localities')+'</option>'+''.join(f'<option value="{html.escape(v,quote=True)}">{html.escape(v)}</option>' for v in options))
    categories=soup.find(id='cat-filter-select')
    for key,label in [('property','Property (all source tags)'),('assault','Assault'),('women','Women’s / girls’ safety'),('vandalism','Vandalism — 0 loaded')]:
        categories.append(fragment(f'<option value="map:{key}">{label}</option>'))
    for ident in ['sphere-entropy-score','metric-avg-sev']:
        set_content(soup.find(id=ident),'Unavailable')
    map_header=soup.find(id='map-frame-container').find('button',attrs={'title':'Center on Bhopal'}).parent
    map_header.insert(0,fragment('<select id="basemap-select" aria-label="Basemap" onchange="setBasemap(this.value)" class="rounded-full bg-surface-container text-on-surface text-xs px-3 py-1 border border-white/10"><option value="osm">OpenStreetMap</option><option value="civic">Civic</option><option value="satellite">Satellite</option></select>'))
    # Keep legacy JS and the map engine. Replace only the data-specific render functions.
    script=soup.new_tag('script')
    script.string=(Path(__file__).resolve().parent/'static/official-dashboard.js').read_text()
    soup.body.append(script)
    return str(soup)
