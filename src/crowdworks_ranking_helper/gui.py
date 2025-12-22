import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
from .scraper import YahooRankingScraper

class RankingHelperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Yahoo Ranking Helper (CrowdWorks)")
        self.root.geometry("800x600")

        self.scraper = None
        self.is_running = False

        self._setup_ui()

    def _setup_ui(self):
        # PanedWindow to separate Input and Output
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left Frame: Input
        left_frame = tk.Frame(paned)
        paned.add(left_frame)

        tk.Label(left_frame, text="検索ワード (1行に1つ)").pack(anchor="w")
        self.input_text = scrolledtext.ScrolledText(left_frame, width=30, height=20)
        self.input_text.pack(fill=tk.BOTH, expand=True)

        # Right Frame: Output
        right_frame = tk.Frame(paned)
        paned.add(right_frame)

        tk.Label(right_frame, text="結果 (URL)").pack(anchor="w")
        self.output_text = scrolledtext.ScrolledText(right_frame, width=40, height=20)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Bottom Frame: Controls
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=5, pady=10)

        self.run_button = tk.Button(bottom_frame, text="実行開始", command=self.start_scraping, bg="green", fg="white")
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.copy_button = tk.Button(bottom_frame, text="結果をコピー", command=self.copy_results)
        self.copy_button.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(bottom_frame, text="待機中")
        self.status_label.pack(side=tk.RIGHT, padx=5)

    def start_scraping(self):
        if self.is_running:
            return

        keywords_raw = self.input_text.get("1.0", tk.END)
        keywords = [k.strip() for k in keywords_raw.splitlines() if k.strip()]

        if not keywords:
            self.status_label.config(text="ワードを入力してください")
            return

        self.is_running = True
        self.run_button.config(state=tk.DISABLED, text="実行中...")
        self.output_text.delete("1.0", tk.END)

        # Run in thread
        thread = threading.Thread(target=self._scraping_task, args=(keywords,))
        thread.daemon = True
        thread.start()

    def _scraping_task(self, keywords):
        try:
            self.scraper = YahooRankingScraper(headless=False) # GUI user sees browser

            for i, keyword in enumerate(keywords):
                self._update_status(f"検索中 ({i+1}/{len(keywords)}): {keyword}")

                result_url = self.scraper.get_3rd_organic_url(keyword)

                # Append result safely
                self.root.after(0, self._append_result, keyword, result_url)

            self._update_status("完了")

        except Exception as e:
            self._update_status(f"エラー: {str(e)}")
        finally:
            if self.scraper:
                self.scraper.close()
            self.is_running = False
            self.root.after(0, self._reset_button)

    def _append_result(self, keyword, url):
        self.output_text.insert(tk.END, f"{keyword} -> {url}\n")
        self.output_text.see(tk.END)

    def _update_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def _reset_button(self):
        self.run_button.config(state=tk.NORMAL, text="実行開始")

    def copy_results(self):
        results = self.output_text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(results)
        self.status_label.config(text="クリップボードにコピーしました")
