# scripts/data_collection/fake_data_generator.py

# Standard library imports
import csv
import json
import uuid
from random import randint, choice, uniform, choices
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

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
        
        # Pre-generate pools for consistent data
        self.users = [str(uuid.uuid4()) for _ in range(100)]
        self.products = [str(uuid.uuid4()) for _ in range(500)]

    def generate_single_user_event(self) -> Dict:
        """Generate a single user event record for OLTP insertion."""
        user_id = choice(self.users)
        session_id = str(uuid.uuid4())
        
        event_types = [
            'page_view', 'product_view', 'search', 'add_to_cart', 
            'remove_from_cart', 'checkout_click'
        ]
        
        ev_type = choice(event_types)
        ev_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        event = {
            'event_id': str(uuid.uuid4()),
            'user_id': user_id,
            'session_id': session_id,
            'event_type': ev_type,
            'event_timestamp': ev_ts,
            'user_agent': self.fake.user_agent(),
            'ip_address': self.fake.ipv4_public(),
            'page_url': self.fake.uri(),
            'page_title': self.fake.sentence(nb_words=6),
            'referrer': self.fake.uri(),
            'product_id': choice(self.products),
            'product_name': self.fake.sentence(nb_words=3),
            'category': self.fake.word(ext_word_list=['Electronics', 'Clothing', 'Home', 'Books', 'Sports']),
            'price': round(uniform(5.0, 500.0), 2),
            'quantity': randint(1, 5),
            'search_query': self.fake.sentence(nb_words=randint(1, 5)),
            'results_count': randint(0, 100),
            'filters_applied': self.fake.boolean(chance_of_getting_true=30),
            'checkout_step': choice(['cart_review', 'shipping_info', 'payment_info', 'order_confirmation']),
            'cart_value': round(uniform(10.0, 2000.0), 2),
            'item_count': randint(1, 15)
        }
        
        return event