from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from utils.human import HumanUtils
from playwright.async_api import Page
import structlog

logger = structlog.get_logger()

# Villain ID Mapping (Domain Agnostic)
VILLAINS = {
    "dark_lord": 1, "ninja_spy": 2, "gruntt": 3, "edwarda": 4,
    "donatien": 5, "silvanus": 6, "bremen": 7, "finalmecia": 8,
    "sensei": 9, "karole": 10, "jackson": 11, "pandora": 12,
    "nike": 13, "sake": 14, "werebunny": 15, "auga": 16,
    "gross": 17, "harriet": 18, "darth_excitor": 19
}

# The Order of Battle
TARGET_PRIORITY = [
    "dark_lord", "ninja_spy", "gruntt", "edwarda", "donatien", "silvanus",
    "bremen", "finalmecia", "sensei", "karole", "jackson", "pandora",
    "nike", "sake", "werebunny", "auga", "gross", "harriet", "darth_excitor"
]

@ActivityRegistry.register
class BattleActivity(BaseActivity):
    @property
    def path(self) -> str:
        return "/troll-pre-battle.html"

    async def get_energy(self, page: Page) -> int:
        """Extract and sanitize energy value from the page."""
        try:
            # Wait for energy bar to ensure dynamic content is loaded
            await page.wait_for_selector('#fight_energy_bar span[energy=""]', timeout=5000)
            energy_text = await page.locator('#fight_energy_bar span[energy=""]').inner_text()
            return int(energy_text.replace(',', '').strip())
        except Exception as e:
            logger.warning("Could not determine energy, assuming 0", error=str(e))
            return 0

    async def execute(self, page: Page):
        logger.info("Battle activity started", url=page.url)
        base_url = "/".join(page.url.split("/")[:3])

        energy = await self.get_energy(page)

        for villain_name in TARGET_PRIORITY:
            if energy <= 0:
                logger.info("Energy depleted. Ending Battle Activity.")
                break

            villain_id = VILLAINS.get(villain_name)
            target_url = f"{base_url}/troll-pre-battle.html?id_opponent={villain_id}"

            logger.info(f"Scouting target: {villain_name}...", url=target_url)
            await page.goto(target_url, wait_until='networkidle')
            await HumanUtils.random_jitter()

            # Check for Reward Girl and fight until she's won or energy is gone
            while energy > 0:
                try:
                    # Quick check for the girl icon
                    has_girl = await page.locator(".girl_ico").count() > 0

                    if not has_girl:
                        logger.info(f"Target {villain_name} has no reward girl. Skipping.")
                        break

                    logger.info(f"Target Acquired: {villain_name} has a reward! Engaging.")

                    # Perform the fight
                    fight_btn = page.locator('button:has-text("Fight!")')
                    await HumanUtils.human_click(page, fight_btn)

                    # Handle the Victory/Defeat Modal
                    try:
                        ok_btn = page.locator('.popup_container button.orange_button_L:has-text("OK")')
                        await ok_btn.wait_for(state="visible", timeout=10000)
                        await HumanUtils.human_click(page, ok_btn)
                        await ok_btn.wait_for(state="hidden", timeout=5000)
                        await HumanUtils.random_jitter()
                    except Exception as e:
                        logger.warning("Error handling post-battle modal", error=str(e))
                        # Even if modal fails, try to continue or break if stuck
                        break

                    # Update energy for next iteration
                    energy = await self.get_energy(page)

                except Exception as e:
                    logger.error(f"Combat error with {villain_name}", error=str(e))
                    break

        logger.info("Battle activity completed")
