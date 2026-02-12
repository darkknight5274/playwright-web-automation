from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from utils.human import HumanUtils
from playwright.async_api import Page
import structlog
import yaml
import os
import asyncio

logger = structlog.get_logger()

@ActivityRegistry.register
class BattleActivity(BaseActivity):
    def __init__(self):
        super().__init__()
        self.villain_config = self.load_villain_config()

    def load_villain_config(self):
        config_path = os.path.join(os.getcwd(), 'config', 'villains.yaml')
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load villains.yaml: {e}")
            return {}

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
            logger.warning("Could not determine energy, retrying after reload...", error=str(e))
            try:
                await page.reload(wait_until="networkidle")
                await asyncio.sleep(5)
                await page.wait_for_selector('#fight_energy_bar span[energy=""]', timeout=5000)
                energy_text = await page.locator('#fight_energy_bar span[energy=""]').inner_text()
                return int(energy_text.replace(',', '').strip())
            except Exception as e2:
                logger.warning("Second attempt to determine energy failed, assuming 0", error=str(e2))
                return 0

    async def execute(self, page: Page):
        logger.info("Battle activity started", url=page.url)
        base_url = "/".join(page.url.split("/")[:3])

        # Identify Domain
        domain_key = "manga" # default
        if "comic" in base_url: domain_key = "comic"
        elif "star" in base_url: domain_key = "stars"
        elif "hero" in base_url: domain_key = "hero"

        # Get Config
        domain_data = self.villain_config.get(domain_key, {})
        villains_map = domain_data.get("villains", {})
        target_list = domain_data.get("priority", [])

        if not target_list:
            logger.warning(f"No priority list found for {domain_key} in villains.yaml")
            return

        energy = await self.get_energy(page)

        for villain_name in target_list:
            if energy <= 0:
                logger.info("Energy depleted. Ending Battle Activity.")
                break

            villain_id = villains_map.get(villain_name)
            if not villain_id:
                logger.warning(f"Villain ID not found for {villain_name} in {domain_key} villains map. Skipping.")
                continue

            target_url = f"{base_url}/troll-pre-battle.html?id_opponent={villain_id}"

            logger.info(f"Scouting target: {villain_name}...", url=target_url)
            for attempt in range(3):
                try:
                    await page.goto(target_url, wait_until='networkidle')
                    break
                except Exception as e:
                    logger.warning(f"Navigation to {target_url} failed (Attempt {attempt+1}/3). Retrying...")
                    await asyncio.sleep(10)
                    if attempt == 2: raise e
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
