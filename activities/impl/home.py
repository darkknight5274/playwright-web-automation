from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from playwright.async_api import Page
import structlog

logger = structlog.get_logger()

@ActivityRegistry.register
class HomeActivity(BaseActivity):
    @property
    def path(self) -> str:
        return "/home"

    async def execute(self, page: Page):
        logger.info("Home page reached", url=page.url, domain=page.url)
        # Standardize the log message as requested
        logger.info("Home page reached")
