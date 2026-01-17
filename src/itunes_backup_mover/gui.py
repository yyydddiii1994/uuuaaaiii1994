import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import threading
import queue
import os

class AppGui:
    def __init__(self, root, logic_manager):
        self.root = root
        self.logic = logic_manager
        self.root.title("iTunesバックアップ保存先変更ツール")
        self.root.geometry("600x580")
        self.root.resizable(False, False)

        # Thread-safe logging queue
        self.log_queue = queue.Queue()

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", font=("Meiryo UI", 10), padding=5)
        self.style.configure("TLabel", font=("Meiryo UI", 10))
        self.style.configure("Header.TLabel", font=("Meiryo UI", 12, "bold"))

        self.create_widgets()
        self.check_initial_state()

        # Start checking the queue
        self.process_log_queue()

    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)

        lbl_title = ttk.Label(header_frame, text="iTunesバックアップ保存先 簡単変更ツール", style="Header.TLabel")
        lbl_title.pack(anchor=tk.CENTER)

        lbl_desc = ttk.Label(header_frame, text="Cドライブの容量不足を解消しましょう。\n安全にバックアップ先を別のドライブ等のフォルダへ移動します。", justify=tk.CENTER)
        lbl_desc.pack(anchor=tk.CENTER, pady=5)

        # Current Path Section
        current_frame = ttk.LabelFrame(self.root, text="現在のバックアップ場所 (自動検出)", padding="10")
        current_frame.pack(fill=tk.X, padx=10, pady=5)

        self.var_current_path = tk.StringVar(value="検出中...")
        lbl_current = ttk.Label(current_frame, textvariable=self.var_current_path, wraplength=560)
        lbl_current.pack(fill=tk.X)

        # Link Status Label
        self.var_link_status = tk.StringVar(value="")
        lbl_link_status = ttk.Label(current_frame, textvariable=self.var_link_status, foreground="blue", wraplength=560)
        lbl_link_status.pack(fill=tk.X, pady=(5, 0))

        # New Path Section
        new_frame = ttk.LabelFrame(self.root, text="新しい保存先 (移動先)", padding="10")
        new_frame.pack(fill=tk.X, padx=10, pady=5)

        input_frame = ttk.Frame(new_frame)
        input_frame.pack(fill=tk.X)

        self.var_new_path = tk.StringVar()
        self.entry_new = ttk.Entry(input_frame, textvariable=self.var_new_path)
        self.entry_new.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.btn_browse = ttk.Button(input_frame, text="参照...", command=self.browse_folder)
        self.btn_browse.pack(side=tk.RIGHT)

        lbl_help = ttk.Label(new_frame, text="※選択したフォルダの中に「Backup」フォルダが作成されます。", font=("Meiryo UI", 9), foreground="gray")
        lbl_help.pack(anchor=tk.W, pady=(5,0))

        # Log Section
        log_frame = ttk.LabelFrame(self.root, text="実行ログ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.txt_log = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9), state='disabled')
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        # Copy Log Button (Small) inside Log Frame? Or below?
        # Let's put it at the bottom inside Action Section or just below log frame.
        # Below log frame seems cleaner.

        # Action Section
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # "Copy Log" button on the left of action frame
        self.btn_copy_log = ttk.Button(action_frame, text="ログをコピー", command=self.copy_log_to_clipboard, width=15)
        self.btn_copy_log.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_execute = ttk.Button(action_frame, text="変更を実行する (一発完了)", command=self.start_execution)
        self.btn_execute.pack(fill=tk.X, ipady=5)

    def log(self, message):
        """Put message into the queue (thread-safe)"""
        self.log_queue.put(message)

    def process_log_queue(self):
        """Check queue and update GUI in the main thread"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.txt_log.config(state='normal')
                self.txt_log.insert(tk.END, msg + "\n")
                self.txt_log.see(tk.END)
                self.txt_log.config(state='disabled')
        except queue.Empty:
            pass
        # Schedule next check
        self.root.after(100, self.process_log_queue)

    def copy_log_to_clipboard(self):
        """Copies the entire log content to clipboard."""
        try:
            log_content = self.txt_log.get("1.0", tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            messagebox.showinfo("コピー完了", "ログの内容をクリップボードにコピーしました。")
        except Exception as e:
            messagebox.showerror("エラー", f"コピーに失敗しました: {e}")

    def check_initial_state(self):
        try:
            path = self.logic.find_current_backup_folder()
            if path:
                self.var_current_path.set(path)
                self.log(f"現在のバックアップフォルダを検出しました:\n{path}")

                # Check if it's already a link
                if self.logic._is_reparse_point(self.logic.found_path):
                     target = self.logic.get_link_target(self.logic.found_path)
                     status_msg = f"★ 現在、このフォルダはリンクになっています。\n→ 参照先: {target}"
                     self.var_link_status.set(status_msg)
                else:
                     self.var_link_status.set("（現在は通常のフォルダです）")
            else:
                self.var_current_path.set("未検出 (標準パスを使用します)")
                self.log("既存のバックアップフォルダが見つかりませんでした。\n標準のパスをターゲットとして処理を進めます。")
        except Exception as e:
             self.log(f"初期化中にエラーが発生しました: {e}")
             messagebox.showerror("初期化エラー", f"バックアップ場所の検出中にエラーが発生しました。\n{e}")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="新しい保存先フォルダを選択してください")
        if folder:
            self.var_new_path.set(folder)

    def set_input_state(self, state):
        """Enable or disable inputs"""
        self.entry_new.config(state=state)
        self.btn_browse.config(state=state)
        self.btn_execute.config(state=state)

    def start_execution(self):
        new_path = self.var_new_path.get()
        if not new_path:
            messagebox.showwarning("入力エラー", "新しい保存先フォルダを選択してください。")
            return

        if not messagebox.askyesno("確認", "バックアップ場所の変更を開始しますか？\n\n※iTunesが起動している場合は終了してください。\n※元データのサイズによっては時間がかかります。"):
            return

        self.set_input_state('disabled')
        self.log("\n=== 処理開始 ===")

        # Run in a separate thread to keep UI responsive
        thread = threading.Thread(target=self.run_logic, args=(new_path,))
        thread.start()

    def run_logic(self, new_path):
        try:
            self.logic.validate_new_path(new_path)
            self.logic.move_and_link(new_path, callback=self.log)
            # Use root.after for message box to ensure main thread execution
            self.root.after(0, lambda: messagebox.showinfo("完了", "すべての処理が完了しました！"))
            # Update status after success
            self.root.after(0, self.check_initial_state)
        except Exception as e:
            self.log(f"エラー発生: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.set_input_state('normal'))

if __name__ == "__main__":
    # Test execution
    from logic import BackupManager
    root = tk.Tk()
    app = AppGui(root, BackupManager())
    root.mainloop()
