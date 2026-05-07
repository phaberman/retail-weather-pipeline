# retail-weather-pipeline

End-to-end ELT pipeline simulating a retail analytics use case: a multi-city retailer needs to understand how weather conditions drive demand variability across markets, so planners can position inventory ahead of weather events.

**[View Live Dashboard →](https://datastudio.google.com/reporting/dfe232e5-a51a-4d86-bcd0-42ad2e845942)**

---

## Architecture

```
Open-Meteo API → GCS (raw JSON) → BigQuery (raw.weather) → dbt (staging + marts) → Looker Studio
```

Orchestrated end-to-end with Dagster. Runs daily at 06:00 UTC.

---

## Stack

| Layer | Tool |
|---|---|
| Ingestion | Python + Open-Meteo Archive API |
| Storage | Google Cloud Storage |
| Warehouse | BigQuery |
| Transformation | dbt Core |
| Orchestration | Dagster |
| Visualization | Looker Studio |

---

## Pipeline Overview

### Ingestion — `ingestion/open_meteo.py`
Pulls daily weather data for 5 US retail markets from the Open-Meteo free archive API (no auth required). Lands one JSON file per city in GCS at `weather/{city}/raw_{start}_{end}.json`.

Markets: New York · Chicago · Los Angeles · Houston · Seattle

Variables: `temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `windspeed_10m_max`, `weathercode`

### Loading — `loading/gcs_to_bq.py`
Reads the latest GCS blob per city, flattens Open-Meteo's columnar JSON into one row per date, and appends all cities into a single BigQuery table (`raw.weather`). Uses `WRITE_APPEND` for incremental loads.

### Transformation — `dbt/`
Three-layer dbt project:

| Model | Type | Description |
|---|---|---|
| `stg_weather` | View | Cleans and renames raw fields. Deduplicates on `(city, date)` via `ROW_NUMBER()` to handle incremental appends. Adds retail weather flags. |
| `mart_daily_weather` | Table | Daily fact table — one row per city per date. Foundation for downstream analysis. |
| `mart_city_monthly` | Table | Monthly aggregates per city: avg temp, total precipitation, rainy/freezing/hot/windy day counts, total weather impact days. |
| `mart_weather_alerts` | Table | Days flagged as high retail weather impact. Scored 0–4 by concurrent alert conditions. |

**Key dbt decision:** custom `generate_schema_name` macro overrides dbt's default schema-appending behavior, routing models to `staging` and `marts` datasets directly.

### Orchestration — `orchestration/`
Dagster software-defined assets wire the full pipeline into a single connected DAG:

```
raw_weather_gcs → weather_bigquery → stg_weather → mart_daily_weather
                                                 → mart_city_monthly
                                                 → mart_weather_alerts
```

**Key Dagster decision:** manual `@asset` + `AssetIn` definitions used instead of `@dbt_assets` decorator — the decorator does not support explicit upstream Python asset dependencies, which would break end-to-end lineage visibility.

---

## Project Structure

```
retail-weather-pipeline/
├── ingestion/
│   └── open_meteo.py         # API → GCS
├── loading/
│   └── gcs_to_bq.py          # GCS → BigQuery
├── dbt/
│   ├── dbt_project.yml
│   ├── macros/
│   │   └── generate_schema_name.sql
│   └── models/
│       ├── staging/
│       │   ├── sources.yml
│       │   ├── stg_weather.sql
│       │   └── stg_weather.yml
│       └── marts/
│           ├── mart_daily_weather.sql
│           ├── mart_city_monthly.sql
│           ├── mart_weather_alerts.sql
│           └── marts.yml
└── orchestration/
    ├── definitions.py
    └── assets/
        ├── ingest.py
        ├── load.py
        └── dbt_assets.py
```

---

## Local Setup

### Prerequisites
- Python 3.12+
- pyenv + pyenv-virtualenv
- GCP project with BigQuery and Cloud Storage APIs enabled
- Service account with BigQuery Admin + Storage Admin roles

### 1. Clone and create environment

```bash
git clone https://github.com/YOUR_USERNAME/retail-weather-pipeline.git
cd retail-weather-pipeline
pyenv virtualenv 3.12.9 retail-weather-pipeline-env
pyenv local retail-weather-pipeline-env
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```
# Must be absolute path — relative paths will fail at runtime
RETAIL_WEATHER_GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/your-key.json
GCP_PROJECT_ID=your-gcp-project-id
GCS_BUCKET_NAME=your-gcs-bucket-name
BQ_DATASET_RAW=raw
BQ_DATASET_STAGING=staging
BQ_DATASET_MARTS=marts
```

### 3. Configure dbt

```bash
cp dbt/profiles.yml.example dbt/profiles.yml
```

Edit `dbt/profiles.yml` with your GCP project ID and service account key path.

```bash
dbt deps --project-dir dbt
dbt debug --project-dir dbt
```

### 4. Run historical backfill

```bash
python ingestion/open_meteo.py
python loading/gcs_to_bq.py
dbt run --project-dir dbt
dbt test --project-dir dbt
```

### 5. Launch Dagster

```bash
dagster dev -f orchestration/definitions.py
```

Open `http://localhost:3000` → Assets → Materialize all.

---

## Key Design Decisions

**Explicit credentials over default ADC** — uses `RETAIL_WEATHER_GOOGLE_APPLICATION_CREDENTIALS` instead of `GOOGLE_APPLICATION_CREDENTIALS` to avoid conflicts with other GCP projects on the same machine.

**Single unified table over per-city tables** — `raw.weather` uses `city` as a dimension column, not a table namespace. Simplifies dbt modeling and mirrors real-world practice.

**WRITE_APPEND + dbt dedup** — incremental append pattern with `ROW_NUMBER()` dedup in staging mirrors production pipeline design. Raw layer accumulates history; staging always emits one clean row per `(city, date)`.

**generate_schema_name macro** — dbt's default `+schema` behavior appends to the profile dataset name rather than replacing it. Custom macro overrides this so models land in `staging` and `marts` directly.
