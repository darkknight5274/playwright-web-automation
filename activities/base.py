from abc import ABC, abstractmethod
from playwright.async_api import Page

class BaseActivity(ABC):
    @abstractmethod
    async def execute(self, page: Page):
        """Execute the activity on the given page."""
        pass
