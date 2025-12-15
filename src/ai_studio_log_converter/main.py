import tkinter as tk
from gui import ConverterGUI

def main():
    root = tk.Tk()
    # Set icon if available, otherwise ignore
    # root.iconbitmap("icon.ico")
    app = ConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
