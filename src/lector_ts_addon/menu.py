# src/lector_ts_addon/menu.py

import sys
from pathlib import Path

# --- Vendorizationのためのパス設定 ---
# __init__.pyと同様に、アドオン内のvendorディレクトリへのパスを通す
vendor_path = Path(__file__).parent / "vendor"
if str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))

# --- 依存関係のインポート ---
try:
    from aqt import mw
    from aqt.qt import QAction
    from .settings_dialog import LectorTSSettingsDialog
except ImportError:
    # Anki環境外での実行を考慮
    mw = None
    QAction = None
    LectorTSSettingsDialog = None


def show_settings_dialog():
    """設定ダイアログを表示する関数"""
    if mw and LectorTSSettingsDialog:
        # 既存のインスタンスがあればそれを使い、なければ新しく作成する
        if not hasattr(mw, "lector_ts_settings_dialog"):
            mw.lector_ts_settings_dialog = LectorTSSettingsDialog(mw)

        # ダイアログを表示
        mw.lector_ts_settings_dialog.show()
        mw.lector_ts_settings_dialog.raise_()
        mw.lector_ts_settings_dialog.activateWindow()


def setup_menu():
    """Ankiのツールメニューに設定項目を追加する"""
    if mw and QAction:
        # 1. メニューアクションの作成
        action = QAction("LECTOR-TS Optimizer...", mw)

        # 2. アクションがトリガーされた時に呼び出す関数を設定
        action.triggered.connect(show_settings_dialog)

        # 3. Ankiのメインウィンドウの「ツール」メニューにアクションを追加
        if hasattr(mw, "form") and hasattr(mw.form, "menuTools"):
             mw.form.menuTools.addSeparator()
             mw.form.menuTools.addAction(action)
