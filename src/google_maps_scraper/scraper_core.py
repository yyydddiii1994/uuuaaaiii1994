import time
import random
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
]

class MapScraper:
    def __init__(self, config, update_log_callback=None, check_pause_callback=None):
        self.config = config
        self.log_callback = update_log_callback
        self.check_pause = check_pause_callback
        self.browser = None
        self.page = None
        self.playwright = None
        self.stop_flag = False

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def random_sleep(self, min_time=None, max_time=None):
        """人間らしいランダムな待機"""
        if self.stop_flag: return

        min_t = min_time if min_time is not None else self.config.get('min_delay', 8)
        max_t = max_time if max_time is not None else self.config.get('max_delay', 15)
        sleep_time = random.uniform(min_t, max_t)
        # self.log(f"⏳ 待機中: {sleep_time:.1f}秒") # ログが多すぎるのでコメントアウト
        time.sleep(sleep_time)

    def start_browser(self):
        """ブラウザを起動する"""
        self.playwright = sync_playwright().start()
        # 安全のためデフォルトでHeadless=Falseを推奨
        headless = self.config.get('headless', False)

        user_agent = random.choice(USER_AGENTS) if self.config.get('user_agent_rotation', True) else USER_AGENTS[0]
        self.log(f"🌐 ブラウザ起動 (UA: {user_agent[:30]}...)")

        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.page = self.browser.new_page(
            user_agent=user_agent,
            viewport={'width': 1280, 'height': 800}
        )
        self.page.goto("https://www.google.com/maps?hl=ja")
        self.random_sleep(3, 5)

    def close_browser(self):
        """ブラウザを閉じる"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def check_captcha(self):
        """CAPTCHA検出と一時停止"""
        try:
            if self.page.locator("iframe[src*='recaptcha']").count() > 0 or \
               "ロボットではありません" in self.page.content():
                self.log("⚠️ CAPTCHA検出！ 手動解決を待機します...")
                self.log("👉 解決後、GUIの「再開」ボタンを押してください。")

                while True:
                    if self.stop_flag: break
                    if self.check_pause and not self.check_pause():
                        break
                    time.sleep(1)
        except Exception:
            pass

    def scrape_keyword(self, keyword):
        """1つのキーワードで検索・収集"""
        if self.stop_flag: return []

        results = []
        try:
            # 検索ボックスに入力
            search_box = self.page.locator(self.config['selectors']['search_box'])
            search_box.fill("")
            search_box.fill(keyword)
            self.random_sleep(1, 2)
            self.page.locator(self.config['selectors']['search_button']).click()
            self.log(f"🔍 検索: {keyword}")
            self.random_sleep(5, 8)

            # フィードスクロール
            self.scroll_feed()

            # 結果数を取得
            card_selector = self.config['selectors']['result_card']
            count = self.page.locator(card_selector).count()
            self.log(f"📍 候補数: {count} (取得制限などで全件ではない場合があります)")

            for i in range(count):
                if self.stop_flag: break

                try:
                    # インデックスで再取得してStale Elementを防ぐ
                    card = self.page.locator(card_selector).nth(i)

                    # 画面内にスクロール
                    card.scroll_into_view_if_needed()
                    card.click()
                    self.random_sleep(3, 5) # 詳細ロード待機

                    data = self.extract_details(keyword)
                    if data:
                        results.append(data)
                        self.log(f"✅ 取得 [{i+1}/{count}]: {data['Name']}")

                    # リストに戻るための処理（詳細パネルが開いてリストが隠れた場合）
                    self.go_back_to_list()

                    self.random_sleep()

                except Exception as e:
                    self.log(f"❌ 個別取得エラー ({i+1}): {e}")
                    continue

        except Exception as e:
            self.log(f"❌ 検索エラー ({keyword}): {e}")

        return results

    def scroll_feed(self):
        """左側パネルをスクロールして結果をロード"""
        feed_selector = self.config['selectors']['feed_panel']
        try:
            self.page.wait_for_selector(feed_selector, timeout=10000)

            # 最大20回または「すべての結果」が出るまでスクロール
            # ※ 安全のため、あまりに多くスクロールしすぎない
            max_scrolls = 10
            for _ in range(max_scrolls):
                if self.stop_flag: break
                self.page.evaluate(f"document.querySelector('{feed_selector}').scrollBy(0, 1000)")
                self.random_sleep(1, 2)

                # アイテム数が増えなくなったら終了などのロジックも入れられるが、
                # ここでは簡易的に一定回数スクロール
        except Exception:
            self.log("⚠️ スクロール可能なフィードが見つかりません（1件のみ表示の可能性）")

    def go_back_to_list(self):
        """詳細表示からリスト一覧に戻る"""
        # "戻る" ボタンを探す
        try:
            # aria-label="戻る" または 一般的なBackアイコンクラス
            back_btn = self.page.locator("button[aria-label='戻る']")
            if back_btn.is_visible():
                back_btn.click()
                self.random_sleep(1, 2)
            else:
                # 英語環境などのフォールバック
                back_btn_en = self.page.locator("button[aria-label='Back']")
                if back_btn_en.is_visible():
                    back_btn_en.click()
                    self.random_sleep(1, 2)
        except:
            pass

    def extract_details(self, keyword):
        """詳細パネルから情報を抽出"""
        try:
            name = self.page.locator(self.config['selectors']['name']).first.inner_text()
        except:
            name = "不明"

        try:
            address = self.page.locator(self.config['selectors']['address']).get_attribute("aria-label")
            if address: address = address.replace("住所: ", "")
        except:
            address = ""

        try:
            phone = self.page.locator(self.config['selectors']['phone']).get_attribute("aria-label")
            if phone: phone = phone.replace("電話: ", "")
        except:
            phone = ""

        try:
            url = self.page.url
        except:
            url = ""

        return {
            "Keyword": keyword,
            "Name": name,
            "Address": address,
            "Phone": phone,
            "URL": url
        }

    def stop(self):
        self.stop_flag = True
