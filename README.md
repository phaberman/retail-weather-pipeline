# retail-weather-pipeline

A production-style ELT pipeline simulating a retail analytics use case: a multi-city retailer needs to understand how weather conditions drive demand variability across markets, so planners can position inventory ahead of weather events.

---

## Architecture

```
Open-Meteo API → GCS (raw JSON) → BigQuery (raw) → dbt (staging + marts) → Looker Studio
                                                              ↑
                                                          Dagster (orchestration)
```

**Stack:** Python 3.12 · Open-Meteo API · Google Cloud Storage · BigQuery · dbt Core · Dagster · Looker Studio

---

## Markets Covered

| City | Climate Profile |
|---|---|
| New York | High seasonality, cold winters |
| Chicago | Volatile weather, extreme temperature swings |
| Los Angeles | Mild baseline — contrast market |
| Houston | Heat and humidity driven demand |
| Seattle | High precipitation, strong rain gear market |

---

## Pipeline Stages

### 1. Ingestion (`ingestion/open_meteo.py`)
Pulls daily weather data from the [Open-Meteo Archive API](https://open-meteo.com/) for all 5 cities. On first run, performs a 2-year historical backfill. On subsequent runs, pulls yesterday's data. Lands one JSON file per city in GCS.

### 2. Loading (`loading/gcs_to_bq.py`)
Reads each city's latest JSON from GCS, flattens Open-Meteo's columnar format into one row per city per date, and loads all cities into a single `raw.weather` table in BigQuery using `WRITE_TRUNCATE` for idempotency.

### 3. Transformation (`dbt/`)
dbt Core models in two layers:

| Layer | Model | Description |
|---|---|---|
| Staging | `stg_weather` | Cleaned, renamed, retail flag columns added |
| Marts | `mart_daily_weather` | Daily fact table — foundation for all analysis |
| Marts | `mart_city_monthly` | Monthly aggregates: temp, precip, weather impact days |
| Marts | `mart_weather_alerts` | High-impact days scored by alert condition count |

### 4. Orchestration (`orchestration/`)
Dagster wires all pipeline steps into a single DAG with explicit asset dependencies:

```
raw_weather_gcs → weather_bigquery → stg_weather → mart_daily_weather
                                                 → mart_city_monthly
                                                 → mart_weather_alerts
```

Scheduled daily at 06:00 UTC via `ScheduleDefinition`.

---

## Key Engineering Decisions

**Single `raw.weather` table over per-city tables**
All 5 cities load into one table with a `city` column. Simpler dbt models, cleaner lineage, mirrors real-world practice.

**Explicit credential isolation**
Uses `RETAIL_WEATHER_GOOGLE_APPLICATION_CREDENTIALS` (not the default `GOOGLE_APPLICATION_CREDENTIALS`) to avoid conflicts with other GCP projects. Credentials loaded explicitly via `google.oauth2.service_account.Credentials.from_service_account_file()` in all scripts.

**Manual `@asset` definitions over `@dbt_assets` decorator**
`@dbt_assets` does not support explicit `deps` wiring to upstream Python assets in current Dagster versions, which splits the lineage graph. Manual `@asset` + `AssetIn` definitions produce a single connected DAG end-to-end.

**`generate_schema_name` macro in dbt**
dbt's `+schema` config appends to the profile dataset by default rather than replacing it. A custom macro overrides this behavior so models land in `staging` and `marts` directly as named — not `raw_staging` or `raw_marts`.

**`WRITE_TRUNCATE` for idempotency**
BigQuery loads use `WRITE_TRUNCATE` so any rerun produces the same result without duplicating rows.

---

## Local Setup

### Prerequisites
- Python 3.12+
- pyenv + pyenv-virtualenv
- GCP project with BigQuery and Cloud Storage APIs enabled
- Service account with BigQuery Admin + Storage Admin roles

### Environment

```bash
git clone https://github.com/YOUR_USERNAME/retail-weather-pipeline.git
cd retail-weather-pipeline
pyenv virtualenv 3.12.9 retail-weather-pipeline-env
pyenv local retail-weather-pipeline-env
pip install -r requirements.txt
```

Copy and populate the env file:

```bash
cp .env.example .env
```

```
RETAIL_WEATHER_GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
GCP_PROJECT_ID=your-gcp-project-id
GCS_BUCKET_NAME=your-gcs-bucket
BQ_DATASET_RAW=raw
BQ_DATASET_STAGING=staging
BQ_DATASET_MARTS=marts
```

Copy and populate the dbt profiles file:

```bash
cp dbt/profiles.yml.example dbt/profiles.yml
```

### Run manually

```bash
# Ingest (backfill on first run)
python ingestion/open_meteo.py

# Load GCS → BigQuery
python loading/gcs_to_bq.py

# Transform with dbt
dbt run --project-dir dbt
dbt test --project-dir dbt
```

### Run via Dagster

```bash
dagster dev -f orchestration/definitions.py
```

Open `http://localhost:3000` → Assets → Materialize all.

---

## Project Structure

```
retail-weather-pipeline/
├── ingestion/
│   └── open_meteo.py          # Open-Meteo API → GCS
├── loading/
│   └── gcs_to_bq.py           # GCS → BigQuery raw
├── dbt/
│   ├── models/
│   │   ├── staging/            # stg_weather view
│   │   └── marts/              # 3 analytical tables
│   ├── macros/                 # generate_schema_name override
│   ├── dbt_project.yml
│   └── profiles.yml.example
├── orchestration/
│   ├── assets/
│   │   ├── ingest.py           # Dagster asset: ingestion
│   │   ├── load.py             # Dagster asset: loading
│   │   └── dbt_assets.py      # Dagster assets: dbt models
│   └── definitions.py          # Jobs, schedules, resources
├── .env.example
├── requirements.txt
└── README.md
```
