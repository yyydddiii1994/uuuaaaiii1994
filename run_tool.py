import sys
import os

# Add the src directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.crowdworks_tool.main import CrowdWorksToolApp
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = CrowdWorksToolApp(root)
    root.mainloop()
