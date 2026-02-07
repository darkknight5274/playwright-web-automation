import asyncio
import importlib
from playwright.async_api import async_playwright
from utils.config_loader import load_config
from utils.session import AsyncSessionManager
from utils.logger import logger

class Orchestrator:
    def __init__(self):
        self.config = load_config()
        self.ad_hoc_active = False
        self.ad_hoc_path = None
        self.state_changed_event = asyncio.Event()
        self.tasks = []
        self.playwright = None
        self.browser = None

    def toggle_ad_hoc(self, active: bool, path: str = None):
        """
        Toggles the global ad-hoc flag and notifies all tasks.
        """
        logger.info("Toggling ad-hoc flag", active=active, path=path)
        self.ad_hoc_active = active
        self.ad_hoc_path = path
        self.state_changed_event.set()
        self.state_changed_event.clear() # Pulse the event

    async def get_activity_func(self, activity_name):
        """
        Dynamically imports and returns the activity function.
        """
        try:
            module = importlib.import_module(f"activities.{activity_name}")
            return module.perform_activity
        except (ImportError, AttributeError) as e:
            logger.error(f"Could not load activity: {activity_name}", error=str(e))
            return None

    async def run_domain_task(self, domain_id, domain_config):
        """
        Independent task loop for each domain using a shared browser but unique context.
        """
        logger.info(f"Starting task for domain: {domain_id}")

        session_manager = AsyncSessionManager(browser=self.browser)
        try:
            page = await session_manager.start()
        except Exception as e:
            logger.error(f"Failed to start session for {domain_id}", error=str(e))
            return

        base_url = domain_config['base_url']
        paths = domain_config['paths']
        path_index = 0

        try:
            while True:
                # 1. Check if ad-hoc mode is currently active
                if self.ad_hoc_active:
                    ad_hoc_url = f"{base_url}{self.ad_hoc_path}"
                    logger.info(f"[{domain_id}] Ad-hoc mode active. Navigating to: {ad_hoc_url}")
                    try:
                        await page.goto(ad_hoc_url, wait_until="networkidle")
                    except Exception as e:
                        logger.error(f"[{domain_id}] Error during ad-hoc navigation", error=str(e))

                    # Wait for any state change, with a periodic re-check to avoid missing pulses
                    logger.info(f"[{domain_id}] Waiting for ad-hoc to be deactivated or changed...")
                    while self.ad_hoc_active and ad_hoc_url == f"{base_url}{self.ad_hoc_path}":
                        waiter = asyncio.create_task(self.state_changed_event.wait())
                        try:
                            await asyncio.wait_for(waiter, timeout=5.0)
                            break # Event was set
                        except asyncio.TimeoutError:
                            pass # Re-check loop condition
                        finally:
                            waiter.cancel()
                    continue

                # 2. Regular Flow
                path_info = paths[path_index]
                url = f"{base_url}{path_info['path']}"
                activity_name = path_info['activity']

                activity_func = await self.get_activity_func(activity_name)
                if activity_func:
                    logger.info(f"[{domain_id}] Regular flow: Running '{activity_name}' on {url}")

                    activity_task = asyncio.create_task(activity_func(page, url))
                    change_waiter = asyncio.create_task(self.state_changed_event.wait())

                    done, pending = await asyncio.wait(
                        [activity_task, change_waiter],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    if change_waiter in done:
                        logger.info(f"[{domain_id}] Interrupted by state change!")
                        activity_task.cancel()
                        try:
                            await activity_task
                        except asyncio.CancelledError:
                            pass
                    else:
                        change_waiter.cancel()
                        try:
                            await activity_task
                        except Exception as e:
                            logger.error(f"[{domain_id}] Activity failed", error=str(e))

                        path_index = (path_index + 1) % len(paths)
                else:
                    logger.warning(f"[{domain_id}] Skipping unknown activity '{activity_name}'")
                    path_index = (path_index + 1) % len(paths)

                # 3. Interruptible sleep between activities
                sleep_waiter = asyncio.create_task(self.state_changed_event.wait())
                try:
                    await asyncio.wait_for(sleep_waiter, timeout=5.0)
                    logger.info(f"[{domain_id}] Sleep interrupted by state change")
                except asyncio.TimeoutError:
                    pass
                finally:
                    sleep_waiter.cancel()

        except asyncio.CancelledError:
            logger.info(f"[{domain_id}] Task was cancelled")
        except Exception as e:
            logger.exception(f"[{domain_id}] Unexpected error in domain task", error=str(e))
        finally:
            await session_manager.stop()
            logger.info(f"[{domain_id}] Context closed for {domain_id}")

    async def start(self):
        """
        Initializes Playwright, Browser and spawns domain tasks.
        """
        logger.info("Starting Orchestrator...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config["browser"]["headless"]
        )

        domains = self.config.get('domains', {})
        for domain_id, domain_config in domains.items():
            if domain_config.get('enabled', False):
                task = asyncio.create_task(self.run_domain_task(domain_id, domain_config))
                self.tasks.append(task)

        if not self.tasks:
            logger.warning("No enabled domains found in config.")
            await self.stop()
            return

        # Start a simulation task to demonstrate ad-hoc toggling
        simulation_task = asyncio.create_task(self.simulate_ad_hoc())

        # Wait for all domain tasks and the simulation task
        await asyncio.gather(*self.tasks, simulation_task, return_exceptions=True)
        await self.stop()

    async def stop(self):
        """
        Closes the browser and stops Playwright.
        """
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        logger.info("Orchestrator stopped.")

    async def simulate_ad_hoc(self):
        """
        Simulates toggling the ad-hoc flag for demonstration purposes.
        """
        await asyncio.sleep(20)
        self.toggle_ad_hoc(True, "/ad-hoc-special-page")
        await asyncio.sleep(15)
        self.toggle_ad_hoc(False)
        await asyncio.sleep(10)
        logger.info("Simulation complete. Shutting down...")
        for task in self.tasks:
            task.cancel()

async def main():
    orchestrator = Orchestrator()
    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Received exit signal.")
    finally:
        await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())
