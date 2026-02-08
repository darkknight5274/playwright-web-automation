from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from playwright.async_api import Page
import structlog

logger = structlog.get_logger()

@ActivityRegistry.register
class BattleActivity(BaseActivity):
    @property
    def path(self) -> str:
        return "/battle"

    async def execute(self, page: Page):
        logger.info("Executing Battle Activity", url=page.url)
