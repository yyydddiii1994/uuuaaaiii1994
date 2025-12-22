from playwright.sync_api import sync_playwright
import time
import random

class YahooRankingScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

    def _setup_browser(self):
        try:
            self.playwright = sync_playwright().start()
            # Launch options for real user simulation
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            self.page = self.browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 1024}
            )
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                raise Exception("Playwright browser not found. Please run 'playwright install' in your terminal.")
            raise e

    def get_3rd_organic_url(self, keyword):
        if not self.page:
            self._setup_browser()

        try:
            # Random delay
            time.sleep(random.uniform(5, 10)) # Increased delay for safety

            url = f"https://search.yahoo.co.jp/search?p={keyword}"
            self.page.goto(url, wait_until="domcontentloaded")

            # Yahoo Japan usually uses .sw-Card for results.
            # Wait for results
            try:
                self.page.wait_for_selector(".sw-Card", timeout=10000)
            except:
                return "取得失敗 (Timeout)"

            # Get all cards
            cards = self.page.query_selector_all("#main .sw-Card")

            organic_results = []
            for card in cards:
                text_content = card.inner_text()
                # Filter ads
                if "広告" in text_content[:20]:
                    continue

                # Get link
                link_elem = card.query_selector("a")
                if link_elem:
                    href = link_elem.get_attribute("href")
                    if href:
                         # Optional: Filter out internal yahoo links if needed
                         # But for now, we trust the 'organic' nature if it's not marked as Ad
                        organic_results.append(href)

            if len(organic_results) >= 3:
                return organic_results[2]
            else:
                return f"取得できず (Found {len(organic_results)})"

        except Exception as e:
            return f"Error: {str(e)}"

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.page = None
        self.browser = None
        self.playwright = None
