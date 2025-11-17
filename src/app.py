# src/app.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QSplitter, QMenuBar, QFrame
)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    """The main window of the application."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Homepage Builder")
        self.setGeometry(100, 100, 1200, 800)

        self._create_menu_bar()
        self._create_main_layout()

    def _create_menu_bar(self):
        """Creates the main menu bar."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        # Add actions later (e.g., New, Open, Save)
        file_menu.addAction("New Project")
        file_menu.addAction("Open Project")
        file_menu.addAction("Save")
        file_menu.addSeparator()
        file_menu.addAction("Exit")


    def _create_main_layout(self):
        """Creates the main 3-pane layout using splitters."""
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Left Pane (Navigation) ---
        left_pane = QFrame()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Navigation / Pages"))
        left_pane.setLayout(left_layout)
        main_splitter.addWidget(left_pane)

        # --- Center/Right Splitter ---
        center_right_splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Center Pane (Canvas) ---
        center_pane = QFrame()
        center_layout = QVBoxLayout()
        center_layout.addWidget(QLabel("Visual Canvas (QWebEngineView will go here)"))
        center_pane.setLayout(center_layout)
        center_right_splitter.addWidget(center_pane)

        # --- Right Pane (Inspector) ---
        right_pane = QFrame()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Inspector / Style Editor"))
        right_pane.setLayout(right_layout)
        center_right_splitter.addWidget(right_pane)

        # Set initial sizes for the center/right panes
        center_right_splitter.setSizes([600, 200])

        main_splitter.addWidget(center_right_splitter)

        # Set initial sizes for the main panes
        main_splitter.setSizes([200, 1000])

        self.setCentralWidget(main_splitter)

def main():
    """The main entry point of the application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
