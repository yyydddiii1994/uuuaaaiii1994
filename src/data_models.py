# src/data_models.py
import json
from typing import List, Dict, Any

class Element:
    """Represents a single HTML element in the page."""
    def __init__(self, tag: str, styles: Dict[str, Any] = None, children: List['Element'] = None, content: str = ""):
        self.tag = tag
        self.styles = styles if styles is not None else {}
        self.children = children if children is not None else []
        self.content = content  # For text nodes or tags like <p>

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the element to a dictionary."""
        return {
            "tag": self.tag,
            "styles": self.styles,
            "content": self.content,
            "children": [child.to_dict() for child in self.children]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Element':
        """Deserializes a dictionary back to an Element instance."""
        children = [cls.from_dict(child_data) for child_data in data.get("children", [])]
        return cls(
            tag=data["tag"],
            styles=data.get("styles", {}),
            content=data.get("content", ""),
            children=children
        )

class Page:
    """Represents a single page within the site."""
    def __init__(self, title: str, elements: List[Element] = None):
        self.title = title
        self.elements = elements if elements is not None else []

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the page to a dictionary."""
        return {
            "title": self.title,
            "elements": [elem.to_dict() for elem in self.elements]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Page':
        """Deserializes a dictionary back to a Page instance."""
        elements = [Element.from_dict(elem_data) for elem_data in data.get("elements", [])]
        return cls(
            title=data["title"],
            elements=elements
        )

class Site:
    """Represents the entire website project."""
    def __init__(self, settings: Dict[str, Any] = None, pages: List[Page] = None):
        self.settings = settings if settings is not None else {"site_name": "My Awesome Site"}
        self.pages = pages if pages is not None else []

    def to_json(self, filepath: str):
        """Saves the site structure to a JSON file."""
        data = {
            "settings": self.settings,
            "pages": [page.to_dict() for page in self.pages]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def from_json(cls, filepath: str) -> 'Site':
        """Loads the site structure from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            pages = [Page.from_dict(page_data) for page_data in data.get("pages", [])]
            return cls(
                settings=data.get("settings", {}),
                pages=pages
            )
        except FileNotFoundError:
            # If no project file exists, return a new default site
            return cls(pages=[Page(title="Home")])
