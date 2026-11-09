"""Rearrange the generated page into the app shell defined in DESIGN.md."""
from bs4 import BeautifulSoup

NAV_ITEMS = [
    ('overview', 'space_dashboard', 'Overview', False),
    ('analytics', 'monitoring', 'Analytics', False),
    ('records', 'table_rows', 'Records', False),
    ('sources', 'verified', 'Sources', False),
    ('hotspots', 'whatshot', 'Hotspots', True),
    ('ai-risk', 'psychology', 'AI Risk', True),
]


def _fragment(markup):
    return BeautifulSoup(markup, 'html.parser')


def _kpi(ident, label, value, note):
    return (f'<article class="ds-kpi" id="ds-kpi-{ident}"><p class="ds-kpi-label">{label}</p>'
            f'<p class="ds-kpi-value" data-ds-kpi="{ident}">{value}</p><p class="ds-kpi-note" data-ds-note="{ident}">{note}</p></article>')


def _nav_button(button, icon, label, awaiting):
    button.clear()
    tag = '<span class="ds-nav-tag">No data</span>' if awaiting else ''
    button.append(_fragment(f'<span class="material-symbols-outlined" aria-hidden="true">{icon}</span><span class="ds-nav-label">{label}</span>{tag}'))


def apply_dashboard_shell(soup, total, facilities, pending):
    """Move existing controls into the shell. Element ids are kept so the data scripts continue to work."""
    root = soup.find('header').parent
    header = soup.find('header')
    analytics = soup.find(id='analytics-section')
    tabs = soup.find(id='nav-tabs-bar')
    status = soup.find(id='official-update-status')
    zone = soup.find(id='ribbon-active-zone')
    footer = soup.find('footer')
    workspace = soup.find(id='map-frame-container').parent
    filters_column = workspace.find(id='left-controls-wrapper').parent

    brand = header.find('h1').find_parent('div', class_='flex-col').parent.extract()
    brand['class'] = ['ds-brand']

    tabs_row = tabs.parent
    tabs.extract()
    tabs_row.decompose()
    tabs['class'] = ['ds-nav']
    tabs['aria-label'] = 'Dashboard views'
    tabs.name = 'nav'
    overview = soup.new_tag('button', id='tab-btn-overview', type='button', onclick="switchTab('overview')")
    overview['class'] = ['nav-tab-btn', 'active']
    tabs.find(id='tab-btn-analytics')['class'] = ['nav-tab-btn']
    buttons = {'overview': overview}
    for ident, *_ in NAV_ITEMS[1:]:
        buttons[ident] = tabs.find(id='tab-btn-' + ident).extract()
    tabs.clear()
    for ident, icon, label, awaiting in NAV_ITEMS:
        _nav_button(buttons[ident], icon, label, awaiting)
        tabs.append(buttons[ident])

    rail = _fragment('<aside id="ds-rail"></aside>').find('aside')
    rail.append(brand)
    rail.append(tabs)
    rail.append(_fragment(f'<p class="ds-rail-note">{facilities} police facilities are mapped. Publication counts are not incident counts.</p>'))

    title = _fragment('<div class="ds-view-heading"><p class="ds-product">Bhopal Safety Intelligence</p><h2 id="ds-view-title">Overview</h2></div>')
    header['class'] = ['ds-topbar']
    header.insert(0, title)
    zone.extract()
    zone['class'] = ['ds-zone']
    zone.string = 'Area: All Bhopal'
    header.find(id='global-search-input').find_parent('div', class_='max-w-xl').insert_after(zone)

    kpis = _fragment('<section id="ds-kpis" aria-label="Key figures">' + ''.join([
        _kpi('selected', 'Publications in view', total, f'of {total} reviewed').replace('</article>', '<div id="ds-spark" aria-hidden="true"></div></article>'),
        _kpi('pins', 'Mapped localities', '–', 'Approximate references'),
        _kpi('category', 'Top category', '–', 'In current selection'),
        _kpi('fresh', 'Source freshness', '–', f'{pending if pending is not None else "Unknown"} posts awaiting review'),
    ]) + '</section>')

    side = _fragment('<aside id="ds-side"><section class="ds-panel"><h3>Report types</h3><div id="ds-side-categories"></div></section>'
                     '<section class="ds-panel ds-feed-panel"><h3>Latest publications</h3><ol id="ds-feed"></ol><button id="ds-feed-more" type="button" onclick="switchTab(\'records\')">View all records</button></section></aside>').find('aside')
    coverage = soup.find(id='official-map-coverage').extract()
    coverage['class'] = ['ds-panel']
    side.append(coverage)

    workspace['id'] = 'ds-overview'
    workspace['class'] = []
    filters_column['class'] = ['ds-filters']
    soup.find(id='map-frame-container')['class'] = []
    workspace.append(side)

    filters = soup.find(id='left-controls-wrapper')
    categories = soup.find(id='map-category-controls').extract()
    categories['class'] = ['ds-category-chips']
    filters.insert(0, categories)
    filters.insert(0, _fragment('<div id="ds-sheet-head"><h3>Filters and layers</h3><button type="button" id="ds-sheet-close" onclick="toggleMobileFilters()">Done</button></div>'))

    # Controls with no supporting data stay out of the working view; their empty states remain in the navigation.
    what_to_see = soup.find(id='what-to-see-bar')
    what_to_see['class'] = ['ds-hidden']
    legend = soup.find(id='map-legend').extract()
    map_box = soup.find(id='leaflet-map').find_parent(class_='relative')
    map_box['class'] = ['relative', 'ds-map-box', 'overflow-hidden']
    map_card = map_box.parent
    map_card['class'] = ['ds-map-card']
    telemetry = map_box.find_next_sibling('div')
    if telemetry:
        telemetry['class'] = ['ds-hidden']
    map_box.insert_after(legend)

    analytics['class'] = ['ds-view']
    if footer:
        soup.find(id='tab-pane-sources').append(footer.extract())

    main = _fragment('<div id="ds-main"></div>').find('div')
    for node in (header.extract(), kpis, workspace.extract(), analytics.extract(), status.extract()):
        main.append(node)
    status['class'] = ['ds-statusbar']
    if not total:
        status.insert(0, 'Data unavailable · no synthetic fallback. ')

    root.clear()
    root['id'] = 'ds-app'
    root['class'] = []
    root.append(rail)
    root.append(main)
    soup.body['data-view'] = 'overview'
