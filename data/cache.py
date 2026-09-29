"""
================================================================================
Bhopal Safety Intelligence - Ingestion Cache Manager
================================================================================
Caches fetched and validated crime records locally with TTL support,
avoiding repetitive network calls while guaranteeing data freshness.
================================================================================
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import pandas as pd

logger = logging.getLogger("bhopal_safety.cache")


class DataCache:
    def __init__(self, cache_dir: str = ".cache", default_ttl_seconds: int = 86400):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl_seconds
        os.makedirs(self.cache_dir, exist_ok=True)
        self.data_file = os.path.join(self.cache_dir, "crime_data_cache.json")
        self.meta_file = os.path.join(self.cache_dir, "cache_metadata.json")

    def is_valid(self) -> bool:
        if not os.path.exists(self.data_file) or not os.path.exists(self.meta_file):
            return False
        try:
            with open(self.meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            cached_time = datetime.fromisoformat(meta["timestamp"])
            ttl = meta.get("ttl_seconds", self.default_ttl)
            if datetime.now() - cached_time < timedelta(seconds=ttl):
                return True
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
        return False

    def load(self) -> Optional[Tuple[pd.DataFrame, Dict[str, Any]]]:
        if not self.is_valid():
            return None
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                records = json.load(f)
            with open(self.meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            df = pd.DataFrame(records)
            logger.info(f"Loaded {len(df)} records from local cache ({meta.get('data_source', 'Unknown')})")
            return df, meta
        except Exception as e:
            logger.error(f"Failed to read cache: {e}")
            return None

    def save(self, df: pd.DataFrame, source_name: str, quality_report: Optional[Dict[str, Any]] = None, ttl_seconds: Optional[int] = None):
        try:
            records = df.to_dict(orient="records")
            # Convert timestamps to string if necessary
            for r in records:
                for k, v in r.items():
                    if isinstance(v, (pd.Timestamp, datetime)):
                        r[k] = v.isoformat()

            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, default=str)

            meta = {
                "timestamp": datetime.now().isoformat(),
                "ttl_seconds": ttl_seconds or self.default_ttl,
                "data_source": source_name,
                "total_records": len(df),
                "quality_report": quality_report or {},
            }
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            logger.info(f"Cached {len(df)} records. Source: {source_name}")
        except Exception as e:
            logger.error(f"Failed to write cache: {e}")
