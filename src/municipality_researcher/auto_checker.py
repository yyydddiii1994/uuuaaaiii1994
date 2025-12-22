import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import requests
from bs4 import BeautifulSoup
import threading
import time
import os
import random
import urllib.parse

class MunicipalityCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自治体サイト完全攻略ツール Mark-III (自動検索機能搭載)")
        self.root.geometry("1000x700")

        # デザイン設定
        style = ttk.Style()
        style.theme_use('clam')

        self.file_path = tk.StringVar()
        self.is_running = False

        # 言語定義 (カラム名: [検索キーワードリスト])
        self.LANG_MAP = {
            "日本語": ["Japanese", "日本語"],
            "やさしい日本語": ["Easy Japanese", "やさしい日本語", "易しい日本語"],
            "英語": ["English", "英語"],
            "中国語（簡体字）": ["简体中文", "Simplified Chinese", "zh-cn"],
            "中国語（繁体字）": ["繁體中文", "Traditional Chinese", "zh-tw"],
            "韓国語": ["한국어", "Korean", "ko-kr"],
            "アイスランド語": ["Íslenskur", "Icelandic"],
            "アイマラ語": ["Aymara"],
            "アイルランド語": ["Gaeilge", "Irish"],
            "アゼルバイジャン語": ["Azərbaycan", "Azerbaijani"],
            "アッサム語": ["অসমীয়া", "Assamese"],
            "アファン・オロモ語": ["Afaan Oromoo", "Oromo"],
            "アフリカーンス語": ["Afrikaans"],
            "アムハラ語": ["አማርኛ", "Amharic"],
            "アラビア語": ["عربي", "Arabic"],
            "アルバニア語": ["Shqip", "Albanian"],
            "アルメニア語": ["Հայերեն", "Armenian"],
            "イタリア語": ["Italiano", "Italian"],
            "イディッシュ語": ["יידיש", "Yiddish"],
            "イヌクティトゥット語": ["ᐃᓄᒃᑎᑐᑦ", "Inuktitut"],
            "イボ語": ["asụsụ Igbo", "Igbo"],
            "イロカノ語": ["Ilocano"],
            "インドネシア語": ["Indonesia", "Indonesian"],
            "ウイグル語": ["ئۇيغۇرچە", "Uyghur"],
            "ウェールズ語": ["Cymraeg", "Welsh"],
            "ウクライナ語": ["Український", "Ukrainian"],
            "ウズベク語": ["Oʻzbek", "Uzbek"],
            "ウルドゥー語": ["اردو", "Urdu"],
            "エウェ語": ["Eʋegbe", "Ewe"],
            "エストニア語": ["Eesti", "Estonian"],
            "エスペラント語": ["Esperanto"],
            "オディア語": ["ଓଡିଆ", "Odia"],
            "オトミ語": ["Hñähñu", "Otomi"],
            "オランダ語": ["Nederlands", "Dutch"],
            "カザフ語": ["Қазақ тілі", "Kazakh"],
            "カタロニア語": ["Català", "Catalan"],
            "ガリシア語": ["Galego", "Galician"],
            "ガンダ語": ["Ganda", "Luganda"],
            "カンナダ語": ["ಕನ್ನಡ", "Kannada"],
            "キニアルワンダ語": ["Kinyarwanda"],
            "ギリシャ語": ["Ελληνικά", "Greek"],
            "キルギス語": ["Кыргызча", "Kyrgyz"],
            "グジャラート語": ["ગુજરાતી", "Gujarati"],
            "クメール語": ["ខ្មែរ", "Khmer"],
            "クルド語": ["Kurdî", "Kurdish"],
            "クロアチア語": ["Hrvatski", "Croatian"],
            "コーサ語": ["Xhosa"],
            "コルシカ語": ["Corsu", "Corsican"],
            "サモア語": ["Samoa", "Samoan"],
            "ジャワ語": ["Basa Jawa", "Javanese"],
            "ジョージア語": ["ქართული", "Georgian"],
            "ショナ語": ["Shona"],
            "シンディ語": ["سنڌي", "Sindhi"],
            "シンハラ語": ["සිංහල", "Sinhala"],
            "スウェーデン語": ["Svenska", "Swedish"],
            "ズールー語": ["Zulu"],
            "スコットランド・ゲール語": ["Gàidhlig na h-Alba", "Scottish Gaelic"],
            "スペイン語": ["Español", "Spanish"],
            "スロバキア語": ["Slovenčina", "Slovak"],
            "スロベニア語": ["Slovenščina", "Slovenian"],
            "スワヒリ語": ["Kiswahili", "Swahili"],
            "スンダ語": ["Basa Sunda", "Sundanese"],
            "セブアノ語": ["Cebuano"],
            "セルビア語": ["Српски", "Serbian"],
            "ソト語": ["Sotho"],
            "ソマリ語": ["Soomaali", "Somali"],
            "タイ語": ["ภาษาไทย", "Thai"],
            "タジク語": ["тоҷикӣ", "Tajik"],
            "タタール語": ["Татар", "Tatar"],
            "タヒチ語": ["Reo Tahiti", "Tahitian"],
            "タミル語": ["தமிழ்", "Tamil"],
            "ダリ―語": ["دری", "Dari"],
            "チェコ語": ["Čeština", "Czech"],
            "チェワ語": ["Chewa", "Nyanja"],
            "チベット語": ["བོད་སྐད་", "Tibetan"],
            "ティグリニャ語": ["ትግር", "Tigrinya"],
            "ディベヒ語": ["ދިވެހިބަސް", "Dhivehi"],
            "テルグ語": ["తెలుగు", "Telugu"],
            "デンマーク語": ["Dansk", "Danish"],
            "ドイツ語": ["Deutsche", "German"],
            "トウィ語（アカン語）": ["Twi", "Akan"],
            "トルクメン語": ["Türkmençe", "Turkmen"],
            "トルコ語": ["Türkçe", "Turkish"],
            "トンガ語": ["Lea Fakatonga", "Tongan"],
            "ネパール語": ["नेपाली", "Nepali"],
            "ノルウェー語": ["Norsk", "Norwegian"],
            "ハイチ語": ["Ayisyen", "Haitian Creole"],
            "ハウサ語": ["Hausa"],
            "バシキール語": ["Bashkir"],
            "パシュト―語": ["پښتو", "Pashto"],
            "バスク語": ["Euskara", "Basque"],
            "ハワイ語": ["ʻŌlelo Hawaiʻi", "Hawaiian"],
            "ハンガリー語": ["Magyar", "Hungarian"],
            "パンジャブ語": ["ਪੰਜਾਬੀ", "Punjabi"],
            "バンバラ語": ["Bamanankan", "Bambara"],
            "ヒンディー語": ["हिन्दी", "Hindi"],
            "フィジー語": ["Na Vosa Vakaviti", "Fijian"],
            "フィリピノ語": ["Filipino", "Tagalog"],
            "フィンランド語": ["Suomi", "Finnish"],
            "フランス語": ["Français", "French"],
            "フリジア語": ["Frysk", "Frisian"],
            "ブルガリア語": ["Български", "Bulgarian"],
            "ベトナム語": ["Tiếng Việt", "Vietnamese"],
            "ヘブライ語": ["עברית", "Hebrew"],
            "ベラルーシ語": ["беларуская", "Belarusian"],
            "ペルシア語": ["فارسی", "Persian"],
            "ベンガル語": ["বাংলা", "Bengali"],
            "ボージュプリー語": ["भोजपुरी", "Bhojpuri"],
            "ポーランド語": ["Język polski", "Polish"],
            "ボスニア語": ["Bosanski", "Bosnian"],
            "ポルトガル語": ["Português", "Portuguese"],
            "マイティリー語": ["मैथिली", "Maithili"],
            "マオリ語": ["Māori", "Maori"],
            "マケドニア語": ["македонски", "Macedonian"],
            "マダガスカル語": ["Malagasy"],
            "マラーティー語": ["मराठी", "Marathi"],
            "マラヤーラム語": ["മലയാളം", "Malayalam"],
            "マルタ語": ["Malti", "Maltese"],
            "マレー語": ["Melayu", "Malay"],
            "ミャンマー語": ["မြန်မာဘာသာစကား", "Myanmar", "Burmese"],
            "モン語": ["Hmong", "Mon"],
            "モンゴル語": ["Монгол", "Mongolian"],
            "ユカテクマヤ語": ["Yucatec Maya"],
            "ヨルバ語": ["Yoruba"],
            "ラオ語": ["ພາສາລາວ", "Lao"],
            "ラトビア語": ["Latviešu", "Latvian"],
            "リトアニア語": ["Lietuvių", "Lithuanian"],
            "リンガラ語": ["Lingala"],
            "ルーマニア語": ["Română", "Romanian"],
            "ルクセンブルク語": ["Lëtzebuergesch", "Luxembourgish"],
            "ロシア語": ["Русский", "Russian"]
        }

        self.create_widgets()

    def create_widgets(self):
        # --- 1. ファイル選択 ---
        frame_top = ttk.LabelFrame(self.root, text="1. 作業用ファイルを選択 (Excel/CSV)", padding=10)
        frame_top.pack(fill="x", padx=10, pady=5)

        entry = ttk.Entry(frame_top, textvariable=self.file_path, width=60)
        entry.pack(side="left", padx=5)

        btn_browse = ttk.Button(frame_top, text="参照...", command=self.browse_file)
        btn_browse.pack(side="left")

        # --- 2. 実行エリア ---
        frame_action = ttk.Frame(self.root, padding=10)
        frame_action.pack(fill="x", padx=10)

        self.btn_run = ttk.Button(frame_action, text="全自動解析スタート (Go)", command=self.start_thread, width=30)
        self.btn_run.pack(side="left", padx=5)

        lbl_hint = ttk.Label(frame_action, text="※URLが空欄の場合、自動で検索して埋めます（少し時間がかかります）", foreground="red")
        lbl_hint.pack(side="left", padx=10)

        # --- 3. ログエリア ---
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

    def start_thread(self):
        if not self.file_path.get():
            messagebox.showwarning("エラー", "ファイルを選んでください")
            return
        self.is_running = True
        self.btn_run.configure(state='disabled')
        threading.Thread(target=self.run_process, daemon=True).start()

    def search_official_url(self, pref, city):
        """自治体名で検索してトップのURLを返す関数（DuckDuckGo使用）"""
        query = f"{pref} {city} 公式ホームページ"
        self.log(f"  🔍 検索中: {query} ...")

        url = "https://html.duckduckgo.com/html/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}
        payload = {'q': query}

        try:
            time.sleep(random.uniform(2.0, 4.0))
            res = requests.post(url, data=payload, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')

            first_link = soup.find('a', class_='result__a')
            if first_link:
                found_url = first_link.get('href')
                if "uddg=" in found_url:
                    parsed = urllib.parse.urlparse(found_url)
                    qs = urllib.parse.parse_qs(parsed.query)
                    if 'uddg' in qs:
                        return qs['uddg'][0]
                return found_url
            else:
                return None
        except Exception as e:
            self.log(f"  ❌ 検索エラー: {e}")
            return None

    def check_site_features(self, url):
        """URLの中身を解析して詳細な言語対応状況を判定する"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        result = {
            "furigana": "無",
            "tool_name": "不明(要確認)",
            "has_translation": "無",
            "langs": {lang: 0 for lang in self.LANG_MAP} # 全言語を0で初期化
        }

        # 日本語はデフォルトで1
        result["langs"]["日本語"] = 1

        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            src = str(soup).lower()
            text_content = soup.get_text().lower()

            # 1. ふりがな判定
            if soup.find('ruby') or 'ふりがな' in text_content or 'ruby.js' in src or 'furigana' in src:
                result["furigana"] = "有"

            # 2. 翻訳ツール判定 & 言語フラグ設定
            is_google = False

            if 'goog-te-combo' in src or 'google_translate' in src:
                result["tool_name"] = "Google翻訳サービス"
                result["has_translation"] = "有"
                is_google = True

            elif 'j-server.com' in src or 'j-server' in src:
                result["tool_name"] = "J-SERVER"
                result["has_translation"] = "有"
                # J-Serverは基本4言語+αだが、ここでは検出ロジックに任せるか、主要言語をONにする
                # とりあえずキーワード検索に任せる

            elif 'wovn' in src:
                result["tool_name"] = "Wovn.io"
                result["has_translation"] = "有"

            elif 'crosslanguage' in src or 'mysite-is' in src:
                result["tool_name"] = "MC-Sop/MySite"
                result["has_translation"] = "有"

            elif 'english' in text_content or 'foreign' in src:
                if result["tool_name"] == "不明(要確認)":
                    result["tool_name"] = "独自リンク(要確認)"
                    result["has_translation"] = "有"

            # 3. 言語別チェック
            if is_google:
                # Google翻訳の場合、やさしい日本語以外の外国語はほぼ全て対応とみなす
                for lang in result["langs"]:
                    if lang != "日本語" and lang != "やさしい日本語":
                        result["langs"][lang] = 1

                # やさしい日本語だけは個別にチェック
                if "やさしい日本語" in text_content or "easy japanese" in src:
                    result["langs"]["やさしい日本語"] = 1

            else:
                # その他のツール or 独自リンクの場合、キーワード検索
                for lang, keywords in self.LANG_MAP.items():
                    if lang == "日本語": continue

                    # HTMLソース全体からキーワードを探す
                    # (精度を高めるなら text_content だけにする手もあるが、altタグ等も考慮しsrcで)
                    for kw in keywords:
                        if kw.lower() in src:
                            result["langs"][lang] = 1
                            break

        except Exception as e:
            result["tool_name"] = "アクセスエラー"

        return result

    def run_process(self):
        input_path = self.file_path.get()
        self.log("--- 全自動処理プロセスを開始 ---")

        try:
            if input_path.endswith('.csv'):
                try:
                    df = pd.read_csv(input_path, encoding='cp932')
                except UnicodeDecodeError:
                    self.log("  ⚠️ CP932での読み込みに失敗、UTF-8で試行します...")
                    df = pd.read_csv(input_path, encoding='utf-8')
            else:
                df = pd.read_excel(input_path)

            # 列名の確認と作成
            pref_col = next((c for c in df.columns if "県名" in str(c)), None)
            city_col = next((c for c in df.columns if "自治体名" in str(c)), None)
            url_col  = next((c for c in df.columns if "公式サイト" in str(c) or "URL" in str(c)), None)

            if not (pref_col and city_col and url_col):
                self.log("エラー: 必須列（県名、自治体名、公式サイト）が見つかりません。")
                self.btn_run.configure(state='normal')
                return

            # 不足している言語カラムを追加
            for lang in self.LANG_MAP:
                if lang not in df.columns:
                    df[lang] = 0

            # メタデータカラムも確認
            meta_cols = ["ふりがな機能", "翻訳種類", "翻訳の有無", "提供言語数"]
            for mc in meta_cols:
                if mc not in df.columns:
                    df[mc] = ""

            total = len(df)
            self.progress["maximum"] = total

            for i, row in df.iterrows():
                if not self.is_running:
                    self.log("--- 中断されました ---")
                    break

                target_url = str(row[url_col])
                pref = str(row[pref_col])
                city = str(row[city_col])

                self.log(f"[{i+1}/{total}] ターゲット: {pref} {city}")

                # --- Step 1: URL取得 ---
                if pd.isna(row[url_col]) or target_url == "nan" or "http" not in target_url:
                    found_url = self.search_official_url(pref, city)
                    if found_url:
                        self.log(f"  → URL発見: {found_url}")
                        target_url = found_url
                        df.at[i, url_col] = found_url
                    else:
                        self.log("  → ❌ URLが見つかりませんでした")
                        self.progress["value"] = i+1
                        continue

                # --- Step 2: サイト解析 ---
                res = self.check_site_features(target_url)

                # 基本情報書き込み
                df.at[i, "ふりがな機能"] = res["furigana"]
                df.at[i, "翻訳種類"] = res["tool_name"]
                df.at[i, "翻訳の有無"] = res["has_translation"]

                # 言語フラグ書き込み & カウント
                lang_count = 0
                for lang, is_supported in res["langs"].items():
                    df.at[i, lang] = is_supported
                    if is_supported == 1:
                        lang_count += 1

                df.at[i, "提供言語数"] = lang_count

                # 中間保存
                if i % 5 == 0:
                    save_path = os.path.splitext(input_path)[0] + "_途中経過.xlsx"
                    df.to_excel(save_path, index=False)

                self.progress["value"] = i+1
                self.root.update_idletasks()

                time.sleep(1.0)

            # 最終保存
            final_save_path = os.path.splitext(input_path)[0] + "_解析完了.xlsx"
            df.to_excel(final_save_path, index=False)

            self.log(f"--- 全ミッション完了 ---")
            messagebox.showinfo("成功", f"完了しました！\n{final_save_path} を確認してください。")

        except Exception as e:
            self.log(f"エラー発生: {e}")
            messagebox.showerror("エラー", str(e))
        finally:
            self.is_running = False
            self.btn_run.configure(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = MunicipalityCheckerApp(root)
    root.mainloop()
