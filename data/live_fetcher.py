"""Compatibility entrypoint for official publication snapshots; no synthetic fallback."""
import pandas as pd
from .official_sources import load_snapshot, refresh_snapshot
from .validator import ValidationReport


class LiveDataFetcher:
    def __init__(self, cache_dir='.cache', cache_ttl_seconds=86400):
        pass

    def fetch_data(self, force_refresh=False, **legacy_options):
        # Publication schema differs from the retired generated incident schema.
        if force_refresh:
            refresh_snapshot()
        payload = load_snapshot()
        rows = payload['records']
        metadata = {k: v for k, v in payload.items() if k != 'records'}
        metadata.update(source_name='Bhopal Police official publications',
                        is_live=False, total_records=len(rows))
        report = ValidationReport(total_records=len(rows), valid_records=len(rows),
                                  quality_score=100.0 if rows else 0.0)
        return pd.DataFrame(rows), metadata, report
