# Dagster Definitions: wires all assets, schedules, and resources into a single
# deployable object. Assets are registered explicitly (not auto-discovered) to
# maintain clear visibility into what the pipeline owns. The dbt resource is
# shared across all dbt assets via Dagster's resource injection pattern.
# Schedule: daily at 06:00 UTC — runs after midnight US time to ensure
# yesterday's data is fully available from Open-Meteo's archive API.


from dagster import Definitions, ScheduleDefinition, define_asset_job
from dotenv import load_dotenv

from orchestration.assets.ingest import raw_weather_gcs
from orchestration.assets.load import weather_bigquery
from orchestration.assets.dbt_assets import (
    DBT_PROJECT_DIR,
    stg_weather,
    mart_daily_weather,
    mart_city_monthly,
    mart_weather_alerts,
)

load_dotenv()

daily_weather_job = define_asset_job(
    name="daily_weather_job",
    selection=[
        raw_weather_gcs,
        weather_bigquery,
        stg_weather,
        mart_daily_weather,
        mart_city_monthly,
        mart_weather_alerts,
    ],
)

daily_schedule = ScheduleDefinition(
    job=daily_weather_job,
    cron_schedule="0 6 * * *",
)

defs = Definitions(
    assets=[
        raw_weather_gcs,
        weather_bigquery,
        stg_weather,
        mart_daily_weather,
        mart_city_monthly,
        mart_weather_alerts,
    ],
    schedules=[daily_schedule],
)
