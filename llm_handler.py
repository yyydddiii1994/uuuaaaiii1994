# llm_handler.py
import requests
import json

# LLMに与えるシステムプロンプト
SYSTEM_PROMPT = """
あなたはAnkiカードの専門家です。
ユーザーから提供される、タブ区切りの「表\\t裏」形式のテキストを、Anki用の「穴埋め形式」のテキストに変換してください。

変換ルールは以下の通りです。
1.  各行が1枚のカードに対応します。
2.  「表」の内容から、最も重要で記憶すべきキーワードを**1つだけ**特定してください。
3.  特定したキーワードを `{{c1::キーワード}}` という形式で囲みます。
4.  元の「表」のテキストの、キーワード以外の部分と、`{{c1::キーワード}}` を結合して、新しい「表」を作成します。
5.  新しい「表」と元の「裏」をタブ(`\\t`)で区切って、1行のテキストとして出力します。
6.  入力されたすべての行に対して、この変換を適用してください。
7.  余計な説明や前置きは一切含めず、変換後のテキストだけを出力してください。

例：
入力:
日本の首都\t東京
アメリカ合衆国の初代大統領\tジョージ・ワシントン

出力:
{{c1::日本の首都}}\t東京
アメリカ合衆国の初代大統領は{{c1::ジョージ・ワシントン}}です。\tジョージ・ワシントン
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
