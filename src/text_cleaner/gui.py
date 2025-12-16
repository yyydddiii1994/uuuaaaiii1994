import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import threading
from src.text_cleaner.logic import clean_text_content

class TextCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("日本語・数字抽出ツール")
        self.root.geometry("600x450")

        # UIのセットアップ
        self.setup_ui()

    def setup_ui(self):
        # メインフレーム
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 説明ラベル
        description = (
            "このツールは、テキストファイルから「日本語（ひらがな・カタカナ・漢字）」と\n"
            "「数字（半角・全角）」以外の文字を削除するツールです。\n"
            "アルファベットや記号などは削除されます。"
        )
        lbl_desc = tk.Label(main_frame, text=description, justify=tk.LEFT, bg="#f0f0f0", padx=10, pady=10, relief=tk.RIDGE)
        lbl_desc.pack(fill=tk.X, pady=(0, 20))

        # ファイル選択エリア
        select_frame = tk.Frame(main_frame)
        select_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_file = tk.Label(select_frame, text="ファイルが選択されていません", anchor="w", fg="gray")
        self.lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_select = tk.Button(select_frame, text="ファイルを選択...", command=self.select_file)
        btn_select.pack(side=tk.RIGHT, padx=(10, 0))

        # オプションエリア
        opt_frame = tk.Frame(main_frame)
        opt_frame.pack(fill=tk.X, pady=(0, 20))

        self.var_keep_newlines = tk.BooleanVar(value=True)
        chk_newlines = tk.Checkbutton(opt_frame, text="改行は削除しない（推奨）", variable=self.var_keep_newlines)
        chk_newlines.pack(side=tk.LEFT)

        # 実行ボタン
        self.btn_run = tk.Button(main_frame, text="処理を開始する", command=self.run_process, state=tk.DISABLED, bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"))
        self.btn_run.pack(fill=tk.X, pady=(0, 20))

        # ログ表示エリア
        lbl_log = tk.Label(main_frame, text="処理ログ:")
        lbl_log.pack(anchor="w")

        self.txt_log = scrolledtext.ScrolledText(main_frame, height=8, state=tk.DISABLED)
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        self.selected_file_path = None

    def log(self, message):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="処理するテキストファイルを選択してください",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.selected_file_path = file_path
            self.lbl_file.config(text=os.path.basename(file_path), fg="black")
            self.btn_run.config(state=tk.NORMAL)
            self.log(f"ファイルを選択しました: {file_path}")

    def run_process(self):
        if not self.selected_file_path:
            return

        # 出力先の確認
        input_dir = os.path.dirname(self.selected_file_path)
        input_filename = os.path.basename(self.selected_file_path)
        output_filename = f"cleaned_{input_filename}"

        output_path = filedialog.asksaveasfilename(
            title="保存先を指定してください",
            initialdir=input_dir,
            initialfile=output_filename,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if not output_path:
            self.log("保存がキャンセルされました。")
            return

        # 処理開始
        self.btn_run.config(state=tk.DISABLED)
        self.log("処理を開始します...")

        # UIフリーズ回避のために別スレッドで実行
        thread = threading.Thread(target=self.process_file, args=(self.selected_file_path, output_path))
        thread.start()

    def process_file(self, input_path, output_path):
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            cleaned_content = clean_text_content(content, keep_newlines=self.var_keep_newlines.get())

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)

            self.root.after(0, lambda: self.on_success(output_path))

        except UnicodeDecodeError:
            # Shift-JISでの再試行
            try:
                with open(input_path, 'r', encoding='shift_jis') as f:
                    content = f.read()
                cleaned_content = clean_text_content(content, keep_newlines=self.var_keep_newlines.get())
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                self.root.after(0, lambda: self.on_success(output_path))
            except Exception as e:
                self.root.after(0, lambda: self.on_error(str(e)))
        except Exception as e:
            self.root.after(0, lambda: self.on_error(str(e)))

    def on_success(self, output_path):
        self.log(f"完了しました！ 保存先: {output_path}")
        messagebox.showinfo("完了", "処理が正常に完了しました。\nアルファベット等が削除されました。")
        self.btn_run.config(state=tk.NORMAL)

    def on_error(self, error_msg):
        self.log(f"エラーが発生しました: {error_msg}")
        messagebox.showerror("エラー", f"処理中にエラーが発生しました。\n{error_msg}")
        self.btn_run.config(state=tk.NORMAL)
