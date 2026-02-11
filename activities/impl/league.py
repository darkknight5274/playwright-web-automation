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
        await page.wait_for_timeout(2000)

        # Guard Logic
        energy_locator = page.locator("#leagues .challenge_points .over span")
        try:
            await energy_locator.wait_for(state="visible", timeout=5000)
            energy_text = await energy_locator.inner_text()
            energy = int(energy_text.strip())
        except Exception:
            logger.warning("Could not determine challenge points, assuming 0")
            energy = 0

        if energy < 3:
            logger.info("Not enough Challenge Points (need 3)", current=energy)
            return

        # Execution
        go_pre_battle_btn = page.locator(".go_pre_battle").first
        await HumanUtils.human_click(page, go_pre_battle_btn)
        await HumanUtils.random_jitter()

        # In the next screen, click .league-multiple-battle-button to use the 'x3' attack
        x3_battle_btn = page.locator(".league-multiple-battle-button")
        try:
            await x3_battle_btn.wait_for(state="visible", timeout=5000)
            await HumanUtils.human_click(page, x3_battle_btn)
            await HumanUtils.random_jitter()
        except Exception:
            logger.error("League x3 battle button not found")

        # Cleanup: common OK button
        ok_btn = page.get_by_role("button", name="OK")
        try:
            await ok_btn.wait_for(state="visible", timeout=5000)
            await HumanUtils.human_click(page, ok_btn)
            await HumanUtils.random_jitter()
        except Exception:
            pass

        logger.info("League activity completed")
