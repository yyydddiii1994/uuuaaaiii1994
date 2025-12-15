import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
from pathlib import Path
import sys

# Import logic
try:
    from .converter import LogConverter
except ImportError:
    # Allow running directly for testing
    from converter import LogConverter

class ConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google AI Studio Log Converter - ログ変換ツール")
        self.root.geometry("600x550")

        # Style configuration
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Meiryo", 10), padding=6)
        self.style.configure("TLabel", font=("Meiryo", 10))
        self.style.configure("Header.TLabel", font=("Meiryo", 12, "bold"))

        self.converter = LogConverter()
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.is_running = False

        self._create_widgets()

        # Set default output to Desktop for convenience
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            self.output_dir.set(str(desktop))

    def _create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Introduction / Instructions
        intro_text = (
            "Google AI Studioのチャットログ（JSONファイル）を\n"
            "読みやすいテキスト形式（.txt）に一括変換するツールです。\n"
            "Googleドライブからダウンロードしたフォルダなどを指定してください。"
        )
        lbl_intro = ttk.Label(main_frame, text=intro_text, justify=tk.LEFT, background="#f0f0f0", padding=10, relief="solid")
        lbl_intro.pack(fill=tk.X, pady=(0, 20))

        # --- Step 1: Input Folder ---
        step1_frame = ttk.LabelFrame(main_frame, text="ステップ 1: 変換元のフォルダを選択", padding=10)
        step1_frame.pack(fill=tk.X, pady=(0, 10))

        row1 = ttk.Frame(step1_frame)
        row1.pack(fill=tk.X)

        entry_input = ttk.Entry(row1, textvariable=self.input_dir, state="readonly")
        entry_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        btn_input = ttk.Button(row1, text="フォルダ参照...", command=self._select_input_folder)
        btn_input.pack(side=tk.RIGHT)

        # --- Step 2: Output Folder ---
        step2_frame = ttk.LabelFrame(main_frame, text="ステップ 2: 保存先のフォルダを選択", padding=10)
        step2_frame.pack(fill=tk.X, pady=(0, 10))

        row2 = ttk.Frame(step2_frame)
        row2.pack(fill=tk.X)

        entry_output = ttk.Entry(row2, textvariable=self.output_dir, state="readonly")
        entry_output.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        btn_output = ttk.Button(row2, text="フォルダ参照...", command=self._select_output_folder)
        btn_output.pack(side=tk.RIGHT)

        # --- Step 3: Action ---
        self.btn_run = ttk.Button(main_frame, text="変換を開始する！", command=self._start_conversion_thread)
        self.btn_run.pack(fill=tk.X, pady=(10, 10))

        # --- Log Area ---
        lbl_log = ttk.Label(main_frame, text="処理ログ:")
        lbl_log.pack(anchor=tk.W)

        self.log_area = scrolledtext.ScrolledText(main_frame, height=10, font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log("準備完了。フォルダを選択して「変換を開始する！」を押してください。")

    def _select_input_folder(self):
        folder = filedialog.askdirectory(title="JSONファイルが入っているフォルダを選択してください")
        if folder:
            self.input_dir.set(folder)
            self.log(f"入力フォルダを設定: {folder}")

    def _select_output_folder(self):
        folder = filedialog.askdirectory(title="変換後のファイルを保存するフォルダを選択してください")
        if folder:
            self.output_dir.set(folder)
            self.log(f"出力フォルダを設定: {folder}")

    def log(self, message):
        """Thread-safe logging"""
        def _append():
            self.log_area.insert(tk.END, message + "\n")
            self.log_area.see(tk.END)
        self.root.after(0, _append)

    def _start_conversion_thread(self):
        if self.is_running:
            return

        in_dir = self.input_dir.get()
        out_dir = self.output_dir.get()

        if not in_dir:
            messagebox.showwarning("確認", "入力フォルダ（ステップ1）を選択してください。")
            return
        if not out_dir:
            messagebox.showwarning("確認", "出力フォルダ（ステップ2）を選択してください。")
            return

        self.is_running = True
        self.btn_run.config(state=tk.DISABLED)
        self.log("\n--- 処理開始 ---")

        thread = threading.Thread(target=self._run_conversion, args=(in_dir, out_dir))
        thread.daemon = True
        thread.start()

    def _run_conversion(self, in_dir, out_dir):
        try:
            in_path = Path(in_dir)
            files = list(in_path.glob("*.json"))

            if not files:
                self.log(f"エラー: 指定フォルダ内に .json ファイルが見つかりませんでした。\n場所: {in_path}")
                self._finish()
                return

            self.log(f"対象ファイル数: {len(files)} 件")
            success_count = 0
            fail_count = 0

            for i, json_file in enumerate(files, 1):
                self.log(f"[{i}/{len(files)}] 変換中: {json_file.name} ...")
                success, msg = self.converter.convert_file(json_file, out_dir)
                if success:
                    success_count += 1
                    # self.log(f"  -> OK") # Keep it clean, simple success log is handled by converter return if specific, but let's just count
                else:
                    fail_count += 1
                    self.log(f"  -> 失敗: {msg}")

            self.log("\n--- 完了 ---")
            self.log(f"成功: {success_count} 件")
            self.log(f"失敗: {fail_count} 件")

            if success_count > 0:
                self.log(f"保存先: {out_dir}")
                self.root.after(0, lambda: messagebox.showinfo("完了", f"変換が完了しました！\n成功: {success_count}件\n失敗: {fail_count}件"))
            else:
                self.root.after(0, lambda: messagebox.showwarning("完了", "変換に成功したファイルはありませんでした。ログを確認してください。"))

        except Exception as e:
            self.log(f"予期せぬエラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self._finish()

    def _finish(self):
        self.is_running = False
        self.root.after(0, lambda: self.btn_run.config(state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()
