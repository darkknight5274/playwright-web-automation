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
        if not os.path.exists(config_path):
            logger.warning(f"Villains config not found at {config_path}")
            return {}
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except Exception as e:
            logger.error(f"Failed to load villains.yaml: {e}")
            return {}

    def get_domain(self, url: str) -> str:
        """Extracts the domain key from the URL."""
        url_lower = url.lower()
        if "manga" in url_lower: return "manga"
        if "comic" in url_lower: return "comic"
        if "star" in url_lower: return "stars"
        if "hero" in url_lower: return "hero"
        return "manga" # Default fallback

    async def is_fight_possible(self, page: Page) -> bool:
        """Verifies if the 'Reward Girl' is present and 'Fight!' button is visible."""
        try:
            # Quick check for the girl icon
            has_girl = await page.locator(".girl_ico").count() > 0
            if not has_girl:
                return False

            # Check for Fight button
            fight_btn = page.locator('button:has-text("Fight!")')
            if not await fight_btn.is_visible():
                return False

            return True
        except Exception:
            return False

    async def perform_fight(self, page: Page):
        """Clicks the 'Fight!' button and handles the post-battle modal."""
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

    @property
    def path(self) -> str:
        return "/troll-pre-battle.html"

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
        domain_key = self.get_domain(page.url)
        logger.info("Battle activity started", url=page.url, domain=domain_key)
        base_url = "/".join(page.url.split("/")[:3])

        # Get Config
        domain_data = self.villain_config.get(domain_key)
        if not domain_data:
            logger.warning(f"No configuration found for domain {domain_key} in villains.yaml")
            return

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
                logger.warning("Villain ID not found in map", villain=villain_name, domain=domain_key)
                continue

            target_url = f"{base_url}/troll-pre-battle.html?id_opponent={villain_id}"

            if page.url != target_url:
                logger.info("Scouting target", domain=domain_key, villain=villain_name, troll_id=villain_id, url=target_url)
                for attempt in range(3):
                    try:
                        await page.goto(target_url, wait_until='networkidle')
                        break
                    except Exception as e:
                        logger.warning(f"Navigation to {target_url} failed (Attempt {attempt+1}/3). Retrying...")
                        await asyncio.sleep(10)
                        if attempt == 2: raise e
                await HumanUtils.random_jitter()

            # Drain energy on this target as long as possible
            while energy > 0:
                if await self.is_fight_possible(page):
                    logger.info("Target Acquired: Engagement possible", domain=domain_key, villain=villain_name, troll_id=villain_id)
                    await self.perform_fight(page)
                    energy = await self.get_energy(page)
                else:
                    logger.info("Target has no reward or fight not possible. Moving to next target.", villain=villain_name)
                    break

        logger.info("Battle activity completed")
