from fastapi import FastAPI
from utils.state import domain_status
from utils.logger import logger
import structlog

app = FastAPI(title="Domain Activity API")

@app.get("/status")
async def get_status():
    """Returns the current status of all domains."""
    return domain_status

@app.get("/trigger/{activity}")
async def trigger_activity(activity: str):
    """Triggers an ad-hoc activity on all domains."""
    logger.info("Triggering activity on all domains", activity_path=activity)

    for domain in domain_status:
        # Update domain status
        domain_status[domain] = activity

        # Log with domain and activity context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            domain_name=domain,
            activity_path=activity
        )
        logger.info(f"Activity started for {domain}")

    # Clear context after finishing
    structlog.contextvars.clear_contextvars()

    return {
        "message": f"Activity '{activity}' triggered on all domains",
        "domains": list(domain_status.keys())
    }
