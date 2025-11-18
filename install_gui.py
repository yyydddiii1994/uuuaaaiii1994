# install_gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys
import os
import shutil
import traceback
import subprocess
from pathlib import Path

class InstallerGUI:
    def __init__(self, master):
        self.master = master
        master.title("LECTOR-TS Anki Addon Installer")
        master.geometry("700x500") # Windowサイズを拡大
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#007bff", foreground="white", font=('Helvetica', 12, 'bold'))
        style.map("TButton", background=[('active', '#0056b3')])

        main_frame = ttk.Frame(master, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        label = ttk.Label(main_frame, text="LECTOR-TS Anki Addon Installer", font=("Helvetica', 16, 'bold"))
        label.pack(pady=(0, 10))
        info_label = ttk.Label(main_frame, text="下のボタンを押すと、依存ライブラリを含めたアドオン全体をAnkiにインストールします。\n初回は数GBのダウンロードを行うため、完了まで数分〜数十分かかる場合があります。", justify=tk.CENTER)
        info_label.pack(pady=(0, 20))

        self.install_button = ttk.Button(main_frame, text="LECTOR-TSをAnkiにインストール！", command=self.start_installation_thread)
        self.install_button.pack(pady=10, ipady=10, fill=tk.X)

        self.log_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15, font=("Courier New", 9))
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
        platform = sys.platform
        if platform == "win32": path = Path(os.getenv('APPDATA')) / "Anki2" / "addons21"
        elif platform == "darwin": path = Path.home() / "Library" / "Application Support" / "Anki2" / "addons21"
        else: path = Path.home() / ".local" / "share" / "Anki2" / "addons21"
        return path

    def install_addon(self):
        try:
            self.log("="*60)
            self.log("インストール処理を開始します...")

            # --- 1. パスの準備 ---
            addon_path = self.get_anki_addon_path()
            if not addon_path.exists():
                raise FileNotFoundError(f"Ankiアドオンフォルダが見つかりません: {addon_path}")

            source_dir = Path(__file__).parent / "src" / "lector_ts_addon"
            requirements_file = Path(__file__).parent / "requirements.txt"
            target_dir = addon_path / "lector_ts_addon"

            self.log(f"OS: {sys.platform} | Anki Addon Path: {addon_path}")
            if not source_dir.exists() or not requirements_file.exists():
                raise FileNotFoundError("ソースファイル (src/lector_ts_addon) または requirements.txt が見つかりません。")

            # --- 2. ソースコードのコピー ---
            self.log(f"アドオンのソースを '{target_dir}' にコピーしています...")
            if target_dir.exists():
                self.log("既存のバージョンを削除しています...")
                shutil.rmtree(target_dir)
            shutil.copytree(source_dir, target_dir)
            shutil.copy(requirements_file, target_dir)
            self.log("ソースコードのコピー完了。")

            # --- 3. 依存ライブラリのインストール ---
            self.log("="*60)
            self.log("依存ライブラリのインストールを開始します... (数分かかる場合があります)")
            vendor_dir = target_dir / "vendor"
            os.makedirs(vendor_dir, exist_ok=True)

            # コマンドを構築
            command = [
                sys.executable, "-m", "pip", "install",
                "--no-cache-dir", # キャッシュを無効化してクリーンインストール
                "-r", str(target_dir / "requirements.txt"),
                "-t", str(vendor_dir)
            ]

            self.log(f"実行コマンド: {' '.join(command)}")

            # サブプロセスとしてpipを実行し、出力をリアルタイムでログに表示
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', bufsize=1)

            # 標準出力を読み取ってログに流す
            for line in iter(process.stdout.readline, ''):
                self.log(line.strip())

            process.stdout.close()
            return_code = process.wait()

            if return_code != 0:
                # エラーが発生した場合
                error_output = process.stderr.read()
                process.stderr.close()
                raise RuntimeError(f"pipの実行に失敗しました (終了コード: {return_code})。\n{error_output}")

            self.log("依存ライブラリのインストールが完了しました。")

            # --- 4. 完了 ---
            # クリーンアップ
            os.remove(target_dir / "requirements.txt")

            self.log("="*60)
            self.log("インストールが正常に完了しました！")
            self.log("Ankiを再起動してアドオンを有効にしてください。")
            self.master.after(0, lambda: self.install_button.config(text="インストール完了（再実行可）"))

        except Exception as e:
            self.log("\n[!!! エラー !!!]")
            self.log("インストール中にエラーが発生しました。")
            self.log(f"エラー種別: {type(e).__name__}: {e}")
            self.log("-" * 20)
            self.log("スタックトレース:")
            self.log(traceback.format_exc())
            self.master.after(0, lambda: self.install_button.config(text="エラー発生（再試行）"))
        finally:
            self.master.after(0, lambda: self.install_button.config(state=tk.NORMAL))


if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()
