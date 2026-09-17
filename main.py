"""
Main entry point for Shogi desktop application.
"""

from src.shogi_app.gui.main_window import ShogiMainWindow

def main():
    app = ShogiMainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
