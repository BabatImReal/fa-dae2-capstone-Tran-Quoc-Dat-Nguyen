import kaggle
import pandas as pd

kaggle.api.authenticate()

# Download the Spotify tracks dataset to the current directory
kaggle.api.dataset_download_files(
    'maharshipandya/-spotify-tracks-dataset',
    path='data/external',
    unzip=True
)

# Path to downloaded dataset
dataset_path = "data/external/dataset.csv"
cleaned_path = "data/external/dataset_clean.csv"

# Load dataset
df = pd.read_csv(dataset_path)

# Drop first column if it's just an index
if df.columns[0].startswith("Unnamed") or df.columns[0] == "0":
    df = df.drop(df.columns[0], axis=1)

# Save cleaned dataset
df.to_csv(cleaned_path, index=False)

print(f"Cleaned dataset saved to {cleaned_path}")
print(df.head())
