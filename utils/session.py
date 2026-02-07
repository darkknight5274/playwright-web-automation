from playwright.sync_api import sync_playwright

class SessionManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    def start(self, headless=True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context()
        return self.context.new_page()

    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
