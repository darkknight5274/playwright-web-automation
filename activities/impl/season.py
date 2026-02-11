from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from utils.human import HumanUtils
from playwright.async_api import Page
import structlog

logger = structlog.get_logger()

@ActivityRegistry.register
class SeasonActivity(BaseActivity):
    @property
    def path(self) -> str:
        return "/season-arena.html"

    async def execute(self, page: Page):
        logger.info("Season activity started", url=page.url)
        await page.get_by_role("button", name="Fight! 1x").nth(2).click()
        await HumanUtils.random_sleep(2, 4)

        # Optional Skip: only click if it exists
        skip_btn = page.get_by_role("button", name="Skip")
        try:
            await skip_btn.wait_for(state="visible", timeout=5000)
            await skip_btn.click()
            await HumanUtils.random_sleep(1, 2)
        except Exception:
            logger.info("Skip button not found or not visible, skipping optional step")

        await page.get_by_role("button", name="OK").click()
        await HumanUtils.random_sleep()
        logger.info("Season activity completed")
