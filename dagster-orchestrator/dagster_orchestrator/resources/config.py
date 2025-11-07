"""Configuration resource for loading YAML config."""

import os
from pathlib import Path
from typing import Dict, Any

import yaml
from dagster import ConfigurableResource
from pydantic import Field


class ConfigResource(ConfigurableResource):
    """Resource to load and provide access to config.yaml."""
    
    config_path: str = Field(
        default="config.yaml",
        description="Path to config.yaml file (relative to project root)"
    )
    
    def get_config(self) -> Dict[str, Any]:
        """Load and return configuration from YAML file."""
        # Find project root (3 levels up: resources -> dagster_orchestrator -> dagster-orchestrator -> project root)
        project_root = Path(__file__).resolve().parents[3]
        cfg_path = project_root / self.config_path
        
        if not cfg_path.exists():
            raise FileNotFoundError(f"Config file not found: {cfg_path}")
        
        with open(cfg_path, 'r') as file:
            return yaml.safe_load(file)
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Get nested configuration value by keys."""
        config = self.get_config()
        for key in keys:
            if isinstance(config, dict):
                config = config.get(key, default)
            else:
                return default
        return config
