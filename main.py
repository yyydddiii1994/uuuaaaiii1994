# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, simpledialog
import requests
import threading

class AnkiCardGeneratorApp:
    """
    A desktop application using tkinter to generate Anki flashcards from text
    by leveraging the DeepSeek API.
    """
    def __init__(self, root):
        """
        Initializes the main application window and its widgets.
        """
        self.root = root
        self.root.title("Ankiカード生成アプリ")
        self.root.geometry("800x650") # Increased height for status bar

        self.api_key = "" # This will be set via the menu

        self._setup_ui()

    def _setup_ui(self):
        """
        Sets up the graphical user interface of the application.
        """
        # --- Main Frame ---
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=10, padx=10, fill="both", expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # --- Input Frame ---
        input_frame = tk.LabelFrame(main_frame, text="ここにテキストを貼り付け")
        input_frame.grid(row=0, column=0, pady=5, sticky="nsew")
        input_frame.grid_rowconfigure(0, weight=1)
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=10)
        self.input_text.pack(pady=5, padx=5, fill="both", expand=True)
        self.input_text.insert("1.0", "ここにAnkiカードにしたい文章を貼り付けて、「Ankiカード生成」ボタンを押してください。")

        # --- Output Frame ---
        output_frame = tk.LabelFrame(main_frame, text="生成されたAnkiカード (表;裏)")
        output_frame.grid(row=1, column=0, pady=5, sticky="nsew")
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=10)
        self.output_text.pack(pady=5, padx=5, fill="both", expand=True)

        # --- Button Frame ---
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5, padx=10, fill="x")

        self.generate_button = tk.Button(button_frame, text="Ankiカード生成", command=self.generate_cards)
        self.generate_button.pack(side="left", padx=5)

        self.save_button = tk.Button(button_frame, text="ファイルに保存", command=self.save_cards)
        self.save_button.pack(side="left", padx=5)

        # --- Menu ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="設定", menu=settings_menu)
        settings_menu.add_command(label="APIキー設定", command=self.set_api_key)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def generate_cards(self):
        """
        Validates input and API key, then starts the card generation process
        in a separate thread to keep the UI responsive.
        """
        input_content = self.input_text.get("1.0", tk.END).strip()
        if not input_content or input_content == "ここにAnkiカードにしたい文章を貼り付けて、「Ankiカード生成」ボタンを押してください。":
            messagebox.showwarning("警告", "入力テキストが空です。")
            return

        if not self.api_key:
            messagebox.showwarning("警告", "APIキーが設定されていません。「設定」メニューからキーを設定してください。")
            return

        self.generate_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.output_text.delete("1.0", tk.END)
        self.status_var.set("Ankiカードを生成中... DeepSeek APIに問い合わせています...")
        self.root.update_idletasks()

        thread = threading.Thread(target=self._api_call_and_update, args=(input_content,))
        thread.start()

    def _api_call_and_update(self, content):
        """
        Handles the actual API call to DeepSeek to generate flashcards.
        This method is executed in a background thread.
        """
        DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        prompt = f"""
        以下のテキストに基づいて、Ankiで学習するためのフラッシュカードを作成してください。
        各カードは「表の内容;裏の内容」という形式で、1行に1カードを記述してください。
        セミコロン(;)は表と裏の区切りとしてのみ使用してください。
        できるだけ多くの重要な概念を網羅し、簡潔で覚えやすいカードを作成してください。

        ---
        {content}
        ---
        """

        data = {
            "model": "deepseek-chat", # Changed to a more general chat model
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that creates Anki flashcards in 'front;back' format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "stream": False
        }

        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=120) # Increased timeout
            response.raise_for_status()
            result = response.json()
            card_data = result['choices'][0]['message']['content'].strip()
            self.root.after(0, self._update_ui_with_result, card_data)
        except requests.exceptions.Timeout:
            self.root.after(0, self._update_ui_with_error, "APIリクエストがタイムアウトしました。時間を置いて再試行してください。")
        except requests.exceptions.RequestException as e:
            self.root.after(0, self._update_ui_with_error, f"APIリクエストエラー: {e}")
        except (KeyError, IndexError) as e:
            self.root.after(0, self._update_ui_with_error, f"APIからの応答形式が不正です: {e}\n\n受信内容:\n{response.text}")
        except Exception as e:
            self.root.after(0, self._update_ui_with_error, f"予期せぬエラーが発生しました: {e}")

    def _update_ui_with_result(self, card_data):
        """
        Updates the UI with the successfully generated card data.
        This method is called from the main thread.
        """
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", card_data)
        self.generate_button.config(state="normal")
        self.save_button.config(state="normal")
        self.status_var.set("カード生成が完了しました。")
        messagebox.showinfo("成功", "Ankiカードの生成が完了しました。")

    def _update_ui_with_error(self, error_message):
        """
        Updates the UI to show an error message.
        This method is called from the main thread.
        """
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", f"エラー:\n{error_message}")
        self.generate_button.config(state="normal")
        self.save_button.config(state="normal")
        self.status_var.set("エラーが発生しました。")
        messagebox.showerror("エラー", error_message)

    def save_cards(self):
        """
        Saves the content of the output text box to a user-selected file.
        """
        cards_content = self.output_text.get("1.0", tk.END).strip()
        if not cards_content or cards_content.startswith("エラー:"):
            messagebox.showwarning("警告", "保存できる有効なカードがありません。")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")],
            title="Ankiカードを保存"
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(cards_content)
                self.status_var.set(f"ファイルを保存しました: {filepath}")
                messagebox.showinfo("成功", f"ファイルを保存しました:\n{filepath}")
            except Exception as e:
                self.status_var.set("ファイルの保存中にエラーが発生しました。")
                messagebox.showerror("エラー", f"ファイルの保存中にエラーが発生しました:\n{e}")

    def set_api_key(self):
        """
        Opens a dialog to ask the user for their DeepSeek API key.
        """
        new_key = simpledialog.askstring(
            "APIキー設定",
            "DeepSeek APIキーを入力してください:",
            show='*'
        )
        if new_key:
            self.api_key = new_key
            self.status_var.set("APIキーが設定されました。")
            messagebox.showinfo("成功", "APIキーを設定しました。")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnkiCardGeneratorApp(root)
    root.mainloop()
