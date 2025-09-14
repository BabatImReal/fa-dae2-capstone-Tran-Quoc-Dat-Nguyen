import os
import requests
import json
import time
from dotenv import load_dotenv
from pathlib import Path


def save_data(data: list, filename: str) -> 'Path':
    """Save data to timestamped JSON file."""
    timestamp = int(time.time())
    file_path = Path("data/external") / f"{filename}_{timestamp}.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return file_path

load_dotenv()
API_KEY = os.getenv("YOUR-OPENAQ-API-KEY")  # Make sure your .env has API_KEY=your_openaq_api_key

url = "https://api.openaq.org/v3/instruments/2  "
headers = {
    "X-API-Key": API_KEY
}

response = requests.get(url, headers=headers)
print("Status code:", response.status_code)
print("Response:", response.json())\

print("Rate limit used:", response.headers.get("x-ratelimit-used"))
print("Rate limit reset:", response.headers.get("x-ratelimit-reset"))
print("Rate limit limit:", response.headers.get("x-ratelimit-limit"))
print("Rate limit remaining:", response.headers.get("x-ratelimit-remaining"))

# Test the /locations/2178/latest API and save response as JSON
latest_url = "https://api.openaq.org/v3/locations/2178/latest"
latest_response = requests.get(latest_url, headers=headers)
print("Latest API Status code:", latest_response.status_code)
latest_data = latest_response.json()
print("Latest API Response:", latest_data)

save_data(latest_data, "location_2178_latest")


