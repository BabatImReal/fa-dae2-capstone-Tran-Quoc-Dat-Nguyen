# Data Engineering Capstone Project

## Overview
Brief description of your capstone project and goals.

## Project Structure
project/
├── .env                          # Configuration file
├── .gitignore                    # Git ignore file
├── main.py                       # Main pipeline script
├── scripts/
│   └── data_collection/         # Data collection scripts
├── data/
│   └── external/                 # Raw data files
└── pyproject.toml               # UV project configuration

## Setup
1. Install dependencies: `uv sync`
2. Configure environment: Copy `env_example.txt` to `.env`
3. Run pipeline: `uv run python main.py`

## Data Sources

### Real-Time Data Source: OpenAQ API
[OpenAQ](https://docs.openaq.org/) provides open, real-time, and historical air quality data from thousands of locations worldwide. The API enables access to measurements of pollutants such as PM2.5, PM10, NO2, O3, and more, supporting environmental analytics, public health research, and data-driven policy making. No API key is required for basic usage.

### Batch/Static Data Source: Kaggle Basketball Dataset
This project also utilizes the [Kaggle Basketball Dataset](https://www.kaggle.com/datasets/wyattowalsh/basketball), which contains extensive basketball statistics, player information, and game records. The dataset is suitable for historical analysis, player and team profiling, and machine learning applications in sports analytics.

For details on the evaluation and validation of data sources used in this project, see the research notes in [docs/research/data_source_validation.md](docs/research/data_source_validation.md).

## Data Source Alternatives & Fallbacks

To ensure robustness and continuity in your data pipeline, the following alternatives are implemented:

### Real-Time Data Source (API) Fallback
- **Primary:** Twelve Data API (real-time financial transactions)
- **Fallback:** [JSONPlaceholder](https://jsonplaceholder.typicode.com/)
  If the Twelve Data API is unavailable or rate-limited, the pipeline will automatically switch to JSONPlaceholder, a free online REST API for testing and prototyping, to simulate API responses and maintain workflow continuity.

### Batch/Static Data Source Fallback
- **Primary:** [Kaggle Transactions Fraud Dataset](https://www.kaggle.com/datasets/computingvictor/transactions-fraud-datasets)
- **Fallback:** Faker-generated synthetic data
  If the Kaggle dataset is unavailable or fails validation, the pipeline will use the `fake_data_generator.py` script to generate realistic synthetic datasets using the Faker library, ensuring that downstream processes can continue without interruption.

## Implemented Features

### scripts/data_collection/api_collector.py
- Uses environment variables for configuration
- Implements error handling and retry logic
- Includes rate limiting for API calls
- Saves raw data to timestamped JSON files
- Handles pagination if supported by the API

### scripts/data_collection/fake_data_generator.py
- Generates realistic user, transaction, and time series data
- Uses the Faker library for data generation
- Saves data as both JSON and CSV files
- Includes logging and error handling

### main.py
- Imports and runs data collection and fake data generator scripts
- Implements logging and error handling
- Provides a complete data collection pipeline

### tests/test_data_pipeline.py
- Tests data file creation
- Validates file formats
- Checks data quality and completeness