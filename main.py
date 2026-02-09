import asyncio
import signal
import sys
from datetime import datetime
import structlog
import uvicorn
from playwright.async_api import Page

from utils.config_loader import load_config
from utils.state import state_manager
from utils.logger import logger
from utils.session_manager import AsyncSessionManager
from activities.registry import ActivityRegistry
from utils.auth import ensure_authenticated
from utils.api import app

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
        await page.goto(full_url)
        await activity.execute(page)
        logger.info("Activity completed successfully", domain=domain_name, activity=activity_path)
    except Exception as e:
        logger.error("Activity execution failed", domain=domain_name, activity=activity_path, error=str(e))
        raise e
    finally:
        # Update state back to Idle
        await state_manager.update_status(domain_name, status="Idle")

async def run_domain_worker(domain_cfg: dict, global_cfg: dict):
    """
    Main worker loop for a specific domain.
    """
    domain_name = domain_cfg["name"]
    check_interval = global_cfg.get("global_settings", {}).get("check_interval_seconds", 60)
    activity_order = global_cfg.get("global_settings", {}).get("activity_order", [])

    while True:
        try:
            logger.info("Starting worker session", domain=domain_name)
            session = AsyncSessionManager()
            page = await session.start()

            try:
                while True:
                    # Check SharedState for ad-hoc requests
                    status = await state_manager.get_domain_status(domain_name)

                    if status and status.is_adhoc_pending:
                        # Priority 1: Ad-hoc activity
                        adhoc_activity = status.current_activity
                        logger.info("Ad-hoc activity pending, executing", domain=domain_name, activity=adhoc_activity)
                        await execute_activity(domain_name, domain_cfg, adhoc_activity, page)

                        # Clear ad-hoc status for this domain
                        await state_manager.update_status(domain_name, is_adhoc_pending=False)
                        await state_manager.clear_adhoc_signal()
                    else:
                        # Priority 2: Regular activity order
                        logger.info("No ad-hoc pending, running regular activities", domain=domain_name)
                        for activity_path in activity_order:
                            if activity_path in domain_cfg.get("disabled_activities", []):
                                logger.info("Activity disabled for domain", domain=domain_name, activity=activity_path)
                                continue

                            await execute_activity(domain_name, domain_cfg, activity_path, page)

                    logger.info("Worker iteration complete, sleeping", domain=domain_name, interval=check_interval)
                    await asyncio.sleep(check_interval)

            except asyncio.CancelledError:
                logger.info("Worker cancelled, cleaning up", domain=domain_name)
                raise
            except Exception as e:
                logger.error("Error in worker loop", domain=domain_name, error=str(e))
                # Let finally block clean up session, then outer loop will restart
                raise e
            finally:
                await session.stop()

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Worker failed, restarting in 60s", domain=domain_name, error=str(e))
            await state_manager.update_status(domain_name, status="Error")
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break

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

    logger.info("Initializing Master Orchestrator")

    # Step 1: Ensure Authentication
    try:
        await ensure_authenticated()
    except Exception as e:
        logger.error("Initial authentication failed", error=str(e))
        # We can still try to start workers if storage_state exists

    # Step 2: Prepare worker tasks
    tasks = []
    for domain_cfg in global_cfg.get("domains", []):
        if domain_cfg.get("enabled", True):
            tasks.append(asyncio.create_task(run_domain_worker(domain_cfg, global_cfg)))

    # Step 3: Add API task
    tasks.append(asyncio.create_task(run_api()))

    # Register signal handlers for SIGINT and SIGTERM
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: [t.cancel() for t in tasks])
        except NotImplementedError:
            # Signal handlers not supported on all platforms (e.g. Windows)
            pass

    # Step 4: Run all tasks
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Orchestrator tasks cancelled")
    except Exception as e:
        logger.error("Orchestrator encountered a critical error", error=str(e))
    finally:
        logger.info("Orchestrator shut down complete.")

if __name__ == "__main__":
    try:
        asyncio.run(orchestrator())
    except KeyboardInterrupt:
        # Already handled by tasks being cancelled via signal handler if possible,
        # or by asyncio.run's default behavior.
        pass
