from activities.base import BaseActivity
from activities.registry import ActivityRegistry
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
        await page.get_by_role("button", name="Skip").click()
        await page.get_by_role("button", name="OK").click()
        logger.info("Season activity completed")
