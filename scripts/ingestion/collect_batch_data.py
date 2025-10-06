# Standard library imports
import logging
from pathlib import Path

# Third-party imports
import kaggle
import pandas as pd
import yaml

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
BATCH_DATASET = config['paths']['cleaned_dataset']

def sanitize_file_path(file_path, base_dir=DATA_DIR):
    """Sanitize file paths to prevent path traversal."""
    # Convert to Path object and resolve
    base_path = Path(base_dir).resolve()
    target_path = (base_path / file_path).resolve()
    
    # Ensure the target path is within the base directory
    if not str(target_path).startswith(str(base_path)):
        raise ValueError(f"Invalid file path: {file_path}")
    
    return target_path

# Use configuration for Kaggle dataset name
kaggle.api.authenticate()

# Download the Spotify tracks dataset to the current directory
kaggle.api.dataset_download_files(
    "maharshipandya/-spotify-tracks-dataset", path=DATA_DIR, unzip=True
)

# Path to downloaded dataset - sanitized
dataset_path = sanitize_file_path(config['paths']['batch_dataset'])
cleaned_path = sanitize_file_path(BATCH_DATASET)

# Load dataset
df = pd.read_csv(dataset_path)

# Drop first column if it's just an index
if df.columns[0].startswith("Unnamed") or df.columns[0] == "0":
    df = df.drop(df.columns[0], axis=1)

# Save cleaned dataset
df.to_csv(cleaned_path, index=False)

logger.info(f"Cleaned dataset saved to {cleaned_path}")
print(df.head())