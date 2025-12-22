import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import pandas as pd
import queue
import time
from .scraper import YahooSearcher, KEYWORDS

class SearchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yahoo! JAPAN 検索順位チェッカー")
        self.geometry("800x600")

        # Configure grid weight
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Variables
        self.keywords = KEYWORDS
        self.results = []
        self.running = False
        self.searcher = None
        self.queue = queue.Queue()

        # UI Components
        self.create_widgets()

        # Start queue processor
        self.after(100, self.process_queue)

    def create_widgets(self):
        # Top Frame: Controls
        control_frame = ttk.Frame(self, padding=10)
        control_frame.grid(row=0, column=0, sticky="ew")

        self.btn_run = ttk.Button(control_frame, text="検索実行 (Run)", command=self.start_search)
        self.btn_run.pack(side="left", padx=5)

        self.btn_clear = ttk.Button(control_frame, text="クリア (Clear)", command=self.clear_results)
        self.btn_clear.pack(side="left", padx=5)

        self.btn_export = ttk.Button(control_frame, text="CSV出力 (Export)", command=self.export_csv)
        self.btn_export.pack(side="left", padx=5)

        # Progress Bar
        self.progress = ttk.Progressbar(control_frame, mode='determinate', length=300)
        self.progress.pack(side="right", padx=5)

        # Middle Frame: Results Table
        tree_frame = ttk.Frame(self, padding=10)
        tree_frame.grid(row=1, column=0, sticky="nsew")

        columns = ("ID", "Keyword", "URL", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        self.tree.heading("ID", text="番号")
        self.tree.column("ID", width=50, anchor="center")

        self.tree.heading("Keyword", text="キーワード")
        self.tree.column("Keyword", width=300)

        self.tree.heading("URL", text="結果 URL")
        self.tree.column("URL", width=300)

        self.tree.heading("Status", text="ステータス")
        self.tree.column("Status", width=100, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Initial Load of Keywords
        self.load_keywords_into_tree()

        # Bottom Frame: Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了 (Ready)")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.grid(row=2, column=0, sticky="ew")

    def load_keywords_into_tree(self):
        self.tree.delete(*self.tree.get_children())
        for idx, kw in enumerate(self.keywords, 1):
            self.tree.insert("", "end", iid=str(idx), values=(idx, kw, "", "待機中"))

    def start_search(self):
        if self.running:
            return

        self.running = True
        self.btn_run.configure(state="disabled")
        self.btn_clear.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.keywords)

        # Start thread
        threading.Thread(target=self.run_search_thread, daemon=True).start()

    def run_search_thread(self):
        try:
            self.queue.put(("status", "ブラウザを起動中..."))
            self.searcher = YahooSearcher(headless=False) # GUI users likely want to see it
            self.searcher.setup_driver()

            for idx, kw in enumerate(self.keywords, 1):
                if not self.running: # Check if cancelled (not implemented but good practice)
                    break

                self.queue.put(("update_status", (str(idx), "検索中...")))
                self.queue.put(("status", f"検索中 ({idx}/{len(self.keywords)}): {kw}"))

                url = self.searcher.search_keyword(kw)

                self.queue.put(("update_result", (str(idx), url)))
                self.queue.put(("progress", idx))

                # Small delay between tasks already handled in scraper, but we can add UI delay if needed

            self.queue.put(("status", "完了しました"))
            self.queue.put(("finish", None))

        except Exception as e:
            self.queue.put(("error", str(e)))
        finally:
            if self.searcher:
                self.searcher.close()

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()

                if msg_type == "update_status":
                    item_id, status = data
                    current_values = self.tree.item(item_id)["values"]
                    # (ID, Keyword, URL, Status)
                    self.tree.item(item_id, values=(current_values[0], current_values[1], current_values[2], status))

                elif msg_type == "update_result":
                    item_id, url = data
                    current_values = self.tree.item(item_id)["values"]
                    self.tree.item(item_id, values=(current_values[0], current_values[1], url, "完了"))
                    # Update local result storage
                    self.results.append({"番号": current_values[0], "キーワード": current_values[1], "URL": url})

                elif msg_type == "progress":
                    self.progress["value"] = data

                elif msg_type == "status":
                    self.status_var.set(data)

                elif msg_type == "error":
                    messagebox.showerror("エラー", data)
                    self.cleanup_search()

                elif msg_type == "finish":
                    messagebox.showinfo("完了", "すべての検索が完了しました。")
                    self.cleanup_search()

                self.queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def cleanup_search(self):
        self.running = False
        self.btn_run.configure(state="normal")
        self.btn_clear.configure(state="normal")
        self.btn_export.configure(state="normal")

    def clear_results(self):
        self.results = []
        self.load_keywords_into_tree()
        self.status_var.set("準備完了")
        self.progress["value"] = 0

    def export_csv(self):
        if not self.results:
            messagebox.showwarning("警告", "データがありません。先に検索を実行してください。")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="CSVとして保存"
        )
        if file_path:
            try:
                df = pd.DataFrame(self.results)
                df.to_csv(file_path, index=False, encoding='utf-8-sig') # utf-8-sig for Excel compatibility
                messagebox.showinfo("成功", f"ファイルを保存しました: {file_path}")
            except Exception as e:
                messagebox.showerror("エラー", f"保存中にエラーが発生しました: {e}")

if __name__ == "__main__":
    app = SearchApp()
    app.mainloop()
