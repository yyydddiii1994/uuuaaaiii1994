# llm_handler.py
import requests
import json

# LLMに与えるシステムプロンプト
SYSTEM_PROMPT = """
あなたは、Ankiカード作成の専門家です。
ユーザーから提供される「問い」と「答え」のペアを分析し、それらを統合して、高品質で自然な「穴埋め問題文」を新たに作成してください。

# 基本ルール
1.  **入力**: 各行は `問い\\t答え` の形式です。
2.  **処理**: 「問い」と「答え」の文脈を完全に理解し、それらを組み合わせて一つの完結した文章を作成してください。これが新しい「オモテ面」のベースとなります。
3.  **穴埋め化**: 新しく作成した文章の中から、学習上、最も重要となるキーワードや数値を特定し、`{{c1::...}}`, `{{c2::...}}`, `{{c3::...}}` の形式で穴埋めにしてください。
4.  **出力形式**: 最終的な出力は、`新しい穴埋め問題文（オモテ面）\\t補足情報（ウラ面）` の形式とします。
5.  **ウラ面について**: 「ウラ面」は基本的に空欄で構いません。ただし、元の「答え」が非常に長い場合や、補足情報として価値があると感じた場合は、元の答えをそのまま記載しても構いません。
6.  **厳守事項**: 余計な説明や前置きは一切含めず、変換後のテキストだけを出力してください。入力された行数と出力する行数は必ず同じにしてください。

# 処理例

## 例1: 定義文の再構成
### 入力:
「デリバティブ取引」とは何か？\t原資産の価格や金利等から派生した商品（金融派生商品）を扱う取引。
### 出力:
デリバティブ取引とは、{{c1::原資産の価格}}や{{c2::金利等}}から派生した商品（{{c3::金融派生商品}}）を扱う取引のことである。\t

## 例2: 計算式の再構成
### 入力:
「コール・オプションの買手」が権利行使する場合、決済時の「現金収入」の計算式は？（差金決済が前提）\t（想定元本） × （権利行使時の為替相場 － 権利行使価格）
### 出力:
コール・オプションの買手（差金決済が前提）が権利行使する場合、現金収入は「（{{c1::想定元本}}） × （{{c2::権利行使時の為替相場}} － {{c3::権利行使価格}}）」で計算される。\t（想定元本） × （権利行使時の為替相場 － 権利行使価格）

## 例3: 列挙の再構成
### 入力:
通貨代用証券（会計学上現金扱い）の具体例は？（10個）\t他人振出小切手、配当金領収証、利払日の到来している公社債利札、郵便為替証書、送金小切手、送金為替手形、預金手形、一覧払手形、振替貯金払出証書等、官公庁支払命令書。
### 出力:
会計学上、現金として扱われる通貨代用証券には、{{c1::他人振出小切手}}、{{c2::配当金領収証}}、{{c3::利払日の到来している公社債利札}}、{{c4::郵便為替証書}}、{{c5::送金小切手}}、{{c6::送金為替手形}}、{{c7::預金手形}}、{{c8::一覧払手形}}、{{c9::振替貯金払出証書等}}、{{c10::官公庁支払命令書}}などがある。\t
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
