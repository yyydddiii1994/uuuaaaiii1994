import streamlit as st
import sqlite3
import json
import pandas as pd
import random

# --- データベース関連の関数 ---

def get_db_connection():
    """データベースへの接続を取得する"""
    conn = sqlite3.connect('quiz.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_categories():
    """データベースからすべてのユニークなカテゴリを取得する"""
    conn = get_db_connection()
    categories = conn.execute('SELECT DISTINCT category FROM questions').fetchall()
    conn.close()
    return [c['category'] for c in categories]

def get_questions(categories=None):
    """指定されたカテゴリの問題を取得する (指定がなければ全問題)"""
    conn = get_db_connection()
    query = 'SELECT * FROM questions'
    if categories:
        placeholders = ','.join('?' for _ in categories)
        query += f' WHERE category IN ({placeholders})'
        questions = conn.execute(query, categories).fetchall()
    else:
        questions = conn.execute(query).fetchall()
    conn.close()
    return questions

# --- Streamlitアプリのメイン部分 ---

def main():
    st.title("公認会計士 財務会計理論クイズ")

    # --- サイドバー ---
    with st.sidebar:
        st.header("設定")
        all_categories = get_all_categories()
        selected_categories = st.multiselect("学習したいカテゴリを選択してください:", all_categories, default=all_categories)

        if st.button("クイズを開始/リセット"):
            # セッション状態をリセット
            st.session_state.questions = get_questions(selected_categories)
            if not st.session_state.questions:
                 st.session_state.error = "選択されたカテゴリの問題が見つかりません。"
            else:
                st.session_state.error = None
                st.session_state.question_indices = list(range(len(st.session_state.questions)))
                random.shuffle(st.session_state.question_indices)
                st.session_state.current_question_index_pos = 0
                st.session_state.score = 0
                st.session_state.answered = False
                st.session_state.results = [] # 結果を保存するリスト
            st.experimental_rerun()

    # --- メインコンテンツ ---
    if 'error' in st.session_state and st.session_state.error:
        st.error(st.session_state.error)
        return

    if 'questions' not in st.session_state or not st.session_state.questions:
        st.info("サイドバーでカテゴリを選択し、「クイズを開始/リセット」ボタンを押してください。")
        return

    # --- クイズの進行管理 ---
    total_questions = len(st.session_state.question_indices)

    if st.session_state.current_question_index_pos >= total_questions:
        st.header("クイズ終了！")
        st.write(f"お疲れ様でした。あなたのスコアは {st.session_state.score} / {total_questions} です。")

        # 結果をDataFrameで表示
        if st.session_state.results:
            df = pd.DataFrame(st.session_state.results)
            st.subheader("結果の詳細")
            st.dataframe(df)
        return

    # 現在の問題を取得
    q_idx = st.session_state.question_indices[st.session_state.current_question_index_pos]
    question = st.session_state.questions[q_idx]

    question_text = question['question']
    options = json.loads(question['options'])
    answer = question['answer']
    explanation = question['explanation']

    st.header(f"問題 {st.session_state.current_question_index_pos + 1}/{total_questions}")
    st.write(f"【カテゴリ】: {question['category']}")
    st.markdown(f"**{question_text}**")

    # 回答の選択肢
    user_answer = st.radio("選択肢:", options, key=f"q_{q_idx}")

    # --- 回答ボタンと次の問題へボタン ---
    if not st.session_state.answered:
        if st.button("回答する", key=f"submit_{q_idx}"):
            is_correct = user_answer == answer
            st.session_state.answered = True

            # 結果を保存
            st.session_state.results.append({
                '問題': question_text,
                'あなたの回答': user_answer,
                '正解': answer,
                '結果': '正解' if is_correct else '不正解'
            })

            if is_correct:
                st.success("正解！ 🎉")
                st.session_state.score += 1
            else:
                st.error(f"不正解... 😢 正解は「{answer}」です。")

            st.info("【解説】")
            st.write(explanation)
            st.experimental_rerun()
    else:
        if st.button("次の問題へ", key=f"next_{q_idx}"):
            st.session_state.current_question_index_pos += 1
            st.session_state.answered = False
            st.experimental_rerun()

if __name__ == "__main__":
    main()
