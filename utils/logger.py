import logging
import structlog
import sys
import os

def add_domain(logger, method_name, event_dict):
    """
    Ensures that a 'domain' key is always present in the log entry.
    """
    if "domain" not in event_dict:
        event_dict["domain"] = "default"
    return event_dict

def setup_logger():
    # Ensure logs directory exists
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "game_bot.log")

    # Configure processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        add_domain,
        structlog.processors.JSONRenderer(),
    ]

    # Standard logging configuration for multi-output (console and file)
    # Since we use JSONRenderer, structlog will pass a JSON string as the message to logging.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
        force=True
    )

    root_logger = logging.getLogger()
    # Add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(file_handler)

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()

# Initialize the logger
logger = setup_logger()
