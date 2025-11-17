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
        content="これは中央のプレビューエリアです。"
    )
    container = Element(
        element_type="div",
        styles={
            "width": "100%",
            "height": "100vh",
            "display": "flex",
            "flex-direction": "column",
            "justify-content": "center",
            "align-items": "center"
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
    """
    # スタイルをCSS文字列に変換
    style_str = "; ".join(f"{key}: {value}" for key, value in element.styles.items())

    # テキストコンテンツを取得
    content_html = element.content if element.content is not None else ""

    # 子要素をHTMLに変換
    children_html = "".join(element_to_html(child) for child in element.children)

    # HTML要素を構築
    if style_str:
        return f'<{element.element_type} style="{style_str}">{content_html}{children_html}</{element.element_type}>'
    else:
        return f'<{element.element_type}>{content_html}{children_html}</{element.element_type}>'


def page_to_html(page: Page) -> str:
    """
    Pageオブジェクトを完全なHTMLドキュメント文字列に変換します。
    """
    body_content = "".join(element_to_html(element) for element in page.elements)

    html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page.settings.get("title", "Untitled")}</title>
    <style>
        /* Basic reset */
        body, h1, p {{ margin: 0; padding: 0; }}
        body {{
            background-color: #f4f4f4;
        }}
    </style>
</head>
<body>
    {body_content}
</body>
</html>
    """
    return html.strip()
