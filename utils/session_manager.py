import os
import asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from utils.config_loader import load_config

async def block_images(route):
    if route.request.resource_type == "image":
        await route.abort()
    else:
        await route.continue_()

class AsyncSessionManager:
    _playwright = None
    _browser = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.context = None
        self.config = load_config()

    @classmethod
    async def get_browser(cls, config):
        async with cls._lock:
            if cls._playwright is None:
                cls._playwright = await async_playwright().start()
            if cls._browser is None:
                cls._browser = await cls._playwright.chromium.launch(
                    headless=config["browser"]["headless"]
                )
        return cls._browser

    async def start(self):
        browser = await self.get_browser(self.config)

        # Load storage state if it exists
        storage_state_path = self.config["global_settings"]["storage_state_path"]
        try:
            if os.path.exists(storage_state_path):
                self.context = await browser.new_context(storage_state=storage_state_path)
            else:
                self.context = await browser.new_context()
        except Exception:
            # If storage_state.json is invalid or corrupted, fallback to standard context
            self.context = await browser.new_context()

        page = await self.context.new_page()

        if self.config["performance"]["block_images"]:
            await page.route("**/*", block_images)

        return page

    async def stop(self):
        if self.context:
            await self.context.close()
            self.context = None

    @classmethod
    async def shutdown(cls):
        async with cls._lock:
            if cls._browser:
                await cls._browser.close()
                cls._browser = None
            if cls._playwright:
                await cls._playwright.stop()
                cls._playwright = None

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
