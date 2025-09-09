# scripts/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data paths
DATA_PATHS = {
    "raw": BASE_DIR / "data" / "raw",
    "processed": BASE_DIR / "data" / "processed",
    "scripts": BASE_DIR / "scripts"
}

# API configuration
API_CONFIG = {
    "base_url": os.getenv("API_BASE_URL", "https://api.example.com"),
    "api_key": os.getenv("API_KEY")
}

# Database configuration
DATABASE_CONFIG = {
    "url": os.getenv("DATABASE_URL"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432"))
}