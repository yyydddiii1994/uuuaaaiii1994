import tkinter as tk
import sys
import os
import traceback
import platform
import datetime

def show_error_gui(error_text):
    """
    緊急時用のエラー表示GUI。
    メインアプリが起動しない場合に、詳細なエラーログを表示します。
    """
    try:
        root = tk.Tk()
        root.title("起動エラー - 詳細ログ")
        root.geometry("800x600")

        lbl = tk.Label(root, text="アプリケーションの起動に失敗しました。\n以下のエラーログを開発者に報告してください。",
                       fg="red", font=("Helvetica", 14, "bold"), pady=10)
        lbl.pack()

        # テキストウィジェット（スクロール可能）
        txt = tk.Text(root, wrap=tk.NONE)
        v_scroll = tk.Scrollbar(root, command=txt.yview)
        h_scroll = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=txt.xview)
        txt.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # システム情報の取得
        sys_info = []
        sys_info.append(f"Timestamp: {datetime.datetime.now()}")
        sys_info.append(f"Python Version: {sys.version}")
        sys_info.append(f"Platform: {platform.platform()}")
        sys_info.append(f"CWD: {os.getcwd()}")
        sys_info.append(f"Executable: {sys.executable}")
        sys_info.append("-" * 40)

        full_log = "\n".join(sys_info) + "\n\n" + error_text

        txt.insert(tk.END, full_log)
        txt.config(state=tk.DISABLED) # 編集不可にする

        # クリップボードにコピーするボタン
        def copy_to_clipboard():
            root.clipboard_clear()
            root.clipboard_append(full_log)
            root.update() # クリップボードの更新を確実にする
            btn_copy.config(text="コピーしました！")
            root.after(2000, lambda: btn_copy.config(text="エラーログをクリップボードにコピー"))

        btn_copy = tk.Button(root, text="エラーログをクリップボードにコピー", command=copy_to_clipboard, height=2, bg="#ddd")
        btn_copy.pack(fill=tk.X, padx=10, pady=10)

        root.mainloop()
    except Exception as e:
        # このGUIすら起動しない場合の最終手段（標準エラー出力）
        print("CRITICAL ERROR: Failed to launch error GUI.", file=sys.stderr)
        print(e, file=sys.stderr)
        print("\nOriginal Error:", file=sys.stderr)
        print(error_text, file=sys.stderr)

# 実行パスの調整
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(os.path.dirname(current_dir))
    if src_dir not in sys.path:
        sys.path.append(src_dir)
except Exception:
    # ここでの失敗は稀だが、tracebackを表示するためにpassして後続のcatchで拾う
    pass

def main():
    try:
        # ここでインポートすることで、インポートエラーもキャッチできるようにする
        from src.text_cleaner.gui import TextCleanerApp

        root = tk.Tk()
        app = TextCleanerApp(root)
        root.mainloop()

    except Exception:
        # すべての例外をキャッチしてGUIで表示
        err_msg = traceback.format_exc()
        show_error_gui(err_msg)

if __name__ == "__main__":
    main()
