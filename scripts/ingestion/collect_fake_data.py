# scripts/data_collection/fake_data_generator.py

# Standard library imports
import csv
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Third-party imports
import yaml
from faker import Faker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration from YAML
def load_config():
    """Load configuration from YAML file."""
    with open("config.yaml", 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# Use configuration values
DATA_DIR = config['paths']['data_dir']


class FakeDataGenerator:
    def __init__(self, seed=None):
        # Initialize the Faker instance and create data directory
        # Always use current time as seed for different data each run
        seed = int(
            datetime.now().timestamp() * 1000000
        )  # Use microseconds for more uniqueness
        self.fake = Faker()
        self.fake.seed_instance(seed)
        self.data_dir = Path(DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_file_path(self, file_path):
        """Sanitize file paths to prevent path traversal."""
        # Convert to Path object and resolve
        base_path = self.data_dir.resolve()
        target_path = (base_path / file_path).resolve()
        
        # Ensure the target path is within the base directory
        if not str(target_path).startswith(str(base_path)):
            raise ValueError(f"Invalid file path: {file_path}")
        
        return target_path


    # Generate a list of fake hospital transaction records
    def generate_hospital_transaction_data(self, count: int = 100) -> List[Dict]:
        """Generate fake hospital transaction data."""
        records = []
        departments = [
            "Emergency", "Cardiology", "Neurology", "Oncology", "Pediatrics",
            "Orthopedics", "Radiology", "Surgery", "Maternity", "ICU"
        ]
        payment_methods = ["insurance", "cash", "credit_card", "debit_card", "online"]
        for _ in range(count):
            records.append({
                "transaction_id": str(self.fake.uuid4()),
                "patient_id": str(self.fake.uuid4()),
                "admission_id": str(self.fake.uuid4()),
                "department": self.fake.random_element(departments),
                "doctor": self.fake.name(),
                "service": self.fake.sentence(nb_words=4).replace(".", ""),
                "cost": round(self.fake.pyfloat(left_digits=4, right_digits=2, positive=True), 2),
                "payment_method": self.fake.random_element(payment_methods),
                "transaction_time": self.fake.date_time_this_year().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "status": self.fake.random_element(["completed", "pending", "failed"]),
            })
        return records

    # Add an 'ingested_at' timestamp to each record in the data
    def add_ingested_at(self, data: List[Dict]) -> List[Dict]:
        # Use strftime for consistent timestamp format compatible with Snowflake
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for record in data:
            record["ingested_at"] = now
            # Ensure all timestamp fields are string
            if "transaction_time" in record and not isinstance(record["transaction_time"], str):
                record["transaction_time"] = str(record["transaction_time"])
        return data

    # Save data as a JSON file with a timestamped filename
    def save_data_as_json(self, data: List[Dict], filename: str) -> Path:
        """Save data to a new JSON file with a timestamp in the filename."""
        # Sanitize filename to prevent path traversal
        clean_filename = Path(filename).name
        timestamp = datetime.utcnow().strftime("%Y_%m_%d_%H_%M")
        file_path = self.sanitize_file_path(f"{clean_filename}_{timestamp}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} records to {file_path}")
        return file_path

    # Save data as a CSV file
    def save_data_as_csv(self, data: List[Dict], filename: str) -> Path:
        """Save data to CSV file."""
        if not data:
            raise ValueError("No data to save.")
        # Sanitize filename to prevent path traversal
        clean_filename = Path(filename).name
        file_path = self.sanitize_file_path(f"{clean_filename}.csv")
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Saved {len(data)} records to {file_path}")
        return file_path


# Main function to demonstrate fake data generation and saving
def main():
    """Main function to demonstrate fake data generation."""
    generator = FakeDataGenerator()


    try:
        # Generate fake hospital transaction data
        hospital_transactions = generator.add_ingested_at(
            generator.generate_hospital_transaction_data(100)
        )
        # Save in different formats
        generator.save_data_as_json(hospital_transactions, "fake_hospital_transactions")
        logger.info("Fake hospital transaction data generation completed successfully!")
    except Exception as e:
        logger.error(f"Fake data generation failed: {e}")
        raise


if __name__ == "__main__":
    main()