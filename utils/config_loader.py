import yaml
import os

def load_config(config_path="config/config.yaml"):
    """
    Loads configuration from a YAML file. Defaults to config/config.yaml.
    """
    if not os.path.exists(config_path):
        # Fallback to settings.yaml if config.yaml doesn't exist
        alt_path = "config/settings.yaml"
        if os.path.exists(alt_path):
            config_path = alt_path

    with open(config_path, "r") as f:
        return yaml.safe_load(f)
