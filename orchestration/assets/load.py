from dagster import asset
from dotenv import load_dotenv

load_dotenv()

@asset(group_name="loading", compute_kind="python", deps=["raw_weather_gcs"])
def weather_bigquery():
    """Load weather data from GCS into BigQuery raw dataset."""
    from loading.gcs_to_bq import run
    run()
