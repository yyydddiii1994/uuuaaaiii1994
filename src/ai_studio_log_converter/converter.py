import json
import os
from pathlib import Path
from datetime import datetime

class LogConverter:
    def __init__(self):
        pass

    def convert_file(self, input_path, output_folder):
        """
        Converts a single JSON file to TXT.
        Returns a tuple (success: bool, message: str)
        """
        try:
            input_path = Path(input_path)
            output_folder = Path(output_folder)

            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Determine the structure and extract messages
            messages = self._extract_messages(data)

            if not messages:
                return False, f"ログデータが見つかりませんでした: {input_path.name}"

            # Generate Output Content
            output_text = self._format_conversation(messages)

            # Save to TXT
            output_filename = input_path.stem + ".txt"
            output_path = output_folder / output_filename

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_text)

            return True, f"変換完了: {output_filename}"

        except json.JSONDecodeError:
            return False, f"JSON形式のエラー: {input_path.name} (有効なJSONファイルではありません)"
        except Exception as e:
            return False, f"エラー ({input_path.name}): {str(e)}"

    def _extract_messages(self, data):
        """
        Attempts to extract messages from various JSON schemas.
        Returns list of dicts: {'role': str, 'text': str}
        """
        messages = []

        # Case 1: Standard Google AI Studio / Gemini API structure
        # {"contents": [{"role": "user", "parts": [{"text": "..."}]}]}
        if isinstance(data, dict) and "contents" in data:
            for item in data["contents"]:
                role = item.get("role", "unknown")
                text = ""
                parts = item.get("parts", [])
                for part in parts:
                    if "text" in part:
                        text += part["text"] + "\n"
                messages.append({"role": role, "text": text.strip()})
            return messages

        # Case 2: List of messages (Simple format)
        # [{"role": "user", "content": "..."}, ...]
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    role = item.get("role", "unknown")
                    # Handle 'content' or 'text' or 'parts'
                    text = item.get("content", item.get("text", ""))
                    if not text and "parts" in item:
                        # recursive check if parts is simple text list or dict list
                        parts = item["parts"]
                        if isinstance(parts, list):
                            for p in parts:
                                if isinstance(p, dict) and "text" in p:
                                    text += p["text"]
                                elif isinstance(p, str):
                                    text += p
                    messages.append({"role": role, "text": str(text).strip()})
            return messages

        # Case 3: "prompts" key (Older formats)
        if isinstance(data, dict) and "prompts" in data:
            # logic for prompts if needed, often similar to contents
            pass

        return messages

    def _format_conversation(self, messages):
        """Formats the messages into a readable string."""
        formatted = []
        formatted.append(f"Conversion Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        formatted.append("=" * 40 + "\n")

        for msg in messages:
            role = msg['role'].upper()
            text = msg['text']

            # Make it look nice
            formatted.append(f"[{role}]")
            formatted.append("-" * 20)
            formatted.append(text)
            formatted.append("\n" + "=" * 40 + "\n")

        return "\n".join(formatted)
