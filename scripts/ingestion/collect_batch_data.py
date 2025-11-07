
import logging
from pathlib import Path
import kaggle
import pandas as pd
import yaml
import zipfile
import shutil

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def load_config():
    # Get project root (this file is at scripts/ingestion/collect_batch_data.py)
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "config.yaml"
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


config = load_config()
DATA_DIR = config['paths']['data_dir']
# Kaggle dataset identifier, e.g. 'olistbr/brazilian-ecommerce'
BATCH_DATASET_ID = config['paths'].get('batch_dataset_id')
# Local folder to extract dataset files to
DLT_INPUT_DIR = Path(config['paths'].get('dlt_input_dir', str(Path(DATA_DIR) / 'olistbr_brazilian_ecommerce')))
# Optional preview file name within the dataset
BATCH_PREVIEW = config['paths'].get('batch_dataset_preview')


def get_preview_path():
    if BATCH_PREVIEW:
        return DLT_INPUT_DIR / BATCH_PREVIEW
    return DLT_INPUT_DIR


def main():
    kaggle.api.authenticate()

    # Ensure the target extraction directory exists
    dltdir = DLT_INPUT_DIR
    dltdir.mkdir(parents=True, exist_ok=True)

    if not BATCH_DATASET_ID:
        logger.error("No 'batch_dataset_id' set in config.paths; nothing to download.")
        return

    # Download Kaggle dataset archive into DATA_DIR
    try:
        logger.info(f"Downloading dataset {BATCH_DATASET_ID} to {DATA_DIR}...")
        kaggle.api.dataset_download_files(BATCH_DATASET_ID, path=DATA_DIR, unzip=False)

        dataset_slug = BATCH_DATASET_ID.split('/')[-1]
        zip_path = Path(DATA_DIR) / f"{dataset_slug}.zip"
        if zip_path.exists():
            logger.info(f"Extracting {zip_path} to {dltdir}...")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(dltdir)
            try:
                zip_path.unlink()
            except Exception:
                pass
            logger.info(f"Dataset extracted to {dltdir}")
        else:
            # Some Kaggle downloads may produce individual files in DATA_DIR
            logger.info(f"No archive {zip_path} found; checking for files in {DATA_DIR}")
            for p in Path(DATA_DIR).iterdir():
                if p.suffix.lower() in ['.csv', '.json']:
                    shutil.copy(p, dltdir / p.name)
    except Exception as e:
        logger.exception("Failed to download dataset from Kaggle: %s", e)
        return

    # List CSV files in the target folder and preview one if available
    csv_files = sorted([p for p in dltdir.rglob('*.csv')])
    if csv_files:
        logger.info(f"Found {len(csv_files)} CSV file(s) under {dltdir}:")
        for p in csv_files:
            try:
                display_path = p.relative_to(Path.cwd())
            except Exception:
                display_path = p
            logger.info(f" - {display_path}")
    else:
        logger.warning(f"No CSV files found under {dltdir}")

    preview_path = get_preview_path()
    if preview_path.exists() and preview_path.suffix.lower() == '.csv':
        logger.info(f"Previewing {preview_path}:")
        df = pd.read_csv(preview_path, nrows=5)
        print(df.head())
    else:
        if BATCH_PREVIEW:
            logger.warning(f"Configured preview file {preview_path} not found.")
        else:
            logger.info("No preview file configured; finished listing files.")


if __name__ == "__main__":
    main()
    main()