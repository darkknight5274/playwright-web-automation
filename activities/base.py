from abc import ABC, abstractmethod
from playwright.async_api import Page

class BaseActivity(ABC):
    @property
    @abstractmethod
    def path(self) -> str:
        """The URL path this activity handles (e.g., '/home')."""
        pass

    @abstractmethod
    async def execute(self, page: Page):
        """Execute the activity on the given page."""
        pass
