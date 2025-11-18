# install_gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys
import os
import shutil
import traceback
from pathlib import Path

class InstallerGUI:
    def __init__(self, master):
        self.master = master
        master.title("LECTOR-TS Anki Addon Installer")
        master.geometry("600x400")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#007bff", foreground="white", font=('Helvetica', 12, 'bold'))
        style.map("TButton", background=[('active', '#0056b3')])

        main_frame = ttk.Frame(master, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        label = ttk.Label(main_frame, text="LECTOR-TS Anki Addon Installer", font=("Helvetica", 16, "bold"))
        label.pack(pady=(0, 10))
        info_label = ttk.Label(main_frame, text="下のボタンを押すと、Ankiのアドオンフォルダを自動検出し、\nLECTOR-TSアドオンをインストールします。", justify=tk.CENTER)
        info_label.pack(pady=(0, 20))

        self.install_button = ttk.Button(main_frame, text="LECTOR-TSをAnkiにインストール！", command=self.start_installation_thread)
        self.install_button.pack(pady=10, ipady=10, fill=tk.X)

        self.log_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10, font=("Courier New", 9))
        self.log_area.pack(pady=10, fill=tk.BOTH, expand=True)
        self.log_area.configure(state='disabled')

    def log(self, message):
        self.master.after(0, self._log_thread_safe, message)

    def _log_thread_safe(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def start_installation_thread(self):
        self.install_button.config(state=tk.DISABLED, text="インストール中...")
        thread = threading.Thread(target=self.install_addon)
        thread.daemon = True
        thread.start()

    def get_anki_addon_path(self):
        """OSに応じてAnkiのアドオンフォルダのパスを返す"""
        platform = sys.platform
        if platform == "win32":
            path = Path(os.getenv('APPDATA')) / "Anki2" / "addons21"
        elif platform == "darwin": # macOS
            path = Path.home() / "Library" / "Application Support" / "Anki2" / "addons21"
        else: # Linux
            path = Path.home() / ".local" / "share" / "Anki2" / "addons21"
        return path

    def install_addon(self):
        """アドオンのインストール処理"""
        try:
            self.log("="*50)
            self.log("インストール処理を開始します...")

            # 1. Ankiのアドオンフォルダパスを取得
            self.log(f"OS: {sys.platform}を検出しました。")
            addon_path = self.get_anki_addon_path()
            self.log(f"Ankiアドオンフォルダを検索中: {addon_path}")

            if not addon_path.exists():
                raise FileNotFoundError("Ankiのアドオンフォルダが見つかりませんでした。Ankiが正しくインストールされているか確認してください。")

            self.log("Ankiアドオンフォルダを発見しました。")

            # 2. ソースファイルとターゲットのパスを定義
            source_dir = Path(__file__).parent / "src" / "lector_ts_addon"
            target_dir = addon_path / "lector_ts_addon"
            self.log(f"コピー元: {source_dir}")
            self.log(f"コピー先: {target_dir}")

            if not source_dir.exists():
                 raise FileNotFoundError("アドオンのソースファイルが見つかりませんでした。")

            # 3. 既存のアドオンがあれば削除（クリーンインストールのため）
            if target_dir.exists():
                self.log("既存のバージョンを検出しました。上書きのため削除します...")
                shutil.rmtree(target_dir)
                self.log("古いバージョンを削除しました。")

            # 4. ファイルをコピー
            self.log("アドオンファイルをコピー中...")
            shutil.copytree(source_dir, target_dir)
            self.log("ファイルのコピーが完了しました。")

            self.log("="*50)
            self.log("インストールが正常に完了しました！")
            self.log("Ankiを再起動してアドオンを有効にしてください。")

            self.master.after(0, lambda: self.install_button.config(text="インストール完了（再実行可）"))

        except Exception as e:
            self.log("\n[!!! エラー !!!]")
            self.log("インストール中にエラーが発生しました。")
            self.log("詳細は以下の通りです：")
            self.log(f"エラー種別: {type(e).__name__}")
            self.log(f"エラー内容: {e}")
            self.log("-" * 20)
            self.log("スタックトレース:")
            self.log(traceback.format_exc())
            self.log("-" * 20)
            self.log("Ankiが実行中の場合は、一度終了してから再度お試しください。")
            self.master.after(0, lambda: self.install_button.config(text="エラー発生（再試行）"))
        finally:
            self.master.after(0, lambda: self.install_button.config(state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()
