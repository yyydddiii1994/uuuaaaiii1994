import sys
import ctypes
import tkinter as tk
from tkinter import messagebox
from logic import BackupManager
from gui import AppGui

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )

def main():
    # Ensure High DPI awareness for Windows
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    # Check Admin Privileges
    # On non-Windows platforms (testing), we skip this
    import platform
    if platform.system() == "Windows":
        if not is_admin():
            # Create a hidden root just to show the message box if needed,
            # or just attempt to elevate immediately.
            # Usually better to try elevate immediately.
            try:
                run_as_admin()
            except Exception as e:
                # If user cancels UAC
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("権限エラー", "このツールは管理者権限で実行する必要があります。\n(シンボリックリンク作成のため)")
            return

    root = tk.Tk()

    # Initialize Manager
    logic = BackupManager()

    # Launch GUI
    app = AppGui(root, logic)

    root.mainloop()

if __name__ == "__main__":
    main()
