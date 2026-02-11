from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from utils.human import HumanUtils
from playwright.async_api import Page
import structlog

logger = structlog.get_logger()

@ActivityRegistry.register
class SeasonActivity(BaseActivity):
    @property
    def path(self) -> str:
        return "/season-arena.html"

    async def execute(self, page: Page):
        logger.info("Season activity started", url=page.url)
        await page.wait_for_timeout(2000)

        # Guard Logic: Navigate and check kisses
        kisses_locator = page.locator(".energy_counter_amount span")
        try:
            await kisses_locator.wait_for(state="visible", timeout=5000)
            kisses_text = await kisses_locator.inner_text()
            kisses = int(kisses_text.strip())
        except Exception:
            logger.warning("Could not determine kisses, assuming 0")
            kisses = 0

        if kisses == 0:
            logger.info("No Kisses Available")
            return

        # Smart Targeting
        try:
            # Get my hero stats
            my_stats_locator = page.locator("[data-hero-carac='damage']").filter(has_not=page.locator(".season_arena_opponent_container")).first
            my_damage = int(await my_stats_locator.inner_text())

            # Find my level - usually nearby damage or in a specific player info div
            # Trying to find it via a common class or nearby text
            my_level_locator = page.locator(".player_level, .hero_level, .level").filter(has_not=page.locator(".season_arena_opponent_container")).first
            my_level = int(await my_level_locator.inner_text())

            logger.info("My Hero Stats", damage=my_damage, level=my_level)

            opponents = await page.locator(".season_arena_opponent_container").all()
            target_found = False
            for opponent in opponents:
                opp_damage_text = await opponent.locator("[data-hero-carac='damage']").inner_text()
                opp_damage = int(opp_damage_text.strip())

                opp_level_text = await opponent.locator(".level").inner_text()
                opp_level = int(opp_level_text.strip())

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
                return

        except Exception as e:
            logger.error("Error during smart targeting", error=str(e))
            # Fallback to first opponent if logic fails but kisses > 0?
            # The prompt says "Click ... for the first opponent whose level is lower than yours", so if none, we stop.
            return

        # Cleanup
        skip_btn = page.get_by_role("button", name="Skip")
        try:
            await skip_btn.wait_for(state="visible", timeout=3000)
            await HumanUtils.human_click(page, skip_btn)
            await HumanUtils.random_jitter()
        except Exception:
            pass

        ok_btn = page.get_by_role("button", name="OK")
        try:
            await ok_btn.wait_for(state="visible", timeout=5000)
            await HumanUtils.human_click(page, ok_btn)
            await HumanUtils.random_jitter()
        except Exception:
            pass

        logger.info("Season activity completed")
