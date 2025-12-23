import time
import random
import datetime
import pandas as pd
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

class GoogleSearchScraper:
    def __init__(self, logger_callback=None, stop_event=None):
        self.logger_callback = logger_callback
        self.stop_event = stop_event or threading.Event()
        self.driver = None

    def log(self, message):
        if self.logger_callback:
            self.logger_callback(message)
        else:
            print(message)

    def setup_driver(self, headless=False):
        options = Options()
        if headless:
            options.add_argument('--headless')

        # Standard options for stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            self.log(f"Error setting up driver: {e}")
            raise

    def run(self, keywords, max_results, output_dir, headless=False):
        self.log(f"【開始】自動リサーチを開始します。全{len(keywords)}件")

        try:
            self.driver = self.setup_driver(headless=headless)
            today_str = datetime.date.today().strftime('%Y%m%d')

            for keyword in keywords:
                if self.stop_event.is_set():
                    self.log("ユーザーによる停止リクエストを受信しました。処理を中断します。")
                    break

                self.log(f"\n検索中...: {keyword}")

                try:
                    # Access Google
                    self.driver.get("https://www.google.com/")
                    time.sleep(random.uniform(2, 4))

                    if self.stop_event.is_set(): break

                    # Search
                    search_box = self.driver.find_element(By.NAME, "q")
                    search_box.send_keys(keyword)
                    search_box.submit()

                    time.sleep(random.uniform(3, 6))

                    results_data = []

                    # Get results
                    elements = self.driver.find_elements(By.CSS_SELECTOR, "div.g")

                    rank = 1
                    for elem in elements:
                        if self.stop_event.is_set(): break
                        if len(results_data) >= max_results:
                            break

                        try:
                            if "スポンサー" in elem.text:
                                continue

                            title_elem = elem.find_element(By.TAG_NAME, "h3")
                            link_elem = elem.find_element(By.TAG_NAME, "a")

                            title = title_elem.text
                            url = link_elem.get_attribute("href")

                            if not url or "google.com" in url:
                                continue

                            results_data.append({
                                "順位": rank,
                                "タイトル": title,
                                "URL": url
                            })
                            rank += 1

                        except Exception:
                            continue

                    if len(results_data) < 5:
                        self.log(f"⚠ 警告: 「{keyword}」は{len(results_data)}件しか取得できませんでした。手動確認推奨。")

                    if results_data:
                        df = pd.DataFrame(results_data)
                        df.drop_duplicates(subset=["URL"], inplace=True)

                        # Handle output directory
                        if output_dir and not os.path.exists(output_dir):
                            os.makedirs(output_dir)

                        filename = f"{keyword}_{today_str}.csv"
                        if output_dir:
                            filename = os.path.join(output_dir, filename)

                        df.to_csv(filename, index=False, encoding='utf-8-sig')
                        self.log(f"保存完了: {filename} ({len(df)}件)")
                    else:
                        self.log(f"エラー: 「{keyword}」の結果が取得できませんでした。")

                except Exception as e:
                    self.log(f"キーワード「{keyword}」の処理中にエラーが発生: {e}")

                # Wait loop with interrupt check
                wait_time = random.uniform(15, 30)
                self.log(f"休憩中...（{int(wait_time)}秒待機）")

                start_wait = time.time()
                while time.time() - start_wait < wait_time:
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)

        except Exception as e:
            self.log(f"予期せぬエラーが発生しました: {e}")
        finally:
            if self.driver:
                self.driver.quit()
            self.log("\n【終了】すべてのタスクが完了しました。")
