import tkinter as tk
from src.google_maps_scraper.gui import ScraperApp
import sys
import os

# Add src to sys.path to ensure modules can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def main():
    try:
        root = tk.Tk()
        # アイコンなどの設定があればここで行う
        app = ScraperApp(root)
        root.mainloop()
    except Exception as e:
        # GUI起動失敗時のフォールバック (ログ出力など)
        print(f"Failed to start GUI: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
