from activities.base import BaseActivity
from activities.registry import ActivityRegistry
from utils.human import HumanUtils
from playwright.async_api import Page
import structlog
import urllib.parse

logger = structlog.get_logger()

@ActivityRegistry.register
class LeagueActivity(BaseActivity):
    @property
    def path(self) -> str:
        return "/leagues.html"

    async def execute(self, page: Page):
        logger.info("League activity started", url=page.url)

        domain_url = "/".join(page.url.split("/")[:3])
        league_url = f"{domain_url}/leagues.html"

        while True:
            if page.url != league_url:
                await page.goto(league_url, wait_until='networkidle')

            # Stale Element Protection: Wait for points and go_pre_battle buttons
            try:
                await page.wait_for_selector('.challenge_points span[energy=""]', timeout=10000)
                await page.wait_for_selector('.go_pre_battle', timeout=10000)
            except Exception as e:
                logger.warning("Required elements not found, exiting loop", error=str(e))
                break

            # Guard Logic
            try:
                points_text = await page.locator('.challenge_points span[energy=""]').inner_text()
                points = int(points_text.replace(',', '').strip())
            except Exception:
                domain = urllib.parse.urlparse(page.url).netloc
                html_content = await page.content()
                with open(f"debug_League{domain}.html", "w", encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"Saved page source to debugLeague_{domain}.html for investigation.")
                logger.warning("Could not determine challenge points, assuming 0")
                points = 0

            if points < 3:
                logger.info("Not enough Challenge Points (need 3 for x3 attack)", current=points)
                break

            # Smart Targeting
            try:
                power_locators = page.locator("div.data-column[column='power']")
                count = await power_locators.count()

                if count == 0:
                    logger.warning("No opponents found in league table")
                    break

                min_power = float('inf')
                best_index = -1

                for i in range(count):
                    power_text = await power_locators.nth(i).inner_text()
                    try:
                        power = int(power_text.replace(',', '').strip())
                        logger.info("Checking league opponent", index=i, power=power)
                        if power < min_power:
                            min_power = power
                            best_index = i
                    except ValueError:
                        continue

                if best_index != -1:
                    logger.info("Targeting lowest power opponent", power=min_power, index=best_index, current_points=points)
                    target_power_locator = power_locators.nth(best_index)
                    target_row = target_power_locator.locator("xpath=./ancestor::*[contains(@class, 'row') or contains(@class, 'container') or contains(@class, 'opponent')][1]")
                    go_btn = target_row.locator(".go_pre_battle")

                    if await go_btn.is_visible():
                        await HumanUtils.human_click(page, go_btn)
                    else:
                        await HumanUtils.human_click(page, page.locator(".go_pre_battle").nth(best_index))
                    await HumanUtils.random_jitter()
                else:
                    break
            except Exception as e:
                logger.error("Error during smart league targeting", error=str(e))
                break

            # In the next screen, click .league-multiple-battle-button to use the 'x3' attack
            x3_battle_btn = page.locator(".league-multiple-battle-button")
            try:
                await x3_battle_btn.wait_for(state="visible", timeout=10000)
                await HumanUtils.human_click(page, x3_battle_btn)
                await HumanUtils.random_jitter()
            except Exception:
                logger.error("League x3 battle button not found")
                break

            # Cleanup: common OK button
            ok_btn = page.get_by_role("button", name="OK")
            try:
                await ok_btn.wait_for(state="visible", timeout=10000)
                await HumanUtils.human_click(page, ok_btn)
                await HumanUtils.random_jitter()
            except Exception:
                logger.warning("OK button not found or not visible")
                break

        logger.info("League activity completed")
