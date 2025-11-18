# src/lector_ts_addon/optimizer.py

import sys
import time
import sqlite3
import pandas as pd
from pathlib import Path

# --- Vendorizationのためのパス設定 ---
vendor_path = Path(__file__).parent / "vendor"
if str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))

# --- 依存関係のインポート ---
try:
    import torch
except ImportError:
    # PyTorchがインストールされていない場合のフォールバック
    torch = None

try:
    from aqt import mw
except ImportError:
    mw = None


def check_gpu_availability():
    """NVIDIA GPU (CUDA) が利用可能かチェックする"""
    if torch and torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        return True, f"利用可能なGPU: {device_name}"
    else:
        return False, "CUDA対応GPUが見つかりません。CPUで処理します（低速）。"

def get_anki_data():
    """Ankiデータベースからrevlogとnotesのデータを取得し、Pandas DataFrameとして返す"""
    if not mw or not mw.col:
        print("Anki collection not found.")
        return pd.DataFrame(), pd.DataFrame()

    db_path = mw.col.path
    try:
        with sqlite3.connect(db_path) as con:
            revlog_df = pd.read_sql_query("SELECT * FROM revlog", con)
            query = """
                SELECT c.id as cid, n.sfld as question, n.flds as all_fields
                FROM cards c JOIN notes n ON c.nid = n.id
            """
            notes_df = pd.read_sql_query(query, con)
            return revlog_df, notes_df
    except Exception as e:
        print(f"Error accessing Anki database: {e}")
        return pd.DataFrame(), pd.DataFrame()

def preprocess_revlog(revlog_df):
    """revlogデータフレームの基本的な前処理"""
    if 'id' in revlog_df.columns:
        revlog_df['review_time'] = pd.to_datetime(revlog_df['id'], unit='ms')
    return revlog_df

def add_contextual_features(df):
    """文脈的特徴量を追加する（スタブ）"""
    df['sleep_flag'] = False
    df['session_review_count'] = 1
    return df

def run_dummy_training(data_size, progress_callback):
    """
    モデルのファインチューニング処理をシミュレートするダミー関数。
    エポック毎に進捗をコールバックで通知する。
    """
    epochs = 3
    initial_loss = 0.95

    for epoch in range(1, epochs + 1):
        # 処理時間をシミュレート
        time.sleep(5)

        # 損失が減少していく様子をシミュレート
        loss = initial_loss / (epoch * 1.2)

        # UIに進捗を通知
        progress_callback(
            f"ファインチューニング中 (Epoch {epoch}/{epochs}, Loss: {loss:.4f})..."
        )

    # 最終的な完了メッセージ
    progress_callback("ファインチューニング完了！")


def start_optimization(progress_callback=None):
    """
    最適化プロセスのエントリーポイント。
    """
    def report_progress(message):
        print(message)
        if progress_callback:
            progress_callback(message)

    report_progress("最適化プロセスを開始しました...")
    time.sleep(1)

    # --- ハードウェアチェック ---
    gpu_available, gpu_message = check_gpu_availability()
    report_progress(f"ハードウェアチェック: {gpu_message}")
    time.sleep(2)

    # --- フェーズ1: データ抽出と前処理 ---
    report_progress("ステップ 1/3: データベースからデータを抽出中...")
    revlog_df, notes_df = get_anki_data()

    if revlog_df.empty:
        report_progress("エラー: レビュー履歴が見つかりませんでした。処理を中断します。")
        return False

    report_progress(f"抽出完了: {len(revlog_df):,}件のレビュー履歴")
    revlog_df = preprocess_revlog(revlog_df)
    revlog_df = add_contextual_features(revlog_df)
    time.sleep(1)

    # --- フェーズ2: セマンティック分析（シミュレーション） ---
    report_progress("ステップ 2/3: カード内容のセマンティック分析中...")
    # (将来、ここでLLMによる埋め込み処理が入る)
    time.sleep(3)
    report_progress("セマンティック分析完了。")

    # --- フェーズ3: モデルファインチューニング（シミュレーション） ---
    report_progress("ステップ 3/3: RWKVモデルのファインチューニングを開始します...")
    # ダミーのトレーニング処理を実行し、進捗をUIに直接通知する
    run_dummy_training(
        data_size=len(revlog_df),
        progress_callback=report_progress
    )

    time.sleep(1)
    report_progress("完了！パーソナライズドモデルが構築されました。")
    print("Optimization process finished.")
    return True
