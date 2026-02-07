import asyncio
from utils.auth import ensure_authenticated
from utils.logger import logger

async def main():
    logger.info("Starting authentication process...")
    try:
        success = await ensure_authenticated()
        if success:
            logger.info("Authentication process completed.")
        else:
            logger.error("Authentication process failed.")
    except Exception as e:
        logger.error("An unexpected error occurred during authentication", error=str(e))

if __name__ == "__main__":
    asyncio.run(main())
