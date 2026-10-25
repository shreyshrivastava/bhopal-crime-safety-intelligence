import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import requests
from data.update_monitor import discover, refresh_all, load_report
from data.official_sources import load_snapshot


def response(posts, pages='1', status=200):
    return SimpleNamespace(status_code=status, headers={'X-WP-TotalPages': pages},
        raise_for_status=lambda: None, json=lambda: posts)


def post(identifier):
    return dict(id=identifier, date='2026-10-20T10:00:00', status='publish',
        link=f'https://bhopal.mppolice.gov.in/?p={identifier}',
        title='Private details must not be retained', content='Never copy raw content')


class UpdateMonitorTests(unittest.TestCase):
    def test_discovers_paginated_metadata_without_promoting_incidents(self):
        replies=iter([response([post(5223),post(6000)],'2'),response([post(6001)],'2')])
        report=discover(get=lambda *a,**kw:next(replies))
        self.assertEqual(report['indexed_publications'],3)
        self.assertEqual([r['source_post_id'] for r in report['pending_review']],[6000,6001])
        self.assertNotIn('Private details',json.dumps(report))
        self.assertNotIn('latitude',json.dumps(report))
        self.assertEqual(set(report['pending_review'][0]),{'source_post_id','publication_date','source_url'})

    def test_rejects_redirects_foreign_urls_duplicates_and_partial_index(self):
        foreign=post(6000);foreign['link']='https://other.example/report'
        fixtures=[response([],status=302),response([foreign]),response([post(6000),post(6000)]),response([],pages='6'),response({},pages='1')]
        for fixture in fixtures:
            with self.subTest(fixture=fixture), self.assertRaises(ValueError):
                discover(get=lambda *a,**kw:fixture)

    def test_source_failure_retains_both_previous_files(self):
        for failure in ('discovery','reviewed'):
            with tempfile.TemporaryDirectory() as d:
                snapshot=Path(d)/'publications.json';report=Path(d)/'updates.json'
                snapshot.write_text('old snapshot');report.write_text('old report')
                kwargs={'side_effect':requests.Timeout('offline')} if failure=='discovery' else {'return_value':{}}
                with patch('data.update_monitor.discover',**kwargs), patch('data.update_monitor.refresh_snapshot',side_effect=ValueError('evidence changed')):
                    with self.assertRaises((ValueError,requests.Timeout)):refresh_all(snapshot,report)
                self.assertEqual(snapshot.read_text(),'old snapshot')
                self.assertEqual(report.read_text(),'old report')

    def test_success_and_invalid_status_are_distinct(self):
        expected=discover(get=lambda *a,**kw:response([post(6000)]))
        snapshot=load_snapshot()
        with tempfile.TemporaryDirectory() as d:
            s=Path(d)/'publications.json';r=Path(d)/'updates.json'
            with patch('data.update_monitor.discover',return_value=expected),patch('data.update_monitor.refresh_snapshot',return_value=snapshot):
                refresh_all(s,r)
            self.assertEqual(load_report(r),expected)
            self.assertEqual(json.loads(s.read_text()),snapshot)
            broken=copy.deepcopy(expected);broken['checked_at']='2026-01-01T10:00:00'
            r.write_text(json.dumps(broken))
            self.assertIsNone(load_report(r))
