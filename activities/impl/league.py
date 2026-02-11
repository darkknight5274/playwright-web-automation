from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from utils.human import HumanUtils
from playwright.async_api import Page
import structlog

logger = structlog.get_logger()

@ActivityRegistry.register
class LeagueActivity(BaseActivity):
    @property
    def path(self) -> str:
        return "/leagues.html"

    async def execute(self, page: Page):
        logger.info("League activity started", url=page.url)
        await page.locator(".go_pre_battle").first.click()
        await HumanUtils.random_sleep()
        await page.get_by_text("Challenge! x3").click()
        await HumanUtils.random_sleep()
        await page.get_by_role("button", name="OK").click()
        await HumanUtils.random_sleep()
        logger.info("League activity completed")
