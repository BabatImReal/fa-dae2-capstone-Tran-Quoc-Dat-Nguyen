# scripts/data_collection/fake_data_generator.py
import json
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from faker import Faker

class FakeDataGenerator:
    def __init__(self, seed=None):
        # Always use current time as seed for different data each run
        seed = int(datetime.now().timestamp() * 1000000)  # Use microseconds for more uniqueness
        self.fake = Faker()
        self.fake.seed_instance(seed)
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
                "dob": self.fake.date_of_birth(minimum_age=18, maximum_age=90).strftime("%Y-%m-%d"),
                "created_at": self.fake.date_time_this_decade().strftime("%Y-%m-%d %H:%M:%S")
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
                "timestamp": self.fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S"),
                "status": self.fake.random_element(["completed", "pending", "failed"])
            })
        return transactions

    def generate_music_transaction_data(self, count: int = 100) -> List[Dict]:
        """Generate unique fake music listening events simulating real-time user interactions."""
        genres = [
            "Pop", "Rock", "Jazz", "Classical", "Hip-Hop", "Electronic",
            "Country", "Reggae", "Blues", "Folk", "Metal", "R&B"
        ]
        # Music listening events/actions
        music_events = [
            "play", "pause", "resume", "next", "previous", "backward", 
            "forward", "stop", "repeat", "shuffle", "skip", "like", 
            "dislike", "add_to_playlist", "remove_from_playlist", "share"
        ]
        # Weighted distribution for more realistic event patterns
        event_weights = {
            "play": 25, "pause": 20, "resume": 15, "next": 12, "previous": 8,
            "backward": 3, "forward": 3, "stop": 5, "repeat": 2, "shuffle": 3,
            "skip": 8, "like": 4, "dislike": 2, "add_to_playlist": 3,
            "remove_from_playlist": 1, "share": 2
        }
        records = []
        used_combinations = set()
        used_titles = set()
        now = datetime.now()
        
        for i in range(count):
            # Simulate events spaced 5 minutes apart for realistic timeline
            # Use strftime for consistent timestamp format compatible with Snowflake
            timestamp = (now.replace(microsecond=0) + timedelta(minutes=i * 5)).strftime("%Y-%m-%d %H:%M:%S")
            while True:
                user_id = self.fake.uuid4()
                song_id = self.fake.uuid4()
                combo = (str(user_id), str(song_id), timestamp)
                title = self.fake.sentence(nb_words=3).replace(".", "")
                if combo not in used_combinations and title not in used_titles:
                    used_combinations.add(combo)
                    used_titles.add(title)
                    break
            
            # Select event based on weights for more realistic distribution
            event_action = self.fake.random_element(elements=list(event_weights.keys()))
            
            # Calculate position in song based on event type
            duration = self.fake.random_int(min=120, max=420)
            if event_action in ["play", "resume"]:
                position_seconds = 0 if event_action == "play" else self.fake.random_int(min=1, max=duration-10)
            elif event_action in ["pause", "stop"]:
                position_seconds = self.fake.random_int(min=10, max=duration-10)
            elif event_action in ["next", "skip", "previous"]:
                position_seconds = self.fake.random_int(min=5, max=duration)
            else:
                position_seconds = self.fake.random_int(min=0, max=duration)
            
            records.append({
                "event_id": self.fake.uuid4(),
                "user_id": user_id,
                "session_id": self.fake.uuid4(),
                "song_id": song_id,
                "song_title": title,
                "artist": self.fake.name(),
                "album": self.fake.word().capitalize() + " Album",
                "genre": self.fake.random_element(genres),
                "duration_seconds": duration,
                "position_seconds": position_seconds,
                "event_action": event_action,
                "device_type": self.fake.random_element(["mobile", "desktop", "tablet", "smart_speaker"]),
                "platform": self.fake.random_element(["spotify", "apple_music", "youtube_music", "amazon_music"]),
                "timestamp": timestamp,
                "user_premium": self.fake.boolean(chance_of_getting_true=30)
            })
        return records

    def add_ingested_at(self, data: List[Dict]) -> List[Dict]:
        # Use strftime for consistent timestamp format compatible with Snowflake
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for record in data:
            record["ingested_at"] = now
        return data

    def save_data_as_json(self, data: List[Dict], filename: str) -> Path:
        """Save data to a new JSON file with a timestamp in the filename."""
        timestamp = datetime.utcnow().strftime("%Y_%m_%d_%H_%M")
        file_path = self.data_dir / f"{filename}_{timestamp}.json"
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
        users = generator.add_ingested_at(generator.generate_user_data(100))
        transactions = generator.add_ingested_at(generator.generate_transaction_data(100))
        music_transactions = generator.add_ingested_at(generator.generate_music_transaction_data(100))


        # Save in different formats
        generator.save_data_as_json(users, "fake_users")
        generator.save_data_as_json(music_transactions, "fake_music_transactions")

        print("Fake data generation completed successfully!")

    except Exception as e:
        print(f"Fake data generation failed: {e}")
        raise

if __name__ == "__main__":
    main()