# llm_handler.py
import requests
import json

# LLMに与えるシステムプロンプト
SYSTEM_PROMPT = """
あなたは、Ankiカードのテキストを、高品質な「穴埋め問題」形式に変換する専門家です。
ユーザーから提供される、タブで区切られた「問い\\t答え」のペアを、以下のルールに厳密に従って変換してください。

# 基本ルール
1.  **入力**: 各行は `問い（表）\\t答え（裏）` の形式です。
2.  **処理対象**: あなたが変換するのは **「答え（裏）」** の部分のみです。「問い（表）」は一切変更しません。
3.  **穴埋め化**: 「答え（裏）」の中から、学習上重要となるキーワード、公式の要素、リストの項目などを特定し、それらを `{{c1::...}}`, `{{c2::...}}`, `{{c3::...}}` の形式で囲んでください。穴の番号は `c1`, `c2`, `c3`... と連番にしてください。
4.  **出力形式**: 最終的な出力は、**元の「問い（表）」** と **穴埋め化した「答え（裏）」** をタブ(`\\t`)で連結した `問い\\t穴埋め変換後の答え` の形式とします。
5.  **補足**: 余計な説明や前置きは一切含めず、変換後のテキストだけを出力してください。入力された行数と出力する行数は必ず同じにしてください。

# 変換パターン別の詳細指示と具体例

## パターン1: 定義・説明文
「答え」が文章の場合、その中核となるキーワードを複数、穴埋めにしてください。

### 例1-1
入力:
「デリバティブ取引」とは何か？\t原資産の価格や金利等から派生した商品（金融派生商品）を扱う取引。

出力:
「デリバティブ取引」とは何か？\t{{c1::原資産の価格}}や{{c2::金利等}}から派生した商品（{{c3::金融派生商品}}）を扱う取引。

## パターン2: 計算式・公式
「答え」が計算式の場合、その構成要素をそれぞれ穴埋めにしてください。

### 例2-1
入力:
「コール・オプションの買手」が権利行使する場合、決済時の「現金収入」の計算式は？（差金決済が前提）\t（想定元本） × （権利行使時の為替相場 － 権利行使価格）

出力:
「コール・オプションの買手」が権利行使する場合、決済時の「現金収入」の計算式は？（差金決済が前提）\t（{{c1::想定元本}}） × （{{c2::権利行使時の為替相場}} － {{c3::権利行使価格}}）

## パターン3: リスト・列挙
「答え」が複数の項目の列挙である場合、各項目をそれぞれ穴埋めにしてください。

### 例3-1
入力:
通貨代用証券（会計学上現金扱い）の具体例は？（10個）\t他人振出小切手、配当金領収証、利払日の到来している公社債利札、郵便為替証書、送金小切手、送金為替手形、預金手形、一覧払手形、振替貯金払出証書等、官公庁支払命令書。

出力:
通貨代用証券（会計学上現金扱い）の具体例は？（10個）\t{{c1::他人振出小切手}}、{{c2::配当金領収証}}、{{c3::利払日の到来している公社債利札}}、{{c4::郵便為替証書}}、{{c5::送金小切手}}、{{c6::送金為替手形}}、{{c7::預金手形}}、{{c8::一覧払手形}}、{{c9::振替貯金払出証書等}}、{{c10::官公庁支払命令書}}。
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
