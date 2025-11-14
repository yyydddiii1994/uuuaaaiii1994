# llm_handler.py
import requests
import json

# LLMに与えるシステムプロンプト
SYSTEM_PROMPT = """
あなたは、テキストをAnkiの穴埋め問題形式に変換する、厳格なルールに従うアシスタントです。
ユーザーから提供される、タブ区切りの「表\\t裏」形式のテキストを、以下のルールに厳密に従って変換してください。

# 命令
各行の「表」の部分全体を、Ankiの穴埋め形式 `{{c1::...}}` で囲んでください。

# ルール
- 各行は独立したカードです。
- 「表」の部分は、内容を一切変更せず、そのまま `{{c1::` と `}}` で囲んでください。
- 元の「裏」の部分は、内容を一切変更せず、タブ文字(`\\t`)の後ろに配置してください。
- 他のテキスト（例：「以下が出力です」などの説明文）は一切含めないでください。
- 入力された行数と、出力する行数は必ず同じにしてください。

# 処理例
## 例1
入力:
日本の首都\t東京

出力:
{{c1::日本の首都}}\t東京

## 例2
入力:
源頼朝が鎌倉幕府を開いた年\t1192年
徳川家康が江戸幕府を開いた年\t1603年

出力:
{{c1::源頼朝が鎌倉幕府を開いた年}}\t1192年
{{c1::徳川家康が江戸幕府を開いた年}}\t1603年
"""

class LLMHandler:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()

    def convert_cards(self, cards_batch):
        llm_type = self.config.get("llm_type")
        prompt = "\\n".join(cards_batch)

        if llm_type == "DeepSeek":
            return self._convert_with_deepseek(prompt)
        elif llm_type == "Ollama":
            return self._convert_with_ollama(prompt)
        else:
            raise ValueError("サポートされていないLLMタイプです。")

    def _convert_with_deepseek(self, prompt):
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("DeepSeekのAPIキーが設定されていません。")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = self.session.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"DeepSeek APIへの接続に失敗しました: {e}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"DeepSeek APIからの予期せぬレスポンス形式です: {e}")


    def _convert_with_ollama(self, prompt):
        model = self.config.get("ollama_model")
        if not model or "(Ollamaが見つかりません)" in model:
            raise ValueError("Ollamaモデルが選択されていないか、Ollamaが利用できません。")

        payload = {
            "model": model,
            "system": SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False # ストリーミングはせず、一度に結果を受け取る
        }

        try:
            response = self.session.post("http://localhost:11434/api/generate", json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()
            return result['response'].strip()
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Ollamaに接続できません。Ollamaが起動していることを確認してください。")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollamaへのリクエスト中にエラーが発生しました: {e}")
        except KeyError:
            raise RuntimeError(f"Ollamaからの予期せぬレスポンス形式です。")

def get_ollama_models():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        models = [model['name'] for model in response.json().get('models', [])]
        return sorted(models)
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
        return []
    except Exception:
        return []
