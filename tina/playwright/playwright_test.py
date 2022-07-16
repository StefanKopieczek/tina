from playwright.sync_api import sync_playwright


def test_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--headless-enable-features=NetworkService,NetworkServiceInProcess",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ]
        )
        page = browser.new_page()
        page.goto("http://playwright.dev")
        title = page.title()
        browser.close()
    return title
