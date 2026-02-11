from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from utils.human import HumanUtils
from playwright.async_api import Page
import structlog

logger = structlog.get_logger()

@ActivityRegistry.register
class BattleActivity(BaseActivity):
    @property
    def path(self) -> str:
        return "/troll-pre-battle.html"

    async def execute(self, page: Page):
        logger.info("Battle activity started", url=page.url)
        # Ensure we have the query param if not present
        if "?id_opponent=1" not in page.url:
            base_url = page.url.split("?")[0]
            await page.goto(f"{base_url}?id_opponent=1")

        await page.get_by_role("button", name="Fight! x1 1").click()
        await HumanUtils.random_sleep()
        await page.get_by_role("button", name="OK").click()
        await HumanUtils.random_sleep()
        logger.info("Battle activity completed")
