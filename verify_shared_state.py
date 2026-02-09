import asyncio
from utils.state import state_manager, DomainStatus
from datetime import datetime
import random

async def simulated_worker(name):
    print(f"Worker {name} started.")
    for i in range(3):
        # Check for ad-hoc signal
        if state_manager.check_adhoc_requested():
            status = await state_manager.get_domain_status(name)
            if status and status.is_adhoc_pending:
                print(f"Worker {name} acknowledging ad-hoc activity: {status.current_activity}")
                await state_manager.update_status(name, is_adhoc_pending=False, status="Busy")
                await state_manager.clear_adhoc_signal()

        # Update status to busy
        await state_manager.update_status(
            name,
            status="Busy",
            current_activity=f"Activity {i}",
            last_run_time=datetime.now()
        )
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Update status to idle
        await state_manager.update_status(name, status="Idle")
        await asyncio.sleep(random.uniform(0.1, 0.5))

    print(f"Worker {name} finished.")

async def monitoring_task():
    print("Monitoring task started.")
    for _ in range(10):
        statuses = await state_manager.get_all_statuses()
        output = []
        for name, status in statuses.items():
            output.append(f"{name}: {status.status} ({status.current_activity})")
        print(f"Current State: {' | '.join(output)}")
        await asyncio.sleep(0.3)
    print("Monitoring task finished.")

async def main():
    # Simulate an external ad-hoc trigger
    async def trigger_after_delay():
        await asyncio.sleep(0.5)
        print("--- Triggering Ad-hoc Activity ---")
        await state_manager.update_status("game_v1", is_adhoc_pending=True, current_activity="Urgent Task")

    # Run everything together
    await asyncio.gather(
        simulated_worker("game_v1"),
        simulated_worker("game_v2"),
        monitoring_task(),
        trigger_after_delay()
    )

if __name__ == "__main__":
    asyncio.run(main())
