import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import pyautogui
import os

class KindleCaptureGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kindle自動キャプチャツール")
        self.geometry("450x400")
        self.resizable(False, False)

        # テーマ設定
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        # キューの初期化 (スレッド間通信用)
        self.queue = queue.Queue()

        self.is_capturing = False

        self.create_widgets()
        self.after(100, self.process_queue)

    def create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # タイトルラベル
        title_label = ttk.Label(main_frame, text="Kindle 自動スクリーンショット", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # 入力エリア
        input_frame = ttk.LabelFrame(main_frame, text="設定", padding="10 10 10 10")
        input_frame.pack(fill=tk.X, pady=(0, 20))

        # 本のタイトル
        ttk.Label(input_frame, text="本のタイトル (フォルダ名):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.book_title_var = tk.StringVar(value="KindleBook")
        ttk.Entry(input_frame, textvariable=self.book_title_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        # ページめくり待機時間
        ttk.Label(input_frame, text="ページめくり待機時間 (秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.delay_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(input_frame, from_=0.1, to=10.0, increment=0.1, textvariable=self.delay_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        # キャプチャするページ数
        ttk.Label(input_frame, text="キャプチャするページ数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.pages_var = tk.IntVar(value=100)
        ttk.Spinbox(input_frame, from_=1, to=5000, textvariable=self.pages_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        # ステータスラベル
        self.status_var = tk.StringVar(value="待機中...")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Helvetica", 10))
        self.status_label.pack(pady=(0, 15))

        # ボタンエリア
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(btn_frame, text="キャプチャ開始", command=self.start_capture)
        self.start_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self.stop_capture, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

        # 説明ラベル
        info_text = "※ 開始後5秒以内にKindleアプリをアクティブにしてください。\n※ 中断したい場合は、マウスを画面の四隅のいずれかに移動してください。"
        ttk.Label(main_frame, text=info_text, font=("Helvetica", 8), foreground="gray", justify=tk.LEFT).pack(pady=(15, 0))

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                if msg_type == "status":
                    self.status_var.set(data)
                elif msg_type == "progress":
                    self.progress_var.set(data)
                elif msg_type == "done":
                    self.status_var.set("完了しました。")
                    self.reset_ui()
                    messagebox.showinfo("完了", f"キャプチャが完了しました。\n保存先: {data}")
                elif msg_type == "stopped":
                    self.status_var.set("ユーザーによって停止されました。")
                    self.reset_ui()
                elif msg_type == "error":
                    self.status_var.set("エラーが発生しました。")
                    self.reset_ui()
                    messagebox.showerror("エラー", data)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def reset_ui(self):
        self.is_capturing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)

    def start_capture(self):
        book_title = self.book_title_var.get().strip()
        if not book_title:
            messagebox.showwarning("警告", "本のタイトルを入力してください。")
            return

        try:
            page_delay = float(self.delay_var.get())
            num_pages = int(self.pages_var.get())
        except ValueError:
            messagebox.showwarning("警告", "数値を正しく入力してください。")
            return

        self.is_capturing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)

        # バックグラウンドスレッドでキャプチャ開始
        threading.Thread(target=self.capture_thread, args=(book_title, page_delay, num_pages), daemon=True).start()

    def stop_capture(self):
        self.is_capturing = False
        self.status_var.set("停止処理中...")
        self.stop_btn.config(state=tk.DISABLED)

    def capture_thread(self, book_title, page_delay, num_pages):
        try:
            output_folder = os.path.join(os.path.expanduser("~"), "Documents", book_title)
            os.makedirs(output_folder, exist_ok=True)

            # カウントダウン
            for i in range(5, 0, -1):
                if not self.is_capturing:
                    self.queue.put(("stopped", None))
                    return
                self.queue.put(("status", f"開始まで {i}秒... (Kindleアプリを前面に出してください)"))
                time.sleep(1)

            self.queue.put(("status", "キャプチャを実行中..."))

            pyautogui.FAILSAFE = True

            for page_count in range(1, num_pages + 1):
                if not self.is_capturing:
                    self.queue.put(("stopped", None))
                    return

                self.queue.put(("status", f"キャプチャ中... {page_count}/{num_pages} ページ"))
                self.queue.put(("progress", (page_count / num_pages) * 100))

                # スクリーンショットを保存
                screenshot_path = os.path.join(output_folder, f"page_{page_count:04d}.png")
                pyautogui.screenshot(screenshot_path)

                # ページめくり
                pyautogui.press('right')

                # 待機 (キャンセルチェックのため細かく分割)
                sleep_interval = 0.1
                sleep_time = 0
                while sleep_time < page_delay:
                    if not self.is_capturing:
                        self.queue.put(("stopped", None))
                        return
                    time.sleep(sleep_interval)
                    sleep_time += sleep_interval

            self.queue.put(("done", output_folder))

        except pyautogui.FailSafeException:
            self.queue.put(("error", "フェイルセーフがトリガーされました。\n(マウスが画面の隅に移動したため中断しました)"))
        except Exception as e:
            self.queue.put(("error", f"予期せぬエラーが発生しました:\n{str(e)}"))

if __name__ == "__main__":
    app = KindleCaptureGUI()
    app.mainloop()
