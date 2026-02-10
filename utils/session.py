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

        # Task 1: The Login Sequence
        login_url = config["global_settings"]["login_url"]
        logger.info("Navigating to login URL", url=login_url)
        await page.goto(login_url)

        # Clear Popup: Wait for #popup_confirm and click it if it appears.
        try:
            logger.info("Checking for popup (#popup_confirm)...")
            # Wait for the selector to be present and visible
            popup_confirm = page.locator("#popup_confirm")
            if await popup_confirm.count() > 0:
                # Give it a small amount of time to become visible if it's animating
                await popup_confirm.wait_for(state="visible", timeout=5000)
                logger.info("Popup detected, clicking #popup_confirm.")
                await popup_confirm.click()
                # Wait for it to be hidden
                await popup_confirm.wait_for(state="hidden", timeout=5000)
                logger.info("Popup cleared.")
            else:
                logger.info("No #popup_confirm element found.")
        except Exception as e:
            logger.debug("Popup handling skipped or failed", error=str(e))

        # Trigger Login: Click the login button: //div[@class='intro_btn_wrap']//a[@title='Login'].
        logger.info("Triggering login frame.")
        try:
            # We use force=True as a fallback in case some other popup part is still blocking
            await page.locator("//div[@class='intro_btn_wrap']//a[@title='Login']").click(timeout=10000)
        except Exception:
            logger.warning("Click intercepted, attempting forced click.")
            await page.locator("//div[@class='intro_btn_wrap']//a[@title='Login']").click(force=True)

        # Handle Iframe: Locate the iframe using the selector iframe[id*='authentication-iframe'].
        logger.info("Waiting for authentication iframe...")
        login_frame_locator = page.frame_locator("iframe[id*='authentication-iframe']")

        # Inner Frame Actions:
        # Click .login-with-email.
        logger.info("Selecting email login in iframe.")
        await login_frame_locator.locator(".login-with-email").click()

        # Fill credentials
        username = os.getenv("GAME_USERNAME")
        password = os.getenv("GAME_PASSWORD")

        if username and password:
            logger.info("Filling credentials.")
            await login_frame_locator.locator("#auth-email").fill(username)
            await login_frame_locator.locator("#auth-password").fill(password)

            # Press 'Enter' to submit.
            await login_frame_locator.locator("#auth-password").press("Enter")
            logger.info("Login submitted.")
        else:
            logger.warning("No credentials found in environment.")

        # Task 2: State Persistence
        logger.info("Verifying login status (waiting for DarkKnight element).")
        try:
            # Wait for the post-login indicator
            await page.wait_for_selector("//div[@title='DarkKnight']", timeout=30000)
            logger.info("Login verified successfully.")
        except Exception as e:
            logger.error("Login verification failed or timed out", error=str(e))

        # Save the session to storage_state.json.
        dir_name = os.path.dirname(storage_state_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        await context.storage_state(path=storage_state_path)
        logger.info("Storage state saved successfully.", path=storage_state_path)

        await browser.close()
    return True
