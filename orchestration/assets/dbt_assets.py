import os
from pathlib import Path
from dagster_dbt import DbtProject, DbtCliResource, dbt_assets

DBT_PROJECT_DIR = Path(__file__).parents[2] / "dbt"

dbt_project = DbtProject(project_dir=DBT_PROJECT_DIR)
dbt_project.prepare_if_dev()

@dbt_assets(manifest=dbt_project.manifest_path)
def retail_weather_dbt_assets(context, dbt: DbtCliResource):
    yield from dbt.cli(["run"], context=context).stream()
