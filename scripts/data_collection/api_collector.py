# scripts/data_collection/api_collector.py
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class APIDataCollector:
    def __init__(self, api_name: str):
        self.api_name = api_name
        self.api_url = os.getenv("API_URL")
        if not self.api_url:
            raise ValueError("API_URL environment variable is not set. Please check your .env or environment configuration.")
        self.api_key = os.getenv("API_KEY")
        self.max_records = int(os.getenv("MAX_RECORDS", 100))
        self.batch_size = int(os.getenv("BATCH_SIZE", 10))
        self.max_retries = int(os.getenv("MAX_RETRIES", 3))
        self.data_dir = Path("data/external")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def collect_data(self, endpoint: str) -> List[Dict]:
        """Collect data from API endpoint."""
        url = f"{self.api_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        all_data = []
        params = {"_limit": self.batch_size, "_start": 0}
        retries = 0
        while len(all_data) < self.max_records:
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                batch = response.json()
                if not batch:
                    break
                all_data.extend(batch)
                if len(batch) < self.batch_size:
                    break
                params["_start"] += self.batch_size
                retries = 0
            except Exception as e:
                retries += 1
                if retries > self.max_retries:
                    raise e
                time.sleep(2 ** retries)
        return all_data[:self.max_records]

    def save_data(self, data: List[Dict], filename: str) -> Path:
        """Save data to timestamped JSON file."""
        timestamp = int(time.time())
        file_path = self.data_dir / f"{filename}_{timestamp}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path

def main():
    """Main function to demonstrate API data collection."""
    collector = APIDataCollector("your_api_name")

    try:
        # Collect data from your chosen endpoint
        data = collector.collect_data("")

        # Save the data
        collector.save_data(data, "your_data")

        print("Data collection completed successfully!")

    except Exception as e:
        print(f"Data collection failed: {e}")
        raise

if __name__ == "__main__":
    main()