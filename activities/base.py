from abc import ABC, abstractmethod
from playwright.async_api import Page
from utils.logger import logger

class BaseActivity(ABC):
    @property
    @abstractmethod
    def path(self) -> str:
        """The URL path this activity handles (e.g., '/home')."""
        pass

    @abstractmethod
    async def execute(self, page: Page):
        """Execute the activity on the given page."""
        pass

    async def handle_age_gate(self, page: Page):
        """Detects and accepts age verification popups."""
        try:
            # Check for the common age verification container
            age_gate = page.locator('#common-popups .age-verification')

            # Wait for visibility with a short timeout
            try:
                await age_gate.wait_for(state="visible", timeout=3000)
            except:
                pass

            if await age_gate.is_visible():
                logger.info("Age verification detected. Attempting to enter...")

                # Try to find the 'Enter' or 'I am 18' button
                enter_btn = age_gate.locator('button').first
                await enter_btn.click()

                # Wait for the popup to disappear
                await age_gate.wait_for(state='hidden', timeout=5000)
                logger.info("Age verification cleared.")
        except Exception as e:
            logger.debug(f"Age gate check skipped or failed: {e}")
