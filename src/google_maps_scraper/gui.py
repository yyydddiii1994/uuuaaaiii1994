import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import json
import os
import time
from .data_manager import DataManager
from .scraper_core import MapScraper

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Maps Scraper - Safety First Edition")
        self.root.geometry("600x700")

        # Config読み込み
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.load_config()
        self.data_manager = DataManager(self.config)
        self.scraper = None
        self.is_running = False
        self.is_paused = False

        self.setup_ui()

    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)

    def setup_ui(self):
        # スタイル設定
        style = ttk.Style()
        style.configure("TButton", font=("Meiryo", 10))
        style.configure("TLabel", font=("Meiryo", 10))

        # --- ファイル選択エリア ---
        frame_file = ttk.LabelFrame(self.root, text="入力ファイル (Keywords)", padding=10)
        frame_file.pack(fill="x", padx=10, pady=5)

        self.filepath_var = tk.StringVar()
        ttk.Entry(frame_file, textvariable=self.filepath_var, width=50).pack(side="left", padx=5)
        ttk.Button(frame_file, text="参照", command=self.browse_file).pack(side="left")

        # --- 設定エリア ---
        frame_settings = ttk.LabelFrame(self.root, text="安全設定", padding=10)
        frame_settings.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_settings, text="最小遅延(秒):").grid(row=0, column=0, padx=5)
        self.min_delay_var = tk.IntVar(value=self.config.get('min_delay', 8))
        ttk.Spinbox(frame_settings, from_=5, to=60, textvariable=self.min_delay_var, width=5).grid(row=0, column=1)

        ttk.Label(frame_settings, text="最大遅延(秒):").grid(row=0, column=2, padx=5)
        self.max_delay_var = tk.IntVar(value=self.config.get('max_delay', 15))
        ttk.Spinbox(frame_settings, from_=10, to=120, textvariable=self.max_delay_var, width=5).grid(row=0, column=3)

        ttk.Label(frame_settings, text="1日上限(件):").grid(row=0, column=4, padx=5)
        self.limit_var = tk.IntVar(value=self.config.get('max_items_per_day', 1000))
        ttk.Entry(frame_settings, textvariable=self.limit_var, width=8).grid(row=0, column=5)

        # --- 進捗エリア ---
        frame_progress = ttk.Frame(self.root, padding=10)
        frame_progress.pack(fill="x", padx=10)

        self.status_var = tk.StringVar(value="待機中")
        ttk.Label(frame_progress, textvariable=self.status_var, foreground="blue").pack(anchor="w")

        self.progress = ttk.Progressbar(frame_progress, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=5)

        # --- コントロールボタン ---
        frame_controls = ttk.Frame(self.root, padding=10)
        frame_controls.pack(fill="x", padx=10)

        self.btn_start = ttk.Button(frame_controls, text="開始 (Start)", command=self.start_scraping)
        self.btn_start.pack(side="left", padx=5)

        self.btn_pause = ttk.Button(frame_controls, text="一時停止 (Pause)", command=self.toggle_pause, state="disabled")
        self.btn_pause.pack(side="left", padx=5)

        self.btn_stop = ttk.Button(frame_controls, text="停止 (Stop)", command=self.stop_scraping, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        # --- ログ表示 ---
        frame_log = ttk.LabelFrame(self.root, text="実行ログ", padding=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = tk.Text(frame_log, height=15, state="disabled", font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(frame_log, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def browse_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text/CSV", "*.txt *.csv")])
        if filepath:
            self.filepath_var.set(filepath)

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def check_pause_status(self):
        """スクレイパーから呼び出される。一時停止中ならTrueを返すーループ待機用"""
        return self.is_paused

    def toggle_pause(self):
        if self.is_paused:
            self.is_paused = False
            self.btn_pause.config(text="一時停止 (Pause)")
            self.status_var.set("稼働中...")
            self.log("▶ 再開しました")
        else:
            self.is_paused = True
            self.btn_pause.config(text="再開 (Resume)")
            self.status_var.set("一時停止中 (CAPTCHA対応など行ってください)")
            self.log("⏸ 一時停止しました。手動操作可能です。")

    def start_scraping(self):
        filepath = self.filepath_var.get()
        if not filepath or not os.path.exists(filepath):
            messagebox.showerror("エラー", "有効なファイルを選択してください。")
            return

        # Config更新
        self.config['min_delay'] = self.min_delay_var.get()
        self.config['max_delay'] = self.max_delay_var.get()
        self.config['max_items_per_day'] = self.limit_var.get()

        keywords = self.data_manager.read_keywords(filepath)
        if not keywords:
            messagebox.showwarning("警告", "キーワードが見つかりません。")
            return

        self.is_running = True
        self.is_paused = False
        self.btn_start.config(state="disabled")
        self.btn_pause.config(state="normal", text="一時停止 (Pause)")
        self.btn_stop.config(state="normal")
        self.progress['maximum'] = len(keywords)
        self.progress['value'] = 0

        # スレッド起動
        thread = threading.Thread(target=self.run_scraping_thread, args=(keywords,))
        thread.daemon = True
        thread.start()

    def stop_scraping(self):
        if self.scraper:
            self.scraper.stop()
            self.is_running = False
            self.log("🛑 停止処理中...")
            self.status_var.set("停止処理中...")
            self.btn_stop.config(state="disabled")
            self.btn_pause.config(state="disabled")

    def run_scraping_thread(self, keywords):
        self.log("🚀 スクレイピングを開始します...")
        self.scraper = MapScraper(
            self.config,
            update_log_callback=self.log_from_thread,
            check_pause_callback=self.check_pause_status
        )

        try:
            self.scraper.start_browser()

            all_results = []

            # resume機能: 既に終わったキーワードはスキップ
            progress_data = self.data_manager.load_progress()
            processed_set = set(progress_data.get("processed_keywords", []))

            for i, keyword in enumerate(keywords):
                if not self.is_running: break

                # 一時停止ループ
                while self.is_paused:
                    time.sleep(1)

                if keyword in processed_set:
                    self.log_from_thread(f"⏭ スキップ (完了済み): {keyword}")
                    self.update_progress(i + 1)
                    continue

                self.log_from_thread(f"--- キーワード処理開始: {keyword} ---")
                results = self.scraper.scrape_keyword(keyword)

                if results:
                    all_results.extend(results)
                    # 都度保存 (データロス防止)
                    self.data_manager.save_results(all_results)

                processed_set.add(keyword)
                self.data_manager.save_progress(list(processed_set))
                self.update_progress(i + 1)

            # 最終保存
            if all_results:
                filename = self.data_manager.save_results(all_results)
                self.log_from_thread(f"💾 最終保存完了: {filename}")
            else:
                self.log_from_thread("⚠ 保存するデータがありませんでした。")

        except Exception as e:
            self.log_from_thread(f"❌ 致命的なエラー: {e}")
        finally:
            self.scraper.close_browser()
            self.finish_scraping()

    def log_from_thread(self, message):
        self.root.after(0, self.log, message)

    def update_progress(self, value):
        self.root.after(0, lambda: self.progress.configure(value=value))

    def finish_scraping(self):
        self.is_running = False
        self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.btn_start.config(state="normal")
        self.btn_pause.config(state="disabled")
        self.btn_stop.config(state="disabled")
        self.status_var.set("完了 (または停止)")
        messagebox.showinfo("完了", "処理が終了しました。ログを確認してください。")
