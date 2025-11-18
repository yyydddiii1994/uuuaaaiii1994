# src/models.py

import uuid
from typing import List, Dict, Any, Optional

class Element:
    """
    Webページの要素を表すクラス。
    ツリー構造を形成します。
    各要素は一意のID(`element_id`)を持ちます。
    """
    def __init__(self,
                 element_type: str,
                 styles: Optional[Dict[str, Any]] = None,
                 content: Optional[str] = None,
                 children: Optional[List['Element']] = None):
        self.element_id: str = str(uuid.uuid4())
        self.element_type: str = element_type
        self.styles: Dict[str, Any] = styles if styles is not None else {}
        self.content: Optional[str] = content
        self.children: List['Element'] = children if children is not None else []

    def to_dict(self) -> Dict[str, Any]:
        """シリアライズのために辞書に変換します。"""
        return {
            "element_id": self.element_id,
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

    def find_element_by_id(self, element_id: str) -> Optional[Element]:
        """ページ内の要素をIDで検索します。"""
        for element in self.elements:
            found = self._find_element_in_tree(element, element_id)
            if found:
                return found
        return None

    def _find_element_in_tree(self, current_element: Element, target_id: str) -> Optional[Element]:
        """要素ツリーを再帰的に検索します。"""
        if current_element.element_id == target_id:
            return current_element
        for child in current_element.children:
            found = self._find_element_in_tree(child, target_id)
            if found:
                return found
        return None


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
