from urllib.parse import urlparse
from activities.registry import TASK_MAPPING
from utils.config_loader import load_config
import structlog

logger = structlog.get_logger()

async def run_activity(page):
    """
    Determines and executes the appropriate activity for the current page URL.
    Skips if the domain or activity is disabled in the configuration.
    """
    url = page.url
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc
    path = parsed_url.path

    config = load_config()
    domains_config = config.get("domains", [])

    # Find matching domain config
    domain_settings = None
    for d in domains_config:
        if d["url"] in netloc:
            domain_settings = d
            break

    if not domain_settings:
        logger.warning("Domain not configured", domain=netloc)
        return

    if not domain_settings.get("enabled", True):
        logger.info("Domain is disabled", domain=netloc)
        return

    disabled_activities = domain_settings.get("disabled_activities", [])
    if path in disabled_activities:
        logger.info("Activity is disabled for this domain", domain=netloc, path=path)
        return

    activity_class = TASK_MAPPING.get(path)
    if activity_class:
        logger.info("Running activity", path=path, class_name=activity_class.__name__)
        activity = activity_class()
        await activity.execute(page)
    else:
        logger.debug("No activity mapped for path", path=path)
