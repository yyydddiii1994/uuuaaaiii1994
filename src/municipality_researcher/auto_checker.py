import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import requests
from bs4 import BeautifulSoup
import threading
import time
import os
import urllib.parse
import random

# --- 全言語リスト ---
ALL_LANG_COLUMNS = [
    "日本語", "やさしい日本語", "英語", "中国語（簡体字）", "中国語（繁体字）", "韓国語",
    "アイスランド語", "アイマラ語", "アイルランド語", "アゼルバイジャン語", "アッサム語",
    "アファン・オロモ語", "アフリカーンス語", "アムハラ語", "アラビア語", "アルバニア語",
    "アルメニア語", "イタリア語", "イディッシュ語", "イヌクティトゥット語", "イボ語",
    "イロカノ語", "インドネシア語", "ウイグル語", "ウェールズ語", "ウクライナ語", "ウズベク語",
    "ウルドゥー語", "エウェ語", "エストニア語", "エスペラント語", "オディア語", "オトミ語",
    "オランダ語", "カザフ語", "カタロニア語", "ガリシア語", "ガンダ語", "カンナダ語",
    "キニアルワンダ語", "ギリシャ語", "キルギス語", "グジャラート語", "クメール語", "クルド語",
    "クロアチア語", "コーサ語", "コルシカ語", "サモア語", "ジャワ語", "ジョージア語",
    "ショナ語", "シンディ語", "シンハラ語", "スウェーデン語", "ズールー語", "スコットランド・ゲール語",
    "スペイン語", "スロバキア語", "スロベニア語", "スワヒリ語", "スンダ語", "セブアノ語",
    "セルビア語", "ソト語", "ソマリ語", "タイ語", "タジク語", "タタール語", "タヒチ語",
    "タミル語", "ダリ―語", "チェコ語", "チェワ語", "チベット語", "ティグリニャ語",
    "ディベヒ語", "テルグ語", "デンマーク語", "ドイツ語", "トウィ語（アカン語）", "トルクメン語",
    "トルコ語", "トンガ語", "ネパール語", "ノルウェー語", "ハイチ語", "ハウサ語",
    "バシキール語", "パシュト―語", "バスク語", "ハワイ語", "ハンガリー語", "パンジャブ語",
    "バンバラ語", "ヒンディー語", "フィジー語", "フィリピノ語", "フィンランド語", "フランス語",
    "フリジア語", "ブルガリア語", "ベトナム語", "ヘブライ語", "ベラルーシ語", "ペルシア語",
    "ベンガル語", "ボージュプリー語", "ポーランド語", "ボスニア語", "ポルトガル語", "マイティリー語",
    "マオリ語", "マケドニア語", "マダガスカル語", "マラーティー語", "マラヤーラム語", "マルタ語",
    "マレー語", "ミャンマー語", "モン語", "モン語", "モンゴル語", "ユカテクマヤ語", "ヨルバ語",
    "ラオ語", "ラトビア語", "リトアニア語", "リンガラ語", "ルーマニア語", "ルクセンブルク語", "ロシア語"
]

class MunicipalityCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自治体サイト攻略ツール Mark-V (広告回避＆空白無視＋一時停止機能)")
        self.root.geometry("900x650")

        style = ttk.Style()
        style.theme_use('clam')

        self.file_path = tk.StringVar()
        self.is_running = False
        self.is_paused = False
        self.create_widgets()

    def create_widgets(self):
        # 1. ファイル選択
        frame_top = ttk.LabelFrame(self.root, text="1. 作業用ファイルを選択 (Excel/CSV)", padding=10)
        frame_top.pack(fill="x", padx=10, pady=5)
        entry = ttk.Entry(frame_top, textvariable=self.file_path, width=70)
        entry.pack(side="left", padx=5)
        btn_browse = ttk.Button(frame_top, text="参照...", command=self.browse_file)
        btn_browse.pack(side="left")

        # 2. 実行エリア
        frame_action = ttk.Frame(self.root, padding=10)
        frame_action.pack(fill="x", padx=10)

        self.btn_run = ttk.Button(frame_action, text="解析スタート (Execute)", command=self.start_thread, width=25)
        self.btn_run.pack(side="left", padx=5)

        self.btn_pause = ttk.Button(frame_action, text="一時停止 (Pause)", command=self.toggle_pause, width=25, state='disabled')
        self.btn_pause.pack(side="left", padx=5)

        # 3. ログ
        frame_log = ttk.LabelFrame(self.root, text="3. 戦況ログ", padding=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        self.txt_log = scrolledtext.ScrolledText(frame_log, height=15, state='disabled', bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.txt_log.pack(fill="both", expand=True)
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=10)

    def log(self, msg):
        self.txt_log.configure(state='normal')
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state='disabled')

    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")])
        if f: self.file_path.set(f)

    def toggle_pause(self):
        if not self.is_running:
            return

        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.configure(text="再開 (Resume)")
            self.log(">>> 一時停止リクエスト... 次の処理区切りで停止します")
        else:
            self.btn_pause.configure(text="一時停止 (Pause)")
            self.log(">>> 再開します")

    def start_thread(self):
        if not self.file_path.get():
            messagebox.showwarning("エラー", "ファイルを選んでください")
            return
        self.is_running = True
        self.is_paused = False
        self.btn_run.configure(state='disabled')
        self.btn_pause.configure(state='normal', text="一時停止 (Pause)")
        threading.Thread(target=self.run_process, daemon=True).start()

    def search_official_url(self, pref, city):
        """広告を回避して公式サイトのURLを取得する"""
        query = f"{pref} {city} 公式ホームページ"
        self.log(f"  🔍 検索中: {query}")

        url = "https://html.duckduckgo.com/html/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/96.0.4664.110 Safari/537.36'}

        try:
            time.sleep(random.uniform(2.0, 4.0))
            res = requests.post(url, data={'q': query}, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')

            # 全てのリンクを取得して、広告かどうかチェックする
            links = soup.find_all('a', class_='result__a')

            for link in links:
                found_url = link.get('href')
                # 広告リンク(y.js)やトラッキングURLを除外するフィルタ
                if "y.js" in found_url or "ad_provider" in found_url:
                    continue # これは広告なのでスルーして次へ

                # DuckDuckGoのリダイレクトを解除してきれいなURLにする
                if "uddg=" in found_url:
                    parsed = urllib.parse.urlparse(found_url)
                    qs = urllib.parse.parse_qs(parsed.query)
                    if 'uddg' in qs:
                        clean_url = qs['uddg'][0]
                        return clean_url

                return found_url # そのまま使えるURLなら返す

            return None # 有効なリンクなし

        except Exception as e:
            self.log(f"  ❌ 検索エラー: {e}")
            return None

    def check_site_features(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        result = {
            "furigana": "無",
            "tool_name": "不明(要確認)",
            "has_translation": "無",
            "lang_flags": {}
        }
        for lang in ALL_LANG_COLUMNS: result["lang_flags"][lang] = 0
        result["lang_flags"]["日本語"] = 1

        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            src = str(soup).lower()
            text = soup.get_text().lower()

            if soup.find('ruby') or 'ふりがな' in text or 'ruby.js' in src or 'furigana' in src:
                result["furigana"] = "有"

            if 'goog-te-combo' in src or 'google_translate' in src:
                result["tool_name"] = "Google翻訳サービス"
                result["has_translation"] = "有"
                for lang in ALL_LANG_COLUMNS: result["lang_flags"][lang] = 1

            elif 'j-server.com' in src or 'j-server' in src:
                result["tool_name"] = "J-SERVER"
                result["has_translation"] = "有"
                for t in ["英語", "中国語（簡体字）", "中国語（繁体字）", "韓国語"]:
                    if t in result["lang_flags"]: result["lang_flags"][t] = 1

                extra_check = {"ベトナム語": "vietnam", "ポルトガル語": "portugu", "タガログ語": "tagalog", "タイ語": "thai"}
                for l_name, l_key in extra_check.items():
                    if l_key in src and l_name in result["lang_flags"]: result["lang_flags"][l_name] = 1

            elif 'wovn' in src or 'crosslanguage' in src or 'mysite-is' in src:
                tool = "Wovn.io" if 'wovn' in src else "MC-Sop/MySite"
                result["tool_name"] = tool
                result["has_translation"] = "有"
                for t in ["英語", "中国語（簡体字）", "中国語（繁体字）", "韓国語"]:
                    if t in result["lang_flags"]: result["lang_flags"][t] = 1

            elif 'english' in text or 'foreign' in src:
                if result["tool_name"] == "不明(要確認)":
                    result["tool_name"] = "独自リンク(要確認)"
                    result["has_translation"] = "有"
                    result["lang_flags"]["英語"] = 1

        except Exception as e:
            result["tool_name"] = "アクセスエラー"

        return result

    def run_process(self):
        input_path = self.file_path.get()
        self.log("--- 解析プロセス開始 ---")

        try:
            if input_path.endswith('.csv'):
                df = pd.read_csv(input_path, encoding='cp932')
            else:
                df = pd.read_excel(input_path)

            pref_col = next((c for c in df.columns if "県名" in str(c)), None)
            city_col = next((c for c in df.columns if "自治体名" in str(c)), None)
            url_col  = next((c for c in df.columns if "公式サイト" in str(c) or "URL" in str(c)), None)

            if not (pref_col and city_col):
                self.log("エラー: 県名/自治体名の列が見つかりません。")
                self.btn_run.configure(state='normal')
                self.btn_pause.configure(state='disabled')
                return

            total = len(df)
            self.progress["maximum"] = total

            for i, row in df.iterrows():
                # 一時停止チェック
                if self.is_paused:
                    self.log(f"--- 一時停止中（{i+1}行目まで完了）---")

                    # データを保存
                    paused_save_path = os.path.splitext(input_path)[0] + "_一時停止データ.xlsx"
                    df.to_excel(paused_save_path, index=False)
                    self.log(f"データを保存しました: {paused_save_path}")
                    self.log("再開ボタンを押すまで待機します...")

                    # 再開されるまでループ待機
                    while self.is_paused and self.is_running:
                        time.sleep(0.5)

                    if not self.is_running: break # 強制終了された場合
                    self.log("--- 処理を再開します ---")

                if not self.is_running: break

                # 空行(NaN)チェック
                pref = row[pref_col]
                city = row[city_col]

                if pd.isna(pref) or pd.isna(city) or str(pref) == "nan":
                    self.progress["value"] = i+1
                    continue

                target_url = str(row[url_col]) if url_col else ""

                self.log(f"[{i+1}/{total}] ターゲット: {pref} {city}")

                if (pd.isna(target_url) or "http" not in target_url):
                    found = self.search_official_url(pref, city)
                    if found:
                        self.log(f"  → URL確保: {found}")
                        target_url = found
                        if url_col: df.at[i, url_col] = found
                    else:
                        self.log("  → URL見つからず")
                        self.progress["value"] = i+1
                        continue

                res = self.check_site_features(target_url)

                if "ふりがな機能" in df.columns: df.at[i, "ふりがな機能"] = res["furigana"]
                if "翻訳種類" in df.columns:    df.at[i, "翻訳種類"] = res["tool_name"]
                if "翻訳の有無" in df.columns:  df.at[i, "翻訳の有無"] = res["has_translation"]

                lang_count = 0
                for lang_name, flag in res["lang_flags"].items():
                    if lang_name in df.columns:
                        df.at[i, lang_name] = flag
                        if lang_name != "日本語" and flag == 1:
                            lang_count += 1

                if "提供言語数" in df.columns:
                    df.at[i, "提供言語数"] = lang_count

                # 通常の途中経過保存（5件ごと）
                if i % 5 == 0:
                    temp_path = os.path.splitext(input_path)[0] + "_途中経過.xlsx"
                    df.to_excel(temp_path, index=False)

                time.sleep(1.0)
                self.progress["value"] = i+1
                # アイドルタスク更新はメインスレッドで行うべきだが、
                # 簡易的なTkinterアプリではスレッドから触っても落ちないことが多い。
                # ただし本来はQueueを使うべき。ここでは既存コードに従う。

            save_path = os.path.splitext(input_path)[0] + "_解析完了.xlsx"
            df.to_excel(save_path, index=False)

            self.log(f"完了！ 保存先: {save_path}")
            messagebox.showinfo("成功", "全ミッション完了！")

        except Exception as e:
            self.log(f"エラー: {e}")
            messagebox.showerror("エラー", str(e))
        finally:
            self.is_running = False
            self.btn_run.configure(state='normal')
            self.btn_pause.configure(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = MunicipalityCheckerApp(root)
    root.mainloop()
