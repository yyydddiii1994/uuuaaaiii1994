import sys
import traceback
import tkinter as tk
from tkinter import scrolledtext

def show_error_gui(error_msg):
    """
    Fallback GUI to display errors when the main application fails to start.
    """
    root = tk.Tk()
    root.title("起動エラー - Google Search Scraper")
    root.geometry("600x400")

    label = tk.Label(root, text="アプリケーションの起動中にエラーが発生しました。\n以下のログを確認してください。", fg="red", pady=10)
    label.pack()

    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    text_area.pack(expand=True, fill='both', padx=10, pady=10)
    text_area.insert(tk.END, error_msg)
    text_area.config(state='disabled')

    btn = tk.Button(root, text="閉じる", command=root.destroy)
    btn.pack(pady=10)

    root.mainloop()

def main():
    try:
        # Import the GUI module here to catch import errors
        from gui import ScraperGUI

        root = tk.Tk()
        app = ScraperGUI(root)
        root.mainloop()

    except Exception:
        # Catch any exception during startup (ImportError, SyntaxError, etc.)
        error_msg = traceback.format_exc()
        print("Fatal Error detected. Launching Fallback GUI.")
        print(error_msg)
        show_error_gui(error_msg)

if __name__ == "__main__":
    main()
