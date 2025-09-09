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

### Real-Time Data Source: Stripe API
Stripe API is a widely used payment processing platform that provides real-time access to transaction, customer, and payment data via a robust RESTful API. In this project, Stripe API will be used to collect up-to-date financial transaction data for analysis and integration into the data pipeline.

### Batch/Static Data Source: Kaggle Financial Transactions Dataset
This project also utilizes the [Kaggle Transactions Fraud Dataset](https://www.kaggle.com/datasets/computingvictor/transactions-fraud-datasets), which combines transaction records, customer information, and card data from a banking institution, spanning the 2010s decade. The dataset is designed for multiple analytical purposes, including synthetic fraud detection, customer behavior analysis, and expense forecasting.

For details on the evaluation and validation of data sources used in this project, see the research notes in [docs/research/data_source_validation.md](docs/research/data_source_validation.md).

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