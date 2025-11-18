# src/lector_ts_addon/model.py

import sys
from pathlib import Path
import torch
import torch.nn as nn

# --- Vendorizationのためのパス設定 ---
vendor_path = Path(__file__).parent / "vendor"
if str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))

class LectorTSModel(nn.Module):
    """
    LECTOR-TSの予測モデルアーキテクチャ。
    Multi-Layer Perceptron (MLP) をベースとし、将来的にRWKVのような
    より複雑な時系列モデルに拡張するための基礎となる。
    """
    def __init__(self, input_dim, hidden_dim1=128, hidden_dim2=64, output_dim=2):
        """
        モデルの層を初期化する。

        Args:
            input_dim (int): 入力特徴量の次元数。
                             (embedding_dim + contextual_features_dim)
            hidden_dim1 (int): 1番目の隠れ層の次元数。
            hidden_dim2 (int): 2番目の隠れ層の次元数。
            output_dim (int): 出力次元数。デフォルトは2 (Stability, Difficulty)。
        """
        super(LectorTSModel, self).__init__()

        self.network = nn.Sequential(
            # 第1層: 入力層 -> 隠れ層1
            nn.Linear(input_dim, hidden_dim1),
            nn.ReLU(),  # 活性化関数
            nn.Dropout(0.3), # 過学習を防ぐためのドロップアウト層

            # 第2層: 隠れ層1 -> 隠れ層2
            nn.Linear(hidden_dim1, hidden_dim2),
            nn.ReLU(),
            nn.Dropout(0.3),

            # 第3層: 隠れ層2 -> 出力層
            nn.Linear(hidden_dim2, output_dim)
        )

    def forward(self, x):
        """
        フォワードパス（順伝播）の定義。
        入力テンソルxがネットワークをどのように流れるかを定義する。

        Args:
            x (torch.Tensor): 入力データ。形状は (batch_size, input_dim)。

        Returns:
            torch.Tensor: モデルの予測値。形状は (batch_size, output_dim)。
        """
        return self.network(x)

# --- テスト用の実行ブロック ---
if __name__ == '__main__':
    # モデルのインスタンス化とテスト
    # all-MiniLM-L6-v2 の埋め込み次元数(384) + 文脈特徴量の数(例: 2)
    INPUT_DIM = 384 + 2

    # モデルを作成
    model = LectorTSModel(input_dim=INPUT_DIM)
    print("Model architecture:")
    print(model)

    # ダミーの入力データを作成 (バッチサイズ=4)
    dummy_input = torch.randn(4, INPUT_DIM)
    print(f"\nDummy input shape: {dummy_input.shape}")

    # フォワードパスを実行
    output = model(dummy_input)
    print(f"Output shape: {output.shape}")
    print("Dummy output:")
    print(output)

    # モデルのパラメータ数を確認
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\nTotal trainable parameters: {total_params:,}")
