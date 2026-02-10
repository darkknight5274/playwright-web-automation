import os
import json
import asyncio
from playwright.async_api import async_playwright
from utils.logger import logger
from utils.config_loader import load_config

async def block_images(route):
    if route.request.resource_type == "image":
        await route.abort()
    else:
        await route.continue_()

async def ensure_authenticated():
    config = load_config()
    storage_state_path = config["global_settings"]["storage_state_path"]

    if os.path.exists(storage_state_path):
        logger.info("Storage state found, skipping login.", path=storage_state_path)
        return True

    logger.info("Storage state not found, initiating login.", path=storage_state_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config["browser"]["headless"])
        context = await browser.new_context()
        page = await context.new_page()

        if config["performance"]["block_images"]:
            await page.route("**/*", block_images)

        await page.goto(config["global_settings"]["login_url"])

        # Attempt automated login if credentials are provided in environment
        username = os.getenv("GAME_USERNAME")
        password = os.getenv("GAME_PASSWORD")

        if username and password:
            logger.info("Attempting automated login with environment credentials.")
            # Adjust selectors as needed for the specific site
            try:
                await page.fill('input[name="username"], input[type="text"], input[type="email"]', username)
                await page.fill('input[name="password"], input[type="password"]', password)
                await page.click('button[type="submit"], input[type="submit"]')
                # Wait for navigation or a specific element that confirms login
                await page.wait_for_load_state("networkidle")
            except Exception as e:
                logger.error("Automated login failed", error=str(e))
        else:
            logger.info("No valid credentials found in environment. Please check your .env file.")
            await asyncio.sleep(2)

        # Save the state
        os.makedirs(os.path.dirname(storage_state_path), exist_ok=True)
        await context.storage_state(path=storage_state_path)
        logger.info("Storage state saved successfully.", path=storage_state_path)

        await browser.close()
    return True
