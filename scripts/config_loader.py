# scripts/config_loader.py
# Example of how to load and use the YAML configuration

import yaml
from pathlib import Path

def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

# Example usage:
# config = load_config()
# STAGE_FQN = config['snowflake']['stage_fqn']
# TABLE_FQN = config['snowflake']['table_fqn']
# TRACK_COLS = config['columns']['track']
# etc.