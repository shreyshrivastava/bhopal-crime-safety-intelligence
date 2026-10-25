"""Verify the original dashboard shell with real publications and official facilities."""
import asyncio
import csv
import io
import json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts'

async def verify():
    results=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        for width,height in [(1400,900),(390,844)]:
            page=await browser.new_page(viewport={'width':width,'height':height},accept_downloads=True)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            await page.goto((ROOT/'index.html').as_uri(),wait_until='networkidle',timeout=60000)
            await page.wait_for_function('typeof map !== "undefined" && map && policeFeatureGroup && policeFeatureGroup.getLayers().length===48')
            await page.locator('#app-preloader').wait_for(state='detached')
            assert await page.locator('.leaflet-tile-loaded').count()>0
            assert await page.evaluate('markerClusterGroup.getLayers().length')==8
            assert await page.evaluate('ALL_CRIMES.every(r=>r.lat===null && r.lon===null && r.severity===null)')
            assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth')
            await page.get_by_label('Basemap',exact=True).select_option('satellite')
            assert 'World_Imagery' in await page.evaluate('currentTileLayer._url')
            await page.get_by_label('Basemap',exact=True).select_option('civic')
            dark=await page.evaluate('document.documentElement.classList.contains("dark")')
            await page.locator('#theme-toggle-btn').click()
            assert await page.evaluate('document.documentElement.classList.contains("dark")') != dark
            await page.get_by_label('Basemap',exact=True).select_option('osm')
            if width<600: await page.get_by_text('Filters & Map Layers',exact=True).click()
            await page.locator('#overlay-police-chk').uncheck()
            assert await page.evaluate('policeFeatureGroup.getLayers().length')==0
            await page.locator('#overlay-police-chk').check()
            assert await page.evaluate('policeFeatureGroup.getLayers().length')==48
            await page.locator('#map-category-property').uncheck()
            assert await page.evaluate('markerClusterGroup.getLayers().length')==5
            await page.locator('#map-category-assault').uncheck()
            assert await page.evaluate('markerClusterGroup.getLayers().length')==4
            await page.locator('#map-category-other').uncheck()
            assert await page.evaluate('markerClusterGroup.getLayers().length')==0
            await page.locator('#map-category-property').check()
            assert await page.evaluate('markerClusterGroup.getLayers().length')==4
            await page.locator('#map-category-assault').check()
            await page.locator('#map-category-other').check()
            await page.locator('#cat-filter-select').select_option('map:women')
            assert await page.evaluate('markerClusterGroup.getLayers().length')==0
            assert await page.evaluate('policeFeatureGroup.getLayers().length')==48
            assert await page.evaluate('currentFiltered.length')==1
            assert await page.evaluate('currentFiltered[0].map_reference') is None
            await page.locator('#cat-filter-select').select_option('map:vandalism')
            assert await page.evaluate('currentFiltered.length')==0
            await page.locator('#cat-filter-select').select_option('Property crime')
            assert await page.evaluate('currentFiltered.length')==4
            await page.locator('#zone-filter-select').select_option('Danish Kunj')
            assert await page.evaluate('currentFiltered.length')==2
            await page.locator('#reset-filters-btn').click()
            assert await page.evaluate('currentFiltered.length')==10
            assert await page.evaluate('SPHERE_SECTORS.every(s=>s.name!=="Bhopal Crime Branch")')
            assert await page.evaluate('SPHERE_SECTORS.some(s=>s.name==="Budhwara, Talaiya")')
            await page.locator('#time-btn-exact').click()
            assert await page.evaluate('currentFiltered.length')==1
            assert await page.evaluate('currentFiltered[0].occurrence_time')=='19:30'
            await page.locator('#time-btn-window').click()
            assert await page.evaluate('currentFiltered.length')==1
            assert await page.evaluate('currentFiltered[0].occurrence_time') is None
            await page.locator('#time-btn-conflicting').click()
            assert await page.evaluate('currentFiltered.length')==1
            await page.locator('#time-btn-unknown').click()
            assert await page.evaluate('currentFiltered.length')==7
            await page.locator('#time-btn-all').click()
            assert await page.evaluate('currentFiltered.length')==10
            await page.locator('#global-search-input').fill('narcotics')
            assert await page.evaluate('currentFiltered.length')==1
            await page.locator('#global-search-input').fill('')
            for tab in ['analytics','ai-risk','hotspots','records','sources']:
                await page.locator('#tab-btn-'+tab).click()
                assert await page.locator('#tab-pane-'+tab).is_visible()
            await page.locator('#tab-btn-records').click()
            assert await page.locator('#records-table-body tr').count()==10
            async with page.expect_download() as event:
                await page.locator('button[onclick="downloadCSV()"]').click()
            download=await event.value;target=OUT/f'dashboard-{width}.csv';await download.save_as(target)
            rows=list(csv.DictReader(io.StringIO(target.read_text(encoding='utf-8-sig'))))
            assert next(r for r in rows if r['PublicationID']=='BHP-PUB-5327')['SelectedEventTimeIST']=='19:30'
            assert len(rows)==10 and all(r['SourceURL'].startswith('https://bhopal.mppolice.gov.in/') for r in rows)
            assert all(r['IncidentLatitude']=='' and r['Severity']=='' for r in rows)
            await page.locator('#tab-btn-analytics').click()
            assert await page.locator('#occurrence-evidence').get_by_text('Exact time: 1',exact=True).is_visible()
            assert await page.locator('#severity-evidence').get_by_text('NDPS Act, sections 8/21 · 1 publication(s)',exact=True).is_visible()
            await page.locator('#sphere-spin-toggle').click()
            assert not await page.evaluate('autoSpinSphere')
            await page.evaluate('setVizMode("heat")')
            assert await page.evaluate('!heatLayer || heatLayer._latlngs.length===0')
            assert await page.evaluate('markerClusterGroup.getLayers().length')==8
            await page.evaluate('setVizMode("cluster"); centerBhopal()')
            await page.screenshot(path=str(OUT/('restored-desktop.png' if width==1400 else 'restored-mobile.png')),full_page=True)
            assert not errors,errors
            results.append(dict(target='restored dashboard',viewport=f'{width}x{height}',facilities=48,publications=10,basemaps='pass',theme='pass',filters='pass',tabs='pass',csv='pass',sphere='pass',fabricated_incident_points=0,locality_reference_pins=8,javascript_errors=errors,horizontal_overflow=False))
            await page.close()
        page=await browser.new_page()
        await page.goto('http://127.0.0.1:8507')
        frame=page.frame_locator('iframe').first
        await frame.locator('.leaflet-tile-loaded').first.wait_for(timeout=30000)
        assert await frame.locator('.leaflet-marker-icon:not(.marker-cluster)').count()==48
        assert await frame.locator('#records-table-body tr').count()==10
        results.append(dict(target='local Streamlit',facilities=48,publications=10,status='pass'))
        await browser.close()
    (OUT/'browser-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
if __name__=='__main__':asyncio.run(verify())
