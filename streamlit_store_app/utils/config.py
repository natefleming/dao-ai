"""Configuration utilities for the Streamlit Store App."""

import os
from typing import Dict, Any
import yaml
from pathlib import Path

def load_config() -> Dict[str, Any]:
    """Load application configuration."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    config = {}
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
    

    return config

def validate_env() -> None:
    """Validate required environment variables."""
    required = ['DATABRICKS_WAREHOUSE_ID', 'DATABRICKS_HOST', 'DATABRICKS_TOKEN', 'SERVING_ENDPOINT']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}") 