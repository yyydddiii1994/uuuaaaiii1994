import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
import threading
import queue
import json
import os
import sys
import traceback
from llm_handler import LLMHandler, get_ollama_models, get_ollama_model_details

# ======================================================================
# I/O Redirection Class
# ======================================================================
class TextRedirector(object):
    def __init__(self, widget):
        self.widget = widget

    def write(self, str):
        self.widget.config(state=tk.NORMAL)
        self.widget.insert(tk.END, str)
        self.widget.see(tk.END)
        self.widget.config(state=tk.DISABLED)

    def flush(self):
        pass

# ======================================================================
# Tooltip Class
# ======================================================================
class Tooltip:
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

        label = ttk.Label(self.tooltip_window, text=self.text, background="#FFFFE0", relief="solid", borderwidth=1, padding=5)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

# ======================================================================
# Main Application Class
# ======================================================================
class AnkiClozeConverter(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Anki穴埋めカード自動生成ツール")
        self.geometry("1200x800")
        self.ollama_num_ctx = None # 設定値を保持する変数

        # --- スタイルの設定 ---
        sv_ttk.set_theme("light")

        # --- メインフレームとタブの設定 ---
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        converter_tab = ttk.Frame(notebook, padding=(0, 10, 0, 0))
        log_tab = ttk.Frame(notebook)

        notebook.add(converter_tab, text="変換")
        settings_tab = ttk.Frame(notebook)
        notebook.add(settings_tab, text="設定")
        notebook.add(log_tab, text="ログ")

        # --- 「設定」タブのUI ---
        self.ollama_settings_frame = ttk.LabelFrame(settings_tab, text="Ollama 設定", padding=10)
        # Initially hidden, shown when Ollama is selected
        # self.ollama_settings_frame.pack(fill=tk.X, padx=10, pady=10)

        ctx_label = ttk.Label(self.ollama_settings_frame, text="コンテキスト長 (num_ctx):")
        ctx_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.ctx_scale_var = tk.IntVar(value=4096) # Default value
        self.ctx_scale = ttk.Scale(self.ollama_settings_frame, from_=2048, to_=32768, orient=tk.HORIZONTAL, variable=self.ctx_scale_var, command=self.on_ctx_scale_changed)
        self.ctx_scale.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.ollama_settings_frame.columnconfigure(1, weight=1)

        self.ctx_value_label = ttk.Label(self.ollama_settings_frame, text="4096")
        self.ctx_value_label.grid(row=0, column=2, sticky="w", padx=5, pady=5)

        mem_label = ttk.Label(self.ollama_settings_frame, text="推定メモリ使用量:")
        mem_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.mem_progressbar = ttk.Progressbar(self.ollama_settings_frame, orient='horizontal', mode='determinate', maximum=100)
        self.mem_progressbar.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        info_label_text = "コンテキスト長は、LLMが一度に考慮できるテキストの量です。\n・値を大きくすると: 長い文章の関連性を捉えやすくなりますが、処理速度が低下し、メモリ使用量が増加します。\n・値を小さくすると: 処理が速くなりメモリ消費も少ないですが、複雑なカードの穴埋め精度が落ちる可能性があります。"
        self.info_label = ttk.Label(self.ollama_settings_frame, text=info_label_text, wraplength=500, justify=tk.LEFT)
        self.info_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=10)

        self.apply_ollama_settings_button = ttk.Button(self.ollama_settings_frame, text="設定を適用", command=self.apply_ollama_settings)
        self.apply_ollama_settings_button.grid(row=3, column=0, columnspan=3, pady=5)


        # --- 「変換」タブのUI ---
        # 上部フレーム (設定エリア)
        top_frame = ttk.LabelFrame(converter_tab, text="設定", padding=10)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        top_frame.columnconfigure(1, weight=1)
        top_frame.columnconfigure(3, weight=1)

        self.open_button = ttk.Button(top_frame, text="ファイルを開く", command=self.open_file)
        self.open_button.grid(row=0, column=0, padx=(0, 5))
        self.save_button = ttk.Button(top_frame, text="名前を付けて保存", command=self.save_file)
        self.save_button.grid(row=0, column=1, padx=(0, 20))

        llm_label = ttk.Label(top_frame, text="LLM:")
        llm_label.grid(row=0, column=2, padx=(0, 5))
        self.llm_selector = ttk.Combobox(top_frame, values=["DeepSeek", "Ollama"], state="readonly")
        self.llm_selector.grid(row=0, column=3, sticky="ew", padx=(0, 20))

        api_key_label = ttk.Label(top_frame, text="APIキー:")
        api_key_label.grid(row=0, column=4, padx=(0, 5))
        self.api_key_entry = ttk.Entry(top_frame, show="*")
        self.api_key_entry.grid(row=0, column=5, sticky="ew", padx=(0, 20))

        self.ollama_model_label = ttk.Label(top_frame, text="Ollamaモデル:")
        self.ollama_model_selector = ttk.Combobox(top_frame, state="readonly")
        self.ollama_model_selector.bind("<<ComboboxSelected>>", self.on_ollama_model_selected)

        batch_size_label = ttk.Label(top_frame, text="一度に処理するカード枚数:")
        batch_size_label.grid(row=0, column=6, padx=(0, 5))
        self.batch_size_spinbox = ttk.Spinbox(top_frame, from_=1, to=100, increment=1, width=5)
        self.batch_size_spinbox.grid(row=0, column=7)

        # 中央フレーム (テキストエリア)
        center_frame = ttk.Frame(converter_tab)
        center_frame.pack(fill=tk.BOTH, expand=True)
        center_frame.columnconfigure(0, weight=1)
        center_frame.columnconfigure(1, weight=1)
        center_frame.rowconfigure(0, weight=1)

        input_frame = ttk.LabelFrame(center_frame, text="入力 (編集可能)", padding=5)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        input_frame.rowconfigure(0, weight=1)
        input_frame.columnconfigure(0, weight=1)

        self.input_text = tk.Text(input_frame, wrap=tk.WORD, relief=tk.FLAT)
        self.input_text.grid(row=0, column=0, sticky="nsew")
        input_scrollbar = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.input_text.yview)
        input_scrollbar.grid(row=0, column=1, sticky="ns")
        self.input_text.config(yscrollcommand=input_scrollbar.set)

        output_frame = ttk.LabelFrame(center_frame, text="出力 (レビュー用)", padding=5)
        output_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output_text = tk.Text(output_frame, wrap=tk.WORD, relief=tk.FLAT, state=tk.DISABLED)
        self.output_text.grid(row=0, column=0, sticky="nsew")
        output_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        output_scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.config(yscrollcommand=output_scrollbar.set)

        # 下部フレーム (実行ボタンとステータス)
        bottom_frame = ttk.Frame(converter_tab, padding=(0, 10, 0, 0))
        bottom_frame.pack(fill=tk.X)
        bottom_frame.columnconfigure(2, weight=1)

        # --- 「ログ」タブのUI ---
        log_frame = ttk.Frame(log_tab, padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, relief=tk.FLAT, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # --- 初期化の続き ---
        # 設定の保存/復元
        self.config_file = "config.json"
        self.load_config()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 非同期処理の準備
        self.queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.after(100, self.process_queue)

        # `convert_button`と`status_label`を先に定義
        self.convert_button = ttk.Button(bottom_frame, text="変換実行", style="Accent.TButton", command=self.start_conversion)
        self.convert_button.grid(row=0, column=0, padx=(0, 5))

        self.cancel_button = ttk.Button(bottom_frame, text="中止", state=tk.DISABLED, command=self.cancel_conversion)
        self.cancel_button.grid(row=0, column=1, padx=(0, 10))

        self.status_label = ttk.Label(bottom_frame, text="準備完了")
        self.status_label.grid(row=0, column=2, sticky="ew", padx=(0, 5))

        self.progress_bar = ttk.Progressbar(bottom_frame, orient='horizontal', mode='determinate')
        self.progress_bar.grid(row=0, column=3, sticky="ew")

        # 初期設定とツールチップ
        self.llm_selector.bind("<<ComboboxSelected>>", self.on_llm_selected)
        self.load_ollama_models()
        self.setup_tooltips()
        self.on_llm_selected(None) # 初期UI状態を設定
        self.on_ctx_scale_changed(self.ctx_scale_var.get()) # 初期スケール値を設定

        # --- 標準出力/エラーのリダイレクト ---
        sys.stdout = TextRedirector(self.log_text)
        sys.stderr = TextRedirector(self.log_text)

    def process_queue(self):
        try:
            message = self.queue.get_nowait()
            if message[0] == "status":
                self.status_label.config(text=message[1])
            elif message[0] == "result":
                self.output_text.config(state=tk.NORMAL)
                # 結果はすでに行ごとに改行が含まれている可能性があるため、そのまま追加
                self.output_text.insert(tk.END, message[1] + "\n")
                self.output_text.config(state=tk.DISABLED)
            elif message[0] == "progress":
                self.progress_bar['value'] = message[1]
            elif message[0] == "simple_error":
                messagebox.showerror("エラー", message[1])
            elif message[0] == "finished":
                self._finalize_conversion(message[1])
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def start_conversion(self):
        # UIを処理中状態に設定
        self.convert_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.status_label.config(text="変換処理を開始します...")
        self.progress_bar['value'] = 0

        # キャンセルイベントをリセット
        self.cancel_event.clear()

        # 出力エリアをクリア
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)

        # スレッドを開始
        thread = threading.Thread(target=self.conversion_thread)
        thread.daemon = True
        thread.start()

    def conversion_thread(self):
        try:
            # 設定を取得
            llm_type = self.llm_selector.get()
            api_key = self.api_key_entry.get()
            batch_size = int(self.batch_size_spinbox.get())

            config = {
                "llm_type": llm_type,
                "api_key": api_key,
                "ollama_model": self.ollama_model_selector.get() if llm_type == "Ollama" else None,
                "ollama_num_ctx": self.ollama_num_ctx
            }

            # カードデータを準備
            input_content = self.input_text.get("1.0", tk.END).strip()
            cards = [line for line in input_content.split('\n') if line]
            total_cards = len(cards)
            self.progress_bar['maximum'] = total_cards

            # LLMハンドラを初期化
            handler = LLMHandler(config)

            total_batches = (total_cards + batch_size - 1) // batch_size
            processed_cards = 0

            for i in range(0, total_cards, batch_size):
                if self.cancel_event.is_set():
                    self.queue.put(("finished", "中止"))
                    return

                batch_cards = cards[i:i + batch_size]
                current_batch_num = (i // batch_size) + 1
                self.queue.put(("status", f"バッチ {current_batch_num}/{total_batches} を処理中... ({len(batch_cards)}枚)"))

                # LLMに処理を依頼 (llm_handler内でエラーハンドリングされる)
                result = handler.convert_cards(batch_cards)
                self.queue.put(("result", result))

                processed_cards += len(batch_cards)
                self.queue.put(("progress", processed_cards))

            if not self.cancel_event.is_set():
                self.queue.put(("finished", "完了"))

        except Exception as e:
            print("="*60)
            print("変換処理中にエラーが発生しました。")
            traceback.print_exc()
            print("="*60)
            self.queue.put(("simple_error", f"変換処理中にエラーが発生しました。\n詳細は「ログ」タブを確認してください。\n\nエラータイプ: {type(e).__name__}"))
            self.queue.put(("status", "エラーが発生しました。詳細は「ログ」タブを確認してください。"))
        finally:
            self.queue.put(("finished", "エラー発生"))

    def cancel_conversion(self):
        self.status_label.config(text="変換を中止しています...")
        self.cancel_event.set()
        self.cancel_button.config(state=tk.DISABLED)

    def _finalize_conversion(self, status_message):
        self.convert_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        final_status = {
            "完了": "変換処理が完了しました。",
            "中止": "変換処理が中止されました。",
            "エラー発生": "エラーが発生しました。詳細は「ログ」タブを確認してください。"
        }.get(status_message, "準備完了")
        self.status_label.config(text=final_status)
        if status_message == "完了":
            self.progress_bar['value'] = self.progress_bar['maximum']

    def on_llm_selected(self, event):
        selected_llm = self.llm_selector.get()
        if selected_llm == "Ollama":
            self.api_key_entry.grid_remove()
            self.ollama_model_label.grid(row=0, column=4, padx=(0, 5))
            self.ollama_model_selector.grid(row=0, column=5, sticky="ew", padx=(0, 20))
            self.ollama_settings_frame.pack(fill=tk.X, padx=10, pady=10, side=tk.TOP)
        else: # DeepSeek
            self.ollama_model_label.grid_remove()
            self.ollama_model_selector.grid_remove()
            self.api_key_entry.grid(row=0, column=5, sticky="ew", padx=(0, 20))
            self.ollama_settings_frame.pack_forget()

    def on_ctx_scale_changed(self, value):
        val = int(float(value))
        self.ctx_value_label.config(text=str(val))

        # スライダーの現在の最小値と最大値を取得
        min_val = self.ctx_scale.cget("from")
        max_val = self.ctx_scale.cget("to")

        if max_val - min_val > 0:
            progress_val = ((val - min_val) / (max_val - min_val)) * 100
            self.mem_progressbar['value'] = progress_val

    def apply_ollama_settings(self):
        ctx_length = self.ctx_scale_var.get()
        self.ollama_num_ctx = ctx_length
        messagebox.showinfo("設定適用", f"Ollamaのコンテキスト長が {ctx_length} に設定されました。\nこの設定は次回の変換から有効になります。")

    def load_ollama_models(self):
        models = get_ollama_models()
        if models:
            self.ollama_model_selector['values'] = models
            if len(models) > 0:
                self.ollama_model_selector.current(0)
                # 初期モデル選択イベントを手動でトリガー
                self.on_ollama_model_selected(None)
        else:
            self.ollama_model_selector['values'] = ["(Ollamaが見つかりません)"]
            self.ollama_model_selector.set("(Ollamaが見つかりません)")

    def on_ollama_model_selected(self, event):
        """Ollamaモデルが選択されたときに呼び出される。"""
        model_name = self.ollama_model_selector.get()
        if model_name and "(Ollamaが見つかりません)" not in model_name:
            print(f"選択されたモデル: {model_name}。詳細情報を取得します...")
            # スケジューリングしてUIのフリーズを防ぐ
            self.after(100, lambda: self.update_ollama_context_settings(model_name))

    def update_ollama_context_settings(self, model_name):
        """Ollamaモデルの詳細を取得し、コンテキスト設定UIを更新する。"""
        details = get_ollama_model_details(model_name)

        # デフォルト値
        min_ctx, max_ctx, default_ctx = 2048, 8192, 4096

        if details and 'parameters' in details:
            params_str = details['parameters']
            # 文字列からnum_ctxの値を見つける
            try:
                # "num_ctx 4096" のような形式を想定
                ctx_line = next(line for line in params_str.split('\n') if 'num_ctx' in line)
                default_ctx = int(ctx_line.split()[-1])

                # 取得した値に基づいて範囲を調整
                min_ctx = 2048
                max_ctx = max(default_ctx * 2, 8192) # デフォルトの2倍か8192の大きい方
                print(f"モデル '{model_name}' のデフォルトコンテキスト長: {default_ctx}")

            except (StopIteration, ValueError, IndexError) as e:
                print(f"モデル '{model_name}' のnum_ctxを解析できませんでした。デフォルト値を使用します。エラー: {e}")
        else:
            print(f"モデル '{model_name}' の詳細を取得できませんでした。デフォルト値を使用します。")

        # スライダーとラベルを更新
        self.ctx_scale.config(from_=min_ctx, to=max_ctx)
        self.ctx_scale_var.set(default_ctx)
        self.ctx_value_label.config(text=str(default_ctx))
        self.on_ctx_scale_changed(default_ctx) # プログレスバーも更新

    def open_file(self):
        filepath = filedialog.askopenfilename(
            title="テキストファイルを選択",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")]
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", content)
            self.status_label.config(text=f"ファイルを開きました: {filepath}")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの読み込み中にエラーが発生しました:\n{e}")
            self.status_label.config(text="ファイルの読み込みに失敗しました")

    def save_file(self):
        filepath = filedialog.asksaveasfilename(
            title="名前を付けて保存",
            defaultextension=".txt",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")]
        )
        if not filepath:
            return

        try:
            # getメソッドは末尾に改行を追加するため、strip()で削除する
            content = self.output_text.get("1.0", tk.END).strip()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.status_label.config(text=f"ファイルを保存しました: {filepath}")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの保存中にエラーが発生しました:\n{e}")
            self.status_label.config(text="ファイルの保存に失敗しました")

    def setup_tooltips(self):
        Tooltip(self.open_button, "Ankiからエクスポートしたテキストファイル（タブ区切り）を開きます。")
        Tooltip(self.save_button, "変換後のテキストをAnkiにインポート可能な形式で保存します。")
        Tooltip(self.llm_selector, "穴埋め問題の生成に使用するLLMを選択します。")
        Tooltip(self.api_key_entry, "DeepSeek APIを利用する場合、ここにAPIキーを入力してください。")
        Tooltip(self.ollama_model_selector, "Ollamaで利用するローカルモデルを選択します。")
        Tooltip(self.batch_size_spinbox, "一度にLLMに送信するカードの枚数を指定します。\n値を大きくすると処理が速くなる可能性がありますが、\nLLMがタスクを誤解する（要約など）リスクも高まります。")
        Tooltip(self.convert_button, "入力テキストを元に、穴埋めカードの生成を開始します。")

    def save_config(self):
        config_data = {
            "llm_type": self.llm_selector.get(),
            "api_key": self.api_key_entry.get(),
            "ollama_model": self.ollama_model_selector.get(),
            "ollama_num_ctx": self.ollama_num_ctx,
            "batch_size": self.batch_size_spinbox.get()
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print(f"設定の保存中にエラーが発生しました: {e}")

    def load_config(self):
        if not os.path.exists(self.config_file):
            return
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            self.llm_selector.set(config_data.get("llm_type", "DeepSeek"))
            self.api_key_entry.insert(0, config_data.get("api_key", ""))

            # Ollamaのコンテキスト長を読み込み
            saved_ctx = config_data.get("ollama_num_ctx")
            if saved_ctx:
                self.ollama_num_ctx = int(saved_ctx)
                # GUIのスケールにも反映
                self.ctx_scale_var.set(self.ollama_num_ctx)

            self.batch_size_spinbox.set(config_data.get("batch_size", "10"))

            # Ollamaモデルは後でload_ollama_modelsで設定されるため、ここでは設定しない
        except Exception as e:
            print(f"設定の読み込み中にエラーが発生しました: {e}")

    def on_closing(self):
        self.save_config()
        self.destroy()


if __name__ == "__main__":
    try:
        app = AnkiClozeConverter()
        app.mainloop()
    except Exception as e:
        import traceback
        # アプリケーションの初期化に失敗した場合、フォールバックとして
        # Tkinterのルートウィンドウを最小限で作成してエラーを表示する
        root = tk.Tk()
        root.withdraw() # メインウィンドウは表示しない
        messagebox.showerror(
            "致命的なエラー",
            f"アプリケーションの起動中に予期せぬエラーが発生しました。\n\n"
            f"エラー内容:\n{e}\n\n"
            f"詳細:\n{traceback.format_exc()}"
        )
        root.destroy()
