import os
import json
import requests
from datetime import date, timedelta
from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2 import service_account


load_dotenv()

CREDENTIALS_PATH = os.getenv("RETAIL_WEATHER_GOOGLE_APPLICATION_CREDENTIALS")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)

CITIES = {
    "new_york":    {"latitude": 40.7128,  "longitude": -74.0060},
    "chicago":     {"latitude": 41.8781,  "longitude": -87.6298},
    "los_angeles": {"latitude": 34.0522,  "longitude": -118.2437},
    "houston":     {"latitude": 29.7604,  "longitude": -95.3698},
    "seattle":     {"latitude": 47.6062,  "longitude": -122.3321},
}

VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "windspeed_10m_max",
    "weathercode",
]

def fetch_weather(city: str, lat: float, lon: float, start: str, end: str) -> dict:
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": ",".join(VARIABLES),
        "timezone": "America/Chicago",
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph",
        "precipitation_unit": "inch",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    data["city"] = city
    return data


def upload_to_gcs(data: dict, city: str, start: str, end: str) -> None:
    client = storage.Client(project=GCP_PROJECT_ID, credentials=credentials)
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob_path = f"weather/{city}/raw_{start}_{end}.json"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(
        json.dumps(data, indent=2),
        content_type="application/json",
    )
    print(f"  Uploaded: gs://{GCS_BUCKET_NAME}/{blob_path}")


def run(start_date: str, end_date: str) -> None:
    for city, coords in CITIES.items():
        print(f"Fetching {city}...")
        data = fetch_weather(
            city=city,
            lat=coords["latitude"],
            lon=coords["longitude"],
            start=start_date,
            end=end_date,
        )
        upload_to_gcs(data, city, start_date, end_date)
    print("Ingestion complete.")


if __name__ == "__main__":
    # Backfill: 3 months of historical data
    start = (date.today() - timedelta(days=730)).isoformat()
    end = (date.today() - timedelta(days=1)).isoformat()
    run(start, end)
