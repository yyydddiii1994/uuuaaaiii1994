import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import os
import re
import requests
import time

class TextProcessingTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("リゼロWeb版 テキスト処理ツール")
        self.geometry("800x600")

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.merge_frame = ttk.Frame(self.notebook, padding="10")
        self.split_frame = ttk.Frame(self.notebook, padding="10")
        self.summarize_frame = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.merge_frame, text="ファイル統合")
        self.notebook.add(self.split_frame, text="ファイル分割")
        self.notebook.add(self.summarize_frame, text="概要生成と挿入")

        self.create_merge_widgets()
        self.create_split_widgets()
        self.create_summarize_widgets()

        # --- PanedWindow for resizable layout ---
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        paned_window.add(self.notebook)

        # --- Log Area ---
        log_frame = ttk.LabelFrame(paned_window, text="進捗ログ", height=150)
        self.log_text = tk.Text(log_frame, state="disabled", wrap=tk.WORD, height=10)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text['yscrollcommand'] = log_scroll.set
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        paned_window.add(log_frame)

        self.queue = queue.Queue()
        self.after(100, self.process_queue)

    def create_merge_widgets(self):
        input_dir_frame = ttk.LabelFrame(self.merge_frame, text="入力設定")
        input_dir_frame.pack(fill=tk.X, pady=5)
        self.merge_input_dir = tk.StringVar()
        ttk.Label(input_dir_frame, text="テキストファイルがあるフォルダ:").pack(side=tk.LEFT, padx=5, pady=5)
        merge_input_entry = ttk.Entry(input_dir_frame, textvariable=self.merge_input_dir, width=60)
        merge_input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
        self.create_tooltip(merge_input_entry, "統合したい「エピソード〇〇.txt」ファイル群が含まれているフォルダを選択してください。")
        merge_input_button = ttk.Button(input_dir_frame, text="参照...", command=lambda: self.select_directory(self.merge_input_dir))
        merge_input_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.create_tooltip(merge_input_button, "フォルダ選択ダイアログを開きます。")

        output_file_frame = ttk.LabelFrame(self.merge_frame, text="出力設定")
        output_file_frame.pack(fill=tk.X, pady=5)
        self.merge_output_file = tk.StringVar()
        ttk.Label(output_file_frame, text="統合後のファイル名:").pack(side=tk.LEFT, padx=5, pady=5)
        merge_output_entry = ttk.Entry(output_file_frame, textvariable=self.merge_output_file, width=60)
        merge_output_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
        self.create_tooltip(merge_output_entry, "統合後のテキストファイルの名前と保存場所をフルパスで指定してください。\n例: C:\\Users\\user\\Desktop\\統合ファイル.txt")
        merge_output_button = ttk.Button(output_file_frame, text="保存先...", command=self.select_save_file)
        merge_output_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.create_tooltip(merge_output_button, "ファイル保存ダイアログを開きます。")

        merge_button = ttk.Button(self.merge_frame, text="統合実行", command=self.start_merge_thread)
        merge_button.pack(pady=20)
        self.create_tooltip(merge_button, "ファイル統合処理を開始します。\n入力フォルダ内のテキストファイルをエピソード番号でソートし、\n指定された出力ファイルに一つにまとめます。")

    def start_merge_thread(self):
        input_dir = self.merge_input_dir.get()
        output_file = self.merge_output_file.get()
        if not input_dir or not output_file:
            messagebox.showerror("エラー", "入力フォルダと出力ファイルの両方を指定してください。")
            return
        thread = threading.Thread(target=self.merge_files_thread, args=(input_dir, output_file))
        thread.start()

    def merge_files_thread(self, input_dir, output_file):
        try:
            self.queue.put(("log", "ファイル統合処理を開始します..."))
            files_to_merge = []
            pattern = re.compile(r"(?:エピソード|episode)(\d+).*?\.txt")
            for filename in os.listdir(input_dir):
                match = pattern.match(filename)
                if match:
                    episode_number = int(match.group(1))
                    files_to_merge.append((episode_number, os.path.join(input_dir, filename)))
            if not files_to_merge:
                self.queue.put(("error", "対象のテキストファイルが見つかりませんでした。ファイル名は「エピソード数字」で始まっていますか？"))
                return
            self.queue.put(("log", f"{len(files_to_merge)}個のファイルを発見。エピソード番号でソートします。"))
            files_to_merge.sort(key=lambda x: x[0])
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for i, (num, path) in enumerate(files_to_merge):
                    self.queue.put(("log", f"  -> 統合中: {os.path.basename(path)} ({i+1}/{len(files_to_merge)})"))
                    with open(path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read().strip())
                    if i < len(files_to_merge) - 1:
                        outfile.write("\n\n====================\n\n")
            self.queue.put(("success", f"ファイル統合が完了しました。\n{len(files_to_merge)}個のファイルを '{os.path.basename(output_file)}' に統合しました。"))
        except Exception as e:
            self.queue.put(("error", f"ファイル統合中にエラーが発生しました: {e}"))

    def create_split_widgets(self):
        input_file_frame = ttk.LabelFrame(self.split_frame, text="入力設定")
        input_file_frame.pack(fill=tk.X, pady=5)
        self.split_input_file = tk.StringVar()
        ttk.Label(input_file_frame, text="統合ファイル:").pack(side=tk.LEFT, padx=5, pady=5)
        split_input_entry = ttk.Entry(input_file_frame, textvariable=self.split_input_file, width=60)
        split_input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
        self.create_tooltip(split_input_entry, "ファイル統合機能で作成した統合テキストファイル（.txt）を選択してください。")
        split_input_button = ttk.Button(input_file_frame, text="参照...", command=lambda: self.select_file(self.split_input_file))
        split_input_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.create_tooltip(split_input_button, "ファイル選択ダイアログを開きます。")

        output_dir_frame = ttk.LabelFrame(self.split_frame, text="出力設定")
        output_dir_frame.pack(fill=tk.X, pady=5)
        self.split_output_dir = tk.StringVar()
        ttk.Label(output_dir_frame, text="分割ファイルの保存先フォルダ:").pack(side=tk.LEFT, padx=5, pady=5)
        split_output_entry = ttk.Entry(output_dir_frame, textvariable=self.split_output_dir, width=60)
        split_output_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
        self.create_tooltip(split_output_entry, "分割されたファイル（part_01.txtなど）を保存するフォルダを選択してください。")
        split_output_button = ttk.Button(output_dir_frame, text="参照...", command=lambda: self.select_directory(self.split_output_dir))
        split_output_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.create_tooltip(split_output_button, "フォルダ選択ダイアログを開きます。")

        split_button = ttk.Button(self.split_frame, text="分割実行", command=self.start_split_thread)
        split_button.pack(pady=20)
        self.create_tooltip(split_button, "ファイル分割処理を開始します。\n統合ファイルを100エピソードずつに分割し、\n指定された出力フォルダに複数のファイルとして保存します。")

    def start_split_thread(self):
        input_file = self.split_input_file.get()
        output_dir = self.split_output_dir.get()
        if not input_file or not output_dir:
            messagebox.showerror("エラー", "入力ファイルと出力フォルダの両方を指定してください。")
            return
        thread = threading.Thread(target=self.split_file_thread, args=(input_file, output_dir))
        thread.start()

    def split_file_thread(self, input_file, output_dir):
        try:
            self.queue.put(("log", "ファイル分割処理を開始します..."))
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            total_size = len(content)
            chunk_size = total_size // 10
            self.queue.put(("log", f"合計文字数: {total_size}。1ファイルあたり約{chunk_size}文字で10個のファイルに分割します。"))

            start_index = 0
            for i in range(10):
                # 最後のチャンクは残りすべてを対象とする
                if i == 9:
                    end_index = total_size
                else:
                    end_index = start_index + chunk_size

                chunk_content = content[start_index:end_index]
                output_filename = os.path.join(output_dir, f"part_{i+1:02d}.txt")
                self.queue.put(("log", f"  -> ファイルを作成中: {os.path.basename(output_filename)} ({i+1}/10)"))
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(chunk_content)

                start_index = end_index

            self.queue.put(("success", f"ファイル分割が完了しました。\n10個のファイルを '{output_dir}' に作成しました。"))
        except Exception as e:
            self.queue.put(("error", f"ファイル分割中にエラーが発生しました: {e}"))

    def start_summarize_thread(self):
        api_key = self.api_key.get()
        source_dir = self.summarize_input_dir.get()
        split_dir = self.summarize_split_dir.get()
        if not all([api_key, source_dir, split_dir]):
            messagebox.showerror("エラー", "APIキー、元のファイルフォルダ、分割ファイルフォルダをすべて指定してください。")
            return
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        thread = threading.Thread(target=self.summarize_and_insert_thread, args=(api_key, source_dir, split_dir))
        thread.start()

    def summarize_and_insert_thread(self, api_key, source_dir, split_dir):
        try:
            self.queue.put(("log", "概要生成処理を開始...\n"))
            self.queue.put(("log", "ステップ1/3: ファイルリストを準備中...\n"))
            source_pattern = re.compile(r"(?:エピソード|episode)(\d+).*?\.txt")
            source_files = sorted(
                [os.path.join(source_dir, f) for f in os.listdir(source_dir) if source_pattern.match(f)],
                key=lambda f: int(source_pattern.match(os.path.basename(f)).group(1))
            )
            split_pattern = re.compile(r"part_(\d+)\.txt")
            split_files = sorted(
                [os.path.join(split_dir, f) for f in os.listdir(split_dir) if split_pattern.match(f)],
                key=lambda f: int(split_pattern.match(os.path.basename(f)).group(1))
            )
            if not source_files or not split_files:
                self.queue.put(("error", "必要なファイルが見つかりません。フォルダを確認してください。"))
                return
            self.queue.put(("log", f"  - 元ファイル: {len(source_files)}個\n  - 分割ファイル: {len(split_files)}個\n"))
            self.queue.put(("log", "\nステップ2/3: 概要を生成中 (APIリクエスト)...\n"))
            all_summaries = []
            source_chunks = [source_files[i:i + 10] for i in range(0, len(source_files), 10)]
            for i, chunk in enumerate(source_chunks):
                first_ep = source_pattern.match(os.path.basename(chunk[0])).group(1)
                last_ep = source_pattern.match(os.path.basename(chunk[-1])).group(1)
                progress_msg = f"  - {i+1}/{len(source_chunks)}: エピソード {first_ep}～{last_ep} の概要を生成中..."
                self.queue.put(("log", progress_msg))
                combined_text = ""
                for file_path in chunk:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        combined_text += f.read().strip() + "\n\n"
                summary = self.call_deepseek_api(api_key, combined_text)
                all_summaries.append(summary)
                self.queue.put(("log", " 完了\n"))
            self.queue.put(("log", "\nステップ3/3: 分割ファイルに概要を挿入中...\n"))
            summaries_per_split = 10
            episodes_per_split = 100
            for i, split_file_path in enumerate(split_files):
                self.queue.put(("log", f"  - {os.path.basename(split_file_path)} を再構築中...\n"))

                # 該当する概要と元のソースファイルを取得
                start_summary_index = i * summaries_per_split
                end_summary_index = start_summary_index + summaries_per_split
                relevant_summaries = all_summaries[start_summary_index:end_summary_index]

                start_episode_file_index = i * episodes_per_split
                end_episode_file_index = start_episode_file_index + episodes_per_split
                relevant_source_files = source_files[start_episode_file_index:end_episode_file_index]

                new_content = ""
                # 10個の概要と100個のソースファイルを組み合わせて新しい内容を作成
                for j, summary in enumerate(relevant_summaries):
                    summary_title_first_ep = (i * 100) + (j * 10) + 1

                    # 概要に対応する10個のソースファイルを取得
                    start_source_index = j * 10
                    end_source_index = start_source_index + 10
                    source_files_group = relevant_source_files[start_source_index:end_source_index]

                    summary_title_last_ep = summary_title_first_ep + len(source_files_group) - 1

                    # 概要を追加
                    new_content += f"【エピソード {summary_title_first_ep}～{summary_title_last_ep} 概要】\n{summary}\n\n"

                    # 10個の本文を連結して追加
                    episodes_content_group = []
                    for source_file in source_files_group:
                        with open(source_file, 'r', encoding='utf-8') as f:
                            episodes_content_group.append(f.read().strip())
                    new_content += "\n\n====================\n\n".join(episodes_content_group)

                    if j < len(relevant_summaries) - 1:
                         new_content += "\n\n====================\n\n"

                with open(split_file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            self.queue.put(("success", "すべてのファイルの処理が完了しました。"))
        except Exception as e:
            self.queue.put(("error", f"エラーが発生しました: {e}"))

    def call_deepseek_api(self, api_key, text_to_summarize):
        api_url = "https://api.deepseek.com/v1/chat/completions"
        headers = { "Content-Type": "application/json", "Authorization": f"Bearer {api_key}" }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "あなたはプロの編集者です。提供されたテキストを日本語で5行程度の簡潔な概要にまとめてください。"},
                {"role": "user", "content": text_to_summarize}
            ]
        }
        for attempt in range(3):
            try:
                response = requests.post(api_url, headers=headers, json=data, timeout=90)
                if response.status_code == 401:
                    raise requests.exceptions.RequestException("APIキーが無効です (401 Unauthorized)")
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']
            except requests.exceptions.RequestException as e:
                if attempt < 2:
                    self.queue.put(("log", f" (APIエラー: {e}, 5秒後にリトライ...)"))
                    time.sleep(5)
                else:
                    raise e

    def create_summarize_widgets(self):
        api_key_frame = ttk.LabelFrame(self.summarize_frame, text="API設定")
        api_key_frame.pack(fill=tk.X, pady=5)
        self.api_key = tk.StringVar()
        ttk.Label(api_key_frame, text="DeepSeek APIキー:").pack(side=tk.LEFT, padx=5, pady=5)
        api_key_entry = ttk.Entry(api_key_frame, textvariable=self.api_key, width=60, show="*")
        api_key_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
        self.create_tooltip(api_key_entry, "DeepSeek APIの認証キーを入力してください。")

        input_frame = ttk.LabelFrame(self.summarize_frame, text="入力設定")
        input_frame.pack(fill=tk.X, pady=5)
        self.summarize_input_dir = tk.StringVar()
        ttk.Label(input_frame, text="元のテキストファイルがあるフォルダ:").pack(side=tk.LEFT, padx=5, pady=5)
        summarize_input_entry = ttk.Entry(input_frame, textvariable=self.summarize_input_dir, width=50)
        summarize_input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
        self.create_tooltip(summarize_input_entry, "概要を生成したい元の「エピソード〇〇.txt」ファイル群が含まれているフォルダを選択してください。")
        summarize_input_button = ttk.Button(input_frame, text="参照...", command=lambda: self.select_directory(self.summarize_input_dir))
        summarize_input_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.create_tooltip(summarize_input_button, "フォルダ選択ダイアログを開きます。")

        self.summarize_split_dir = tk.StringVar()
        ttk.Label(input_frame, text="分割ファイルがあるフォルダ:").pack(side=tk.LEFT, padx=5, pady=5)
        summarize_split_entry = ttk.Entry(input_frame, textvariable=self.summarize_split_dir, width=50)
        summarize_split_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
        self.create_tooltip(summarize_split_entry, "概要の挿入先となる分割済みファイル（part_01.txtなど）が保存されているフォルダを選択してください。")
        summarize_split_button = ttk.Button(input_frame, text="参照...", command=lambda: self.select_directory(self.summarize_split_dir))
        summarize_split_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.create_tooltip(summarize_split_button, "フォルダ選択ダイアログを開きます。")

        summarize_button = ttk.Button(self.summarize_frame, text="概要を生成して挿入", command=self.start_summarize_thread)
        summarize_button.pack(pady=20)
        self.create_tooltip(summarize_button, "概要生成と挿入処理を開始します。\n元のファイルを10個単位でAPIに送信して要約し、\n分割済みファイル内の適切な位置に挿入して上書き保存します。\n（警告：処理には時間がかかり、APIの利用料金が発生します）")

    def select_directory(self, string_var):
        dir_name = filedialog.askdirectory()
        if dir_name:
            string_var.set(dir_name)

    def select_file(self, string_var):
        file_name = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_name:
            string_var.set(file_name)

    def select_save_file(self):
        file_name = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_name:
            self.merge_output_file.set(file_name)

    def process_queue(self):
        try:
            msg_type, content = self.queue.get_nowait()
            if msg_type == "log":
                self.log_text.config(state="normal")
                self.log_text.insert(tk.END, content + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state="disabled")
            elif msg_type == "success":
                self.queue.put(("log", f"成功: {content}"))
                messagebox.showinfo("成功", content)
            elif msg_type == "error":
                self.queue.put(("log", f"エラー: {content}"))
                messagebox.showerror("エラー", content)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def create_tooltip(self, widget, text):
        tool_tip = tk.Toplevel(widget)
        tool_tip.wm_overrideredirect(True)
        tool_tip.wm_geometry("+0+0")
        tool_tip.withdraw()
        label = tk.Label(tool_tip, text=text, justify='left',
                      background='#ffffe0', relief='solid', borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)
        def enter(event):
            x, y, cx, cy = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            tool_tip.wm_geometry(f"+{x}+{y}")
            tool_tip.deiconify()
        def leave(event):
            tool_tip.withdraw()
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

if __name__ == "__main__":
    app = TextProcessingTool()
    app.mainloop()
