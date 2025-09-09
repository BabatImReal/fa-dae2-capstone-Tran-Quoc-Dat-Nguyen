import logging
from pathlib import Path

from dotenv import load_dotenv

# Import your scripts
from scripts.data_collection.api_collector import main as collect_api_data
from scripts.data_collection.fake_data_generator import main as generate_fake_data

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
        # Step 1: Collect data from API
        logger.info("📡 Step 1: Collecting real data from API")
        collect_api_data()

        # Step 2: Generate fake data for testing
        logger.info("🎭 Step 2: Generating fake data for testing")
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
