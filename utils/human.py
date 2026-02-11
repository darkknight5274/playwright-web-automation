import asyncio
import random
from playwright.async_api import Page

class HumanUtils:
    @staticmethod
    async def random_sleep(min_sec: float = 1.5, max_sec: float = 4.0):
        """
        Sleeps for a random duration between min_sec and max_sec to simulate human behavior.
        """
        duration = random.uniform(min_sec, max_sec)
        await asyncio.sleep(duration)

    @staticmethod
    async def random_jitter(min_sec: float = 1.5, max_sec: float = 4.5):
        """
        Alias for random_sleep with specific defaults for jitter.
        """
        await HumanUtils.random_sleep(min_sec, max_sec)

    @staticmethod
    async def human_click(page: Page, locator):
        """
        Clicks an element with a slight random offset to simulate human inaccuracy.
        """
        if isinstance(locator, str):
            locator = page.locator(locator)

        try:
            # Ensure element is visible and scrolled into view
            await locator.scroll_into_view_if_needed()
            box = await locator.bounding_box()
            if box:
                # Click at a random point within the inner 80% of the element
                x = box['x'] + box['width'] * random.uniform(0.1, 0.9)
                y = box['y'] + box['height'] * random.uniform(0.1, 0.9)
                await page.mouse.click(x, y)
            else:
                await locator.click()
        except Exception:
            # Fallback to standard click if something goes wrong
            await locator.click()
