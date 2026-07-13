"""Fetch pages with Playwright (site blocks plain HTTP requests)."""

import logging

from playwright.sync_api import Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout, sync_playwright

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

LISTING_READY_SELECTORS = (
    ".ics-comp-results-item",
    ".ics-featured-competition",
    "#ics-competitions-archive",
)

STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = { runtime: {} };
"""


class BrowserClient:
    def __init__(self, *, headed: bool = False) -> None:
        self.headed = headed
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    def __enter__(self) -> "BrowserClient":
        self._playwright = sync_playwright().start()
        launch_kwargs = {
            "headless": not self.headed,
            "args": ["--disable-blink-features=AutomationControlled"],
            "ignore_default_args": ["--enable-automation"],
        }

        self._browser = None
        for channel in ("chrome", "msedge", None):
            try:
                if channel:
                    self._browser = self._playwright.chromium.launch(channel=channel, **launch_kwargs)
                    logger.info("Using installed %s browser (headed=%s)", channel, self.headed)
                else:
                    self._browser = self._playwright.chromium.launch(**launch_kwargs)
                    logger.info("Using Playwright Chromium (headed=%s)", self.headed)
                break
            except Exception as exc:
                logger.debug("Could not launch channel=%s: %s", channel, exc)

        if self._browser is None:
            raise RuntimeError("Could not launch any browser for Playwright")

        self._context = self._browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        self._context.add_init_script(STEALTH_INIT_SCRIPT)
        return self

    def __exit__(self, *args: object) -> None:
        if self._context is not None:
            self._context.close()
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()

    def fetch_html(self, url: str, wait_ms: int = 3000) -> str:
        if self._context is None:
            raise RuntimeError("BrowserClient is not started")
        page: Page = self._context.new_page()
        try:
            # Visit homepage first to pick up cookies (helps with some WAF rules).
            page.goto("https://www.competitionsciences.org/", wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(1500)
            page.goto(url, wait_until="domcontentloaded", timeout=90_000)
            for selector in LISTING_READY_SELECTORS:
                try:
                    page.wait_for_selector(selector, timeout=20_000)
                    break
                except PlaywrightTimeout:
                    continue
            page.wait_for_timeout(wait_ms)
            title = page.title()
            html = page.content()
            if "403" in title or "forbidden" in title.lower():
                logger.warning("Got blocked page for %s (title=%s). Try: python -m scraper.main --headed", url, title)
            logger.debug("Fetched %s (%s bytes, title=%s)", url, len(html), title)
            return html
        finally:
            page.close()
