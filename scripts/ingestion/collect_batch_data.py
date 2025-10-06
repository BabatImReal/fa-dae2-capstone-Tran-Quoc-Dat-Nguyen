import kaggle
import pandas as pd
from pathlib import Path

def sanitize_file_path(file_path, base_dir="data/external"):
    """Sanitize file paths to prevent path traversal."""
    # Convert to Path object and resolve
    base_path = Path(base_dir).resolve()
    target_path = (base_path / file_path).resolve()
    
    # Ensure the target path is within the base directory
    if not str(target_path).startswith(str(base_path)):
        raise ValueError(f"Invalid file path: {file_path}")
    
    return target_path

kaggle.api.authenticate()

# Download the Spotify tracks dataset to the current directory
kaggle.api.dataset_download_files(
    "maharshipandya/-spotify-tracks-dataset", path="data/external", unzip=True
)

# Path to downloaded dataset - sanitized
dataset_path = sanitize_file_path("dataset.csv")
cleaned_path = sanitize_file_path("dataset_clean.csv")

# Load dataset
df = pd.read_csv(dataset_path)

# Drop first column if it's just an index
if df.columns[0].startswith("Unnamed") or df.columns[0] == "0":
    df = df.drop(df.columns[0], axis=1)

# Save cleaned dataset
df.to_csv(cleaned_path, index=False)

print(f"Cleaned dataset saved to {cleaned_path}")
print(df.head())