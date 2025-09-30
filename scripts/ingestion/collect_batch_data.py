import kagglehub
import shutil
from pathlib import Path

# Try multiple Spotify datasets
datasets = [
    "maharshipandya/-spotify-tracks-dataset",
    "zaheenhamidani/ultimate-spotify-tracks-db",
    "yamaerenay/spotify-dataset-19212020-160k-tracks"
]

# Define target directory
target_dir = Path("data/external")
target_dir.mkdir(parents=True, exist_ok=True)

for dataset in datasets:
    try:
        print(f"\n📥 Trying dataset: {dataset}")
        path = kagglehub.dataset_download(dataset)
        print("Path to dataset files:", path)

        # Check what files exist in the downloaded path
        download_path = Path(path)
        files_found = list(download_path.rglob("*.csv")) + list(download_path.rglob("*.json")) + list(download_path.rglob("*.parquet"))
        
        print(f"Files in download path:")
        for item in files_found:
            print(f"  - {item} ({'file' if item.is_file() else 'directory'})")

        if not files_found:
            print(f"  ⚠️ No data files found in {dataset}")
            continue

        # Move all files from downloaded path to data/external
        moved_files = 0
        for item in files_found:
            if item.is_file():
                dest = target_dir / item.name
                try:
                    shutil.copy2(str(item), str(dest))
                    print(f"  ✅ Copied: {item.name}")
                    moved_files += 1
                except Exception as e:
                    print(f"  ❌ Failed to copy {item.name}: {e}")

        if moved_files > 0:
            print(f"✅ Successfully downloaded {dataset}")
            break
        
    except Exception as e:
        print(f"❌ Failed to download {dataset}: {e}")
        continue

print(f"\nDataset files location: {target_dir}")
print(f"Total files moved: {moved_files}")

# Verify files in target directory
print("All files in target directory:")
for f in target_dir.iterdir():
    if f.is_file():
        print(f"  - {f.name} ({f.stat().st_size} bytes)")