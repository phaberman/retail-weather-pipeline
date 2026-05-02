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
