// Real publication data adapter. Retains the original map, theme, navigation and 3D engine.
function officialText(id, value) {const e=document.getElementById(id);if(e)e.textContent=value;}
function officialElement(tag,text,cls=''){const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e;}
function officialCounts(key){const counts={};for(const r of currentFiltered){if(key==='neighborhood'&&!r[key])continue;counts[r[key]]=(counts[r[key]]||0)+1;}return Object.entries(counts).sort((a,b)=>b[1]-a[1]);}
function officialBars(id,key){const e=document.getElementById(id);if(!e)return;e.replaceChildren();const counts=officialCounts(key);const max=counts.length?counts[0][1]:1;for(const [name,count] of counts){const row=officialElement('div','', 'flex items-center gap-3 py-2 text-xs');const label=officialElement('button',name,'text-left w-40 shrink-0');label.type='button';label.onclick=()=>key==='neighborhood'?filterByZone(name):setCategoryFilter(name);row.append(label);const bar=officialElement('div',String(count),'rounded-full bg-sky-600 text-white px-3 py-1');bar.style.width=(count/max*60)+'%';row.append(bar);e.append(row);}if(!counts.length)e.append(officialElement('p','No publications match these filters.'));}
function updateKPIs(){officialText('metric-total-count',currentFiltered.length);officialText('header-records-count',currentFiltered.length+' Publications');officialText('metric-avg-sev','Unknown');officialText('metric-top-crime',officialCounts('category')[0]?.[0]||'No matching data');officialText('metric-top-sector',officialCounts('neighborhood')[0]?.[0]||'No matching data');officialText('training-record-count','Unavailable');}
function updateSphericalGraph(){officialText('source-locality-coverage',currentFiltered.filter(r=>r.neighborhood).length+' of '+currentFiltered.length+' selected publications have a source-named locality. Unlocated publications are excluded from area nodes; percentages use all selected publications.');const counts=Object.fromEntries(officialCounts('neighborhood'));const max=Math.max(...Object.values(counts),1);for(const s of SPHERE_SECTORS){s.count=counts[s.name]||0;s.avgSev='Unknown';s.nodeRadius=6+s.count/max*12;const cats={};for(const r of currentFiltered.filter(r=>r.neighborhood===s.name))cats[r.category]=(cats[r.category]||0)+1;s.dominant=Object.keys(cats).sort((a,b)=>cats[b]-cats[a])[0]||'No matching publications';}const top=officialCounts('neighborhood')[0];officialText('sphere-apex-sector',top?.[0]||'No matching data');officialText('sphere-apex-pct',top?Math.round(top[1]/currentFiltered.length*100)+'%':'Unavailable');officialText('sphere-entropy-score','Selected sample');officialBars('sphere-category-dispersion-list','category');}
function updateCharts(){officialBars('sector-bar-container','neighborhood');officialBars('modalities-container','category');const body=document.getElementById('official-coverage-body');if(body){body.replaceChildren();for(const [unit,count] of officialCounts('neighborhood')){const row=document.createElement('tr');for(const v of [unit,String(count),'Unavailable'])row.append(officialElement('td',v,'p-3 text-xs'));body.append(row);}}updateSphericalGraph();renderEvidencePanels();}
function renderRecordsTable() {
 const body=document.getElementById('records-table-body');if(!body)return;body.replaceChildren();
 const rows=currentFiltered.slice(0,showAllRecords?currentFiltered.length:50);
 officialText('records-shown-count',rows.length);officialText('records-total-count',currentFiltered.length);
 for(const r of rows){const row=officialElement('tr','','border-b border-white/10 text-xs');row.dataset.publicationId=r.id;
  for(const value of [r.id,r.date,r.neighborhood||'Occurrence locality not established',r.reporting_unit,r.category,r.occurrence_label,r.legal_basis])row.append(officialElement('td',value,'py-3 px-3'));
  if(r.map_reference){const view=officialElement('button','View approximate locality','block text-primary underline mt-1');view.type='button';view.onclick=()=>{map.flyTo([r.map_reference.latitude,r.map_reference.longitude],15);scrollToMap();};row.children[2].append(view);}
  const cell=document.createElement('td');cell.className='py-3 px-3';cell.append(officialSourceLink(r));row.append(cell);body.append(row);
 }
 if(!rows.length){const row=document.createElement('tr');const cell=officialElement('td','No publications match these filters.','p-4');cell.colSpan=8;row.append(cell);body.append(row);}
}
function downloadCSV() {
 const columns=['id','date','neighborhood','reporting_unit','category','subtype','incident_date','occurrence_time','occurrence_start','occurrence_end','time_of_day','legal_basis','source_notes','related_case_group','source_url','source_sha256','lat','lon','severity','map_reference'];
 const headings=['PublicationID','PublicationDate','SourceLocality','ReportingUnit','Category','Summary','SelectedEventDate','SelectedEventTimeIST','OccurrenceWindowStart','OccurrenceWindowEnd','TimeEvidenceKind','ReportedLegalBasis','SourceNotes','RelatedCaseGroup','SourceURL','SourceSHA256','IncidentLatitude','IncidentLongitude','Severity','LocalityReference'];
 const cell=v=>'"'+String(v??'').replace(/^[=+@-]/,"'$&").replaceAll('"','""')+'"';
 const csv=[headings.join(','),...currentFiltered.map(r=>columns.map(c=>cell(c==='map_reference'?JSON.stringify(r.map_reference):r[c])).join(','))].join('\r\n');
 const u=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=u;a.download='bhopal-official-publications.csv';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);
}
function renderPoliceLayer(){policeFeatureGroup.clearLayers();if(!showPolice)return;for(const ps of POLICE_STATIONS){const icon=L.divIcon({html:'<div style="background:#0284c7;color:white;border:2px solid white;border-radius:8px;padding:3px;line-height:1">P</div>',className:'',iconSize:[24,24]});const popup=officialElement('div','');popup.append(officialElement('strong',ps.name));popup.append(officialElement('p','Published police facility location. Not a crime location.'));const source=officialElement('a','Official map and contacts');source.href=ps.contact_url;source.target='_blank';source.rel='noopener noreferrer';popup.append(source);L.marker([ps.lat,ps.lon],{icon}).bindPopup(popup).addTo(policeFeatureGroup);}}
window.addEventListener('DOMContentLoaded',()=>{updateKPIs();updateCharts();renderRecordsTable();});
function setBasemap(type){currentBasemap=type;const dark=document.documentElement.classList.contains('dark');const key=type==='civic'?(dark?'civic_dark':'civic_light'):type;applyTileUrl(BASEMAP_TILES[key],BASEMAP_ATTRIBUTIONS[key],19);}
function updateMapTheme(){if(currentBasemap==='civic')setBasemap('civic');}
showCorridors=false;showAiZones=false;showAnomalies=false;showHotspots=false;
function setSeverityThreshold(){minSeverity=1;officialText('sev-slider-val','No official score');applyFilters();}
function officialSourceLink(record) {
 const link=officialElement('a','Official source ↗','text-primary underline');
 link.href=record.source_url;link.target='_blank';link.rel='noopener noreferrer';return link;
}
function setTimeFilter(value) {
 currentTimeOfDay=value;
 for(const b of document.querySelectorAll('[data-time-kind]')){
  b.classList.toggle('bg-primary-container',b.dataset.timeKind===value);
  b.setAttribute('aria-pressed',String(b.dataset.timeKind===value));
 }
 officialText('time-filter-label',value==='ALL'?'All evidence':value);
 applyFilters();
}
function renderEvidencePanels() {
 const time=document.getElementById('occurrence-evidence');
 const severity=document.getElementById('severity-evidence');
 const labels={exact:'Exact time',window:'Reported window',unknown:'Time not stated',conflicting:'Conflicting chronology'};
 if(time){
  time.replaceChildren();
  const summary=officialElement('div','','flex flex-wrap gap-2 mb-3');
  for(const [kind,label] of Object.entries(labels)){
   const count=currentFiltered.filter(r=>r.time_of_day===kind).length;
   const button=officialElement('button',`${label}: ${count}`,'px-3 py-1 rounded-full bg-surface-container border border-white/10 text-xs');
   button.onclick=()=>setTimeFilter(kind);summary.append(button);
  }
  time.append(summary);
  for(const r of currentFiltered){
   const row=officialElement('div','','py-2 border-b border-white/10 text-xs');
   row.append(officialElement('strong',(r.neighborhood||'Locality not established')+' · '+r.id));
   row.append(officialElement('p',r.occurrence_label,'my-1 text-on-surface-variant'));
   row.append(officialSourceLink(r));time.append(row);
  }
  if(!currentFiltered.length)time.append(officialElement('p','No matching publications.'));
 }
 if(severity){
  severity.replaceChildren();
  severity.append(officialElement('p',`Official numeric severity: not published for ${currentFiltered.length} selected publications.`,'font-bold text-sm mb-3'));
  for(const [basis,count] of officialCounts('legal_basis')){
   const row=officialElement('div','','py-2 border-b border-white/10 text-xs');
   row.append(officialElement('strong',basis+' · '+count+' publication(s)'));
   for(const r of currentFiltered.filter(r=>r.legal_basis===basis)){
    const detail=officialElement('p',r.id+' · '+(r.neighborhood||'Locality not established')+' ','mt-1');detail.append(officialSourceLink(r));row.append(detail);
    if(r.time_of_day==='conflicting')row.append(officialElement('p',r.source_notes,'mt-1 text-on-surface-variant'));
   }
   severity.append(row);
  }
 }
}
// Locality references and incident GPS coordinates remain separate in memory and CSV.
const mapCategoryEnabled={property:true,assault:true,women:true,vandalism:true,other:true};
const mapCategoryColors={property:'#f59e0b',assault:'#ef4444',women:'#d946ef',vandalism:'#10b981',other:'#8b5cf6'};
function toggleMapCategory(key,checked){mapCategoryEnabled[key]=checked;renderMapLayers();}
function renderMapLayers(){
 if(!map||!markerClusterGroup)return;
 if(!map.getPane('sourceLocalityPins'))map.createPane('sourceLocalityPins').style.zIndex='650';
 markerClusterGroup.clearLayers();
 if(heatLayer&&map.hasLayer(heatLayer))map.removeLayer(heatLayer);
 for(const group of [aiZonesFeatureGroup,anomaliesFeatureGroup,hotspotsFeatureGroup])if(group)group.clearLayers();
 const groups=new Map();
 for(const r of currentFiltered){
  if(!r.map_reference||!r.map_categories.some(k=>mapCategoryEnabled[k]))continue;
  if(!groups.has(r.related_case_group))groups.set(r.related_case_group,[]);
  groups.get(r.related_case_group).push(r);
 }
 for(const records of groups.values()){
  const r=records[0],ref=r.map_reference;
  const kind=r.map_categories.includes('assault')&&mapCategoryEnabled.assault?'assault':r.map_categories.find(k=>mapCategoryEnabled[k]);
  const popup=officialElement('div','','text-xs');
  popup.style.maxWidth='290px';popup.append(officialElement('strong',r.category+' · '+r.neighborhood));
  popup.append(officialElement('p','APPROXIMATE LOCALITY REFERENCE — NOT INCIDENT GPS','font-bold my-2'));
  popup.append(officialElement('p',ref.basis,'my-2'));
  popup.append(officialElement('p','Reference landmark: '+ref.reference_name,'my-2'));
  popup.append(officialElement('p',r.subtype,'my-2'));
  popup.append(officialElement('p',r.occurrence_label,'my-2'));
  for(const item of records){const line=officialElement('p',item.id+' · published '+item.date+' · '+item.occurrence_label+' ');line.append(officialSourceLink(item));popup.append(line);}
  const geo=officialElement('a','Published geographic reference');geo.href=ref.source_url;geo.target='_blank';geo.rel='noopener noreferrer';popup.append(geo);
  popup.append(officialElement('p','Linked publications may update the same investigation; this pin is not an independent incident count.','mt-2'));
  L.circleMarker([ref.latitude,ref.longitude],{pane:'sourceLocalityPins',radius:10,color:mapCategoryColors[kind],fillColor:mapCategoryColors[kind],fillOpacity:.4,weight:3,dashArray:'3,2'}).bindPopup(popup).addTo(markerClusterGroup);
 }
 officialText('telemetry-node-count',groups.size);
 for(const key of Object.keys(mapCategoryEnabled))officialText('map-count-'+key,'('+currentFiltered.filter(r=>r.map_categories.includes(key)).length+' loaded)');
 const notice=document.getElementById('official-map-coverage');
 if(notice){
  const missing=currentFiltered.filter(r=>!r.map_reference).length;
  notice.textContent=`${groups.size} approximate locality pins from ${currentFiltered.length} selected source publications. Pins are published area/landmark references, not exact crime locations. Related updates share one pin. ${missing} selected publications lack a usable locality reference. A women’s/girls’ safety report is loaded without an established occurrence location. Vandalism has no verified records loaded; coverage is incomplete.`;
  if(currentVizMode==='heat')notice.textContent+=' A crime-density heatmap requires incident GPS; approximate reference pins remain visible instead.';
 }
}
const resetOfficialBase=resetAllFilters;
resetAllFilters=function(){resetOfficialBase();setDateRangeFilter('ALL');document.getElementById('date-range-filter-select').value='ALL';};
