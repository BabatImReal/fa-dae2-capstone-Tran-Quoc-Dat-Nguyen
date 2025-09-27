import logging
from pathlib import Path

from dotenv import load_dotenv

# Import your scripts
from scripts.ingestion.collect_fake_data import main as generate_fake_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

def main():
    """Main data collection pipeline."""
    logger.info("🚀 Starting Data Collection Pipeline")

    try:

        # Step 1: Generate fake data for testing
        logger.info("🎭 Step 1: Generating fake data for testing")
        generate_fake_data()

        logger.info("🎉 Data collection completed successfully!")
        logger.info("📁 Check the 'data/external' folder for your collected data files")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Create data directory structure if it doesn't exist
    Path("data/external").mkdir(parents=True, exist_ok=True)

    # Run pipeline
    main()
