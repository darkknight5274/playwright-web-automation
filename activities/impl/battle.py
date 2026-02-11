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

        while True:
            # Ensure we have the query param if not present
            if "?id_opponent=1" not in page.url:
                base_url = page.url.split("?")[0]
                await page.goto(f"{base_url}?id_opponent=1", wait_until='networkidle')

            # Stale Element Protection: Wait for energy bar and fight button
            try:
                await page.wait_for_selector('#fight_energy_bar span[energy=""]', timeout=10000)
                await page.wait_for_selector('button:has-text("Fight!")', timeout=10000)
            except Exception as e:
                logger.warning("Required elements not found, exiting loop", error=str(e))
                break

            # Guard Logic: Check energy
            try:
                energy_text = await page.locator('#fight_energy_bar span[energy=""]').inner_text()
                energy = int(energy_text.replace(',', '').strip())
            except Exception:
                logger.warning("Could not determine energy, assuming 0")
                energy = 0

            if energy <= 0:
                logger.info("No Energy Available", energy=energy)
                break

            # Execution
            logger.info("Performing battle", current_energy=energy)
            fight_btn = page.get_by_role("button", name="Fight! x1 1")
            await HumanUtils.human_click(page, fight_btn)
            await HumanUtils.random_jitter()

            # Click OK on reward popup
            ok_btn = page.get_by_role("button", name="OK")
            try:
                await ok_btn.wait_for(state="visible", timeout=10000)
                await HumanUtils.human_click(page, ok_btn)
                await HumanUtils.random_jitter()
            except Exception:
                logger.warning("OK button not found or not visible")
                # If OK button doesn't appear, maybe something is wrong, but we'll try next iteration or exit
                break

        logger.info("Battle activity completed")
