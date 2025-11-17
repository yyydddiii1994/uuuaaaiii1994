# src/main.py

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QTextEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView

# プロジェクト管理とHTML生成ロジックをインポート
from src.core import create_default_project, page_to_html


class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ。
    3ペインレイアウト（左：ナビゲーション、中央：キャンバス、右：インスペクタ）を持つ。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Web Builder")
        self.setGeometry(100, 100, 1600, 900)

        # デフォルトのプロジェクトデータをロード
        self.current_site = create_default_project()
        self.current_page = self.current_site.pages[0]

        # --- 3ペインレイアウトの実装 ---

        # 1. 左ペイン (ナビゲーション)
        self.left_pane = QTextEdit("左ペイン: ページ一覧や要素")
        self.left_pane.setMinimumWidth(200)

        # 2. 中央ペイン (ビジュアルキャンバス)
        self.canvas = QWebEngineView()
        # self.center_pane = QTextEdit("中央ペイン: Webプレビュー") # プレースホルダーを置き換え
        self.load_page_to_canvas() # ページをキャンバスに表示

        # 3. 右ペイン (インスペクタ)
        self.right_pane = QTextEdit("右ペイン: スタイル設定")
        self.right_pane.setMinimumWidth(240)

        # QSplitterを使って中央と右を分割
        right_splitter = QSplitter(Qt.Orientation.Horizontal)
        right_splitter.addWidget(self.canvas) # 中央ペインをcanvasに変更
        right_splitter.addWidget(self.right_pane)
        right_splitter.setSizes([1000, 200]) # 初期サイズの比率を調整

        # さらにQSplitterを使って左と(中央+右)を分割
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.left_pane)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([200, 1200]) # 初期サイズの比率を調整

        # メインウィンドウのセントラルウィジェットとして設定
        self.setCentralWidget(main_splitter)

    def load_page_to_canvas(self):
        """
        現在のページデータをHTMLに変換し、中央のQWebEngineViewに表示します。
        """
        html_content = page_to_html(self.current_page)
        self.canvas.setHtml(html_content)


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
