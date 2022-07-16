from playwright.sync_api import sync_playwright


def test_playwright():
    with PlaywrightSession as session:
        page = session.browser.new_page()
        page.goto("http://playwright.dev")
        return page.title()


class PlaywrightSession:
    def __enter__(self):
        self._playwright_wrapper = sync_playwright()
        self._playwright = self._playwright_wrapper.__enter__()
        self.browser = self._playwright.chromium.launch(
            # headless=False,
            args=[
                "--headless-enable-features=NetworkService,NetworkServiceInProcess",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ],
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.browser.close()
        return self._playwright_wrapper.__exit__(exc_type, exc_value, traceback)
