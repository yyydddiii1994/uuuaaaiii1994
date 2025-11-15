import tkinter as tk
from tkinter import ttk, scrolledtext
import sv_ttk
import platform
import os
import shutil
from datetime import datetime
import sys

# アドオンのディレクトリ名
ADDON_NAME = "anki_cognitive_load_analyzer"

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ankiアドオンインストーラー")
        self.root.geometry("700x450")

        # --- スタイル設定 ---
        try:
            sv_ttk.set_theme("light")
        except RuntimeError as e:
            print(f"sv-ttkテーマの設定に失敗しました: {e}")
            # フォールバックテーマやデフォルトスタイルを使用する可能性があります

        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # --- ボタンフレーム ---
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.install_button = ttk.Button(button_frame, text="インストール", command=self.install_addon)
        self.install_button.pack(side=tk.LEFT, padx=(0, 5), ipadx=10, ipady=5)
        self.install_button.bind("<Enter>", lambda e: self.show_tooltip("Ankiにアドオンをインストールします。"))
        self.install_button.bind("<Leave>", lambda e: self.hide_tooltip())

        self.uninstall_button = ttk.Button(button_frame, text="アンインストール", command=self.uninstall_addon)
        self.uninstall_button.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)
        self.uninstall_button.bind("<Enter>", lambda e: self.show_tooltip("Ankiからアドオンをアンインストールします。"))
        self.uninstall_button.bind("<Leave>", lambda e: self.hide_tooltip())

        # --- ログエリア ---
        log_frame = ttk.LabelFrame(self.main_frame, text="ログ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, font=("Meiryo UI", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state='disabled')

        # --- ツールチップ ---
        self.tooltip = None

        self.log("インストーラーを起動しました。")
        self.log(f"OS: {platform.system()} {platform.release()}")
        self.log(f"Pythonバージョン: {sys.version}")

    def show_tooltip(self, text):
        if self.tooltip is not None:
            self.hide_tooltip()

        # マウスカーソルの位置を取得
        x, y = self.root.winfo_pointerxy()

        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True) # ウィンドウ枠を非表示に
        self.tooltip.wm_geometry(f"+{x+20}+{y+10}") # 位置を調整

        label = ttk.Label(self.tooltip, text=text, padding="5", background="#FFFFE0", relief="solid", borderwidth=1, font=("Meiryo UI", 9))
        label.pack()

    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def log(self, message, level="INFO"):
        """ログエリアにメッセージを追記します。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{now}] [{level}] {message}\n"

        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, formatted_message)
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)
        self.root.update_idletasks() # UIを即時更新

    def get_anki_addon_dir(self):
        """OSに基づいてAnkiのアドオンディレクトリを取得します。"""
        system = platform.system()
        try:
            if system == "Windows":
                # APPDATA環境変数が存在するか確認
                appdata = os.getenv("APPDATA")
                if not appdata:
                    self.log("環境変数 'APPDATA' が見つかりません。", "ERROR")
                    return None
                return os.path.join(appdata, "Anki2", "addons21")
            elif system == "Darwin":  # macOS
                return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Anki2", "addons21")
            elif system == "Linux":
                return os.path.join(os.path.expanduser("~"), ".local", "share", "Anki2", "addons21")
            else:
                self.log(f"サポートされていないOSです: {system}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Ankiディレクトリの取得中にエラーが発生しました: {e}", "ERROR")
            return None

    def install_addon(self):
        """アドオンをAnkiにインストールします。"""
        self.log("インストール処理を開始します...")

        addon_dir = self.get_anki_addon_dir()
        if not addon_dir:
            self.log("Ankiのアドオンディレクトリが見つからないため、処理を中断します。", "ERROR")
            return

        # Ankiディレクトリが存在しない場合、作成を試みる（初回起動時など）
        if not os.path.isdir(addon_dir):
            self.log(f"Ankiアドオンディレクトリが見つかりません: {addon_dir}", "WARNING")
            self.log("ディレクトリの作成を試みます...")
            try:
                os.makedirs(addon_dir, exist_ok=True)
                self.log("ディレクトリを作成しました。", "INFO")
            except OSError as e:
                self.log(f"ディレクトリの作成に失敗しました: {e}", "ERROR")
                return

        # スクリプト自身の場所に基づいてソースディレクトリを決定
        source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anki_plugin")
        if not os.path.isdir(source_dir):
             self.log(f"ソースディレクトリが見つかりません: {source_dir}", "ERROR")
             return

        target_dir = os.path.join(addon_dir, ADDON_NAME)
        self.log(f"インストール先: {target_dir}")

        # 既に存在する場合は、一度アンインストールする
        if os.path.exists(target_dir):
            self.log("古いバージョンが検出されたため、先にアンインストールします。")
            self.uninstall_addon()

        try:
            shutil.copytree(source_dir, target_dir)
            self.log("アドオンのインストールが正常に完了しました。", "INFO")
            self.log("Ankiを再起動してアドオンを有効化してください。")
        except Exception as e:
            self.log(f"インストール中にエラーが発生しました: {e}", "ERROR")

    def uninstall_addon(self):
        """アドオンをAnkiからアンインストールします。"""
        self.log("アンインストール処理を開始します...")

        addon_dir = self.get_anki_addon_dir()
        if not addon_dir:
            self.log("Ankiのアドオンディレクトリが見つからないため、処理を中断します。", "ERROR")
            return

        target_dir = os.path.join(addon_dir, ADDON_NAME)

        if not os.path.exists(target_dir):
            self.log("アドオンはインストールされていません。")
            return

        try:
            shutil.rmtree(target_dir)
            self.log("アドオンのアンインストールが正常に完了しました。", "INFO")
        except Exception as e:
            self.log(f"アンインストール中にエラーが発生しました: {e}", "ERROR")

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()
