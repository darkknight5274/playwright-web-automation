from fastapi import FastAPI
from utils.state import state_manager
from utils.logger import logger
from datetime import datetime
import structlog

app = FastAPI(title="Domain Activity API")

@app.get("/status")
async def get_status():
    """Returns the current status of all domains."""
    return await state_manager.get_all_statuses()

@app.get("/trigger/{activity}")
async def trigger_activity(activity: str):
    """Triggers an ad-hoc activity on all domains."""
    logger.info("Triggering activity on all domains", activity_path=activity)

    statuses = await state_manager.get_all_statuses()
    for domain in statuses:
        # Update domain status via state manager
        await state_manager.update_status(
            domain,
            current_activity=activity,
            is_adhoc_pending=True,
            status="Busy",
            last_run_time=datetime.now()
        )

        # Log with domain and activity context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            domain_name=domain,
            activity_path=activity
        )
        logger.info(f"Ad-hoc activity '{activity}' scheduled for {domain}")

    # Clear context after finishing
    structlog.contextvars.clear_contextvars()

    return {
        "message": f"Activity '{activity}' triggered on all domains",
        "domains": list(statuses.keys())
    }
