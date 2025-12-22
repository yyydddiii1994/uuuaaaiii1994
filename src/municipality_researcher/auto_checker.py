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
import queue

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
        self.root.title("自治体サイト攻略ツール Mark-VII (リダイレクト追跡・完全自動版)")
        self.root.geometry("950x750")

        style = ttk.Style()
        style.theme_use('clam')

        self.file_path = tk.StringVar()
        self.is_running = False
        self.is_paused = False
        self._paused_saved = False

        # Thread-safe communication
        self.gui_queue = queue.Queue()

        self.create_widgets()
        self.root.after(100, self.process_queue)

    def create_widgets(self):
        # 1. ファイル選択
        frame_top = ttk.LabelFrame(self.root, text="1. 作業用ファイルを選択", padding=10)
        frame_top.pack(fill="x", padx=10, pady=5)
        entry = ttk.Entry(frame_top, textvariable=self.file_path, width=70)
        entry.pack(side="left", padx=5)
        btn_browse = ttk.Button(frame_top, text="参照...", command=self.browse_file)
        btn_browse.pack(side="left")

        # 2. 操作パネル
        frame_action = ttk.LabelFrame(self.root, text="2. 操作パネル", padding=10)
        frame_action.pack(fill="x", padx=10)
        self.btn_run = ttk.Button(frame_action, text="解析スタート (Execute)", command=self.start_thread, width=25)
        self.btn_run.pack(side="left", padx=5)
        self.btn_pause = ttk.Button(frame_action, text="一時停止＆保存 (Pause)", command=self.toggle_pause, width=25, state='disabled')
        self.btn_pause.pack(side="left", padx=5)
        lbl_hint = ttk.Label(frame_action, text="※「English」等のリンク先まで追跡して判定します", foreground="red")
        lbl_hint.pack(side="left", padx=10)

        # 3. ログ
        frame_log = ttk.LabelFrame(self.root, text="3. 戦況ログ", padding=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        self.txt_log = scrolledtext.ScrolledText(frame_log, height=15, state='disabled', bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.txt_log.pack(fill="both", expand=True)
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=10)

    def process_queue(self):
        """Handle GUI updates from the background thread"""
        try:
            while True:
                task = self.gui_queue.get_nowait()
                action = task.get("action")

                if action == "log":
                    self.txt_log.configure(state='normal')
                    self.txt_log.insert(tk.END, task["msg"] + "\n")
                    self.txt_log.see(tk.END)
                    self.txt_log.configure(state='disabled')
                elif action == "progress_max":
                    self.progress["maximum"] = task["value"]
                elif action == "progress_update":
                    self.progress["value"] = task["value"]
                elif action == "finish":
                    messagebox.showinfo(task["title"], task["msg"])
                    self.btn_run.configure(state='normal')
                    self.btn_pause.configure(state='disabled')
                elif action == "error":
                    messagebox.showerror("エラー", task["msg"])
                    self.btn_run.configure(state='normal')
                    self.btn_pause.configure(state='disabled')
                elif action == "enable_pause":
                     self.btn_pause.configure(state='normal', text="一時停止＆保存 (Pause)")

                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def log(self, msg):
        self.gui_queue.put({"action": "log", "msg": msg})

    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")])
        if f: self.file_path.set(f)

    def toggle_pause(self):
        if self.is_paused:
            self.is_paused = False
            self.btn_pause.configure(text="一時停止＆保存 (Pause)")
            self.log(">>> 再開します... Go!")
        else:
            self.is_paused = True
            self.btn_pause.configure(text="再開 (Resume)")
            self.log(">>> 一時停止中。データ保存待機...")

    def start_thread(self):
        if not self.file_path.get():
            messagebox.showwarning("エラー", "ファイルを選んでください")
            return
        self.is_running = True
        self.is_paused = False
        self.btn_run.configure(state='disabled')
        # Use queue to enable pause button safely from thread start logic if needed,
        # but here we are in main thread so direct config is fine.
        # But for consistency with finish logic, we set initial state here.
        self.btn_pause.configure(state='normal', text="一時停止＆保存 (Pause)")
        threading.Thread(target=self.run_process, daemon=True).start()

    def search_official_url(self, pref, city):
        query = f"{pref} {city} 公式ホームページ"
        self.log(f"  🔍 URL検索: {query}")
        url = "https://html.duckduckgo.com/html/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/96.0.4664.110 Safari/537.36'}
        try:
            time.sleep(random.uniform(2.0, 4.0))
            res = requests.post(url, data={'q': query}, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', class_='result__a')
            for link in links:
                found_url = link.get('href')
                if "y.js" in found_url or "ad_provider" in found_url: continue
                if "uddg=" in found_url:
                    parsed = urllib.parse.urlparse(found_url)
                    qs = urllib.parse.parse_qs(parsed.query)
                    if 'uddg' in qs: return qs['uddg'][0]
                return found_url
            return None
        except Exception:
            return None

    def analyze_source(self, src, text):
        """ソースコードとテキストからツールを判定する共通ロジック"""
        tool = None
        langs_found = {} # 追加で発見した言語

        # 1. Google
        if 'goog-te-combo' in src or 'google_translate' in src or 'google.co.jp/translate' in src:
            tool = "Google翻訳サービス"

        # 2. J-SERVER
        elif 'j-server.com' in src or 'j-server' in src:
            tool = "J-SERVER"
            # J-SERVER特有の言語チェック
            extra = {"ベトナム語": "vietnam", "ポルトガル語": "portugu", "タガログ語": "tagalog", "タイ語": "thai", "インドネシア語": "indonesi"}
            for l_name, l_key in extra.items():
                if l_key in src: langs_found[l_name] = 1

        # 3. Wovn
        elif 'wovn' in src:
            tool = "Wovn.io"

        # 4. CrossLanguage (Mic-Sop)
        elif 'crosslanguage' in src or 'transer.com' in src or 'honyaku' in src or 'mysite-is' in src:
            tool = "MC-Sop/MySite"

        return tool, langs_found

    def check_site_features(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        result = {"furigana": "無", "tool_name": "不明(要確認)", "has_translation": "無", "lang_flags": {}}
        for lang in ALL_LANG_COLUMNS: result["lang_flags"][lang] = 0
        result["lang_flags"]["日本語"] = 1

        try:
            # --- 1. メインページへのアクセス ---
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            src = str(soup).lower()
            text = soup.get_text().lower()

            # ふりがな判定
            if soup.find('ruby') or 'ふりがな' in text or 'ruby.js' in src or 'furigana' in src:
                result["furigana"] = "有"

            # ツール判定 (第1段階)
            detected_tool, extra_langs = self.analyze_source(src, text)

            # --- 2. ツールが見つからない場合：リンク追跡モード (Mark VIIの新機能) ---
            if not detected_tool:
                # 翻訳ページへのリンクを探す
                potential_links = []
                for a in soup.find_all('a', href=True):
                    link_text = a.get_text().lower()
                    href = a['href'].lower()
                    # キーワードで探す
                    if 'english' in link_text or 'foreign' in link_text or 'translation' in link_text or '翻訳' in link_text or 'foreign' in href:
                        potential_links.append(a['href'])

                # 最初の数個だけチェック（負荷対策）
                for link_href in potential_links[:3]:
                    try:
                        # 絶対URLに変換
                        target_link = urllib.parse.urljoin(url, link_href)

                        # ★リンク先URLだけで判定できるか？ (北海道庁パターン)
                        if 'google' in target_link and 'translate' in target_link:
                            detected_tool = "Google翻訳サービス"
                            break
                        if 'j-server.com' in target_link:
                            detected_tool = "J-SERVER"
                            break
                        if 'transer.com' in target_link:
                            detected_tool = "MC-Sop/MySite"
                            break

                        # ★リンク先に飛んでみる (札幌市パターン)
                        # redirect=Trueで飛ばされた先のURLを確認する
                        self.log(f"    → 追跡中: {target_link[:40]}...")
                        sub_res = requests.get(target_link, headers=headers, timeout=8, allow_redirects=True)
                        sub_res.encoding = sub_res.apparent_encoding

                        # 飛ばされた先のURLをチェック
                        final_url = sub_res.url.lower()
                        sub_src = sub_res.text.lower()

                        if 'j-server.com' in final_url:
                            detected_tool = "J-SERVER"
                            # 飛ばされた先のソースも見て言語チェック
                            _, sub_extra = self.analyze_source(sub_src, "")
                            extra_langs.update(sub_extra)
                            break
                        elif 'transer.com' in final_url:
                            detected_tool = "MC-Sop/MySite"
                            break
                        elif 'google' in final_url and 'translate' in final_url:
                            detected_tool = "Google翻訳サービス"
                            break

                        # 飛ばされた先でツールが埋め込まれているかチェック
                        sub_tool, sub_extra = self.analyze_source(sub_src, "")
                        if sub_tool:
                            detected_tool = sub_tool
                            extra_langs.update(sub_extra)
                            break

                    except Exception:
                        continue

            # --- 3. 最終判定とフラグ立て ---
            if detected_tool:
                result["tool_name"] = detected_tool
                result["has_translation"] = "有"

                # Googleなら全言語ON
                if detected_tool == "Google翻訳サービス":
                    for lang in ALL_LANG_COLUMNS: result["lang_flags"][lang] = 1

                # その他なら主要言語 + 発見した言語
                else:
                    targets = ["英語", "中国語（簡体字）", "中国語（繁体字）", "韓国語"]
                    for t in targets:
                        if t in result["lang_flags"]: result["lang_flags"][t] = 1
                    for l_name in extra_langs:
                        if l_name in result["lang_flags"]: result["lang_flags"][l_name] = 1

            # ツールは見つからないがEnglishリンクはあった場合
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
            if input_path.endswith('.csv'): df = pd.read_csv(input_path, encoding='cp932')
            else: df = pd.read_excel(input_path)

            pref_col = next((c for c in df.columns if "県名" in str(c)), None)
            city_col = next((c for c in df.columns if "自治体名" in str(c)), None)
            url_col  = next((c for c in df.columns if "公式サイト" in str(c) or "URL" in str(c)), None)

            if not (pref_col and city_col):
                self.gui_queue.put({"action": "error", "msg": "エラー: 列名が見つかりません"})
                return

            total = len(df)
            self.gui_queue.put({"action": "progress_max", "value": total})

            for i, row in df.iterrows():
                # 一時停止処理
                while self.is_paused:
                    if not self._paused_saved:
                        save_path_pause = os.path.splitext(input_path)[0] + "_一時停止データ.xlsx"
                        df.to_excel(save_path_pause, index=False)
                        self.log(f"💾 一時保存: {save_path_pause}")
                        self._paused_saved = True
                    time.sleep(0.5)
                self._paused_saved = False

                # メイン処理
                pref, city = row[pref_col], row[city_col]
                if pd.isna(pref) or pd.isna(city) or str(pref) == "nan":
                    self.gui_queue.put({"action": "progress_update", "value": i+1})
                    continue

                target_url = str(row[url_col]) if url_col else ""
                self.log(f"[{i+1}/{total}] {pref} {city}")

                if (pd.isna(target_url) or "http" not in target_url):
                    found = self.search_official_url(pref, city)
                    if found:
                        self.log(f"  → URL確保: {found}")
                        target_url = found
                        if url_col: df.at[i, url_col] = found
                    else:
                        self.log("  → URL不明")
                        self.gui_queue.put({"action": "progress_update", "value": i+1})
                        continue

                # ★ここでMark VIIの追跡ロジックが動く
                res = self.check_site_features(target_url)

                if "ふりがな機能" in df.columns: df.at[i, "ふりがな機能"] = res["furigana"]
                if "翻訳種類" in df.columns:    df.at[i, "翻訳種類"] = res["tool_name"]
                if "翻訳の有無" in df.columns:  df.at[i, "翻訳の有無"] = res["has_translation"]

                lang_count = 0
                for lang_name, flag in res["lang_flags"].items():
                    if lang_name in df.columns:
                        df.at[i, lang_name] = flag
                        if lang_name != "日本語" and flag == 1: lang_count += 1

                if "提供言語数" in df.columns: df.at[i, "提供言語数"] = lang_count

                time.sleep(1.0)
                self.gui_queue.put({"action": "progress_update", "value": i+1})

            save_path = os.path.splitext(input_path)[0] + "_解析完了.xlsx"
            df.to_excel(save_path, index=False)
            self.log(f"完了！ 保存先: {save_path}")

            self.gui_queue.put({"action": "finish", "title": "成功", "msg": "全ミッション完了！"})

        except Exception as e:
            self.log(f"エラー: {e}")
            self.gui_queue.put({"action": "error", "msg": str(e)})
        finally:
            self.is_running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = MunicipalityCheckerApp(root)
    root.mainloop()
