"""
bigquery_loader.py
==================
Loads transformed DataFrames into Google BigQuery.
Supports both full-refresh and incremental (append) load strategies.

Author: Uday Mourya
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from etl.utils.config import config
from etl.utils.logger import logger


class BigQueryLoader:
    """Handles all BigQuery write operations for the pipeline."""

    def __init__(self):
        self.client     = bigquery.Client(project=config.GCP_PROJECT_ID)
        self.project    = config.GCP_PROJECT_ID
        self.dataset    = config.GCP_DATASET
        self.location   = config.GCP_LOCATION

    def _table_ref(self, table_name: str) -> str:
        return f"{self.project}.{self.dataset}.{table_name}"

    def load(
        self,
        df: pd.DataFrame,
        table_name: str,
        write_disposition: str = "WRITE_APPEND",
        schema: list | None = None,
    ) -> int:
        """
        Load a DataFrame to BigQuery.

        Args:
            df:                 DataFrame to load
            table_name:         Target table name (without project/dataset prefix)
            write_disposition:  'WRITE_APPEND' (default) or 'WRITE_TRUNCATE'
            schema:             Optional BigQuery schema list. Auto-detected if None.

        Returns:
            Number of rows loaded.
        """
        if df.empty:
            logger.warning(f"[LOADER] Skipping {table_name} — empty DataFrame")
            return 0

        table_ref = self._table_ref(table_name)
        logger.info(f"[LOADER] Loading {len(df):,} rows → {table_ref} ({write_disposition})")

        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
            autodetect=(schema is None),
            schema=schema or [],
            create_disposition="CREATE_IF_NEEDED",
        )

        try:
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()   # Wait for completion
            loaded = self.client.get_table(table_ref).num_rows
            logger.info(f"[LOADER] ✓ {table_name}: {len(df):,} rows loaded successfully")
            return len(df)
        except Exception as e:
            logger.error(f"[LOADER] ✗ Failed to load {table_name}: {e}")
            raise

    def load_quarantine(self, df: pd.DataFrame, run_id: str) -> None:
        """Append quarantined records to the data quality table."""
        if df.empty:
            return
        df["run_id"] = run_id
        self.load(df, "data_quality_quarantine", write_disposition="WRITE_APPEND")

    def log_pipeline_run(
        self,
        run_id: str,
        source_system: str,
        records_extracted: int,
        records_loaded: int,
        records_quarantined: int,
        status: str,
        started_at: datetime,
        error_message: str | None = None,
    ) -> None:
        """Write a row to the pipeline_run_log audit table."""
        completed_at = datetime.utcnow()
        log_row = pd.DataFrame([{
            "run_id":               run_id,
            "run_date":             started_at.date().isoformat(),
            "source_system":        source_system,
            "records_extracted":    records_extracted,
            "records_loaded":       records_loaded,
            "records_quarantined":  records_quarantined,
            "status":               status,
            "error_message":        error_message,
            "started_at":           started_at.isoformat(),
            "completed_at":         completed_at.isoformat(),
            "duration_seconds":     int((completed_at - started_at).total_seconds()),
        }])
        self.load(log_row, "pipeline_run_log", write_disposition="WRITE_APPEND")
        logger.info(f"[LOADER] Pipeline run logged: {run_id} | {status}")

    def table_exists(self, table_name: str) -> bool:
        try:
            self.client.get_table(self._table_ref(table_name))
            return True
        except NotFound:
            return False

    def run_query(self, sql: str) -> pd.DataFrame:
        """Execute a SQL query and return results as a DataFrame."""
        logger.debug(f"[LOADER] Running query: {sql[:100]}...")
        return self.client.query(sql).to_dataframe()
