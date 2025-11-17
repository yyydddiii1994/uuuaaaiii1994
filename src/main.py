# src/main.py

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow

class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ。
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Web Builder")
        self.setGeometry(100, 100, 1200, 800) # x, y, width, height

def main():
    """
    アプリケーションのエントリーポイント。
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
