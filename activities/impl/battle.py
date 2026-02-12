from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from utils.human import HumanUtils
from playwright.async_api import Page
import structlog
import yaml
import os
import asyncio

logger = structlog.get_logger()

BATTLE_PATH = "/troll-pre-battle.html"

@ActivityRegistry.register
class BattleActivity(BaseActivity):
    def __init__(self):
        super().__init__()
        self.villain_config = self.load_villain_config()
        self.page = None

    @property
    def base_url(self) -> str:
        if not self.page:
            return ""
        return "/".join(self.page.url.split("/")[:3])

    @property
    def domain(self) -> str:
        base_url = self.base_url
        if "comic" in base_url: return "comic"
        elif "star" in base_url: return "stars"
        elif "hero" in base_url: return "hero"
        return "manga"

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
        return BATTLE_PATH

    async def get_energy(self, page: Page) -> int:
        # 1. Wait for the container first (it loads before the text)
        try:
            await page.wait_for_selector('.energy_counter', state='visible', timeout=10000)
        except:
            logger.warning("Energy container not found. reloading...")
            await page.reload()
            await page.wait_for_load_state("networkidle")

        # 2. Attempt to find the specific value span
        try:
            # Targeting the span with energy="" attribute
            energy_locator = page.locator('#fight_energy_bar span[energy=""]')
            await energy_locator.wait_for(state="visible", timeout=10000)
            text = await energy_locator.inner_text()

            # 3. Sanitize and Return
            return int(text.replace(',', '').strip())
        except Exception as e:
            # Determine domain for the screenshot filename
            domain = "unknown"
            if "manga" in page.url: domain = "manga"
            elif "comic" in page.url: domain = "comic"
            elif "star" in page.url: domain = "stars"
            elif "hero" in page.url: domain = "hero"

            # Take a debug screenshot only if we truly fail
            await page.screenshot(path=f"debug_energy_fail_{domain}.png")
            logger.error(f"Failed to read energy after retry: {e}")
            return 0

    async def execute(self, page: Page):
        self.page = page
        logger.info("Battle activity started", url=page.url)

        # 1. Load the config
        config = self.load_villain_config()
        domain_config = config.get(self.domain, {})

        # 2. Identify the target and its ID
        priority_list = domain_config.get('priority', [])
        villain_map = domain_config.get('villains', {})

        if not priority_list:
            logger.warning(f"No priority targets for {self.domain}. Skipping battle.")
            return

        # For now, we take the first available priority target
        target_name = priority_list[0]
        target_id = villain_map.get(target_name, 1) # Default to 1 if not found

        # 3. Construct the dynamic URL
        target_url = f"{self.base_url}/troll-pre-battle.html?id_opponent={target_id}"

        logger.info(f"Targeting {target_name} (ID: {target_id}) on {self.domain}")

        # 4. Navigate only if necessary
        if target_url not in page.url:
            for attempt in range(3):
                try:
                    await page.goto(target_url, wait_until="networkidle")
                    break
                except Exception as e:
                    logger.warning(f"Navigation to {target_url} failed (Attempt {attempt+1}/3). Retrying...")
                    await asyncio.sleep(10)
                    if attempt == 2: raise e

        await HumanUtils.random_jitter()
        energy = await self.get_energy(page)

        # Check for Reward Girl and fight until she's won or energy is gone
        while energy > 0:
            try:
                # Quick check for the girl icon
                has_girl = await page.locator(".girl_ico").count() > 0

                if not has_girl:
                    logger.info(f"Target {target_name} has no reward girl. Skipping.")
                    break

                logger.info(f"Target Acquired: {target_name} has a reward! Engaging.")

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
                logger.error(f"Combat error with {target_name}", error=str(e))
                break

        logger.info("Battle activity completed")
