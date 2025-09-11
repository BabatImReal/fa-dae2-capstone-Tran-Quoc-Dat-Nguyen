import os
import requests
from dotenv import load_dotenv

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