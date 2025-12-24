import re

def clean_text_content(text: str, keep_newlines: bool = True) -> str:
    """
    テキストから日本語（ひらがな、カタカナ、漢字）と数字（半角・全角）以外を削除します。

    Args:
        text (str): 入力テキスト
        keep_newlines (bool): 改行コードを残すかどうか

    Returns:
        str: 処理後のテキスト
    """
    # 許可する文字の定義
    # \u3040-\u309F: ひらがな
    # \u30A0-\u30FF: カタカナ
    # \u4E00-\u9FFF: 漢字 (基本範囲)
    # 0-9: 半角数字
    # \uFF10-\uFF19: 全角数字

    # 正規表現パターンの構築
    # 否定(^)を使って、「許可するもの以外」をマッチさせる
    # \u3005: 々 (踊り字) - 漢字の繰り返し記号として頻出するため追加
    pattern_str = r'[^0-9０-９\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3005'

    if keep_newlines:
        pattern_str += r'\n\r'

    pattern_str += r']+'

    pattern = re.compile(pattern_str)

    # マッチした「不要な文字」を空文字に置換
    cleaned_text = pattern.sub('', text)

    return cleaned_text
