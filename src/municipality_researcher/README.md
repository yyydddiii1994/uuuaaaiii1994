# 自治体ウェブサイト調査ツール

このプロジェクトは、日本の自治体ウェブサイトの多言語対応状況やふりがな機能の有無などを調査するためのツール群です。

## 含まれるツール

1.  **自治体サイト完全攻略ツール Mark-III (自動検索機能搭載)** (`src/municipality_researcher/auto_checker.py`)
    *   **機能:**
        *   Excel/CSVファイルを読み込み、自動的にウェブサイトを解析します。
        *   URLが不明な場合はDuckDuckGoで検索して補完します。
        *   ふりがな機能、翻訳ツール（Google, J-SERVER, Wovn等）の有無を自動判定します。
        *   結果をExcelファイルに保存します。
    *   **使い方:**
        ```bash
        python3 src/municipality_researcher/auto_checker.py
        ```

2.  **手動調査用GUIツール** (`src/municipality_researcher/main.py`)
    *   **機能:**
        *   自治体リストを表示し、詳細を手動で入力・確認できます。
        *   細かい言語対応状況（アイスランド語など多数）をチェックボックスで記録できます。
    *   **使い方:**
        ```bash
        python3 src/municipality_researcher/main.py
        ```

## インストール

必要なライブラリをインストールしてください。

```bash
pip install -r src/municipality_researcher/requirements.txt
```

## データについて

*   自動ツールは、読み込んだExcel/CSVファイルに結果を追記して保存します。
*   手動ツールは `data/municipality_data.xlsx` を使用します。
