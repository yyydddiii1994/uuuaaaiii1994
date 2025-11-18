# src/lector_ts_addon/settings_dialog.py

import sys
from pathlib import Path

# --- Vendorizationのためのパス設定 ---
vendor_path = Path(__file__).parent / "vendor"
if str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))

# --- 依存関係のインポート ---
try:
    from aqt.qt import (
        QDialog,
        QVBoxLayout,
        QPushButton,
        QLabel,
        QDialogButtonBox,
        Qt,
        QThread,
        pyqtSignal
    )
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QPushButton,
        QLabel,
        QDialogButtonBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal

# バックエンドの最適化ロジックをインポート
from . import optimizer

# --- バックグラウンド処理のためのワーカースレッド ---
class OptimizationWorker(QThread):
    """
    重い最適化処理をバックグラウンドで実行するためのワーカースレッド。
    AnkiのUIをフリーズさせないために必須。
    """
    # --- シグナルの定義 ---
    # progress_updated: 処理の進捗を文字列でUIスレッドに通知するシグナル
    progress_updated = pyqtSignal(str)
    # finished: 処理が完了したことを通知するシグナル
    finished = pyqtSignal()

    def run(self):
        """スレッドのメイン処理。start()が呼ばれると実行される。"""
        # optimizer.pyのstart_optimizationを呼び出し、
        # 進捗通知のコールバックとして、progress_updatedシグナルを発火させるラムダ関数を渡す。
        optimizer.start_optimization(
            progress_callback=lambda msg: self.progress_updated.emit(msg)
        )
        # 処理完了後、finishedシグナルを発火させる
        self.finished.emit()


class LectorTSSettingsDialog(QDialog):
    """LECTOR-TS用の設定ダイアログボックス"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LECTOR-TS Advanced Optimizer")
        self.setMinimumWidth(400)

        self.worker = None # ワーカースレッドを保持する変数

        # --- UI要素の作成 ---
        layout = QVBoxLayout(self)
        info_label = QLabel(
            "以下のボタンを押すと、あなたのレビュー履歴とカード内容を分析し、\n"
            "RTX 4070 GPUを活用してパーソナライズされた\n"
            "次世代スケジューリングモデルを構築します。\n"
            "（処理には数十分かかる場合があります）"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.optimize_button = QPushButton("圧倒的に最適化！ (ローカルRTX 4070を使用)")
        self.optimize_button.setStyleSheet("font-weight: bold; padding: 10px;")
        self.status_label = QLabel("待機中...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- レイアウトへのウィジェット追加 ---
        layout.addWidget(info_label)
        layout.addSpacing(20)
        layout.addWidget(self.optimize_button)
        layout.addWidget(self.status_label)
        layout.addSpacing(20)
        layout.addWidget(button_box)
        self.setLayout(layout)

        # --- シグナルとスロットの接続 ---
        self.optimize_button.clicked.connect(self.start_optimization_thread)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def start_optimization_thread(self):
        """「最適化」ボタンがクリックされたときに呼び出されるスロット"""
        # ボタンを無効化し、多重実行を防ぐ
        self.optimize_button.setEnabled(False)
        self.status_label.setText("初期化中...")

        # 1. ワーカースレッドのインスタンスを作成
        self.worker = OptimizationWorker()

        # 2. ワーカーからのシグナルをダイアログのスロットに接続
        self.worker.progress_updated.connect(self.update_status_label)
        self.worker.finished.connect(self.on_optimization_finished)

        # 3. スレッドを開始
        self.worker.start()

    def update_status_label(self, message):
        """ワーカースレッドからの進捗メッセージを受けてUIを更新するスロット"""
        self.status_label.setText(message)

    def on_optimization_finished(self):
        """最適化が完了したときに呼び出されるスロット"""
        self.status_label.setText("最適化が完了しました。")
        self.optimize_button.setEnabled(True)
        self.worker = None # ワーカースレッドの参照を破棄

    def closeEvent(self, event):
        """ダイアログが閉じられるときの処理"""
        # もしワーカースレッドが実行中なら、終了を試みる
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait() # 終了を待つ
        super().closeEvent(event)


# --- テスト用の実行ブロック ---
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = LectorTSSettingsDialog()
    dialog.show()
    sys.exit(app.exec())
