# src/cars_addon/settings_dialog.py

import json
import sys

# --- Conditional Imports for Standalone Testing ---
if __name__ == "__main__":
    try:
        from PyQt6.QtWidgets import (
            QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
            QComboBox, QLabel, QDialogButtonBox, QTextBrowser,
        )
    except ImportError:
        print("NOTE: To run this test standalone, you must have PyQt6 installed.")
        print("You can install it with: pip install PyQt6")
        sys.exit(1)

    class MockAddonManager:
        def getConfig(self, _):
            return {
                "selected_preset": "Long-Term Learning",
                "presets": {"Long-Term Learning": {}, "Exam Cramming": {}}
            }
        def writeConfig(self, _, config):
            print(f"Mock writeConfig called with: {config}")

    class MockMw:
        addonManager = MockAddonManager()

    mock_aqt = type('aqt', (), {'mw': MockMw()})
    sys.modules['aqt'] = mock_aqt
    mock_utils = type('aqt.utils', (), {'showInfo': lambda text: print(f"showInfo: {text}")})
    sys.modules['aqt.utils'] = mock_utils
else:
    from aqt.qt import (
        QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
        QComboBox, QLabel, QDialogButtonBox, QTextBrowser,
    )

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        from aqt import mw
        self.setWindowTitle("HAR アルゴリズム 設定＆仕様")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self.config = mw.addonManager.getConfig(__name__)
        self.presets = self.config.get("presets", {})
        self.selected_preset_name = self.config.get("selected_preset", "")

        vbox = QVBoxLayout(self)
        self.tabs = QTabWidget()
        vbox.addWidget(self.tabs)

        self.setup_settings_tab()
        self.setup_details_tab()

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.reject)
        vbox.addWidget(self.buttonBox)

    def setup_settings_tab(self):
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        preset_layout = QHBoxLayout()
        preset_label = QLabel("学習目標プリセット:")
        self.preset_combo = QComboBox()
        for name in self.presets.keys():
            self.preset_combo.addItem(name)
        if self.selected_preset_name in self.presets:
            self.preset_combo.setCurrentText(self.selected_preset_name)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)
        layout.addStretch()
        self.tabs.addTab(tab_widget, "設定")

    def setup_details_tab(self):
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)

        details_html = """
        <h2>HAR (ヒューリスティック・アダプティブ・レゾナンス) アルゴリズム仕様</h2>
        <p>HARは、ユーザーの「体感」を重視した、透明性の高いスケジューリングアルゴリズムです。</p>

        <h3>1. インターバル・ラダー</h3>
        <p>カードの習熟度は、<b>レベル (Level)</b> として管理され、各レベルには<b>基本間隔</b>が割り当てられています。正解するとレベルが1つ上昇します。</p>

        <h3>2. 二段階フィードバック</h3>
        <p>客観的な「正誤」と主観的な「体感」を分離します。
            <ul>
                <li><b>ステップ1 (客観):</b> 「正解」「不正解」を回答します。不正解の場合、カードは「ラプス・レベル」（通常L1）に戻ります。</li>
                <li><b>ステップ2 (主観):</b> 正解した場合にのみ、「難しい」「普通」「簡単」の体感難易度を回答します。</li>
            </ul>
        </p>

        <h3>3. レゾナンス・ファクター (RF)</h3>
        <p>各カードは固有の乗数である<b>RF値</b>（デフォルト1.0）を保持します。主観的フィードバックはこのRF値のみを更新します。
            <ul>
                <li><b>難しい:</b> RF値を減少させます (例: 1.0 → 0.9)。</li>
                <li><b>普通:</b> RF値をデフォルトの1.0にリセットします。</li>
                <li><b>簡単:</b> RF値を増加させます (例: 1.0 → 1.1)。</li>
            </ul>
        </p>

        <h3>最終的な間隔の計算式</h3>
        <p><code>次の間隔 = 基本間隔[新しいレベル] * RF値</code></p>
        <hr>
        <h3>数学的解説</h3>
        <p>アルゴリズムの状態は、カードcの状態S&#x209C; = (l&#x209C;, r&#x209C;) で定義されます。</p>
        <ul>
            <li><b>l&#x209C;</b>: カードの現在のレベル (Level) を示す整数。</li>
            <li><b>r&#x209C;</b>: カードの現在のレゾナンス・ファクター (RF) を示す浮動小数点数。</li>
        </ul>
        <p>ユーザーの入力Uは、U = (p, s) で定義されます。</p>
        <ul>
            <li><b>p</b>: パフォーマンス（正誤）。{correct, incorrect} のいずれか。</li>
            <li><b>s</b>: 主観的知覚（体感難易度）。{hard, normal, easy} のいずれか。</li>
        </ul>
        <p>状態遷移関数 T(S&#x209C;, U) は、新しい状態 S'&#x209C; = (l'&#x209C;, r'&#x209C;) を返します。</p>
        <ul>
            <li><b>l'&#x209C;</b>:
                <ul>
                    <li>もし p = incorrect ならば、l'&#x209C; = l&#x209A;ₐₚₛₑ （ラプス・レベル）</li>
                    <li>もし p = correct ならば、l'&#x209C; = min(l&#x209C; + 1, lₘₐₓ)</li>
                </ul>
            </li>
            <li><b>r'&#x209C;</b>:
                <ul>
                    <li>もし p = incorrect ならば、r'&#x209C; = r&#x209C; （変更なし）</li>
                    <li>もし p = correct かつ s = easy ならば、r'&#x209C; = min(rₘₐₓ, r&#x209C; + Δr)</li>
                    <li>もし p = correct かつ s = hard ならば、r'&#x209C; = max(rₘᵢₙ, r&#x209C; - Δr)</li>
                    <li>もし p = correct かつ s = normal ならば、r'&#x209C; = 1.0</li>
                </ul>
            </li>
        </ul>
        <p>最終的な間隔 I(S'&#x209C;) は、 I = Ladder[l'&#x209C;] * r'&#x209C; で計算されます。</p>
        """
        text_browser.setHtml(details_html)
        layout.addWidget(text_browser)
        self.tabs.addTab(tab_widget, "アルゴリズムの詳細仕様")

    def on_accept(self):
        from aqt import mw
        from aqt.utils import showInfo

        new_preset_name = self.preset_combo.currentText()
        self.config["selected_preset"] = new_preset_name

        try:
            mw.addonManager.writeConfig(__name__, self.config)
            showInfo("設定を保存しました。")
            super().accept()
        except Exception as e:
            showInfo(f"設定の保存中にエラーが発生しました: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = SettingsDialog()
    dialog.exec()
    app.quit()
