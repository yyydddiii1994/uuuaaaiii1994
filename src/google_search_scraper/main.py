import time
import random
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定エリア ---
# 検索したいキーワードリスト
KEYWORDS = ["伊万里 ラーメン", "N-BOX 維持費", "海外FX ボーナス"]
# 取得したい最大件数
MAX_RESULTS = 20
# 出力フォルダ（空欄なら同じ場所）
OUTPUT_DIR = ""

# --- ブラウザ起動設定 ---
def setup_driver():
    options = Options()
    # 完全に隠さず、ブラウザを表示する（CAPTCHAが出た時に手動対応するため）
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def main():
    driver = setup_driver()
    today_str = datetime.date.today().strftime('%Y%m%d')

    print(f"【開始】自動リサーチを開始します。全{len(KEYWORDS)}件")

    try:
        for keyword in KEYWORDS:
            print(f"\n検索中...: {keyword}")

            # Google検索へアクセス
            driver.get("https://www.google.com/")
            time.sleep(random.uniform(2, 4))

            # 検索ボックスに入力して送信
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(keyword)
            search_box.submit()

            # 読み込み待機（人間らしく振る舞う）
            time.sleep(random.uniform(3, 6))

            results_data = []

            # 検索結果のブロックを取得（クラス名はGoogleの仕様変更で変わる可能性あり）
            # 一般的に 'div.g' がオーガニック検索結果のコンテナ
            elements = driver.find_elements(By.CSS_SELECTOR, "div.g")

            rank = 1
            for elem in elements:
                if len(results_data) >= MAX_RESULTS:
                    break

                try:
                    # 広告や地図などのノイズを除去する簡易チェック
                    # テキストを取得して「スポンサー」が含まれていたらスキップ
                    if "スポンサー" in elem.text:
                        continue

                    # タイトル(h3)とURL(aタグ)を抽出
                    title_elem = elem.find_element(By.TAG_NAME, "h3")
                    link_elem = elem.find_element(By.TAG_NAME, "a")

                    title = title_elem.text
                    url = link_elem.get_attribute("href")

                    # URLが空、またはGoogle関連リンクならスキップ
                    if not url or "google.com" in url:
                        continue

                    # データ格納
                    results_data.append({
                        "順位": rank,
                        "タイトル": title,
                        "URL": url
                    })
                    rank += 1

                except Exception as e:
                    # 要素が見つからない場合などはスキップ
                    continue

            # --- 5件未満チェック（kotetsu354仕様）---
            if len(results_data) < 5:
                print(f"⚠ 警告: 「{keyword}」は{len(results_data)}件しか取得できませんでした。手動確認推奨。")
                # 備考欄用に空行を追加するなどの処理が可能

            # --- CSV保存 ---
            if results_data:
                df = pd.DataFrame(results_data)

                # 重複排除（念のため）
                df.drop_duplicates(subset=["URL"], inplace=True)

                filename = f"{OUTPUT_DIR}{keyword}_{today_str}.csv"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"保存完了: {filename} ({len(df)}件)")
            else:
                print(f"エラー: 「{keyword}」の結果が取得できませんでした。")

            # 次の検索までの待機時間（重要！短すぎるとBANされます）
            # イブの夜くらいゆっくり待ちましょう
            wait_time = random.uniform(15, 30)
            print(f"休憩中...（{int(wait_time)}秒待機）")
            time.sleep(wait_time)

    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
    finally:
        driver.quit()
        print("\n【終了】すべてのタスクが完了しました。")

if __name__ == "__main__":
    main()
