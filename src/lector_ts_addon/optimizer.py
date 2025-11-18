# src/lector_ts_addon/optimizer.py

import sys
import time
import sqlite3
import os
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
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    from sentence_transformers import SentenceTransformer
    from .model import LectorTSModel
except ImportError as e:
    torch, nn, Dataset, DataLoader, SentenceTransformer, LectorTSModel = None, None, None, None, None, None
    print(f"Error importing ML libraries: {e}")

try:
    from aqt import mw
except ImportError:
    mw = None

# --- PyTorch Dataset ---
class ReviewDataset(Dataset):
    def __init__(self, dataframe):
        contextual_features = dataframe[['sleep_flag', 'session_review_count']].astype(float).values
        embeddings = np.stack(dataframe['embedding'].values)
        self.X = np.concatenate([embeddings, contextual_features], axis=1)
        self.y = dataframe[['ivl']].astype(float).values

        self.X = torch.tensor(self.X, dtype=torch.float32)
        self.y = torch.tensor(self.y, dtype=torch.float32)

    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return self.X[idx], self.y[idx]

# --- Helper Functions ---
def check_gpu_availability():
    if torch:
        if torch.cuda.is_available(): return True, f"利用GPU: {torch.cuda.get_device_name(0)}", "cuda"
        if torch.backends.mps.is_available(): return True, "利用GPU: Apple MPS", "mps"
    return False, "CUDA/MPS対応GPUが見つかりません。CPUで処理します。", "cpu"

def get_anki_data():
    if not mw or not mw.col: return pd.DataFrame(), pd.DataFrame()
    db_path = mw.col.path
    try:
        with sqlite3.connect(db_path) as con:
            revlog_df = pd.read_sql_query("SELECT * FROM revlog", con)
            query = "SELECT c.id as cid, n.sfld as question FROM cards c JOIN notes n ON c.nid = n.id"
            notes_df = pd.read_sql_query(query, con)
            return revlog_df, notes_df
    except Exception as e:
        print(f"Error accessing Anki database: {e}"); return pd.DataFrame(), pd.DataFrame()

def preprocess_revlog(df):
    df['review_time'] = pd.to_datetime(df['id'], unit='ms')
    return df.sort_values(by='id').reset_index(drop=True)

def add_contextual_features(df, progress_callback):
    progress_callback("文脈的特徴量を追加中...")
    df = df.sort_values(by=['cid', 'review_time'])
    time_diff = df.groupby('cid')['review_time'].diff()
    df['sleep_flag'] = time_diff > pd.Timedelta(hours=8)
    new_session_starts = time_diff > pd.Timedelta(minutes=30)
    session_id = new_session_starts.groupby(df['cid']).cumsum().fillna(0)
    df['session_review_count'] = df.groupby(['cid', session_id]).cumcount() + 1
    progress_callback("文脈的特徴量の追加完了。")
    return df

def generate_semantic_features(df, device, progress_callback):
    if not SentenceTransformer: return df
    model_name = 'all-MiniLM-L6-v2'
    progress_callback(f"言語モデル ({model_name}) をロード中...")
    try:
        model = SentenceTransformer(model_name, device=device)
    except Exception as e:
        progress_callback(f"モデルのロードエラー: {e}"); return df
    progress_callback("カード内容をベクトルに変換中...")
    texts = df['question'].fillna('').astype(str).tolist()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    df['embedding'] = list(embeddings)
    progress_callback("セマンティック特徴量の生成完了。")
    return df

def integrate_features(revlog_df, notes_df, progress_callback):
    progress_callback("内容特徴量と文脈特徴量を統合中...")
    notes_with_embeddings = notes_df[['cid', 'embedding']]
    integrated_df = pd.merge(revlog_df, notes_with_embeddings, on='cid', how='left')
    integrated_df.dropna(subset=['embedding'], inplace=True)
    progress_callback("特徴量の統合完了。")
    return integrated_df

def create_dataloader(df, progress_callback):
    progress_callback("モデル学習用のデータローダーを作成中...")
    dataset = ReviewDataset(df)
    if len(dataset) == 0: return None
    batch_size = min(128, len(dataset))
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    progress_callback(f"データローダー作成完了。 (データ数: {len(dataset)}, バッチサイズ: {batch_size})")
    return dataloader

# --- Training Loop ---
def run_training_loop(dataloader, device, progress_callback):
    input_dim = dataloader.dataset.X.shape[1]
    output_dim = 1
    model = LectorTSModel(input_dim=input_dim, output_dim=output_dim).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    num_epochs = 5

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0.0
        for features, targets in dataloader:
            features, targets = features.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(dataloader)
        progress_callback(f"ファインチューニング中 (Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f})")

    progress_callback("ファインチューニング完了！")
    return model

# --- Main Entry Point ---
def start_optimization(progress_callback=None):
    def report_progress(message):
        print(message)
        if progress_callback: progress_callback(message)

    report_progress("最適化プロセスを開始しました...")
    _, gpu_message, device = check_gpu_availability()
    report_progress(f"ハードウェアチェック: {gpu_message}")

    report_progress("ステップ 1/5: データベースからデータを抽出中...")
    revlog_df, notes_df = get_anki_data()
    if revlog_df.empty or notes_df.empty:
        report_progress("エラー: データが見つかりません。"); return None
    revlog_df = preprocess_revlog(revlog_df)

    report_progress("ステップ 2/5: 文脈的特徴量を生成中...")
    revlog_df = add_contextual_features(revlog_df, report_progress)

    report_progress("ステップ 3/5: セマンティック特徴量を生成中...")
    notes_df = generate_semantic_features(notes_df, device, report_progress)
    if 'embedding' not in notes_df.columns:
        report_progress("セマンティック分析に失敗しました。"); return None

    report_progress("ステップ 4/5: 全特徴量を統合し、モデル入力データを準備中...")
    final_df = integrate_features(revlog_df, notes_df, report_progress)
    dataloader = create_dataloader(final_df, report_progress)
    if not dataloader:
        report_progress("学習データがありません。"); return None

    report_progress("ステップ 5/5: パーソナライズモデルのファインチューニングを開始します...")
    trained_model = run_training_loop(dataloader, device, report_progress)

    # --- モデルの保存 ---
    if trained_model and mw:
        report_progress("トレーニング済みモデルを保存中...")
        profile_folder = mw.pm.profileFolder()
        addon_data_folder = os.path.join(profile_folder, "lector_ts_data")
        os.makedirs(addon_data_folder, exist_ok=True)
        model_path = os.path.join(addon_data_folder, "lector_ts_model.pth")
        try:
            torch.save(trained_model.state_dict(), model_path)
            report_progress(f"モデルを {model_path} に保存しました。")
        except Exception as e:
            report_progress(f"モデルの保存中にエラーが発生しました: {e}")
            return None

    report_progress("完了！パーソナライズドモデルが構築されました。")
    return model_path if 'model_path' in locals() else None
