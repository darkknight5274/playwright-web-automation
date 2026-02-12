import asyncio
import random
import signal
from datetime import datetime
import structlog
import uvicorn
from playwright.async_api import Page

from utils.config_loader import load_config
from utils.state import state_manager
from utils.logger import logger
from utils.session_manager import AsyncSessionManager
from activities.registry import ActivityRegistry
from utils.session import ensure_authenticated, login
from utils.human import HumanUtils
from utils.api import app
import os
import time

async def execute_activity(domain_name: str, domain_cfg: dict, activity_path: str, page: Page):
    """
    Retrieves and executes an activity, updating SharedState.
    """
    activity = ActivityRegistry.get_activity(activity_path)
    if not activity:
        logger.warning("Activity not found in registry", activity=activity_path, domain=domain_name)
        return

    full_url = f"{domain_cfg['url'].rstrip('/')}{activity.path}"

    # Update state to Busy
    await state_manager.update_status(
        domain_name,
        current_activity=activity_path,
        status="Busy",
        last_run_time=datetime.now()
    )

    try:
        logger.info("Executing activity", domain=domain_name, activity=activity_path, url=full_url)
        # Note: /collect is handled specially in its implementation
        if activity.path != "/collect":
            await page.goto(full_url, wait_until='networkidle')
        await activity.execute(page)
        logger.info("Activity completed successfully", domain=domain_name, activity=activity_path)
    except Exception as e:
        logger.error("Activity execution failed", domain=domain_name, activity=activity_path, error=str(e))
        raise e
    finally:
        # Update state back to Idle
        await state_manager.update_status(domain_name, status="Idle")

async def run_domain_sequence(domain_cfg: dict, global_cfg: dict):
    """
    Runs a single activity sequence for a specific domain.
    """
    domain_name = domain_cfg["name"]
    activity_order = domain_cfg.get("activity_order") or global_cfg.get("global_settings", {}).get("activity_order", [])
    if not activity_order:
        activity_order = ["/collect", "/troll-pre-battle.html", "/season-arena.html", "/leagues.html"]

    try:
        logger.info("Starting domain sequence", domain=domain_name)
        session = AsyncSessionManager()
        page = await session.start()

        # Navigation and Authentication check
        try:
            await page.goto(domain_cfg["url"], wait_until='networkidle', timeout=30000)
            if page.url == "about:blank":
                raise Exception("Landed on about:blank")
        except Exception as e:
            logger.error("Initial navigation failed", domain=domain_name, error=str(e))
            raise e

        # Authentication Gating
        home_url = f"{domain_cfg['url'].rstrip('/')}/home.html"
        await page.goto(home_url, wait_until='networkidle')

        if await page.locator("//div[@title='DarkKnight']").is_visible(timeout=5000):
            logger.info("Active session detected", domain=domain_name)
            await state_manager.update_status(domain_name, is_authenticated=True)
        else:
            logger.info("Attempting login", domain=domain_name)
            is_logged_in = await login(page, domain_cfg["url"])
            if is_logged_in:
                await state_manager.update_status(domain_name, is_authenticated=True)
            else:
                logger.error("Login failed", domain=domain_name)
                return

        # Execute scheduled activities
        logger.info("Executing activity sequence", domain=domain_name, order=activity_order)
        for activity_path in activity_order:
            if activity_path in domain_cfg.get("disabled_activities", []):
                logger.info("Activity disabled", domain=domain_name, activity=activity_path)
                continue

            # Check for ad-hoc requests
            status = await state_manager.get_domain_status(domain_name)
            if status and status.is_adhoc_pending:
                adhoc_activity = status.current_activity
                logger.info("Ad-hoc activity pending, executing", domain=domain_name, activity=adhoc_activity)
                await execute_activity(domain_name, domain_cfg, adhoc_activity, page)
                await state_manager.update_status(domain_name, is_adhoc_pending=False)
                await HumanUtils.random_jitter()

            await execute_activity(domain_name, domain_cfg, activity_path, page)
            await HumanUtils.random_jitter() # Anti-ban: sleep between activities

        logger.info("Domain sequence complete", domain=domain_name)

    except Exception as e:
        logger.error("Error in domain sequence", domain=domain_name, error=str(e))
        await state_manager.update_status(domain_name, status="Error")
    finally:
        await session.stop()

async def run_api():
    """
    Runs the FastAPI application.
    """
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def orchestrator():
    """
    Main entry point for the bot orchestrator.
    """
    global_cfg = load_config()
    enabled_domains = [d for d in global_cfg.get("domains", []) if d.get("enabled", True)]

    logger.info("Initializing Master Orchestrator")

    # Start API task
    api_task = asyncio.create_task(run_api())

    # Signal handling
    tasks_to_cancel = [api_task]
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: [t.cancel() for t in tasks_to_cancel])
        except NotImplementedError:
            pass

    try:
        while True:
            try:
                logger.info("Starting global activity iteration")

                # Run Activity Sequence for all domains with staggered starts
                worker_tasks = []
                for d in enabled_domains:
                    task = asyncio.create_task(run_domain_sequence(d, global_cfg))
                    worker_tasks.append(task)

                    # Stagger starts to prevent network congestion
                    delay = random.uniform(5, 12)
                    logger.info("Staggering domain start", domain=d["name"], delay=f"{delay:.2f}s")
                    await asyncio.sleep(delay)

                await asyncio.gather(*worker_tasks)

                logger.info("All activities completed. Entering 30-minute cooldown.")
            except Exception as e:
                logger.error("Orchestrator encountered an error in this cycle", error=str(e))

            for i in range(1, 7):
                await asyncio.sleep(300)
                logger.info("Heartbeat: Orchestrator waiting...", minutes_elapsed=i*5, total_wait="30m")

    except asyncio.CancelledError:
        logger.info("Orchestrator tasks cancelled")
    finally:
        api_task.cancel()
        await AsyncSessionManager.shutdown()
        logger.info("Orchestrator shut down complete.")

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(orchestrator())
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error("Master Orchestrator crashed, restarting in 10 seconds...", error=str(e))
            time.sleep(10)
