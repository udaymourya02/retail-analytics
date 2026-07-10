"""
config.py
=========
Central config loader. Reads from environment variables (set via .env locally
or GitHub Actions secrets in production). Never hardcode credentials.

Usage:
    from etl.utils.config import config
    project_id = config.GCP_PROJECT_ID
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Google Cloud
    GCP_PROJECT_ID: str   = os.getenv("GCP_PROJECT_ID", "retailco-analytics")
    GCP_DATASET:    str   = os.getenv("GCP_DATASET",    "warehouse")
    GCP_LOCATION:   str   = os.getenv("GCP_LOCATION",   "EU")

    # POS API
    POS_API_BASE_URL: str = os.getenv("POS_API_BASE_URL", "https://api.pos.retailco.internal")
    POS_CLIENT_ID:    str = os.getenv("POS_CLIENT_ID",    "")
    POS_CLIENT_SECRET:str = os.getenv("POS_CLIENT_SECRET","")

    # Salesforce CRM
    SF_INSTANCE_URL:  str = os.getenv("SF_INSTANCE_URL",  "")
    SF_CLIENT_ID:     str = os.getenv("SF_CLIENT_ID",     "")
    SF_CLIENT_SECRET: str = os.getenv("SF_CLIENT_SECRET", "")

    # Google Ads
    GOOGLE_ADS_DEVELOPER_TOKEN: str = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
    GOOGLE_ADS_CUSTOMER_ID:     str = os.getenv("GOOGLE_ADS_CUSTOMER_ID",     "")

    # Meta Ads
    META_ACCESS_TOKEN: str = os.getenv("META_ACCESS_TOKEN", "")
    META_AD_ACCOUNT:   str = os.getenv("META_AD_ACCOUNT",   "")

    # WMS SFTP
    WMS_SFTP_HOST:     str = os.getenv("WMS_SFTP_HOST", "")
    WMS_SFTP_USER:     str = os.getenv("WMS_SFTP_USER", "")
    WMS_SFTP_KEY_PATH: str = os.getenv("WMS_SFTP_KEY_PATH", "")

    # Alerting
    ALERT_EMAIL_TO:    str = os.getenv("ALERT_EMAIL_TO", "data-team@retailco.com")
    SENDGRID_API_KEY:  str = os.getenv("SENDGRID_API_KEY", "")

    # Pipeline behaviour
    MAX_RETRIES:       int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_S:   int = int(os.getenv("RETRY_BACKOFF_S", "30"))
    BATCH_SIZE:        int = int(os.getenv("BATCH_SIZE", "1000"))

    # Local dev: use CSV files instead of live APIs
    USE_SAMPLE_DATA:   bool = os.getenv("USE_SAMPLE_DATA", "true").lower() == "true"
    SAMPLE_DATA_DIR:   str  = os.getenv("SAMPLE_DATA_DIR", "data/raw")


config = Config()
