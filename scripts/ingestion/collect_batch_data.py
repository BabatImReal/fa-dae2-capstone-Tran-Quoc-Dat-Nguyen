
import logging
from pathlib import Path
import kaggle
import pandas as pd
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def load_config():
    with open("config.yaml", 'r') as file:
        return yaml.safe_load(file)

config = load_config()
DATA_DIR = config['paths']['data_dir']
BATCH_DATASET = config['paths']['batch_dataset']

def get_dataset_path():
    # Returns the absolute path to the heart disease dataset
    return str(Path(DATA_DIR) / BATCH_DATASET)

# Download the heart disease dataset from Kaggle if not present
kaggle.api.authenticate()
dataset_path = get_dataset_path()
if not Path(dataset_path).exists():
    kaggle.api.dataset_download_files(
        "kamilpytlak/personal-key-indicators-of-heart-disease", path=DATA_DIR, unzip=True
    )
    logger.info(f"Downloaded heart disease dataset to {DATA_DIR}")
else:
    logger.info(f"Dataset already exists at {dataset_path}")

# Load and print the dataset head
if Path(dataset_path).exists():
    df = pd.read_csv(dataset_path)
    print(df.head())
else:
    logger.error(f"Dataset file not found at {dataset_path}")