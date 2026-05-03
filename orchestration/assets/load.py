# Loading asset: reads raw JSON from GCS and loads all cities into a single
# BigQuery table (raw.weather) using WRITE_TRUNCATE for idempotency.
# One unified table (vs. per-city tables) simplifies the dbt staging layer —
# city is a column, not a table namespace.


from dagster import asset
from dotenv import load_dotenv

load_dotenv()

@asset(group_name="loading", compute_kind="python", deps=["raw_weather_gcs"])
def weather_bigquery():
    """Load weather data from GCS into BigQuery raw dataset."""
    from loading.gcs_to_bq import run
    run()
