# anki_plugin/__init__.py

import sqlite3
import math
from typing import List, Dict, Any

from aqt import mw, dialogs
from aqt.qt import (
    QAction, QDialog, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
)
from aqt.utils import showInfo, qconnect

class MainDialog(QDialog):
    """アドオンのメインダイアログ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cognitive Load Analyzer")
        self.setMinimumSize(950, 700)

        main_layout = QVBoxLayout(self)

        info_label = QLabel(
            "「分析実行」ボタンで、認知科学に基づき負荷が高いカードを分析します。\n"
            "リスト内のカードをダブルクリックすると、そのカードを編集できます。\n"
            "<b>スコア = (失敗の深刻度) + (主観的な困難度) + (想起の流暢性)</b>\n"
            "<ul><li><b>失敗の深刻度:</b> (失敗率 * 50) * log(インターバル + 2)</li>"
            "<li><b>主観的な困難度:</b> ((2500 - 易しさ) / 100) * 5</li>"
            "<li><b>想起の流暢性:</b> (平均レビュー時間[秒]) * 10</li></ul>"
        )
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)


        self.analyze_button = QPushButton("分析実行")
        qconnect(self.analyze_button.clicked, self.analyze_cards)
        main_layout.addWidget(self.analyze_button)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(9)
        self.results_table.setHorizontalHeaderLabels([
            "負荷スコア", "カード内容", "失敗回数", "レビュー回数", "易しさ(%)",
            "インターバル(日)", "平均時間(秒)", "カードID", "ノートID"
        ])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(2, self.results_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        self.results_table.itemDoubleClicked.connect(self.edit_card)
        main_layout.addWidget(self.results_table)
        self.setLayout(main_layout)

    def edit_card(self, item):
        """テーブルでダブルクリックされたカードのブラウザを開く (リファクタリング版)"""
        if not item:
            return

        # 選択された行からノートIDを取得 (ノートIDは9番目のカラム)
        row = item.row()
        nid_item = self.results_table.item(row, 8)
        if not nid_item:
            return

        nid = int(nid_item.text())

        # Ankiの推奨するヘルパー関数を使い、特定のカードを検索した状態でブラウザを開く
        dialogs.open('Browser', mw, search=f"nid:{nid}")


    def calculate_new_score(self, lapses: int, reps: int, factor: int, ivl: int, avg_time_sec: float) -> float:
        """提案された新しい認知科学的スコアを計算する"""
        reviews = reps if reps > 0 else 1
        failure_ratio = lapses / reviews
        failure_severity = (failure_ratio * 50) * math.log(ivl + 2)

        subjective_difficulty = ((2500 - factor) / 100.0) * 5

        retrieval_fluency = avg_time_sec * 10

        score = failure_severity + subjective_difficulty + retrieval_fluency
        return score

    def analyze_cards(self):
        """カードを分析し、結果をテーブルに表示する"""
        if not mw or not mw.col:
            showInfo("Ankiコレクションが読み込まれていません。")
            return

        try:
            avg_times_raw = mw.col.db.all("SELECT cid, AVG(time) FROM revlog WHERE type = 1 GROUP BY cid")
            avg_times = {cid: avg_time for cid, avg_time in avg_times_raw}

            cards_data = mw.col.db.all("SELECT id, nid, reps, lapses, factor, ivl FROM cards")

            scored_cards: List[Dict[str, Any]] = []
            for cid, nid, reps, lapses, factor, ivl in cards_data:
                avg_time_ms = avg_times.get(cid, 0)
                avg_time_sec = avg_time_ms / 1000.0

                score = self.calculate_new_score(lapses, reps, factor, ivl, avg_time_sec)

                scored_cards.append({
                    "cid": cid, "nid": nid, "reps": reps, "lapses": lapses,
                    "factor": factor, "ivl": ivl, "avg_time_sec": avg_time_sec, "score": score
                })

            scored_cards.sort(key=lambda x: x["score"], reverse=True)
            display_cards = scored_cards[:100]

            self.results_table.setRowCount(0)

            for i, card_data in enumerate(display_cards):
                note = mw.col.get_note(card_data["nid"])
                if not note: continue
                question_field = note.fields[0]

                self.results_table.insertRow(i)
                self.results_table.setItem(i, 0, QTableWidgetItem(f"{card_data['score']:.2f}"))
                self.results_table.setItem(i, 1, QTableWidgetItem(question_field))
                self.results_table.setItem(i, 2, QTableWidgetItem(str(card_data['lapses'])))
                self.results_table.setItem(i, 3, QTableWidgetItem(str(card_data['reps'])))
                self.results_table.setItem(i, 4, QTableWidgetItem(f"{card_data['factor']/10}%"))
                self.results_table.setItem(i, 5, QTableWidgetItem(str(card_data['ivl'])))
                self.results_table.setItem(i, 6, QTableWidgetItem(f"{card_data['avg_time_sec']:.2f}"))
                self.results_table.setItem(i, 7, QTableWidgetItem(str(card_data['cid'])))
                self.results_table.setItem(i, 8, QTableWidgetItem(str(card_data['nid'])))

            self.results_table.resizeColumnsToContents()
            showInfo(f"{len(display_cards)}件のカードを分析・表示しました。")

        except Exception as e:
            showInfo(f"カードの分析中にエラーが発生しました: {e}")


def show_main_dialog():
    dialog = MainDialog(mw)
    dialog.exec()

def setup_menu():
    if not mw: return
    action = QAction("Cognitive Load Analyzer", mw)
    qconnect(action.triggered, show_main_dialog)
    if hasattr(mw, "form") and hasattr(mw.form, "menuTools"):
        mw.form.menuTools.addAction(action)

setup_menu()
