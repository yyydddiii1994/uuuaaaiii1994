import tkinter as tk
from tkinter import ttk
import sys
import os
import traceback
import platform
import datetime

# Add the project root to sys.path to allow relative imports to work
# when running this script directly.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.steam_stat_viewer.gui import SteamStatApp
except ImportError as e:
    # If imports fail here, we need to handle it in the main block
    # But strictly speaking, main() hasn't started.
    # We will let the main try/except catch this if we move imports inside,
    # or rely on the fact that if this fails, the script crashes before main.
    # To be "forced startup", we should probably import inside main or try/except here.
    pass

def generate_detailed_log(traceback_str):
    """Generates a detailed system report with the traceback."""
    log = []
    log.append("=" * 60)
    log.append(f"CRITICAL ERROR REPORT - {datetime.datetime.now().isoformat()}")
    log.append("=" * 60)

    log.append(f"\n[System Information]")
    log.append(f"OS Platform: {platform.platform()}")
    log.append(f"Python Version: {sys.version}")
    log.append(f"Executable: {sys.executable}")
    log.append(f"Working Directory: {os.getcwd()}")
    log.append(f"Script Path: {os.path.abspath(__file__)}")

    log.append(f"\n[Traceback]")
    log.append(traceback_str)

    log.append(f"\n[Environment Variables]")
    for k, v in sorted(os.environ.items()):
        # Sanitize sensitive keys
        if any(s in k.upper() for s in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'CREDENTIAL']):
            log.append(f"{k}: ********")
        else:
            log.append(f"{k}: {v}")

    return "\n".join(log)

def show_error_gui(error_msg):
    """
    Attempts to show a fallback GUI with the error message.
    If GUI creation fails, falls back to printing to stderr/file.
    """
    try:
        # We try to create a new root window
        err_root = tk.Tk()
        err_root.title("Steam Stat Viewer - Error Report")
        err_root.geometry("900x700")

        # Style
        style = ttk.Style()
        style.theme_use('default')

        container = ttk.Frame(err_root, padding=10)
        container.pack(fill="both", expand=True)

        lbl_header = ttk.Label(
            container,
            text="アプリケーション起動時または実行中に重大なエラーが発生しました。\n以下のログを確認してください。",
            foreground="red",
            font=("Helvetica", 12, "bold")
        )
        lbl_header.pack(pady=(0, 10))

        # Text area with scrollbar
        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_area = tk.Text(text_frame, wrap="none", yscrollcommand=scrollbar.set, font=("Consolas", 10))
        text_area.pack(side="left", fill="both", expand=True)
        text_area.insert("1.0", error_msg)
        text_area.config(state="disabled") # Read-only

        scrollbar.config(command=text_area.yview)

        # Bottom buttons
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill="x", pady=10)

        def copy_log():
            err_root.clipboard_clear()
            err_root.clipboard_append(error_msg)
            tk.messagebox.showinfo("Copied", "ログをクリップボードにコピーしました。")

        def close_app():
            err_root.destroy()
            sys.exit(1)

        btn_copy = ttk.Button(btn_frame, text="ログをコピー (Copy Log)", command=copy_log)
        btn_copy.pack(side="left", padx=5)

        btn_close = ttk.Button(btn_frame, text="終了 (Exit)", command=close_app)
        btn_close.pack(side="right", padx=5)

        # Make sure this window is on top
        err_root.lift()
        err_root.attributes('-topmost', True)
        err_root.after_idle(err_root.attributes, '-topmost', False)

        err_root.mainloop()

    except Exception as gui_e:
        # If GUI fails, we have no choice but to print to console/file
        fallback_msg = f"!!! FAILED TO LAUNCH ERROR GUI !!!\n{gui_e}\n\nORIGINAL ERROR:\n{error_msg}"
        print(fallback_msg, file=sys.stderr)

        try:
            with open("FATAL_ERROR.log", "w", encoding="utf-8") as f:
                f.write(fallback_msg)
        except:
            pass
        sys.exit(1)

def main():
    try:
        # Late import to catch import errors inside the try block
        from src.steam_stat_viewer.gui import SteamStatApp

        root = tk.Tk()

        # Override the default exception handler for Tkinter callbacks
        def report_callback_exception(exc_type, exc_value, exc_traceback):
            err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            detailed = generate_detailed_log(err_msg)
            # Destroy old root to clean up
            try:
                root.destroy()
            except:
                pass
            show_error_gui(detailed)

        root.report_callback_exception = report_callback_exception

        app = SteamStatApp(root)
        root.mainloop()

    except Exception:
        # Catch errors during startup (before mainloop)
        err_msg = traceback.format_exc()
        detailed = generate_detailed_log(err_msg)
        show_error_gui(detailed)

if __name__ == "__main__":
    main()
