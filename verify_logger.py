from utils.logger import logger
import structlog

def main():
    # Test log with no context (should have domain="default")
    logger.info("Test message 1")

    # Test log with context
    log = logger.bind(domain="example.com")
    log.info("Test message 2")

if __name__ == "__main__":
    main()
