from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from utils.human import HumanUtils
from playwright.async_api import Page
import structlog
import urllib.parse

logger = structlog.get_logger()

@ActivityRegistry.register
class SeasonActivity(BaseActivity):
    @property
    def path(self) -> str:
        return "/season-arena.html"

    async def execute(self, page: Page):
        logger.info("Season activity started", url=page.url)

        while True:
            await page.wait_for_load_state('networkidle')

            # Stale Element Protection: Wait for kiss bar and attack buttons
            try:
                await page.wait_for_selector('div.energy_counter_bar', timeout=10000)
                await page.wait_for_selector('.opponent_perform_button', timeout=10000)
            except Exception as e:
                logger.warning("Required elements not found, exiting loop", error=str(e))
                break

            # Guard Logic: Check kisses
            try:
                kiss_bar = page.locator('div.energy_counter_bar').filter(has=page.locator('.hudKiss_mix_icn'))
                kisses_text = await kiss_bar.locator('span[energy=""]').inner_text()
                kisses = int(kisses_text.replace(',', '').strip())
            except Exception:
                domain = urllib.parse.urlparse(page.url).netloc
                html_content = await page.content()
                with open(f"debug_Season{domain}.html", "w", encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"Saved page source to debugSeason_{domain}.html for investigation.")
                logger.warning("Could not determine kisses, assuming 0")
                kisses = 0

            if kisses <= 0:
                logger.info("No Kisses Available", kisses=kisses)
                break

            # Smart Targeting
            try:
                # Get my hero stats
                my_stats_locator = page.locator("[data-hero-carac='damage']").filter(has_not=page.locator(".season_arena_opponent_container")).first
                my_damage = int((await my_stats_locator.inner_text()).replace(',', '').strip())

                # Find my level - usually nearby damage or in a specific player info div
                my_level_locator = page.locator(".player_level, .hero_level, .level").filter(has_not=page.locator(".season_arena_opponent_container")).first
                my_level = int((await my_level_locator.inner_text()).replace(',', '').strip())

                logger.info("My Hero Stats", damage=my_damage, level=my_level, current_kisses=kisses)

                opponents = await page.locator(".season_arena_opponent_container").all()
                target_found = False
                for opponent in opponents:
                    opp_damage_text = await opponent.locator("[data-hero-carac='damage']").inner_text()
                    opp_damage = int(opp_damage_text.replace(',', '').strip())

                    opp_level_text = await opponent.locator(".level").inner_text()
                    opp_level = int(opp_level_text.replace(',', '').strip())

                    logger.info("Checking opponent", damage=opp_damage, level=opp_level)

                    if opp_level < my_level:
                        logger.info("Target found: Opponent level is lower than mine", opp_level=opp_level, my_level=my_level)
                        fight_btn = opponent.locator(".opponent_perform_button")
                        await HumanUtils.human_click(page, fight_btn)
                        await HumanUtils.random_jitter()
                        target_found = True
                        break

                if not target_found:
                    logger.info("No suitable opponent found")
                    break

            except Exception as e:
                logger.error("Error during smart targeting", error=str(e))
                break

            # OK button handling
            try:
                await page.wait_for_selector('.popup_container', state='visible', timeout=10000)
                ok_btn = page.locator('.popup_container button.orange_button_L:has-text("OK")')
                await HumanUtils.human_click(page, ok_btn)
                await page.wait_for_selector('.popup_container', state='hidden', timeout=10000)
                await HumanUtils.random_jitter()
            except Exception:
                logger.warning("Post-battle modal not handled correctly")
                break

        logger.info("Season activity completed")
