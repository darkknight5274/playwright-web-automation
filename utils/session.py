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

        # 1. Initial Navigation
        login_url = config["global_settings"]["login_url"]
        logger.info("Navigating to login URL", url=login_url)
        await page.goto(login_url)

        # 2. Popup Clearing: Attempt to click page.locator("#popup_confirm") with a short timeout.
        try:
            await page.locator("#popup_confirm").click(timeout=3000)
            logger.info("Popup #popup_confirm cleared.")
        except Exception:
            pass

        # 3. Open Auth Modal: await page.get_by_role("link", name="Login").click()
        logger.info("Opening auth modal.")
        try:
            # We use force=True because we've seen it's often blocked by a transparent overlay
            await page.get_by_role("link", name="Login").click(force=True, timeout=10000)
            logger.info("Clicked Login link.")
        except Exception as e:
            logger.error("Failed to click Login link", error=str(e))
            await browser.close()
            return False

        # 4. Frame Interaction
        # Define the frame using frame_locator for robustness
        auth_frame = page.frame_locator("#authentication-iframe")

        # Crucial Step: Check if the 'Login with Email' button exists and click it.
        try:
            email_login_btn = auth_frame.get_by_role("button", name="Login with Email")
            if await email_login_btn.is_visible(timeout=5000):
                logger.info("Clicking 'Login with Email' button inside frame.")
                await email_login_btn.click()
        except Exception:
            logger.debug("'Login with Email' button not found or already on email form.")

        # 5. Fill Credentials
        username = os.getenv("GAME_USERNAME")
        password = os.getenv("GAME_PASSWORD")

        if username and password:
            logger.info("Filling credentials.")
            try:
                # We use fill which handles waiting for visibility
                await auth_frame.get_by_role("textbox", name="E-mail").fill(username, timeout=10000)
                await auth_frame.get_by_role("textbox", name="Password").fill(password, timeout=10000)

                # 6. Submit: await auth_frame.get_by_role("button", name="Play Now").click()
                logger.info("Submitting login form.")
                await auth_frame.get_by_role("button", name="Play Now").click(force=True)
                logger.info("Login form submitted.")
            except Exception as e:
                logger.error("Failed to fill or submit login form", error=str(e))
        else:
            logger.warning("GAME_USERNAME or GAME_PASSWORD not set.")

        # 7. Persistence: Wait for the //div[@title='DarkKnight'] element to appear.
        logger.info("Verifying login persistence.")
        try:
            await page.wait_for_selector("//div[@title='DarkKnight']", timeout=30000)
            logger.info("Login verified: DarkKnight element found.")
        except Exception:
            logger.info("Login verification element not found. Checking URL.", url=page.url)

        # Save the session to storage_state.json.
        dir_name = os.path.dirname(storage_state_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        await context.storage_state(path=storage_state_path)
        logger.info("Storage state saved successfully.", path=storage_state_path)

        await browser.close()
    return True
