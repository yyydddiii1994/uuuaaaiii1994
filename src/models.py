# src/models.py

from typing import List, Dict, Any, Optional

class Element:
    """
    Webページの要素を表すクラス。
    ツリー構造を形成します。
    テキストコンテンツは`content`属性で、子要素は`children`リストで表現します。
    """
    def __init__(self,
                 element_type: str,
                 styles: Optional[Dict[str, Any]] = None,
                 content: Optional[str] = None,
                 children: Optional[List['Element']] = None):
        self.element_type: str = element_type
        self.styles: Dict[str, Any] = styles if styles is not None else {}
        self.content: Optional[str] = content
        self.children: List['Element'] = children if children is not None else []

    def to_dict(self) -> Dict[str, Any]:
        """シリアライズのために辞書に変換します。"""
        return {
            "element_type": self.element_type,
            "styles": self.styles,
            "content": self.content,
            "children": [child.to_dict() for child in self.children]
        }

class Page:
    """
    単一のWebページを表すクラス。
    要素のツリー構造（ElementTree）とページ設定を持ちます。
    """
    def __init__(self,
                 name: str,
                 settings: Optional[Dict[str, Any]] = None,
                 elements: Optional[List[Element]] = None):
        self.name: str = name
        self.settings: Dict[str, Any] = settings if settings is not None else {}
        self.elements: List[Element] = elements if elements is not None else []

    def to_dict(self) -> Dict[str, Any]:
        """シリアライズのために辞書に変換します。"""
        return {
            "name": self.name,
            "settings": self.settings,
            "elements": [element.to_dict() for element in self.elements]
        }

class Site:
    """
    Webサイト全体を表すクラス。
    サイト設定、ページリスト、アセットリストを保持します。
    """
    def __init__(self,
                 name: str,
                 settings: Optional[Dict[str, Any]] = None,
                 pages: Optional[List[Page]] = None,
                 assets: Optional[List[str]] = None):
        self.name: str = name
        self.settings: Dict[str, Any] = settings if settings is not None else {}
        self.pages: List[Page] = pages if pages is not None else []
        self.assets: List[str] = assets if assets is not None else []

    def to_dict(self) -> Dict[str, Any]:
        """シリアライズのために辞書に変換します。"""
        return {
            "name": self.name,
            "settings": self.settings,
            "pages": [page.to_dict() for page in self.pages],
            "assets": self.assets
        }
