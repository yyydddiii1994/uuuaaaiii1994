# src/lector_ts_addon/optimizer.py

import sys
import time
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# --- Vendorizationのためのパス設定 ---
vendor_path = Path(__file__).parent / "vendor"
if str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))

# --- 依存関係のインポート ---
try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    torch, SentenceTransformer = None, None
    print(f"Error importing ML libraries: {e}")

try:
    from aqt import mw
except ImportError:
    mw = None


def check_gpu_availability():
    """GPUの可用性をチェックし、デバイス名を返す"""
    if torch:
        if torch.cuda.is_available():
            return True, f"利用可能なGPU: {torch.cuda.get_device_name(0)}", "cuda"
        if torch.backends.mps.is_available():
            return True, "利用可能なGPU: Apple MPS", "mps"
    return False, "CUDA/MPS対応GPUが見つかりません。CPUで処理します（低速）。", "cpu"

def get_anki_data():
    """Ankiデータベースからデータを取得する"""
    if not mw or not mw.col: return pd.DataFrame(), pd.DataFrame()
    db_path = mw.col.path
    try:
        with sqlite3.connect(db_path) as con:
            revlog_df = pd.read_sql_query("SELECT * FROM revlog", con)
            query = "SELECT c.id as cid, n.sfld as question FROM cards c JOIN notes n ON c.nid = n.id"
            notes_df = pd.read_sql_query(query, con)
            return revlog_df, notes_df
    except Exception as e:
        print(f"Error accessing Anki database: {e}")
        return pd.DataFrame(), pd.DataFrame()

def preprocess_revlog(revlog_df):
    """revlogの基本的な前処理"""
    revlog_df['review_time'] = pd.to_datetime(revlog_df['id'], unit='ms')
    return revlog_df.sort_values(by='id').reset_index(drop=True)

def add_contextual_features(revlog_df, progress_callback):
    """時間的文脈に基づいた特徴量を追加する"""
    progress_callback("文脈的特徴量を追加中...")
    df = revlog_df.sort_values(by=['cid', 'review_time'])
    time_diff = df.groupby('cid')['review_time'].diff()
    df['sleep_flag'] = time_diff > pd.Timedelta(hours=8)
    new_session_starts = time_diff > pd.Timedelta(minutes=30)
    session_id = new_session_starts.groupby(df['cid']).cumsum().fillna(0)
    df['session_review_count'] = df.groupby(['cid', session_id]).cumcount() + 1
    progress_callback("文脈的特徴量の追加完了。")
    return df

def generate_semantic_features(notes_df, device, progress_callback):
    """セマンティック特徴量（埋め込み）を生成する"""
    if not SentenceTransformer:
        progress_callback("エラー: SentenceTransformersライブラリがありません。")
        return notes_df
    model_name = 'all-MiniLM-L6-v2'
    progress_callback(f"言語モデル ({model_name}) をロード中...")
    try:
        model = SentenceTransformer(model_name, device=device)
    except Exception as e:
        progress_callback(f"モデルのロードエラー: {e}")
        return notes_df
    progress_callback("カード内容をベクトルに変換中...")
    texts = notes_df['question'].fillna('').astype(str).tolist()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    notes_df['embedding'] = list(embeddings)
    progress_callback("セマンティック特徴量の生成完了。")
    return notes_df

def integrate_features(revlog_df, notes_df, progress_callback):
    """revlogとnotesのデータフレームを統合する"""
    progress_callback("内容特徴量と文脈特徴量を統合中...")

    # notes_dfから必要なカラム（cidとembedding）のみを選択
    notes_with_embeddings = notes_df[['cid', 'embedding']]

    # revlog_dfにマージ
    # how='left'で、レビュー履歴は全て残し、対応するカードのembeddingを追加
    integrated_df = pd.merge(revlog_df, notes_with_embeddings, on='cid', how='left')

    # embeddingが見つからなかったレビュー（カードが削除された場合など）の処理
    # とりあえずベクトルの次元数に合わせてゼロで埋める
    embedding_dim = len(notes_with_embeddings['embedding'].iloc[0])
    integrated_df['embedding'] = integrated_df['embedding'].apply(
        lambda x: x if isinstance(x, np.ndarray) else np.zeros(embedding_dim)
    )

    progress_callback("特徴量の統合完了。")
    return integrated_df

def prepare_sequences_for_model(integrated_df, progress_callback):
    """時系列モデルの入力用にシーケンスデータを準備する（プレースホルダー）"""
    progress_callback("モデル入力用にデータをシーケンス化中...")

    # 将来的な実装:
    # - データをカードごとにグループ化
    # - 各グループをレビューの時系列シーケンスに変換
    # - テンソル形式に変換し、パディングなどを行う

    num_sequences = integrated_df['cid'].nunique()
    progress_callback(f"準備完了: {num_sequences:,}個のカードシーケンスがモデルに入力されます。")
    return integrated_df # 現状はそのまま返す


def start_optimization(progress_callback=None):
    """最適化プロセスのエントリーポイント"""
    def report_progress(message):
        print(message)
        if progress_callback: progress_callback(message)

    report_progress("最適化プロセスを開始しました...")

    # --- ステップ 1: ハードウェアチェック ---
    _, gpu_message, device = check_gpu_availability()
    report_progress(f"ハードウェアチェック: {gpu_message}")

    # --- ステップ 2: データ抽出と前処理 ---
    report_progress("ステップ 1/5: データベースからデータを抽出中...")
    revlog_df, notes_df = get_anki_data()
    if revlog_df.empty or notes_df.empty:
        report_progress("エラー: データが見つかりません。")
        return False
    report_progress(f"抽出完了: {len(revlog_df):,}件のレビュー, {len(notes_df):,}件のノート")
    revlog_df = preprocess_revlog(revlog_df)

    # --- ステップ 3: 特徴量エンジニアリング ---
    report_progress("ステップ 2/5: 文脈的特徴量を生成中...")
    revlog_df = add_contextual_features(revlog_df, report_progress)

    report_progress("ステップ 3/5: セマンティック特徴量を生成中...")
    notes_df = generate_semantic_features(notes_df, device, report_progress)
    if 'embedding' not in notes_df.columns:
        report_progress("セマンティック分析に失敗しました。")
        return False

    # --- ステップ 4: 特徴量の統合とデータ準備 ---
    report_progress("ステップ 4/5: 全特徴量を統合し、モデル入力データを準備中...")
    final_df = integrate_features(revlog_df, notes_df, report_progress)
    model_input_data = prepare_sequences_for_model(final_df, report_progress)

    print("Sample of final integrated data:")
    print(model_input_data.head())
    time.sleep(1)

    # --- ステップ 5: モデルファインチューニング（シミュレーション） ---
    report_progress("ステップ 5/5: RWKVモデルのファインチューニングを開始します...")
    time.sleep(5)
    report_progress("ファインチューニング完了！（シミュレーション）")

    report_progress("完了！パーソナライズドモデルが構築されました。")
    return True
