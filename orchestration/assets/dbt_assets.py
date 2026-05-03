# Why manual @asset definitions instead of @dbt_assets:
# dagster-dbt's @dbt_assets decorator does not support explicit upstream deps
# to Python assets (e.g. weather_bigquery), breaking end-to-end lineage.
# Manual @asset + AssetIn gives Dagster full DAG visibility.
# Why subprocess instead of DbtCliResource:
# DbtCliResource.cli() requires @dbt_assets manifest metadata — incompatible
# with manual @asset definitions. subprocess gives equivalent execution without
# that constraint.

import subprocess
from pathlib import Path
from dagster import asset, AssetIn, OpExecutionContext

DBT_PROJECT_DIR = Path(__file__).parents[2] / "dbt"


def run_dbt_model(context: OpExecutionContext, model: str) -> None:
    """Run a single dbt model via subprocess."""
    result = subprocess.run(
        ["dbt", "run", "--select", model, "--project-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise Exception(f"dbt model '{model}' failed. See logs above.")


@asset(
    group_name="dbt_staging",
    compute_kind="dbt",
    ins={"weather_bigquery": AssetIn(key="weather_bigquery")},
)
def stg_weather(context: OpExecutionContext, weather_bigquery):
    """Cleaned and renamed daily weather data for 5 US retail markets."""
    run_dbt_model(context, "stg_weather")


@asset(
    group_name="dbt_marts",
    compute_kind="dbt",
    ins={"stg_weather": AssetIn(key="stg_weather")},
)
def mart_daily_weather(context: OpExecutionContext, stg_weather):
    """Daily weather fact table for all 5 retail markets."""
    run_dbt_model(context, "mart_daily_weather")


@asset(
    group_name="dbt_marts",
    compute_kind="dbt",
    ins={"stg_weather": AssetIn(key="stg_weather")},
)
def mart_city_monthly(context: OpExecutionContext, stg_weather):
    """Monthly weather aggregates per city."""
    run_dbt_model(context, "mart_city_monthly")


@asset(
    group_name="dbt_marts",
    compute_kind="dbt",
    ins={"stg_weather": AssetIn(key="stg_weather")},
)
def mart_weather_alerts(context: OpExecutionContext, stg_weather):
    """Days flagged as high retail weather impact."""
    run_dbt_model(context, "mart_weather_alerts")
