import logging
import structlog

def setup_logger():
    # Standard logging configuration to handle multiple outputs
    log_format = "%(message)s"

    # Create handlers for console and file
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler("app.log")

    # Configure base logging
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[stream_handler, file_handler],
        force=True  # Ensure config is applied even if logging was already configured
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger()

logger = setup_logger()
