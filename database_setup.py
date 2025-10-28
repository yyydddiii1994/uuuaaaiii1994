import sqlite3
import json
import random

def setup_database():
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()

    # テーブルが存在すれば削除して再作成
    cursor.execute('DROP TABLE IF EXISTS questions')
    cursor.execute('''
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            answer TEXT NOT NULL,
            explanation TEXT
        )
    ''')

    categories = ["企業会計原則", "金融商品取引法", "会社法", "監査論", "管理会計論"]

    # ダミー問題を100問生成
    for i in range(1, 101):
        category = random.choice(categories)
        question_text = f"これは{category}に関するダミー問題 {i} です。正しい選択肢はどれですか？"

        options = [f"選択肢A-{i}", f"選択肢B-{i}", f"選択肢C-{i}", f"選択肢D-{i}"]
        random.shuffle(options)

        correct_answer = options[0] # 簡単のため、常にシャッフル後の一つ目を正解とする

        explanation_text = f"これは問題 {i} の解説です。正解は {correct_answer} です。"

        cursor.execute('''
            INSERT INTO questions (category, question, options, answer, explanation)
            VALUES (?, ?, ?, ?, ?)
        ''', (category, question_text, json.dumps(options), correct_answer, explanation_text))

    conn.commit()
    conn.close()
    print(f"データベースのセットアップが完了し、{len(categories)}カテゴリに100問のダミーデータが投入されました。")

if __name__ == '__main__':
    setup_database()
