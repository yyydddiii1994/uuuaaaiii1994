import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
import os
import sys

# Add the parent directory to sys.path to allow importing scraper_logic if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper_logic import GoogleSearchScraper

class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Search Scraper Tool")
        self.root.geometry("600x700")

        # Variables
        self.max_results_var = tk.StringVar(value="20")
        self.output_dir_var = tk.StringVar(value=os.getcwd())
        self.headless_var = tk.BooleanVar(value=False)
        self.debug_mode_var = tk.BooleanVar(value=False)
        self.is_running = False

        # Queue for logging
        self.log_queue = queue.Queue()

        self._create_widgets()
        self._process_logs()

    def _create_widgets(self):
        # Settings Frame
        settings_frame = ttk.LabelFrame(self.root, text="設定", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Output Directory
        ttk.Label(settings_frame, text="出力フォルダ:").grid(row=0, column=0, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.output_dir_var, width=40).grid(row=0, column=1, padx=5)
        ttk.Button(settings_frame, text="参照", command=self._browse_dir).grid(row=0, column=2)

        # Max Results
        ttk.Label(settings_frame, text="取得件数(最大):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(settings_frame, textvariable=self.max_results_var, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Headless Mode
        ttk.Checkbutton(settings_frame, text="Headlessモード (ブラウザ非表示)", variable=self.headless_var).grid(row=2, column=0, columnspan=2, sticky="w")

        # Debug Mode
        ttk.Checkbutton(settings_frame, text="詳細デバッグモード (HTML保存など)", variable=self.debug_mode_var).grid(row=2, column=2, sticky="w")

        # Keywords Frame
        keywords_frame = ttk.LabelFrame(self.root, text="検索キーワード (1行に1つ)", padding=10)
        keywords_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.keywords_text = tk.Text(keywords_frame, height=10)
        self.keywords_text.pack(fill="both", expand=True)

        # Buttons Frame
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x")

        self.start_btn = ttk.Button(btn_frame, text="開始", command=self._start_scraping)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self._stop_scraping, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="実行ログ", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, state="disabled", height=10)
        self.log_area.pack(fill="both", expand=True)

    def _browse_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)

    def _log(self, message):
        self.log_queue.put(message)

    def _process_logs(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_area.config(state="normal")
            self.log_area.insert("end", msg + "\n")
            self.log_area.see("end")
            self.log_area.config(state="disabled")

        self.root.after(100, self._process_logs)

    def _start_scraping(self):
        keywords_raw = self.keywords_text.get("1.0", "end").strip()
        if not keywords_raw:
            messagebox.showwarning("入力エラー", "キーワードを入力してください。")
            return

        keywords = [k.strip() for k in keywords_raw.split("\n") if k.strip()]

        try:
            max_results = int(self.max_results_var.get())
        except ValueError:
            messagebox.showerror("入力エラー", "取得件数は数値を入力してください。")
            return

        output_dir = self.output_dir_var.get()

        self.is_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.keywords_text.config(state="disabled")

        self.stop_event = threading.Event()
        self.scraper = GoogleSearchScraper(logger_callback=self._log, stop_event=self.stop_event)

        self.thread = threading.Thread(
            target=self._run_thread,
            args=(keywords, max_results, output_dir, self.headless_var.get(), self.debug_mode_var.get())
        )
        self.thread.start()

    def _run_thread(self, keywords, max_results, output_dir, headless, debug_mode):
        try:
            self.scraper.run(keywords, max_results, output_dir, headless, debug_mode=debug_mode)
        except Exception as e:
            self._log(f"重大なエラー: {e}")
        finally:
            self.root.after(0, self._on_finished)

    def _stop_scraping(self):
        if self.is_running:
            self._log("停止リクエスト送信中...")
            self.stop_event.set()
            self.stop_btn.config(state="disabled")

    def _on_finished(self):
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.keywords_text.config(state="normal")
        self._log("処理が終了しました。")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()
