# scripts/config_loader.py
# Example of how to load and use the YAML configuration

# Standard library imports

# Third-party imports
import yaml


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path) as file:
        return yaml.safe_load(file)


# Example usage:
# config = load_config()
# STAGE_FQN = config['snowflake']['stage_fqn']
# TABLE_FQN = config['snowflake']['table_fqn']
# TRACK_COLS = config['columns']['track']
# etc.
