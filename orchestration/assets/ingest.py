# Ingestion asset: pulls daily weather data from Open-Meteo's free archive API
# for 5 US retail markets and lands raw JSON in GCS.
# Runs in incremental mode (yesterday only) when triggered by the daily schedule.
# Backfill (2 years) is handled by running open_meteo.py directly — not via
# Dagster — to keep the orchestration layer focused on daily operations.


import os
from datetime import date, timedelta
from dagster import asset
from dotenv import load_dotenv

load_dotenv()

@asset(group_name="ingestion", compute_kind="python")
def raw_weather_gcs():
    """Fetch daily weather from Open-Meteo and land in GCS."""
    from ingestion.open_meteo import run
    start = (date.today() - timedelta(days=1)).isoformat()
    end   = (date.today() - timedelta(days=1)).isoformat()
    run(start, end)
