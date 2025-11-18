# src/lector_ts_addon/scheduler.py

import sys
import os
import time
import torch
import numpy as np
import pandas as pd
from pathlib import Path

# --- Vendorizationのためのパス設定 ---
vendor_path = Path(__file__).parent / "vendor"
if str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))

# --- 依存関係のインポート ---
try:
    from aqt import mw, gui_hooks
    from anki.cards import Card
    from .model import LectorTSModel
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    mw, gui_hooks, Card, LectorTSModel, SentenceTransformer = None, None, None, None, None
    print(f"Error importing modules: {e}")

# --- グローバル変数 ---
# モデルはAnki起動時に一度だけロードし、メモリに保持する
g_lector_model = None
g_sentence_model = None
g_device = "cpu"

def initialize_inference_models():
    """推論に必要なモデルをファイルからロードし、グローバル変数に格納する"""
    global g_lector_model, g_sentence_model, g_device

    if not mw or not LectorTSModel or not SentenceTransformer: return

    # 1. デバイスを決定
    if torch.cuda.is_available(): g_device = "cuda"
    elif torch.backends.mps.is_available(): g_device = "mps"

    # 2. パーソナライズドモデルをロード
    profile_folder = mw.pm.profileFolder()
    model_path = os.path.join(profile_folder, "lector_ts_data", "lector_ts_model.pth")

    if os.path.exists(model_path):
        try:
            # 入力次元数は保存されていないため、ダミー値で初期化し、state_dictから復元する
            # 埋め込み(384) + 文脈(2) = 386
            input_dim = 386
            g_lector_model = LectorTSModel(input_dim=input_dim, output_dim=1)
            g_lector_model.load_state_dict(torch.load(model_path, map_location=g_device))
            g_lector_model.to(g_device)
            g_lector_model.eval() # 推論モードに設定
            print(f"LECTOR-TS model loaded from {model_path}")
        except Exception as e:
            print(f"Error loading LECTOR-TS model: {e}")
            g_lector_model = None

    # 3. テキスト埋め込み用のSentenceTransformerをロード
    try:
        model_name = 'all-MiniLM-L6-v2'
        g_sentence_model = SentenceTransformer(model_name, device=g_device)
        print(f"SentenceTransformer model '{model_name}' loaded.")
    except Exception as e:
        print(f"Error loading SentenceTransformer model: {e}")
        g_sentence_model = None

def get_last_review_time(card_id):
    """指定されたカードIDの前回のレビュー時刻を取得する"""
    if not mw: return None
    # revlogから最新のレビューを取得 (現在のレビューを除く)
    query = "SELECT id FROM revlog WHERE cid = ? ORDER BY id DESC LIMIT 1"
    res = mw.col.db.first(query, card_id)
    return pd.to_datetime(res[0], unit='ms') if res else None

def predict_next_interval(card: Card) -> float:
    """現在のカードの状態から次の最適な間隔を予測する"""
    if not g_lector_model or not g_sentence_model:
        return None # モデルがなければ何もしない

    with torch.no_grad(): # 勾配計算をオフにし、推論を高速化
        # 1. セマンティック特徴量の生成
        question_text = card.question()
        embedding = g_sentence_model.encode(question_text, convert_to_tensor=True, device=g_device)
        embedding = embedding.cpu().numpy()

        # 2. 文脈的特徴量の生成
        last_review_time = get_last_review_time(card.id)
        current_time = pd.Timestamp.now()

        sleep_flag = 0.0
        if last_review_time:
            time_diff = current_time - last_review_time
            if time_diff > pd.Timedelta(hours=8):
                sleep_flag = 1.0

        # セッション内レビュー回数は単純化のため1とする
        session_review_count = 1.0

        contextual_features = np.array([sleep_flag, session_review_count])

        # 3. 特徴量の結合とテンソル化
        features = np.concatenate([embedding, contextual_features])
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(g_device)

        # 4. モデルによる推論
        predicted_ivl = g_lector_model(features_tensor)

        # 5. 結果の抽出
        return predicted_ivl.item()

def on_scheduler_did_answer(scheduler, card: Card, ease: int):
    """ユーザーが回答ボタンを押した直後に呼び出されるフック関数"""
    predicted_ivl = predict_next_interval(card)

    if predicted_ivl is not None:
        new_interval = max(1, int(round(predicted_ivl))) # 1日未満にはしない

        print("-" * 30)
        print("LECTOR-TS Inference:")
        print(f"  Card ID: {card.id}")
        print(f"  Default Interval: {card.ivl} -> (Anki would calculate new)")
        print(f"  Predicted Interval: {predicted_ivl:.2f} days")
        print(f"  Setting New Interval to: {new_interval} days")
        print("-" * 30)

        # --- ここがスケジューラ介入の核心 ---
        # Ankiのスケジューラが計算した値を上書きする
        card.ivl = new_interval
    else:
        # モデルがない場合はログだけ表示
        print("LECTOR-TS: No model found, using default Anki scheduler.")

def register_scheduler_hooks():
    """アドオンのスケジューリング関連フックをAnkiに登録する"""
    if gui_hooks:
        initialize_inference_models()
        gui_hooks.scheduler_did_answer_card.append(on_scheduler_did_answer)
        print("LECTOR-TS scheduler hooks registered.")
