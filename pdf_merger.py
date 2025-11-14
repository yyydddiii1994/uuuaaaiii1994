import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import os
import re
from collections import defaultdict
from pypdf import PdfWriter, PdfReader
import threading
import queue

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                      background="#ffffe0", relief='solid', borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class PdfMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF結合ツール")
        self.root.geometry("600x480")
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.queue = queue.Queue()
        self.create_widgets()
        self.process_queue()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10"); main_frame.pack(fill=tk.BOTH, expand=True)
        input_frame = ttk.LabelFrame(main_frame, text="入力フォルダ", padding="10"); input_frame.pack(fill=tk.X, pady=5)
        input_entry = ttk.Entry(input_frame, textvariable=self.input_dir, width=60); input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        input_button = ttk.Button(input_frame, text="選択...", command=self.select_input_dir); input_button.pack(side=tk.LEFT)
        output_frame = ttk.LabelFrame(main_frame, text="出力フォルダ", padding="10"); output_frame.pack(fill=tk.X, pady=5)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir, width=60); output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        output_button = ttk.Button(output_frame, text="選択...", command=self.select_output_dir); output_button.pack(side=tk.LEFT)

        buttons_frame = ttk.Frame(main_frame); buttons_frame.pack(pady=10)

        self.merge_by_issue_button = ttk.Button(buttons_frame, text="回ごとに結合", command=self.start_merge_by_issue_thread); self.merge_by_issue_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.merge_by_issue_button, "各回のPDFを個別のファイルに結合します。\n例: 第158回.pdf, 第159回.pdf")

        self.merge_all_button = ttk.Button(buttons_frame, text="全回を1つに結合", command=self.start_merge_all_thread); self.merge_all_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.merge_all_button, "すべての回のPDFを番号順に1つのファイルに結合します。\n例: 全回統合版.pdf")

        self.boki_textbook_button = ttk.Button(buttons_frame, text="日商簿記１級テキスト統合", command=self.start_boki_textbook_merge_thread); self.boki_textbook_button.pack(side=tk.LEFT, padx=5)
        boki_tooltip_text = (
            "【特殊機能】日商簿記1級の特定テキスト群を学習順に統合します。\n\n"
            "この機能は、以下の8つのPDFファイルが入力フォルダに\n"
            "すべて存在する場合にのみ正しく動作します。\n"
            "ファイル名が完全に一致している必要がありますのでご注意ください。\n\n"
            "--- 結合されるファイルの順序 ---\n"
            "1. 日商簿記1級+工業_原計(植田)-簿記1級+工原+教科書+第Ⅰ部.pdf\n"
            "2. 日商簿記1級+工業_原計(植田)-簿記1級+工原+教科書+第Ⅱ部.pdf\n"
            "3. 日商簿記1級+工業_原計(植田)-簿記1級+工原+問題集.pdf\n"
            "4. 日商簿記1級+商業_会計(登川)-簿記1級+商会+教科書+第Ⅰ部.pdf\n"
            "5. 日商簿記1級+商業_会計(登川)-簿記1級+商会+教科書+第Ⅱ部.pdf\n"
            "6. 日商簿記1級+商業_会計(登川)-簿記1級+商会+教科書+第Ⅲ部.pdf\n"
            "7. 日商簿記1級+商業_会計(登川)-簿記1級+商会+問題集+第Ⅰ部.pdf\n"
            "8. 日商簿記1級+商業_会計(登川)-簿記1級+商会+問題集+第Ⅱ部.pdf\n\n"
            "出力ファイル名: 日商簿記1級_統合テキスト.pdf"
        )
        ToolTip(self.boki_textbook_button, boki_tooltip_text)

        log_frame = ttk.LabelFrame(main_frame, text="進捗ログ", padding="10"); log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10); self.log_area.pack(fill=tk.BOTH, expand=True); self.log_area.config(state=tk.DISABLED)

    def select_input_dir(self): dir_path = filedialog.askdirectory(title="入力フォルダを選択"); self.input_dir.set(dir_path); self.log_message(f"入力フォルダ設定: {dir_path}")
    def select_output_dir(self): dir_path = filedialog.askdirectory(title="出力フォルダを選択"); self.output_dir.set(dir_path); self.log_message(f"出力フォルダ設定: {dir_path}")
    def log_message(self, message): self.log_area.config(state=tk.NORMAL); self.log_area.insert(tk.END, message + "\n"); self.log_area.see(tk.END); self.log_area.config(state=tk.DISABLED)
    def set_buttons_state(self, state): self.merge_by_issue_button.config(state=state); self.merge_all_button.config(state=state); self.boki_textbook_button.config(state=state)

    def start_merge_by_issue_thread(self): self.prepare_and_start_merge(self.merge_pdfs_by_issue)
    def start_merge_all_thread(self): self.prepare_and_start_merge(self.merge_all_pdfs)
    def start_boki_textbook_merge_thread(self): self.prepare_and_start_merge(self.merge_boki_textbooks)

    def prepare_and_start_merge(self, merge_function):
        input_path = self.input_dir.get(); output_path = self.output_dir.get()
        if not input_path or not output_path: self.log_message("エラー: 入力フォルダと出力フォルダを両方選択してください。"); return
        if not os.path.isdir(input_path): self.log_message(f"エラー: 入力フォルダが見つかりません: {input_path}"); return
        if not os.path.isdir(output_path):
            try: os.makedirs(output_path); self.log_message(f"情報: 出力フォルダを作成しました: {output_path}")
            except OSError as e: self.log_message(f"エラー: 出力フォルダの作成に失敗しました: {e}"); return
        self.set_buttons_state(tk.DISABLED)
        self.log_message("="*20); self.log_message("結合処理を開始します...")
        thread = threading.Thread(target=merge_function, args=(input_path, output_path)); thread.daemon = True; thread.start()

    def get_pdf_groups(self, input_path):
        pdf_groups = defaultdict(list); pattern = re.compile(r"第(\d+)回")
        for filename in os.listdir(input_path):
            if filename.lower().endswith('.pdf'):
                match = pattern.search(filename)
                if match: pdf_groups[int(match.group(1))].append(os.path.join(input_path, filename))
        return pdf_groups

    def merge_pdfs_by_issue(self, input_path, output_path):
        try:
            pdf_groups = self.get_pdf_groups(input_path)
            if not pdf_groups: self.queue.put("ログ: 結合対象のPDFファイルが見つかりませんでした。"); return
            total_groups = len(pdf_groups); self.queue.put(f"ログ: {total_groups}個のグループが見つかりました。")
            for i, (exam_number, files) in enumerate(sorted(pdf_groups.items())):
                merger = PdfWriter(); output_filename = f"第{exam_number}回_統合版.pdf"; output_filepath = os.path.join(output_path, output_filename)
                self.queue.put(f"処理中 ({i+1}/{total_groups}): 第{exam_number}回 ({len(files)} ファイル)")
                files.sort()
                for pdf_file in files:
                    try:
                        reader = PdfReader(pdf_file)
                        for page in reader.pages: merger.add_page(page)
                    except Exception as e: self.queue.put(f"警告: 「{os.path.basename(pdf_file)}」読込エラー: {e}")
                if len(merger.pages) > 0:
                    with open(output_filepath, "wb") as f_out: merger.write(f_out)
                    self.queue.put(f"-> 完了: {output_filename}")
                else: self.queue.put(f"警告: 第{exam_number}回の結合失敗。")
                merger.close()
            self.queue.put("="*20); self.queue.put("全ての処理が完了しました。")
        except Exception as e: self.queue.put(f"致命的なエラー: {e}")
        finally: self.queue.put("MERGE_COMPLETE")

    def merge_all_pdfs(self, input_path, output_path):
        try:
            pdf_groups = self.get_pdf_groups(input_path)
            if not pdf_groups: self.queue.put("ログ: 結合対象のPDFファイルが見つかりませんでした。"); return
            total_groups = len(pdf_groups); self.queue.put(f"ログ: {total_groups}個のグループをスキャン中...")
            final_merger = PdfWriter(); output_filename = "全回統合版.pdf"; output_filepath = os.path.join(output_path, output_filename)
            for i, (exam_number, files) in enumerate(sorted(pdf_groups.items())):
                self.queue.put(f"追加中 ({i+1}/{total_groups}): 第{exam_number}回")
                files.sort()
                for pdf_file in files:
                    try:
                        reader = PdfReader(pdf_file)
                        for page in reader.pages: final_merger.add_page(page)
                    except Exception as e: self.queue.put(f"警告: 「{os.path.basename(pdf_file)}」読込エラー: {e}")
            if len(final_merger.pages) > 0:
                with open(output_filepath, "wb") as f_out: final_merger.write(f_out)
                self.queue.put(f"-> 完了: {output_filename}")
            else: self.queue.put("警告: 最終的なPDFの作成に失敗しました（ページが空です）。")
            final_merger.close()
            self.queue.put("="*20); self.queue.put("全ての処理が完了しました。")
        except Exception as e: self.queue.put(f"致命的なエラー: {e}")
        finally: self.queue.put("MERGE_COMPLETE")

    def merge_boki_textbooks(self, input_path, output_path):
        try:
            files_to_merge = [
                "日商簿記1級+工業_原計(植田)-簿記1級+工原+教科書+第Ⅰ部.pdf",
                "日商簿記1級+工業_原計(植田)-簿記1級+工原+教科書+第Ⅱ部.pdf",
                "日商簿記1級+工業_原計(植田)-簿記1級+工原+問題集.pdf",
                "日商簿記1級+商業_会計(登川)-簿記1級+商会+教科書+第Ⅰ部.pdf",
                "日商簿記1級+商業_会計(登川)-簿記1級+商会+教科書+第Ⅱ部.pdf",
                "日商簿記1級+商業_会計(登川)-簿記1級+商会+教科書+第Ⅲ部.pdf",
                "日商簿記1級+商業_会計(登川)-簿記1級+商会+問題集+第Ⅰ部.pdf",
                "日商簿記1級+商業_会計(登川)-簿記1級+商会+問題集+第Ⅱ部.pdf"
            ]

            missing_files = [f for f in files_to_merge if not os.path.exists(os.path.join(input_path, f))]
            if missing_files:
                self.queue.put("エラー: 以下の必須ファイルが見つかりません。")
                for f in missing_files: self.queue.put(f"- {f}")
                self.queue.put("処理を中断しました。"); return

            merger = PdfWriter()
            output_filename = "日商簿記1級_統合テキスト.pdf"
            output_filepath = os.path.join(output_path, output_filename)
            self.queue.put(f"{len(files_to_merge)}個のファイルを指定順で結合します...")
            for i, filename in enumerate(files_to_merge):
                self.queue.put(f"処理中 ({i+1}/{len(files_to_merge)}): {filename}")
                try:
                    reader = PdfReader(os.path.join(input_path, filename))
                    for page in reader.pages: merger.add_page(page)
                except Exception as e: self.queue.put(f"警告: 「{filename}」読込エラー: {e}")
            if len(merger.pages) > 0:
                with open(output_filepath, "wb") as f_out: merger.write(f_out)
                self.queue.put(f"-> 完了: {output_filename}")
            else: self.queue.put("警告: 最終的なPDFの作成に失敗しました（ページが空です）。")
            merger.close()
            self.queue.put("="*20); self.queue.put("全ての処理が完了しました。")
        except Exception as e: self.queue.put(f"致命的なエラー: {e}")
        finally: self.queue.put("MERGE_COMPLETE")

    def process_queue(self):
        try:
            message = self.queue.get_nowait()
            if message == "MERGE_COMPLETE":
                self.set_buttons_state(tk.NORMAL)
            else:
                self.log_message(message)
        except queue.Empty: pass
        finally: self.root.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = PdfMergerApp(root)
    root.mainloop()
