import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Hardcoded list of 32 keywords
KEYWORDS = [
    "岡山 出張買取 買取大吉Pモール岡山雄町店",  # Example provided
    "iPhone 修理 東京",
    "不用品回収 大阪",
    "格安SIM 比較",
    "クレジットカード おすすめ",
    "FX 口座開設 キャンペーン",
    "プログラミングスクール 無料",
    "ダイエット サプリ 効果",
    "英会話教室 横浜",
    "引っ越し 費用 見積もり",
    "中古車 買取 相場",
    "ウォーターサーバー 比較",
    "青汁 ランキング",
    "脱毛サロン 口コミ",
    "育毛剤 おすすめ 男性",
    "マンション売却 査定",
    "リフォーム 費用 キッチン",
    "結婚相談所 東京",
    "着物 買取 高額",
    "ブランド買取 銀座",
    "即日融資 カードローン",
    "薬剤師 転職 サイト",
    "看護師 求人 大阪",
    "エンジニア 転職 未経験",
    "ふるさと納税 おすすめ",
    "動画配信サービス 比較",
    "光回線 キャッシュバック",
    "格安航空券 予約",
    "ホテル予約 比較",
    "レンタカー 格安",
    "キャットフード おすすめ",
    "ドッグフード 安全"
]

class YahooSearcher:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless

    def setup_driver(self):
        """Initializes the Selenium WebDriver with appropriate options."""
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")

        # Anti-detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # Additional script to hide webdriver property
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    })
                """
            })
            logger.info("Driver initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise

    def search_keyword(self, keyword):
        """
        Searches for the keyword on Yahoo! JAPAN and returns the first organic result URL.
        Returns: URL string or None if not found/error.
        """
        if not self.driver:
            self.setup_driver()

        search_url = f"https://search.yahoo.co.jp/search?p={keyword}"
        logger.info(f"Searching for: {keyword}")

        try:
            self.driver.get(search_url)

            # Random sleep to mimic human behavior
            time.sleep(random.uniform(2, 4))

            # Wait for results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "wrapper"))
            )

            # Check for CAPTCHA or blocking text (simplified check)
            page_source = self.driver.page_source
            if "利用規約に違反する行為" in page_source or "robot" in page_source.lower():
                logger.warning("Possible blocking detected.")
                return "BLOCKED/CAPTCHA"

            # Logic to find organic results
            # Yahoo JP results are typically in generic containers.
            # We look for the main column results, excluding ads.

            # Common structure for organic results in Yahoo JP (Mobile/Desktop vary, but often similar)
            # Desktop: #web > ol > li or .sw-Card
            # We try to target generic result containers.

            # Strategy: Find all result containers, filter out those that look like ads.
            # Ads often have "広告" text or specific classes like "sw-Ad".

            # Get all potential result elements
            # .sw-Card is a very common class for Yahoo JP search results (both ad and organic)
            results = self.driver.find_elements(By.CSS_SELECTOR, ".sw-Card, .sw-Equiv, .result")

            if not results:
                # Fallback: look for generic list items in the web results section
                results = self.driver.find_elements(By.CSS_SELECTOR, "#web ol li")

            for res in results:
                try:
                    text_content = res.text
                    # Check for Ad markers
                    if "広告" in text_content[:50] or "スポンサー" in text_content[:50]:
                        continue

                    # Also check for specific ad classes if visible
                    class_attr = res.get_attribute("class")
                    if "Ad" in class_attr or "ad" in class_attr.lower():
                        continue

                    # Try to find the main link (h3 > a or just a)
                    link = res.find_element(By.CSS_SELECTOR, "h3 a")
                    url = link.get_attribute("href")

                    # Exclude Yahoo internal links if necessary (though usually they are relevant)
                    if url:
                        logger.info(f"Found organic URL: {url}")
                        return url
                except Exception:
                    # If element structure doesn't match, skip it
                    continue

            logger.info("No organic result found.")
            return "No Organic Result Found"

        except Exception as e:
            logger.error(f"Error searching {keyword}: {e}")
            return f"Error: {str(e)}"

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

if __name__ == "__main__":
    # Simple test
    searcher = YahooSearcher(headless=True)
    try:
        url = searcher.search_keyword("Python")
        print(f"Result: {url}")
    finally:
        searcher.close()
