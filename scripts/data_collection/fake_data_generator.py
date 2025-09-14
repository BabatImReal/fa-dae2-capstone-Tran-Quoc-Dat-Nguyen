# scripts/data_collection/fake_data_generator.py
import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from faker import Faker

class FakeDataGenerator:
    def __init__(self):
        self.fake = Faker()
        self.data_dir = Path("data/external")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def generate_user_data(self, count: int = 100) -> List[Dict]:
        """Generate fake user data."""
        users = []
        for _ in range(count):
            users.append({
                "user_id": self.fake.uuid4(),
                "name": self.fake.name(),
                "email": self.fake.email(),
                "address": self.fake.address().replace("\n", ", "),
                "phone": self.fake.phone_number(),
                "dob": self.fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
                "created_at": self.fake.date_time_this_decade().isoformat()
            })
        return users

    def generate_transaction_data(self, count: int = 100) -> List[Dict]:
        """Generate fake transaction data."""
        transactions = []
        for _ in range(count):
            transactions.append({
                "transaction_id": self.fake.uuid4(),
                "user_id": self.fake.uuid4(),
                "amount": round(self.fake.pyfloat(left_digits=3, right_digits=2, positive=True), 2),
                "currency": self.fake.currency_code(),
                "timestamp": self.fake.date_time_this_year().isoformat(),
                "status": self.fake.random_element(["completed", "pending", "failed"])
            })
        return transactions

    def generate_data_quality(self, count: int = 100) -> List[Dict]:
        """Generate fake air quality sensor data."""
        records = []
        for _ in range(count):
            records.append({
                "sensor_id": self.fake.uuid4(),
                "timestamp": self.fake.date_time_this_year().isoformat(),
                "pm25": round(self.fake.pyfloat(left_digits=3, right_digits=2, min_value=0, max_value=500), 2),
                "pm10": round(self.fake.pyfloat(left_digits=3, right_digits=2, min_value=0, max_value=600), 2),
                "co": round(self.fake.pyfloat(left_digits=2, right_digits=2, min_value=0, max_value=50), 2),
                "no2": round(self.fake.pyfloat(left_digits=3, right_digits=2, min_value=0, max_value=200), 2),
                "o3": round(self.fake.pyfloat(left_digits=3, right_digits=2, min_value=0, max_value=300), 2),
                "temperature": round(self.fake.pyfloat(left_digits=2, right_digits=2, min_value=-20, max_value=50), 2),
                "humidity": round(self.fake.pyfloat(left_digits=3, right_digits=2, min_value=0, max_value=100), 2),
                "quality_flag": self.fake.random_element(["good", "moderate", "unhealthy", "hazardous"])
            })
        return records

    def save_data_as_json(self, data: List[Dict], filename: str) -> Path:
        """Save data to JSON file."""
        file_path = self.data_dir / f"{filename}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path

    def save_data_as_csv(self, data: List[Dict], filename: str) -> Path:
        """Save data to CSV file."""
        if not data:
            raise ValueError("No data to save.")
        file_path = self.data_dir / f"{filename}.csv"
        with open(file_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return file_path

def main():
    """Main function to demonstrate fake data generation."""
    generator = FakeDataGenerator()

    try:
        # Generate different types of data
        users = generator.generate_user_data(100)
        transactions = generator.generate_transaction_data(100)
        data_quality = generator.generate_data_quality(100)

        # Save in different formats
        generator.save_data_as_json(users, "fake_users")
        generator.save_data_as_csv(transactions, "fake_transactions")
        generator.save_data_as_json(data_quality, "fake_data_quality")
        generator.save_data_as_csv(data_quality, "fake_data_quality")

        print("Fake data generation completed successfully!")

    except Exception as e:
        print(f"Fake data generation failed: {e}")
        raise

if __name__ == "__main__":
    main()