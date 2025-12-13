import tkinter as tk
import sys
import os

# Add the project root to sys.path to allow relative imports to work
# when running this script directly.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.steam_stat_viewer.gui import SteamStatApp

def main():
    root = tk.Tk()
    app = SteamStatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
