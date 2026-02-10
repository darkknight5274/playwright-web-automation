from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from utils.config_loader import load_config

async def block_images(route):
    if route.request.resource_type == "image":
        await route.abort()
    else:
        await route.continue_()

class AsyncSessionManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.config = load_config()

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config["browser"]["headless"]
        )

        # Load storage state if it exists
        storage_state = self.config["global_settings"]["storage_state_path"]
        import os
        if os.path.exists(storage_state):
            self.context = await self.browser.new_context(storage_state=storage_state)
        else:
            self.context = await self.browser.new_context()

        page = await self.context.new_page()

        if self.config["performance"]["block_images"]:
            await page.route("**/*", block_images)

        return page

    async def stop(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

class SessionManager:
    """Original Sync Session Manager"""
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.config = load_config()

    def start(self, headless=None):
        if headless is None:
            headless = self.config["browser"]["headless"]
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context()
        return self.context.new_page()

    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
