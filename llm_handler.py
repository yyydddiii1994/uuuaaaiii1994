# llm_handler.py
import requests
import json

# LLMに与えるシステムプロンプト（改善案）
SYSTEM_PROMPT = """
あなたは、ユーザーの指示に「絶対服従」するテキスト変換ボットです。
絶対に指示以外のタスク（要約、翻訳、整理など）を実行してはいけません。

# 命令
ユーザーから提供される「問い\t答え」形式の日本語テキストを、以下のルールに厳密に従い、「日本語の穴埋めカード」に変換してください。

# 厳格なルール
1.  **処理対象**: 「問い」と「答え」の両方を使います。
2.  **再構築**: 「問い」と「答え」の情報を組み合わせて、**「答え」のキーワードを穴埋めにした「新しいオモテ面（問題文）」**を作成します。
3.  **キーワード選定**: 意味の中心となる**専門用語、固有名詞、重要な概念**を優先して穴埋めにしてください。一般的な動詞（例: 扱う、する）や助詞は可能な限り穴埋めにしないでください。
4.  **キーワード分割**: 「AやB」「AとB」のような複合的なキーワードは、`{{c1::A}}`や`{{c2::B}}`のように、可能な限り個別に分割してください。
5.  **形式**: `{{c1::キーワード}}` `{{c2::キーワード}}` ... の形式を使います。
5.  **出力**: `新しい穴埋め文（オモテ面）\t元の答え（ウラ面）` のタブ区切り形式で出力します。ウラ面には元の答えをそのまま残してください。
6.  **言語**: 絶対に日本語のまま処理し、英語に翻訳してはいけません。
7.  **その他**: 説明文（「以下が出力です」など）は一切不要です。

# 健司戦略（ベストプラクティス）の具体例
これを完璧に真似してください。

## 例1: 定義の構成要素
入力:
「資産」（概念FW）の定義とは？\t①過去の取引の結果、②支配している、③経済的資源である。
出力:
「資産」（概念FW）の定義とは、①{{c1::過去の取引}}の結果、②{{c2::支配}}している、③{{c3::経済的資源}}である。\t①過去の取引の結果、②支配している、③経済的資源である。

## 例2: 複合キーワードの分割（最重要ルール）
入力:
デリバティブ取引とは何か？\t原資産の価格や金利等から派生した商品（金融派生商品）を扱う取引。
出力:
デリバティブ取引とは、{{c1::原資産の価格}}や{{c2::金利等}}から派生した{{c3::金融派生商品}}を扱う取引である。\t原資産の価格や金利等から派生した商品（金融派生商品）を扱う取引。

## 例3: プロセス（連結）
入力:
連結1年目・S社株式80%取得時のステップ\t1.投資と資本の相殺 2.差額をのれんとして計上 3.少数株主持分（20%）を非支配株主持分に振り替え
出力:
【連結1年目・S社株式80%取得】 1.（親）投資勘定と（子）資本勘定を{{c1::相殺}}する。 2. 差額（投資＞資本）を {{c2::のれん}} として計上する。 3. 子会社資本のうち20%を {{c3::非支配株主持分}} に振り替える。\t1.投資と資本の相殺 2.差額をのれんとして計上 3.少数株主持分（20%）を非支配株主持分に振り替え

## 例3: 公式の構成要素（原価計算）
入力:
材料費価格差異の計算式\t（標準価格 － 実際価格） × 実際消費量
出力:
材料費価格差異 ＝ （標準価格 － 実際価格） × {{c1::実際消費量}} （※{{c2::標準消費量}} ではない点に注意）\t（標準価格 － 実際価格） × 実際消費量

## 例4: 差異の解釈
入力:
予算差異（実際発生額 － 予算許容額）の解釈（プラスの場合）\t不利差異
出力:
【差異の解釈】予算差異（実際発生額 － 予算許容額）の計算結果が**プラス（＋）**であれば {{c1::不利差異}} である。\t不利差異
"""

class LLMHandler:
    def __init__(self, config, cancel_event=None):
        self.config = config
        self.session = requests.Session()
        self.cancel_event = cancel_event

    def convert_cards(self, cards_batch):
        """
        複数のカードをバッチ処理します。
        ★★ 戦略的変更点 ★★
        LLMのタスク誤解を防ぐため、バッチを内部で1件ずつループ処理します。
        """
        llm_type = self.config.get("llm_type")
        for single_card_line in cards_batch:
            if self.cancel_event and self.cancel_event.is_set():
                print("LLMハンドラ内でキャンセルを検知。処理を中断します。")
                break # ジェネレータを終了

            prompt = single_card_line
            try:
                result = None
                if llm_type == "DeepSeek":
                    result = self._convert_with_deepseek(prompt)
                elif llm_type == "Ollama":
                    result = self._convert_with_ollama(prompt)
                else:
                    raise ValueError("サポートされていないLLMタイプです。")

                if result:
                    yield result

            except Exception as e:
                error_message = f"カード「{single_card_line[:30]}...」の処理中にエラー: {e}"
                print(error_message)
                # エラー情報もストリームに流す
                yield f"エラー: {single_card_line} -> {e}"

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

        options = {}
        if self.config.get("ollama_num_ctx"):
            options["num_ctx"] = self.config.get("ollama_num_ctx")

        payload = {
            "model": model,
            "system": SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False,
            "options": options
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

def get_ollama_model_details(model_name):
    """指定されたOllamaモデルの詳細情報を取得する。"""
    try:
        response = requests.post("http://localhost:11434/api/show", json={"name": model_name}, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
        print(f"モデル詳細取得エラー: Ollamaに接続できません。")
        return None
    except requests.exceptions.RequestException as e:
        print(f"モデル詳細取得中にリクエストエラーが発生しました ({model_name}): {e}")
        return None
    except Exception as e:
        print(f"モデル詳細の取得中に予期せぬエラーが発生しました: {e}")
        return None
