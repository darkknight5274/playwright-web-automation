import asyncio
import random

class HumanUtils:
    @staticmethod
    async def random_sleep(min_sec: float = 1.5, max_sec: float = 4.0):
        """
        Sleeps for a random duration between min_sec and max_sec to simulate human behavior.
        """
        duration = random.uniform(min_sec, max_sec)
        await asyncio.sleep(duration)
