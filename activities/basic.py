from utils.logger import logger

async def perform_activity(page, url):
    """
    A basic activity that navigates to a URL and logs the page title.
    """
    logger.info(f"Executing basic activity on {url}")
    try:
        await page.goto(url, wait_until="networkidle")
        title = await page.title()
        logger.info(f"Successfully reached {url}", title=title)
    except Exception as e:
        logger.error(f"Failed to execute activity on {url}", error=str(e))
