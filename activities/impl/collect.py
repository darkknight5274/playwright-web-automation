from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from utils.human import HumanUtils
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

        collect_btn = page.locator("#collect_all")
        if await collect_btn.is_visible():
            await HumanUtils.human_click(page, collect_btn)
            await HumanUtils.random_jitter()
            logger.info("Collected all items")
        else:
            logger.info("Nothing to collect")
        logger.info("Collect activity completed")
