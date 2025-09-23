import kagglehub
import shutil
from pathlib import Path

# Download latest version
path = kagglehub.dataset_download("maharshipandya/-spotify-tracks-dataset")

print("Path to dataset files:", path)

# Define target directory
target_dir = Path("data/external")
target_dir.mkdir(parents=True, exist_ok=True)

# Move all files from downloaded path to data/external
for item in Path(path).iterdir():
    dest = target_dir / item.name
    if item.is_file():
        shutil.move(str(item), str(dest))
    elif item.is_dir():
        shutil.move(str(item), str(dest))

print(f"Dataset files moved to: {target_dir}")