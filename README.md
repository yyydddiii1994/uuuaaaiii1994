# Jules Shogi Engine (将棋エンジン)

これはPythonと`python-shogi`ライブラリを使用して作成された、USI (Universal Shogi Interface) プロトコル対応の将棋エンジンです。ShogiGUIなどの将棋ソフトに登録して対局させることができます。

## 特徴 (Features)

* **USIプロトコル対応**: 既存の将棋GUI（ShogiGUI、将棋所など）とシームレスに通信可能です。
* **アルファベータ法 (Alpha-Beta Pruning)**: 探索空間を効率的に削減し、より深く手を読みます。
* **PVS (Principal Variation Search)**: 主要変化探索。最善手と予想される手を最初に探索することで、それ以降の探索の枝刈り効率を飛躍的に高めます。
* **Null Move Pruning (空隙探索)**: 手番をパスしてもなお自分が有利な場合、その枝の探索を打ち切ることで計算時間を大幅に短縮します。
* **置換表 (Transposition Table)**: ゾブリストハッシュ(Zobrist Hashing)を用いて、一度計算した盤面の評価値をメモリに保存し、同一局面が現れた際に再計算を防ぎます。
* **静止探索 (Quiescence Search)**: 探索の深さ制限に達した際、駒の取り合いが続いている激しい局面での「水平線効果（悪い結果を先送りしてしまう現象）」を防ぐため、取り合いが落ち着くまで追加で探索を行います。
* **非同期時間管理**: 探索を別スレッドで実行することで、GUIからの`stop`コマンドを即座に受け付け、時間切れによる負けを防ぎます。

## ディレクトリ構成

* `main.py` : プログラムの実行エントリーポイント。
* `build_exe.py` : Windows用の実行ファイル（.exe）を作成するためのビルドスクリプト。
* `src/shogi_engine/engine.py` : 盤面の評価関数（駒の価値、駒の配置バランスなど）を定義しています。
* `src/shogi_engine/search.py` : アルファベータ法やPVSなどの探索アルゴリズムを担う心臓部です。
* `src/shogi_engine/usi.py` : GUIからのコマンド（usi, position, go, stopなど）を受信・応答するインターフェース部分です。

---

## 導入方法（ShogiGUIで動かすまで）

ShogiGUI等のソフトに登録するためには、**Windows用の実行ファイル（.exe）** が必要です。以下の手順に従って、ご自身のWindows PC上で`.exe`ファイルを作成してください。

### 1. 必要な環境の準備
Windows PCにPythonがインストールされている必要があります。
インストールされていない場合は、[Python公式サイト](https://www.python.org/downloads/)からダウンロードしてインストールしてください。（インストール時、「Add Python to PATH」にチェックを入れてください）

### 2. 必要なライブラリのインストール
コマンドプロンプト（またはPowerShell）を開き、以下のコマンドを実行して必要なライブラリをインストールします。

```cmd
pip install python-shogi pyinstaller
```

### 3. 実行ファイルのビルド
コマンドプロンプトで、このプロジェクトのフォルダ（`main.py`や`build_exe.py`がある場所）に移動し、以下のコマンドを実行します。

```cmd
python build_exe.py
```

ビルドが完了すると、新しく作成された `dist` フォルダの中に `shogi_engine.exe` が生成されます。

### 4. ShogiGUIへの登録
1. ShogiGUIを起動します。
2. メニューバーの「ツール」→「エンジン設定」を開きます。
3. 「追加」ボタンをクリックし、先ほど生成された `dist/shogi_engine.exe` を選択して追加します。
4. これで登録完了です！対局や検討機能で「Jules Shogi」を選択できるようになります。
