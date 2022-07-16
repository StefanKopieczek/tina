import logging
import re
from dataclasses import dataclass
from typing import List
from .credentials import get_test_login
from ...playwright import PlaywrightSession


logger = logging.getLogger(__name__)


PRODUCT_ID_RE = re.compile("([^/]+)$")


@dataclass
class ShoppingItem:
    item_id: str
    title: str
    size: str


class OcadoSession:
    def __init__(self, playwright_wrapper=None, credentials=None):
        if playwright_wrapper is None:
            playwright_wrapper = PlaywrightSession()
        if credentials is None:
            credentials = get_test_login()
        self._playwright_wrapper = playwright_wrapper
        self.credentials = credentials

    def __enter__(self):
        self.playwright = self._playwright_wrapper.__enter__()
        self.page = self.playwright.browser.new_page()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.playwright.__exit__(exc_type, exc_value, traceback)

    def log_in(self) -> None:
        self.page.goto("https://www.ocado.com")
        if self.page.locator("#onetrust-accept-btn-handler").count() > 0:
            self.page.click("#onetrust-accept-btn-handler", force=True)
        self.page.click("#loginButton")
        self.page.fill("#login-input", self.credentials[0])
        self.page.fill(
            "div[data-password-input] input[type=password]", self.credentials[1]
        )
        self.page.dblclick("#login-submit-button", delay=100)

    def search(self, query: str) -> List[ShoppingItem]:
        # self.page.goto("https://www.ocado.com/webshop/startWebshop.do")
        self.page.fill("#findText", query)
        self.page.click("#findButton")
        shelf = self.page.locator("ul.fops-shelf")
        shelf.wait_for()
        matches = shelf.locator("div.fop-contentWrapper")
        self.page.mouse.wheel(0, 99999999)
        results = []
        for match_idx in range(matches.count()):
            match = matches.nth(match_idx)
            # print(match.get_attribute("innerHTML"))
            item_id = PRODUCT_ID_RE.search(
                match.locator("a").first.get_attribute("href")
            ).group(0)
            title = match.locator(".fop-title").get_attribute("title")
            size = match.locator(".fop-catch-weight").inner_text()
            results.append(ShoppingItem(item_id=item_id, title=title, size=size))
        return results

    def add_to_basket(self, item_id: str):
        self.page.goto(f"https://www.ocado.com/products/{item_id}")
        self.page.click("button.basketControls__add")


def main():
    with OcadoSession() as session:
        session.log_in()
        items = session.search("tomatoes")
        session.add_to_basket(items[0].item_id)
        print("Done")
