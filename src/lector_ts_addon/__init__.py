# src/lector_ts_addon/__init__.py

import sys
from pathlib import Path

# --- Step 1: Vendorization（最重要） ---
vendor_path = Path(__file__).parent / "vendor"
if str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))

# --- Step 2: アドオン機能の初期化 ---
try:
    from aqt import mw
except ImportError:
    mw = None

if mw:
    from aqt import gui_hooks

    # --- オプティマイザ機能の初期化 ---
    # UI（メニュー項目）関連のモジュールをインポート
    from . import menu
    # Ankiのメインウィンドウが初期化された後、メニュー項目をセットアップ
    gui_hooks.main_window_did_init.append(menu.setup_menu)

    # --- スケジューラ機能の初期化 ---
    # 推論（スケジューリング介入）関連のモジュールをインポート
    from . import scheduler
    # Ankiのプロファイルがロードされた後（= データベースにアクセス可能になった後）、
    # スケジューラのフックを登録し、推論モデルをロードする
    gui_hooks.profile_did_open.append(scheduler.register_scheduler_hooks)

    print("LECTOR-TS Addon (Optimizer & Scheduler) Initialized.")
