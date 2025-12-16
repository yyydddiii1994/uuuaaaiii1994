import tkinter as tk
import sys
import os

# 実行パスの調整 (srcディレクトリが見えるようにする)
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.text_cleaner.gui import TextCleanerApp

def main():
    root = tk.Tk()
    app = TextCleanerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
