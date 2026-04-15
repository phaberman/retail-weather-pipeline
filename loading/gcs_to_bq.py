import os
import json
from dotenv import load_dotenv
from google.cloud import storage, bigquery
from google.oauth2 import service_account

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
BQ_DATASET_RAW = os.getenv("BQ_DATASET_RAW")
CREDENTIALS_PATH = os.getenv("RETAIL_WEATHER_GOOGLE_APPLICATION_CREDENTIALS")

credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)

CITIES = [
    "new_york",
    "chicago",
    "los_angeles",
    "houston",
    "seattle",
]

SCHEMA = [
    bigquery.SchemaField("city",                 "STRING",  mode="REQUIRED"),
    bigquery.SchemaField("date",                 "DATE",    mode="REQUIRED"),
    bigquery.SchemaField("temperature_2m_max",   "FLOAT",   mode="NULLABLE"),
    bigquery.SchemaField("temperature_2m_min",   "FLOAT",   mode="NULLABLE"),
    bigquery.SchemaField("precipitation_sum",    "FLOAT",   mode="NULLABLE"),
    bigquery.SchemaField("windspeed_10m_max",    "FLOAT",   mode="NULLABLE"),
    bigquery.SchemaField("weathercode",          "INTEGER", mode="NULLABLE"),
]


def parse_city_data(raw: dict) -> list[dict]:
    """Flatten Open-Meteo's columnar JSON into one row per date."""
    daily = raw["daily"]
    city = raw["city"]
    rows = []
    for i, date in enumerate(daily["time"]):
        rows.append({
            "city":               city,
            "date":               date,
            "temperature_2m_max": daily["temperature_2m_max"][i],
            "temperature_2m_min": daily["temperature_2m_min"][i],
            "precipitation_sum":  daily["precipitation_sum"][i],
            "windspeed_10m_max":  daily["windspeed_10m_max"][i],
            "weathercode":        daily["weathercode"][i],
        })
    return rows


def load_all_cities(bq_client: bigquery.Client, gcs_client: storage.Client) -> None:
    all_rows = []

    for city in CITIES:
        bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        blobs = list(bucket.list_blobs(prefix=f"weather/{city}/"))
        if not blobs:
            print(f"  No files found for {city}, skipping.")
            continue

        blob = sorted(blobs, key=lambda b: b.updated, reverse=True)[0]
        print(f"  Reading: gs://{GCS_BUCKET_NAME}/{blob.name}")
        raw = json.loads(blob.download_as_text())
        rows = parse_city_data(raw)
        all_rows.extend(rows)
        print(f"  Parsed {len(rows)} rows for {city}")

    if not all_rows:
        print("No rows to load. Exiting.")
        return

    # Write all cities to a single table — WRITE_TRUNCATE makes this idempotent
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.weather"
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    job = bq_client.load_table_from_json(all_rows, table_id, job_config=job_config)
    job.result()
    print(f"\nLoaded {len(all_rows)} total rows → {table_id}")


def run() -> None:
    bq_client = bigquery.Client(project=GCP_PROJECT_ID, credentials=credentials)
    gcs_client = storage.Client(project=GCP_PROJECT_ID, credentials=credentials)
    load_all_cities(bq_client, gcs_client)
    print("Loading complete.")


if __name__ == "__main__":
    run()
