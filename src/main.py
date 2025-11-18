# src/main.py

import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QObject, pyqtSlot, QFile, QIODevice
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebChannel import QWebChannel

# プロジェクト管理とHTML生成ロジックをインポート
from src.core import create_default_project, page_to_html
from src.models import Element


# --- JavaScriptとの通信を受け持つバックエンドオブジェクト ---
class Backend(QObject):
    """
    JavaScriptからの呼び出しを受け取るためのクラス。
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    @pyqtSlot(str)
    def onElementClicked(self, element_id: str):
        """
        JavaScript側で要素がクリックされたときに呼び出される。
        """
        # print(f"Element clicked in web view, ID: {element_id}")
        self.main_window.select_element(element_id)


class WebEnginePage(QWebEnginePage):
    """
    コンソールログをPython側に表示するためのカスタムWebEnginePage。
    """
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"JS Console ({sourceID}:{lineNumber}): {message}")


class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ。
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Web Builder")
        self.setGeometry(100, 100, 1600, 900)

        # 状態管理
        self.current_site = create_default_project()
        self.current_page = self.current_site.pages[0]
        self.selected_element: Element | None = None

        # --- JavaScriptブリッジのセットアップ ---
        self.backend = Backend(self)
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.backend)

        # --- 3ペインレイアウトの実装 ---
        self.left_pane = QTextEdit("左ペイン: ページ一覧や要素")
        self.left_pane.setMinimumWidth(200)

        self.canvas = QWebEngineView()
        self.page = WebEnginePage(self.canvas)
        self.page.setWebChannel(self.channel)
        self.canvas.setPage(self.page)

        self.right_pane = QTextEdit("右ペイン: スタイル設定")
        self.right_pane.setMinimumWidth(240)

        right_splitter = QSplitter(Qt.Orientation.Horizontal)
        right_splitter.addWidget(self.canvas)
        right_splitter.addWidget(self.right_pane)
        right_splitter.setSizes([1000, 200])

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.left_pane)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([200, 1200])
        self.setCentralWidget(main_splitter)

        # ページ読み込み完了時のシグナルに接続
        self.page.loadFinished.connect(self.on_load_finished)

        # ページをキャンバスにロード開始
        self.load_page_to_canvas()


    def load_page_to_canvas(self):
        """
        現在のページデータをHTMLに変換し、中央のQWebEngineViewに表示します。
        """
        # qwebchannel.jsのパスを解決
        from PyQt6.QtWebEngineCore import QWebEngineProfile
        js_path = os.path.join(
            os.path.dirname(QWebEngineProfile.__file__),
            "qt_webengine/qwebchannel.js"
        )
        qwebchannel_js_uri = f"file:///{js_path.replace(os.sep, '/')}"

        html_content = page_to_html(self.current_page, qwebchannel_js_uri)
        self.canvas.setHtml(html_content, baseUrl=Qt.QtCore.QUrl("file:///"))

    def on_load_finished(self, ok):
        """
        ページの読み込みが完了した後に呼ばれ、JSブリッジを注入する。
        """
        if ok:
            js_file = QFile("src/bridge.js")
            if js_file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
                js_code = js_file.readAll().data().decode("utf-8")
                self.page.runJavaScript(js_code)
                print("bridge.js injected and executed.")
            else:
                print("Error: Could not open src/bridge.js")

    def select_element(self, element_id: str):
        """
        要素IDに基づいて要素を選択し、UIを更新する。
        """
        if self.selected_element and self.selected_element.element_id == element_id:
            return # 同じ要素が再度クリックされた場合は何もしない

        element = self.current_page.find_element_by_id(element_id)
        if element:
            self.selected_element = element
            print(f"Selected element: <{element.element_type}> with ID: {element.element_id}")

            # 1. 右ペイン（インスペクタ）の表示を更新
            self.update_inspector()

            # 2. Webプレビュー上の要素をハイライトするようJSに指示
            self.page.runJavaScript(f"window.highlightElement('{element_id}');")
        else:
            self.selected_element = None
            print(f"Element with ID {element_id} not found in data model.")
            self.update_inspector()

    def update_inspector(self):
        """
        右ペイン（インスペクタ）の表示を現在の選択要素に基づいて更新する。
        """
        if self.selected_element:
            info_text = f"選択中の要素:\n\n"
            info_text += f"タイプ: {self.selected_element.element_type}\n"
            info_text += f"ID: {self.selected_element.element_id}"
            self.right_pane.setText(info_text)
        else:
            self.right_pane.setText("要素が選択されていません。")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
