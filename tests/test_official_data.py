import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests
from data.official_sources import load_snapshot, validate_snapshot, refresh_snapshot
from data.live_fetcher import LiveDataFetcher
from data.public_records import get_verified_public_records
from dashboard import generate_dashboard as generate_official_html, load_facilities


class OfficialDataTests(unittest.TestCase):
    def setUp(self):
        self.payload = load_snapshot()

    def test_checked_in_sources_are_valid(self):
        self.assertEqual(validate_snapshot(self.payload), self.payload)
        self.assertEqual(len(self.payload['records']), 10)
        self.assertEqual(len({r['related_case_group'] for r in self.payload['records']}), 9)
        self.assertTrue(all(r['latitude'] is None and r['longitude'] is None for r in self.payload['records']))
        selected = {r['source_post_id']:r for r in self.payload['records']}
        self.assertEqual(selected[5327]['incident_date'],'2026-09-10')
        self.assertIsNone(selected[5380]['incident_date'])

    def test_reject_unofficial_or_injected_url(self):
        for url in ['https://example.com/', 'javascript:alert(1)', 'https://bhopal.mppolice.gov.in.attacker.invalid/']:
            p = copy.deepcopy(self.payload)
            p['records'][0]['source_url'] = url
            with self.assertRaises(ValueError): validate_snapshot(p)

    def test_reject_duplicates_invented_locations_and_unreviewed_fields(self):
        changes = [lambda p: p['records'].append(p['records'][0]),
                   lambda p: p['records'][0].update(latitude=23.2),
                   lambda p: p['records'][0].update(summary='Unsupported report'),
                   lambda p: p['records'][0].update(name='Person'),
                   lambda p: p.update(retrieved_at='2026-10-25T10:00:00')]
        for change in changes:
            p = copy.deepcopy(self.payload); change(p)
            with self.assertRaises(ValueError): validate_snapshot(p)

    def test_missing_or_corrupt_snapshot_has_empty_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'
            for value in [None, '{broken', json.dumps({'data_kind':'synthetic'})]:
                if value is not None: path.write_text(value)
                payload = load_snapshot(path)
                self.assertEqual(payload['records'], [])
                self.assertIn('Data unavailable', generate_official_html(payload))

    def test_failed_refresh_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'; path.write_text('original')
            def fail(*args, **kwargs): raise requests.Timeout('source unavailable')
            with self.assertRaises(requests.Timeout): refresh_snapshot(path, get=fail)
            self.assertEqual(path.read_text(), 'original')

    def test_legacy_cache_cannot_reintroduce_generated_data(self):
        with patch('data.cache.DataCache.load', side_effect=AssertionError('old cache used')):
            df, meta, report = LiveDataFetcher().fetch_data()
        self.assertEqual(len(df), 10)
        self.assertFalse(meta['is_live'])
        self.assertIn('source_post_id', df)
        self.assertNotIn('severity', df)

    def test_production_avoids_demo_and_unverified_people(self):
        from streamlit.testing.v1 import AppTest
        with patch('data_generator.generate_crime_dataset', side_effect=AssertionError('synthetic generator called')), patch('ai.risk_model.train_and_evaluate_risk_model', side_effect=AssertionError('demo model called')):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(get_verified_public_records()['records'], [])

    def test_demo_model_requires_explicit_opt_in(self):
        import pandas as pd
        from ai.risk_model import train_and_evaluate_risk_model
        with self.assertRaises(ValueError): train_and_evaluate_risk_model(pd.DataFrame())
        with self.assertRaises(ValueError): train_and_evaluate_risk_model(pd.DataFrame(self.payload['records']), synthetic_demo=True)

    def test_html_has_no_generated_records_or_performance_claims(self):
        page = generate_official_html(self.payload)
        self.assertNotIn('80% accurate', page)
        self.assertNotIn('BHP-2026-', page)
        self.assertIn('No production model or accuracy claim is available', page)
        self.assertIn('Publication dates do not determine', page)
        self.assertIn('source_sha256', page)

    def test_original_map_navigation_and_charts_remain(self):
        page = generate_official_html(self.payload)
        for key in ['leaflet-map','theme-toggle-btn','tab-btn-analytics','tab-btn-ai-risk','tab-btn-hotspots','tab-btn-records','tab-btn-sources','spherical-graph-canvas','basemap-select']:
            self.assertIn('id="'+key+'"', page)
        self.assertNotIn('10 PS • 3 Corridors', page)

    def test_facilities_have_official_map_provenance(self):
        from dashboard import FACILITIES
        metadata = json.loads(FACILITIES.read_text())
        self.assertEqual(metadata['source_url'],'https://bhopal.mppolice.gov.in/')
        self.assertEqual(len(load_facilities()),48)
        self.assertEqual(load_facilities()[0]['name'],'TT Nagar Police Station')
        self.assertAlmostEqual(load_facilities()[0]['lat'],23.2359122)

    def test_3d_nodes_are_source_localities_not_police_units(self):
        import re
        page = generate_official_html(self.payload)
        nodes = json.loads(re.search(r'const SPHERE_SECTORS = (\[.*?\]);', page, re.S).group(1))
        names = {n['name'] for n in nodes}
        self.assertNotIn('Bhopal Crime Branch', names)
        self.assertIn('MP Nagar Zone 1', names)
        self.assertIn('Budhwara, Talaiya', names)
        self.assertEqual(len(names),8)
        self.assertIn('const AMBIENT_PARTICLES = [];',page)

    def test_source_time_evidence_preserves_exact_windows_and_conflicts(self):
        rows = {r['source_post_id']:r['reviewed_facts'] for r in self.payload['records']}
        self.assertEqual(rows[5327]['occurrence']['time'],'19:30')
        self.assertEqual(rows[5347]['occurrence']['kind'],'window')
        self.assertIsNone(rows[5347]['occurrence']['time'])
        self.assertEqual(rows[5380]['occurrence']['kind'],'conflicting')
        self.assertIsNone(rows[5380]['occurrence']['date'])
        self.assertEqual(rows[5340]['locality'],'MP Nagar Zone 1')
        self.assertEqual(rows[5337]['locality'],'Budhwara, Talaiya')

    def test_invented_time_or_locality_rejected(self):
        for key,value in [('locality','Bhopal Crime Branch'),('occurrence',{'time':'23:00'})]:
            payload=copy.deepcopy(self.payload)
            payload['records'][0]['reviewed_facts'][key]=value
            with self.assertRaises(ValueError):validate_snapshot(payload)

    def test_changed_source_evidence_does_not_overwrite_snapshot(self):
        from types import SimpleNamespace
        def get(*args,**kwargs):
            return SimpleNamespace(status_code=200,raise_for_status=lambda:None,
                json=lambda:{'id':5223,'status':'publish','content':{'rendered':'Changed source without reviewed evidence'}})
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'snapshot.json';target.write_text('original')
            with self.assertRaisesRegex(ValueError,'Reviewed evidence changed'):refresh_snapshot(target,get=get)
            self.assertEqual(target.read_text(),'original')

    def test_map_references_are_separate_from_incident_coordinates(self):
        from dashboard import load_map_references
        refs=load_map_references()
        self.assertEqual(len(refs),8)
        self.assertTrue(all(r['precision']=='locality_reference' for r in refs.values()))
        self.assertAlmostEqual(refs['Mata Mandir']['latitude'],23.224633)
        self.assertIn('not the private burglary location',refs['Danish Kunj']['basis'])
        self.assertTrue(all(r['latitude'] is None and r['longitude'] is None for r in self.payload['records']))

    def test_unavailable_categories_are_not_filled_with_fake_records(self):
        from data.reviewed_facts import MAP_CATEGORIES
        self.assertEqual(MAP_CATEGORIES[5017],['property','assault'])
        self.assertFalse(any('vandalism' in tags for tags in MAP_CATEGORIES.values()))
        self.assertEqual(MAP_CATEGORIES[5223],['women'])
        source=next(r for r in self.payload['records'] if r['source_post_id']==5223)
        self.assertIsNone(source['reviewed_facts']['locality'])

if __name__ == '__main__': unittest.main()
