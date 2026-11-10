// Implements the Motion and shell behavior in DESIGN.md. Loaded after official-dashboard.js, so these functions replace the legacy renderer.
const DS_REDUCED = matchMedia('(prefers-reduced-motion: reduce)');
const DS_LATTICE = (() => {
  const points = [], total = 520, golden = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < total; i++) {
    const y = 1 - (i / (total - 1)) * 2, radius = Math.sqrt(1 - y * y), theta = golden * i;
    points.push([Math.cos(theta) * radius, y, Math.sin(theta) * radius]);
  }
  return points;
})();

function dsThemeColor(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim().replace(/\s+/g, ',');
}

function dsProjector(cx, cy, radius, yaw, pitch) {
  const cosY = Math.cos(yaw), sinY = Math.sin(yaw), cosP = Math.cos(pitch), sinP = Math.sin(pitch), focal = radius * 4;
  return (x, y, z) => {
    const x1 = x * cosY + z * sinY, z1 = -x * sinY + z * cosY;
    const y2 = y * cosP - z1 * sinP, z2 = y * sinP + z1 * cosP;
    const scale = focal / (focal - z2);
    return { x: cx + x1 * scale, y: cy + y2 * scale, z: z2, scale };
  };
}

function dsDrawLattice(ctx, project, radius, dotSize) {
  const ink = dsThemeColor('--ink');
  for (const [x, y, z] of DS_LATTICE) {
    const p = project(x * radius, y * radius, z * radius), depth = (p.z / radius + 1) / 2;
    ctx.fillStyle = `rgba(${ink},${(0.05 + depth * depth * 0.5).toFixed(3)})`;
    ctx.beginPath();
    ctx.arc(p.x, p.y, dotSize * (0.45 + depth * 0.75), 0, Math.PI * 2);
    ctx.fill();
  }
}

function renderSphericalGraph() {
  if (!sphereCtx || !sphereCanvas) return;
  const ctx = sphereCtx, w = sphereWidth, h = sphereHeight, cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.4;
  const project = dsProjector(cx, cy, R, sphereYaw, spherePitch);
  const ink = dsThemeColor('--ink');
  ctx.clearRect(0, 0, w, h);
  dsDrawLattice(ctx, project, R, 1.15);
  const nodes = SPHERE_SECTORS.map(sector => {
    const lat = sector.lat * Math.PI / 180, lon = sector.lon * Math.PI / 180;
    sector.projected = project(R * Math.cos(lat) * Math.sin(lon), -R * Math.sin(lat), R * Math.cos(lat) * Math.cos(lon));
    return sector;
  }).sort((a, b) => a.projected.z - b.projected.z);
  for (const node of nodes) {
    const p = node.projected, front = p.z >= 0, radius = (node.nodeRadius || 8) * p.scale * (node === hoveredSphereNode ? 1.18 : 1);
    ctx.globalAlpha = front ? 0.95 : 0.25;
    ctx.fillStyle = node.color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
    ctx.fill();
    if (front && node.count) {
      ctx.globalAlpha = 0.45;
      ctx.strokeStyle = node.color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, radius + 4, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
    if (front) {
      ctx.fillStyle = `rgba(${ink},${node === hoveredSphereNode ? 1 : 0.82})`;
      ctx.font = '600 11px -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif';
      ctx.textAlign = 'center';
      const half = ctx.measureText(node.name).width / 2 + 6;
      ctx.fillText(node.name, Math.max(half, Math.min(w - half, p.x)), p.y - radius - 8);
    }
  }
}

function dsWhileVisible(element, draw) {
  let frame = null, visible = false;
  const run = () => { draw(); frame = visible && !document.hidden ? requestAnimationFrame(run) : null; };
  const sync = () => { if (visible && !document.hidden && frame === null) frame = requestAnimationFrame(run); };
  new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; sync(); }).observe(element);
  document.addEventListener('visibilitychange', sync);
}

function startSphereLoop() {
  if (!sphereCanvas) return;
  if (DS_REDUCED.matches) {
    autoSpinSphere = false;
    const label = document.getElementById('sphere-spin-label');
    if (label) label.textContent = 'Auto-Spin: Off';
  }
  let lastYaw = sphereYaw, velocity = 0;
  dsWhileVisible(sphereCanvas, () => {
    if (isSphereDragging) velocity = sphereYaw - lastYaw;
    else if (!DS_REDUCED.matches) {
      sphereYaw += velocity + (autoSpinSphere ? 0.004 : 0);
      velocity *= 0.94;
    }
    lastYaw = sphereYaw;
    renderSphericalGraph();
  });
}

function dsTilt() {
  if (DS_REDUCED.matches || !matchMedia('(pointer:fine)').matches) return;
  for (const card of document.querySelectorAll('.official-analytics-card, .ds-kpi')) {
    card.classList.add('ds-tilt');
    card.addEventListener('pointermove', event => {
      const box = card.getBoundingClientRect(), x = (event.clientX - box.left) / box.width - 0.5, y = (event.clientY - box.top) / box.height - 0.5;
      card.style.setProperty('--mx', `${(x + 0.5) * 100}%`);
      card.style.setProperty('--my', `${(y + 0.5) * 100}%`);
      card.style.transform = `perspective(900px) rotateX(${(-y * 2.5).toFixed(2)}deg) rotateY(${(x * 2.5).toFixed(2)}deg)`;
    });
    card.addEventListener('pointerleave', () => { card.style.transform = ''; });
  }
}

// Page scrolling must not be captured by the map until the visitor engages with it.
function dsMapScrollGuard() {
  if (typeof map === 'undefined' || !map) return;
  const flyTo = map.flyTo.bind(map);
  map.flyTo = (...args) => {
    if (document.body.dataset.view !== 'overview') window.switchTab('overview');
    map.invalidateSize();
    return flyTo(...args);
  };
  map.on('moveend', dsRenderLegend);
  dsRenderLegend();
  map.scrollWheelZoom.disable();
  map.on('click', () => map.scrollWheelZoom.enable());
  map.getContainer().addEventListener('mouseleave', () => map.scrollWheelZoom.disable());
}

const dsMapReady = setInterval(() => {
  if (typeof map === 'undefined' || !map || !markerClusterGroup) return;
  clearInterval(dsMapReady);
  dsMapScrollGuard();
  dsPopupSafeArea();
  window.addEventListener('resize', dsPopupSafeArea);
  map.on('popupopen', () => document.body.classList.add('ds-popup-open'));
  map.on('popupclose', () => document.body.classList.remove('ds-popup-open'));
  const select = document.getElementById('basemap-select');
  if (select) select.value = 'civic';
  setBasemap('civic');
}, 40);

// Esri's dark canvas has no place names, so its label tiles are added on top.
let dsDarkLabels = null;
const dsLegacySetBasemap = window.setBasemap;
window.setBasemap = function (type) {
  dsLegacySetBasemap(type);
  if (!dsDarkLabels) dsDarkLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', { className: 'ds-map-labels', zIndex: 20, maxZoom: 16 });
  const showLabels = type === 'civic' && document.documentElement.classList.contains('dark');
  if (showLabels && !map.hasLayer(dsDarkLabels)) dsDarkLabels.addTo(map);
  if (!showLabels && map.hasLayer(dsDarkLabels)) map.removeLayer(dsDarkLabels);
};

// The basemap follows the theme so glass panels keep their contrast.
const dsLegacyToggleTheme = window.toggleTheme;
window.toggleTheme = function () { dsLegacyToggleTheme(); updateMapTheme(); };


// Native fullscreen is blocked inside the Streamlit embed and on iPhones, so the map expands to fill the page instead.
function toggleMapFullscreen() {
  const expanded = document.body.classList.toggle('ds-map-expanded');
  const button = document.querySelector('button[onclick="toggleMapFullscreen()"]');
  if (button) {
    button.setAttribute('aria-pressed', String(expanded));
    button.title = expanded ? 'Exit full screen' : 'Full screen';
    button.querySelector('span').textContent = expanded ? 'fullscreen_exit' : 'fullscreen';
  }
  requestAnimationFrame(() => requestAnimationFrame(() => map.invalidateSize()));
}
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && document.body.classList.contains('ds-map-expanded')) toggleMapFullscreen();
});

function centerBhopal() {
  if (map) map.flyTo([23.25, 77.417], 13, { animate: !DS_REDUCED.matches, duration: 0.8 });
}

// Map legend: counts come from the markers actually drawn, and categories with no mapped report say why.
const DS_THANA_COLOR = '#0284c7';

function dsLegendItem(letter, color, label, state, modifiers = '') {
  const item = officialElement('span', '', `ds-legend-item ${modifiers}`);
  item.style.setProperty('--swatch', color);
  item.append(officialElement('b', letter), officialElement('strong', label), officialElement('span', state));
  return item;
}

function dsRenderLegend() {
  const legend = document.getElementById('map-legend');
  if (!legend || !map || !markerClusterGroup) return;
  const titles = markerClusterGroup.getLayers().map(layer => layer.options.title || '');
  const items = Object.keys(mapCategoryEnabled).map(key => {
    const pins = titles.filter(title => title.startsWith(mapCategoryLabels[key] + ' · ')).length;
    const reports = currentFiltered.filter(record => record.map_categories.includes(key)).length;
    const state = pins ? `${pins} ${pins === 1 ? 'pin' : 'pins'}`
      : !mapCategoryEnabled[key] ? 'Hidden'
      : reports ? (titles.length && currentFiltered.some(r => r.map_categories.includes(key) && r.map_reference) ? 'Shown under another pin' : 'No mapped location')
      : 'No verified records';
    return dsLegendItem(mapCategoryLetters[key], mapCategoryColors[key], mapCategoryLabels[key], state, pins ? '' : 'is-empty');
  });
  const thanas = policeFeatureGroup ? policeFeatureGroup.getLayers() : [], bounds = map.getBounds();
  const inView = thanas.filter(layer => bounds.contains(layer.getLatLng())).length;
  items.push(dsLegendItem('T', DS_THANA_COLOR, 'Thanas', thanas.length ? `${inView} of ${thanas.length} in view` : 'Hidden', `is-thana ${thanas.length ? '' : 'is-empty'}`));
  legend.replaceChildren(...items);

  const unmapped = document.getElementById('ds-unmapped');
  const without = currentFiltered.filter(record => !record.map_reference);
  unmapped.replaceChildren();
  if (without.length) {
    unmapped.append(officialElement('strong', 'Not on the map: '));
    without.forEach(record => {
      unmapped.append(`${record.category}, because the police post does not establish a location. `, officialSourceLink(record), ' ');
    });
  }
}

const dsLegacyRenderMap = window.renderMapLayers, dsLegacyRenderPolice = window.renderPoliceLayer;
window.renderMapLayers = function () { dsLegacyRenderMap(); dsRenderLegend(); };
window.renderPoliceLayer = function () { dsLegacyRenderPolice(); dsRenderLegend(); };

function dsShowEverything() {
  resetAllFilters();
  for (const key of Object.keys(mapCategoryEnabled)) {
    mapCategoryEnabled[key] = true;
    document.getElementById('map-category-' + key).checked = true;
  }
  const police = document.getElementById('overlay-police-chk');
  if (!police.checked) police.click();
  window.renderMapLayers();
  const points = [...markerClusterGroup.getLayers(), ...policeFeatureGroup.getLayers()].map(layer => layer.getLatLng());
  dsFitPoints(points, !DS_REDUCED.matches);
}

// A report category keeps its map color in every chart; localities cycle through a bright set.
const DS_BAR_COLORS = ['#fb7185', '#2fcf9a', '#fb923c', '#a78bfa', '#f472b6', '#22d3ee', '#facc15', '#f87171'];
function dsCategoryColor(category) {
  const record = ALL_CRIMES.find(item => item.category === category);
  return record ? mapCategoryColors[record.map_categories.includes('assault') ? 'assault' : record.map_categories[0]] : DS_BAR_COLORS[0];
}
const dsLegacyBars = window.officialBars;
window.officialBars = function (id, key) {
  dsLegacyBars(id, key);
  document.querySelectorAll(`#${id} .official-bar-row`).forEach((row, index) => {
    row.querySelector('.official-bar-fill').style.background = key === 'category' ? dsCategoryColor(row.querySelector('.official-bar-label').textContent) : DS_BAR_COLORS[index % DS_BAR_COLORS.length];
  });
};

// Dashboard shell: views, live KPIs and the publication feed all read the same filtered selection.
const DS_VIEW_TITLES = { overview: 'Overview', analytics: 'Analytics', records: 'Records', sources: 'Data sources', hotspots: 'Hotspots', 'ai-risk': 'AI risk' };
// Fits keep markers clear of the floating panels.
function dsMapPadding() {
  const edge = (selector, side, fallback) => { const box = document.querySelector(selector)?.getBoundingClientRect(); return box && box.width ? box[side] : fallback; };
  const wide = innerWidth >= 1024, gap = 24;
  const insets = wide
    ? { left: edge('.ds-filters', 'right', 0) + gap, top: edge('#ds-kpis', 'bottom', 0) + 72, right: innerWidth - edge('#ds-side', 'left', innerWidth) + gap, bottom: innerHeight - edge('#ds-map-footer', 'top', innerHeight) + gap }
    : { left: 24, top: edge('.ds-map-card>div:first-child', 'bottom', 200) + 28, right: 64, bottom: Math.max(90, innerHeight - edge('#ds-map-footer', 'top', innerHeight) + 28) };
  return { paddingTopLeft: [insets.left, insets.top], paddingBottomRight: [insets.right, insets.bottom] };
}
// Popups pan and shrink to stay in the clear map area, so their controls are never under a panel.
function dsPopupSafeArea() {
  const padding = dsMapPadding();
  L.Popup.mergeOptions({
    autoPanPaddingTopLeft: padding.paddingTopLeft,
    autoPanPaddingBottomRight: padding.paddingBottomRight,
    maxHeight: Math.max(180, innerHeight - padding.paddingTopLeft[1] - padding.paddingBottomRight[1] - 48),
  });
}
function dsFitPoints(points, animate) {
  if (points.length) map.fitBounds(L.latLngBounds(points), { ...dsMapPadding(), maxZoom: 14, animate });
}
window.fitReportPins = function () {
  if (map && markerClusterGroup) dsFitPoints(markerClusterGroup.getLayers().map(layer => layer.getLatLng()), false);
};
const dsLegacySwitchTab = window.switchTab, dsLegacyRender = window.renderRecordsTable;

window.switchTab = function (view) {
  document.body.dataset.view = view;
  officialText('ds-view-title', DS_VIEW_TITLES[view] || 'Overview');
  if (view === 'overview') {
    document.querySelectorAll('.nav-tab-btn').forEach(button => button.classList.toggle('active', button.id === 'tab-btn-overview'));
    map.invalidateSize();
  } else {
    dsLegacySwitchTab(view);
    if (view === 'analytics') requestAnimationFrame(() => window.dispatchEvent(new Event('resize')));  // The canvas measures zero while its view is hidden.
  }
  for (const button of document.querySelectorAll('.nav-tab-btn')) {
    if (button.classList.contains('active')) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  }
};
window.scrollToMap = window.navigateToMap = () => window.switchTab('overview');

function dsSetNumber(key, value) {
  const element = document.querySelector(`[data-ds-kpi="${key}"]`);
  if (!element) return;
  const from = Number(element.textContent), start = performance.now(), run = (element.dsRun || 0) + 1;
  element.dsRun = run;  // A newer update cancels any count still animating.
  if (DS_REDUCED.matches || !Number.isFinite(from) || from === value) { element.textContent = value; return; }
  const tick = now => {
    if (element.dsRun !== run) return;
    const progress = Math.min(1, (now - start) / 420);
    element.textContent = Math.round(from + (value - from) * (1 - Math.pow(1 - progress, 3)));
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function dsSetNote(key, value) {
  const element = document.querySelector(`[data-ds-note="${key}"]`);
  if (element) element.textContent = value;
}

function dsSpark() {
  const element = document.getElementById('ds-spark');
  if (!element) return;
  const months = {};
  for (const record of currentFiltered) months[record.date.slice(0, 7)] = (months[record.date.slice(0, 7)] || 0) + 1;
  const peak = Math.max(1, ...Object.values(months));
  element.replaceChildren(...Object.keys(months).sort().map(month => {
    const bar = document.createElement('i');
    bar.style.height = Math.max(14, months[month] / peak * 100) + '%';
    return bar;
  }));
}

function dsUpdateKpis() {
  const mapped = new Set(currentFiltered.filter(r => r.map_reference).map(r => r.neighborhood));
  const unlocated = currentFiltered.filter(r => !r.map_reference).length;
  const categories = officialCounts('category');
  dsSetNumber('selected', currentFiltered.length);
  dsSetNote('selected', `of ${ALL_CRIMES.length} reviewed`);
  dsSetNumber('pins', mapped.size);
  dsSetNote('pins', unlocated ? `${unlocated} selected without a usable locality` : 'Approximate references');
  const top = document.querySelector('[data-ds-kpi="category"]');
  if (top) top.textContent = categories[0]?.[0] || 'None';
  dsSetNote('category', categories[0] ? `${categories[0][1]} of ${currentFiltered.length} selected` : 'No publications selected');
  dsSpark();
}

function dsUpdateFreshness() {
  const status = document.getElementById('official-update-status'), element = document.querySelector('[data-ds-kpi="fresh"]');
  if (!status || !element) return;
  const days = Math.floor((Date.now() - new Date(status.dataset.checkedAt).getTime()) / 86400000);
  element.textContent = Number.isNaN(days) ? 'Unknown' : days === 0 ? 'Today' : `${days}d ago`;
  document.getElementById('ds-kpi-fresh').classList.toggle('is-stale', !(days < 2));
}

function dsRenderFeed() {
  const feed = document.getElementById('ds-feed');
  if (!feed) return;
  officialBars('ds-side-categories', 'category');
  const rows = [...currentFiltered].sort((a, b) => b.date.localeCompare(a.date));
  feed.replaceChildren(...rows.map(record => {
    const item = document.createElement('li');
    const category = officialElement('span', record.category);
    category.style.setProperty('--dot', dsCategoryColor(record.category));
    item.append(officialElement('time', record.date), officialElement('strong', record.neighborhood || 'Locality not established'), category);
    const actions = officialElement('div', '', 'ds-feed-actions');
    if (record.map_reference) {
      const show = officialElement('button', 'Show on map');
      show.type = 'button';
      show.onclick = () => { window.switchTab('overview'); map.flyTo([record.map_reference.latitude, record.map_reference.longitude], 14); };
      actions.append(show);
    }
    actions.append(officialSourceLink(record));
    item.append(actions);
    return item;
  }));
  if (!rows.length) feed.append(officialElement('li', 'No publications match these filters.'));
}

// Phones show each record as a card, so every cell carries its column name.
function dsLabelRecords() {
  const headings = [...document.querySelectorAll('#records-table thead th')].map(th => th.textContent.trim());
  for (const row of document.querySelectorAll('#records-table-body tr')) {
    [...row.children].forEach((cell, index) => { if (headings[index] && cell.colSpan === 1) cell.dataset.label = headings[index]; });
  }
  for (const button of document.querySelectorAll('#tab-pane-records button')) {
    if (/^Show All \(/.test(button.textContent.trim())) button.textContent = `Show All (${currentFiltered.length})`;
  }
  const more = document.getElementById('ds-feed-more');
  if (more) more.textContent = `View all ${currentFiltered.length} in Records`;
}

// The long legal evidence list starts collapsed on phones; the heading is a real button.
function dsCollapsibleSeverity() {
  const card = document.getElementById('severity-evidence')?.parentElement, heading = card?.querySelector('h3');
  if (!heading) return;
  const toggle = officialElement('button', heading.textContent, 'ds-collapse-toggle');
  toggle.type = 'button';
  toggle.setAttribute('aria-expanded', 'false');
  toggle.onclick = () => {
    const open = card.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
  };
  heading.replaceChildren(toggle);
  card.classList.add('ds-collapsible');
}

window.renderRecordsTable = function () {
  dsLegacyRender();
  dsLabelRecords();
  dsUpdateKpis();
  dsRenderFeed();
};

window.addEventListener('DOMContentLoaded', () => { dsTilt(); dsUpdateFreshness(); dsCollapsibleSeverity(); });
