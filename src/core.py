# src/core.py

from typing import List
from src.models import Site, Page, Element

def create_default_project() -> Site:
    """
    アプリケーション起動時に表示するための、
    デフォルトのWebサイトプロジェクトデータを生成します。
    """
    # 「ようこそ」ページのコンテンツを作成
    heading = Element(
        element_type="h1",
        styles={"color": "#333", "font-family": "sans-serif"},
        content="ようこそ Python Web Builder へ"
    )
    paragraph = Element(
        element_type="p",
        styles={"color": "#666", "font-family": "sans-serif"},
        content="これは中央のプレビューエリアです。クリックして要素を選択できます。"
    )
    container = Element(
        element_type="div",
        styles={
            "width": "100%",
            "height": "100vh",
            "display": "flex",
            "flex-direction": "column",
            "justify-content": "center",
            "align-items": "center",
            "text-align": "center"
        },
        children=[heading, paragraph]
    )

    # ページを作成
    welcome_page = Page(
        name="index.html",
        elements=[container]
    )

    # サイト全体を作成
    default_site = Site(
        name="My First Site",
        pages=[welcome_page]
    )
    return default_site

def element_to_html(element: Element) -> str:
    """
    単一のElementオブジェクトをHTML文字列に再帰的に変換します。
    各要素には `data-element-id` 属性が付与されます。
    """
    # スタイルをCSS文字列に変換
    style_str = "; ".join(f"{key}: {value}" for key, value in element.styles.items())
    style_attr = f' style="{style_str}"' if style_str else ""

    # テキストコンテンツを取得
    content_html = element.content if element.content is not None else ""

    # 子要素をHTMLに変換
    children_html = "".join(element_to_html(child) for child in element.children)

    # HTML要素を構築
    return f'<{element.element_type} data-element-id="{element.element_id}"{style_attr}>{content_html}{children_html}</{element.element_type}>'


def page_to_html(page: Page, qwebchannel_js_path: str) -> str:
    """
    Pageオブジェクトを完全なHTMLドキュメント文字列に変換します。
    QWebChannelの初期化スクリプトも埋め込みます。
    """
    body_content = "".join(element_to_html(element) for element in page.elements)

    html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page.settings.get("title", "Untitled")}</title>
    <script src="{qwebchannel_js_path}"></script>
    <style>
        /* Basic reset */
        body, h1, p {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-color: #f4f4f4;
        }}
        /* クリック可能な要素を示すカーソル */
        [data-element-id] {{
            cursor: pointer;
        }}
        /* 選択された要素のハイライト（例） */
        .selected-element {{
            outline: 2px solid #0078d4;
            box-shadow: 0 0 10px rgba(0, 120, 212, 0.5);
        }}
    </style>
</head>
<body>
    {body_content}
</body>
</html>
    """
    return html.strip()
