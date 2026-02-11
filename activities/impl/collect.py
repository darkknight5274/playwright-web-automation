from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from playwright.async_api import Page
import structlog

logger = structlog.get_logger()

@ActivityRegistry.register
class CollectActivity(BaseActivity):
    @property
    def path(self) -> str:
        return "/collect"

    async def execute(self, page: Page):
        logger.info("Collect activity started", url=page.url)
        # Navigate to home.html as per logic
        domain = "/".join(page.url.split("/")[:3])
        await page.goto(f"{domain}/home.html")

        if await page.locator("#collect_all").is_visible():
            await page.locator("#collect_all").click()
            logger.info("Collected all items")
        else:
            logger.info("Nothing to collect")
        logger.info("Collect activity completed")
