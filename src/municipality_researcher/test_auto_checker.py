import unittest
from unittest.mock import MagicMock, patch
import sys

# Mocks setup
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()

import src.municipality_researcher.auto_checker as auto_checker

class TestAutoCheckerMarkV(unittest.TestCase):
    def setUp(self):
        self.root = MagicMock()
        auto_checker.ttk.Style = MagicMock()
        self.app = auto_checker.MunicipalityCheckerApp(self.root)

    @patch('src.municipality_researcher.auto_checker.requests.get')
    def test_check_google_translate_all_langs_mark_v(self, mock_get):
        """Test that detecting Google Translate enables all foreign languages in Mark V"""
        mock_response = MagicMock()
        mock_response.text = '<html><body><div class="goog-te-combo"></div></body></html>'
        mock_response.apparent_encoding = 'utf-8'
        mock_get.return_value = mock_response

        result = self.app.check_site_features("http://example.com")
        self.assertEqual(result['tool_name'], "Google翻訳サービス")

        # In Mark V, checking Google Translate sets ALL flags in ALL_LANG_COLUMNS to 1
        self.assertEqual(result['lang_flags']['アイスランド語'], 1)
        self.assertEqual(result['lang_flags']['英語'], 1)

    @patch('src.municipality_researcher.auto_checker.requests.get')
    def test_check_j_server(self, mock_get):
        """Test J-Server detection logic"""
        mock_response = MagicMock()
        mock_response.text = '<html><body>src="http://j-server.com/js"</body></html>'
        mock_response.apparent_encoding = 'utf-8'
        mock_get.return_value = mock_response

        result = self.app.check_site_features("http://example.com")
        self.assertEqual(result['tool_name'], "J-SERVER")

        # J-Server logic in Mark V sets only specific languages
        self.assertEqual(result['lang_flags']['英語'], 1)
        self.assertEqual(result['lang_flags']['中国語（簡体字）'], 1)
        # Icelandic is NOT in the J-Server list in Mark V
        self.assertEqual(result['lang_flags']['アイスランド語'], 0)

if __name__ == "__main__":
    unittest.main()
