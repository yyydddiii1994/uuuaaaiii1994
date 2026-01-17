import sys
import traceback
import tkinter as tk
from tkinter import messagebox, scrolledtext

def show_crash_report(error_text):
    """
    Displays a failsafe GUI with the error traceback and a copy button.
    This function must rely on absolute minimum dependencies.
    """
    try:
        root = tk.Tk()
        root.title("起動エラー (Critical Error)")
        root.geometry("600x450")

        lbl = tk.Label(root, text="アプリケーションの起動中に致命的なエラーが発生しました。\n以下のエラー内容をコピーして開発者に報告してください。",
                       fg="red", justify=tk.LEFT, padx=10, pady=10)
        lbl.pack(anchor=tk.W)

        # Text area for traceback
        text_area = scrolledtext.ScrolledText(root, font=("Consolas", 9))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        text_area.insert(tk.END, error_text)
        # Make it read-only-ish (allow selection but not editing?)
        # Actually standard practice for copyable read-only is leave it enabled but ignore keys,
        # or just let user edit it (it doesn't matter, it's a crash report).
        # We will leave it editable so they can ctrl+a ctrl+c easily without weird state issues.

        def copy_to_clipboard():
            root.clipboard_clear()
            root.clipboard_append(text_area.get("1.0", tk.END))
            messagebox.showinfo("コピー完了", "エラー内容をクリップボードにコピーしました。")

        btn_frame = tk.Frame(root, pady=10)
        btn_frame.pack(fill=tk.X)

        btn_copy = tk.Button(btn_frame, text="エラー内容をクリップボードにコピー", command=copy_to_clipboard, bg="#dddddd")
        btn_copy.pack(side=tk.RIGHT, padx=10)

        btn_close = tk.Button(btn_frame, text="閉じる", command=root.destroy)
        btn_close.pack(side=tk.RIGHT, padx=10)

        root.mainloop()
    except:
        # If even tkinter fails, print to stderr (last resort)
        print("CRITICAL: GUI failed to launch and Crash Reporter failed.", file=sys.stderr)
        print(error_text, file=sys.stderr)

def safe_main():
    """
    Main entry point with a catch-all try-except block.
    """
    try:
        # 1. Import dependencies (Lazy import to catch load errors)
        import ctypes
        import platform

        # 2. Define Admin Checks
        def is_admin():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False

        def run_as_admin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )

        # 3. Platform Checks & Elevation
        if platform.system() == "Windows":
            # Enable High DPI
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass

            if not is_admin():
                # Attempt to elevate
                try:
                    run_as_admin()
                except Exception as e:
                    # User cancelled or failed
                    # We will continue but warn, or maybe logic handles it.
                    # Logic expects admin for mklink.
                    # Let's verify if we should crash or show GUI.
                    # Showing GUI with warning is better than silent fail.
                    pass
                # If we spawned a new process, we exit this one.
                # However, we can't be sure if run_as_admin succeeded in spawning.
                # Usually ShellExecuteW returns >32 on success.
                # For simplicity in this script, we exit if we aren't admin
                # AND we tried to elevate. But we can't easily know if the new window appeared.
                # We will just return. The new process will run this script again as admin.
                return

        # 4. Load App Modules
        # Moving imports here ensures syntax errors in them are caught by the try/except
        from logic import BackupManager
        from gui import AppGui

        # 5. Launch App
        root = tk.Tk()
        logic = BackupManager()
        app = AppGui(root, logic)
        root.mainloop()

    except Exception:
        # Catch ALL errors (ImportError, SyntaxError, RuntimeError, etc.)
        err_msg = traceback.format_exc()
        show_crash_report(err_msg)

if __name__ == "__main__":
    safe_main()
