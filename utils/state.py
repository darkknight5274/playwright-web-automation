from utils.config_loader import load_config

def initialize_domain_status():
    config = load_config()
    domains = config.get("domains", [])
    return {domain: "idle" for domain in domains}

# Global dictionary to track domain status
domain_status = initialize_domain_status()
