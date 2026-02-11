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

        # Guard Logic: Check energy
        energy_locator = page.locator("//div[@type='fight']//span[@energy]")
        try:
            await energy_locator.wait_for(state="visible", timeout=5000)
            energy_text = await energy_locator.get_attribute("energy") or await energy_locator.inner_text()
            energy = int(energy_text.strip())
        except Exception:
            logger.warning("Could not determine energy, assuming 0")
            energy = 0

        if energy == 0:
            logger.info("No Energy Available")
            return

        # Execution
        fight_btn = page.get_by_role("button", name="Fight! x1 1")
        await HumanUtils.human_click(page, fight_btn)
        await HumanUtils.random_jitter()

        # Try to click Skip button if it appears within 3 seconds
        skip_btn = page.get_by_role("button", name="Skip")
        try:
            await skip_btn.wait_for(state="visible", timeout=3000)
            await HumanUtils.human_click(page, skip_btn)
            await HumanUtils.random_jitter()
        except Exception:
            logger.info("Skip button did not appear")

        # Click OK on reward popup
        ok_btn = page.get_by_role("button", name="OK")
        try:
            await ok_btn.wait_for(state="visible", timeout=5000)
            await HumanUtils.human_click(page, ok_btn)
            await HumanUtils.random_jitter()
        except Exception:
            logger.warning("OK button not found or not visible")

        logger.info("Battle activity completed")
