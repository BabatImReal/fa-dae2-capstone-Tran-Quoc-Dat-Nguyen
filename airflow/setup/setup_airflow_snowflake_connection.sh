#!/bin/bash

# Script to set up Airflow Snowflake connection using .env variables
# Run this script from the lab directory

set -e

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found in current directory"
    echo "Please create a .env file with your Snowflake credentials"
    exit 1
fi

# Source the .env file
source .env

# Check if Airflow is running
if ! docker-compose -f docker-compose-airflow.yml ps | grep -q "airflow-scheduler"; then
    echo "Error: Airflow is not running. Start it first: docker-compose -f docker-compose-airflow.yml up -d"
    exit 1
fi

# Extract private key file name from path
PRIVATE_KEY_FILE=$(basename "$SNOWFLAKE_PRIVATE_KEY_FILE_PATH")
CONTAINER_KEY_PATH="/opt/airflow/.secret/$PRIVATE_KEY_FILE"

echo "Setting up Snowflake connection: snowflake_default"

# Delete existing connection if it exists
docker-compose -f docker-compose-airflow.yml exec -T airflow-scheduler airflow connections delete snowflake_default 2>/dev/null || true

# Add new connection
docker-compose -f docker-compose-airflow.yml exec -T airflow-scheduler airflow connections add 'snowflake_default' \
    --conn-type 'snowflake' \
    --conn-login "$SNOWFLAKE_USER" \
    --conn-password "$SNOWFLAKE_PRIVATE_KEY_FILE_PWD" \
    --conn-schema "$SNOWFLAKE_SCHEMA" \
    --conn-extra "{\"account\": \"$SNOWFLAKE_ACCOUNT\", \"warehouse\": \"$SNOWFLAKE_WAREHOUSE\", \"database\": \"$SNOWFLAKE_DATABASE\", \"role\": \"$SNOWFLAKE_ROLE\", \"private_key_file\": \"$CONTAINER_KEY_PATH\"}"

echo "✅ Snowflake connection setup complete"