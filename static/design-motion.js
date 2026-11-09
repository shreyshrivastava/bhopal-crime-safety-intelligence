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
  const accent = dsThemeColor('--accent'), ink = dsThemeColor('--ink');
  ctx.clearRect(0, 0, w, h);
  dsDrawLattice(ctx, project, R, 1.15);
  const nodes = SPHERE_SECTORS.map(sector => {
    const lat = sector.lat * Math.PI / 180, lon = sector.lon * Math.PI / 180;
    sector.projected = project(R * Math.cos(lat) * Math.sin(lon), -R * Math.sin(lat), R * Math.cos(lat) * Math.cos(lon));
    return sector;
  }).sort((a, b) => a.projected.z - b.projected.z);
  for (const node of nodes) {
    const p = node.projected, front = p.z >= 0, radius = (node.nodeRadius || 8) * p.scale * (node === hoveredSphereNode ? 1.18 : 1);
    ctx.fillStyle = `rgba(${accent},${front ? 0.92 : 0.22})`;
    ctx.beginPath();
    ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
    ctx.fill();
    if (front && node.count) {
      ctx.strokeStyle = `rgba(${accent},.35)`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, radius + 4, 0, Math.PI * 2);
      ctx.stroke();
    }
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
      card.style.transform = `perspective(900px) rotateX(${(-y * 2.5).toFixed(2)}deg) rotateY(${(x * 2.5).toFixed(2)}deg)`;
    });
    card.addEventListener('pointerleave', () => { card.style.transform = ''; });
  }
}

// Page scrolling must not be captured by the map until the visitor engages with it.
function dsMapScrollGuard() {
  if (typeof map === 'undefined' || !map) return;
  map.scrollWheelZoom.disable();
  map.on('click', () => map.scrollWheelZoom.enable());
  map.getContainer().addEventListener('mouseleave', () => map.scrollWheelZoom.disable());
}

window.addEventListener('load', () => setTimeout(dsMapScrollGuard, 1500));


// Dashboard shell: views, live KPIs and the publication feed all read the same filtered selection.
const DS_VIEW_TITLES = { overview: 'Overview', analytics: 'Analytics', records: 'Records', sources: 'Data sources', hotspots: 'Hotspots', 'ai-risk': 'AI risk' };
const dsLegacySwitchTab = window.switchTab, dsLegacyRender = window.renderRecordsTable;

window.switchTab = function (view) {
  document.body.dataset.view = view;
  officialText('ds-view-title', DS_VIEW_TITLES[view] || 'Overview');
  if (view === 'overview') {
    document.querySelectorAll('.nav-tab-btn').forEach(button => button.classList.toggle('active', button.id === 'tab-btn-overview'));
    requestAnimationFrame(() => map.invalidateSize());
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
  const from = Number(element.textContent), start = performance.now();
  if (DS_REDUCED.matches || !Number.isFinite(from) || from === value) { element.textContent = value; return; }
  const tick = now => {
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
    item.append(officialElement('time', record.date), officialElement('strong', record.neighborhood || 'Locality not established'), officialElement('span', record.category));
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
