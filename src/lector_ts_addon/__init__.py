# src/lector_ts_addon/__init__.py

import sys
from pathlib import Path

# --- Step 1: Vendorization（最重要） ---
# このアドオンが依存するライブラリ群が格納されている'vendor'ディレクトリへのパスを取得します。
# pathlibを使って、この__init__.pyファイルが存在するディレクトリからの相対パスで指定します。
vendor_path = Path(__file__).parent / "vendor"

# sys.path（Pythonがモジュールを検索する際のパスリスト）に、
# vendorディレクトリのパスがまだ含まれていない場合、リストの先頭に追加します。
# これにより、Anki本体や他のアドオンが使用するライブラリよりも先に、
# 我々が同梱したライブラリ（torch, transformersなど）が優先的に読み込まれるようになります。
# これが、ユーザーにpip installを要求せずに複雑な依存関係を解決する鍵となります。
if str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))

# --- Step 2: アドオン機能の初期化 ---
# aqt.mw (Ankiのメインウィンドウオブジェクト) が存在するかどうかを確認します。
# これが存在しない場合、AnkiがGUIなしで実行されている（例: ターミナルからのテスト実行）
# ことを意味するため、UI関連のコードは実行しないようにします。
# これにより、アドオンのテスト容易性が向上します。
try:
    from aqt import mw
except ImportError:
    mw = None

if mw:
    # AnkiのGUI環境で実行されている場合のみ、メニュー設定用のモジュールをインポートします。
    from . import menu

    # Ankiの起動が完了した後にメニュー設定を実行するためのフックを設定します。
    # gui_hooks.main_window_did_initフックは、メインウィンドウの準備が整った後に呼び出されます。
    from aqt import gui_hooks
    gui_hooks.main_window_did_init.append(menu.setup_menu)

print("LECTOR-TS Addon Initialized.")
