import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
from src.crowdworks_tool.logic import fetch_yahoo_ranking, random_sleep

class CrowdWorksToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CrowdWorks Ranking Helper")
        self.root.geometry("900x600")

        # Thread-safe communication
        self.msg_queue = queue.Queue()

        # --- Frames ---
        left_frame = ttk.Frame(root, padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(root, padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Left Side: Input ---
        ttk.Label(left_frame, text="Task Details / Keywords (Paste here)").pack(anchor=tk.W)
        self.input_text = scrolledtext.ScrolledText(left_frame, width=30, height=20)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Button(left_frame, text="Extract & Clean Keywords", command=self.extract_keywords).pack(fill=tk.X, pady=5)

        ttk.Label(left_frame, text="Keywords to Search:").pack(anchor=tk.W, pady=(10, 0))
        self.keywords_text = scrolledtext.ScrolledText(left_frame, width=30, height=10)
        self.keywords_text.pack(fill=tk.BOTH, expand=True, pady=5)

        self.run_btn = ttk.Button(left_frame, text="Run Search", command=self.start_search)
        self.run_btn.pack(fill=tk.X, pady=10)

        # --- Right Side: Output ---
        ttk.Label(right_frame, text="Results (URL)").pack(anchor=tk.W)
        self.output_text = scrolledtext.ScrolledText(right_frame, width=40, height=30)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Button(right_frame, text="Copy Results", command=self.copy_results).pack(fill=tk.X, pady=5)

        # --- Status ---
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)
        self.progress = ttk.Progressbar(root, mode='determinate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)

        self.is_running = False

        # Start queue polling
        self.process_queue()

    def process_queue(self):
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                msg_type = msg.get('type')

                if msg_type == 'status':
                    self.status_var.set(msg['text'])
                elif msg_type == 'result':
                    self.output_text.insert(tk.END, msg['text'] + "\n")
                    self.output_text.see(tk.END)
                elif msg_type == 'progress':
                    self.progress['value'] = msg['value']
                elif msg_type == 'max_progress':
                    self.progress['maximum'] = msg['value']
                elif msg_type == 'done':
                    self.is_running = False
                    self.run_btn.config(state=tk.NORMAL)
                    self.status_var.set("Completed.")
                    messagebox.showinfo("Done", "Search completed.")

        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def extract_keywords(self):
        raw_text = self.input_text.get("1.0", tk.END)
        lines = raw_text.split('\n')
        keywords = []

        # Simple heuristic to clean up the CrowdWorks dump
        skip_phrases = [
            "スマホ版YahooJapan", "作業内容", "依頼タイトル", "作業制限時間",
            "ご意見箱", "報酬", "契約一覧", "メッセージ", "相談から契約まで",
            "マイページ", "気になる！リスト", "クラウドワークス", "以下",
            "1文字以上", "注意", "該当がない場合", "当方のパソコン",
            "http", "https"
        ]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip lines containing system phrases
            if any(phrase in line for phrase in skip_phrases):
                continue

            # Skip lines that are too long (likely instructions)
            if len(line) > 50:
                continue

            keywords.append(line)

        self.keywords_text.delete("1.0", tk.END)
        self.keywords_text.insert(tk.END, "\n".join(keywords))
        self.status_var.set(f"Extracted {len(keywords)} keywords.")

    def start_search(self):
        if self.is_running:
            return

        raw_keywords = self.keywords_text.get("1.0", tk.END).strip()
        if not raw_keywords:
            messagebox.showwarning("Warning", "No keywords to search.")
            return

        keywords = [k.strip() for k in raw_keywords.split('\n') if k.strip()]
        if not keywords:
            return

        self.is_running = True
        self.run_btn.config(state=tk.DISABLED)
        self.output_text.delete("1.0", tk.END)

        # Reset Progress
        self.msg_queue.put({'type': 'max_progress', 'value': len(keywords)})
        self.msg_queue.put({'type': 'progress', 'value': 0})

        thread = threading.Thread(target=self.run_search_thread, args=(keywords,))
        thread.daemon = True
        thread.start()

    def run_search_thread(self, keywords):
        for i, keyword in enumerate(keywords):
            self.msg_queue.put({'type': 'status', 'text': f"Searching {i+1}/{len(keywords)}: {keyword}"})

            url = fetch_yahoo_ranking(keyword)
            result_line = f"{url}" if url else "Not Found"

            self.msg_queue.put({'type': 'result', 'text': result_line})
            self.msg_queue.put({'type': 'progress', 'value': i + 1})

            if i < len(keywords) - 1:
                random_sleep()

        self.msg_queue.put({'type': 'done'})

    def copy_results(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.output_text.get("1.0", tk.END))
        self.status_var.set("Copied to clipboard.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CrowdWorksToolApp(root)
    root.mainloop()
