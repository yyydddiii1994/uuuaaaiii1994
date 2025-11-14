# anki_plugin/__init__.py

import sqlite3
from typing import List, Dict, Any

from aqt import mw
from aqt.qt import (
    QAction, QDialog, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
)
from aqt.utils import showInfo, qconnect
from aqt.browser import Browser

class MainDialog(QDialog):
    """アドオンのメインダイアログ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cognitive Load Analyzer")
        self.setMinimumSize(800, 600)

        main_layout = QVBoxLayout(self)

        info_label = QLabel(
            "「分析実行」ボタンをクリックすると、認知的な負荷が高いと思われるカードをリストアップします。\n"
            "リスト内のカードをダブルクリックすると、そのカードを編集できます。\n"
            "スコア = (失敗率 * 50) + ((2500 - 易しさ) / 100 * 5)\n"
            "失敗率 = 失敗回数 / (レビュー回数 + 1)"
        )
        main_layout.addWidget(info_label)

        self.analyze_button = QPushButton("分析実行")
        qconnect(self.analyze_button.clicked, self.analyze_cards)
        main_layout.addWidget(self.analyze_button)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "認知的負荷スコア", "カード内容 (Question)", "失敗回数", "レビュー回数", "易しさ(%)", "カードID", "ノートID"
        ])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)

        # ダブルクリックイベントを編集機能に接続
        self.results_table.itemDoubleClicked.connect(self.edit_card)

        main_layout.addWidget(self.results_table)
        self.setLayout(main_layout)

    def edit_card(self, item):
        """テーブルでダブルクリックされたカードを編集する"""
        if not item:
            return

        # 選択された行からノートIDを取得 (ノートIDは最後の列)
        row = item.row()
        nid_item = self.results_table.item(row, 6)
        if not nid_item:
            return

        nid = int(nid_item.text())

        # Ankiブラウザを起動し、対象のノートを編集
        browser = Browser(mw)
        browser.search(query=f"nid:{nid}")
        editor = browser.form.editor
        editor.set_note(mw.col.get_note(nid), focus=True)
        # show the main window and browser
        browser.show()
        browser.activateWindow()
        browser.raise_()

    def calculate_cognitive_load_score(self, lapses: int, reps: int, factor: int) -> float:
        """認知的負荷スコアを計算する"""
        # ゼロ除算を避けるため、repsが0の場合は1とする
        reviews = reps if reps > 0 else 1

        failure_ratio = lapses / reviews

        ease_hell_degree = (2500 - factor) / 100.0

        score = (failure_ratio * 50) + (ease_hell_degree * 5)
        return score

    def analyze_cards(self):
        """カードを分析し、結果をテーブルに表示する"""
        if not mw or not mw.col:
            showInfo("Ankiコレクションが読み込まれていません。")
            return

        try:
            cards_data = mw.col.db.all("""
                SELECT id, nid, reps, lapses, factor
                FROM cards
            """)

            scored_cards: List[Dict[str, Any]] = []
            for cid, nid, reps, lapses, factor in cards_data:
                score = self.calculate_cognitive_load_score(lapses, reps, factor)
                scored_cards.append({
                    "cid": cid,
                    "nid": nid,
                    "reps": reps,
                    "lapses": lapses,
                    "factor": factor,
                    "score": score
                })

            scored_cards.sort(key=lambda x: x["score"], reverse=True)
            display_cards = scored_cards[:100]

            self.results_table.setRowCount(0)

            for i, card_data in enumerate(display_cards):
                note = mw.col.get_note(card_data["nid"])
                if not note:
                    continue

                question_field = note.fields[0]

                self.results_table.insertRow(i)
                self.results_table.setItem(i, 0, QTableWidgetItem(f"{card_data['score']:.2f}"))
                self.results_table.setItem(i, 1, QTableWidgetItem(question_field))
                self.results_table.setItem(i, 2, QTableWidgetItem(str(card_data['lapses'])))
                self.results_table.setItem(i, 3, QTableWidgetItem(str(card_data['reps'])))
                self.results_table.setItem(i, 4, QTableWidgetItem(f"{card_data['factor']/10}%"))
                self.results_table.setItem(i, 5, QTableWidgetItem(str(card_data['cid'])))
                self.results_table.setItem(i, 6, QTableWidgetItem(str(card_data['nid'])))

            self.results_table.resizeColumnsToContents()
            showInfo(f"{len(display_cards)}件のカードを分析・表示しました。")

        except Exception as e:
            showInfo(f"カードの分析中にエラーが発生しました: {e}")


def show_main_dialog():
    dialog = MainDialog(mw)
    dialog.exec()

def setup_menu():
    if not mw:
        return

    action = QAction("Cognitive Load Analyzer", mw)
    qconnect(action.triggered, show_main_dialog)

    if hasattr(mw, "form") and hasattr(mw.form, "menuTools"):
        mw.form.menuTools.addAction(action)

setup_menu()
