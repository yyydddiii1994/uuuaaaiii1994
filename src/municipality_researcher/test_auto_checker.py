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

class TestAutoCheckerExtended(unittest.TestCase):
    def setUp(self):
        self.root = MagicMock()
        auto_checker.ttk.Style = MagicMock()
        self.app = auto_checker.MunicipalityCheckerApp(self.root)

    @patch('src.municipality_researcher.auto_checker.requests.get')
    def test_check_google_translate_all_langs(self, mock_get):
        """Test that detecting Google Translate enables all foreign languages"""
        mock_response = MagicMock()
        mock_response.text = '<html><body><div class="goog-te-combo"></div></body></html>'
        mock_response.apparent_encoding = 'utf-8'
        mock_get.return_value = mock_response

        result = self.app.check_site_features("http://example.com")
        self.assertEqual(result['tool_name'], "Google翻訳サービス")

        # Check specific languages
        self.assertEqual(result['langs']['アイスランド語'], 1, "Icelandic should be 1 for Google Translate")
        self.assertEqual(result['langs']['英語'], 1, "English should be 1")

    @patch('src.municipality_researcher.auto_checker.requests.get')
    def test_check_keyword_detection(self, mock_get):
        """Test keyword detection for non-Google sites"""
        mock_response = MagicMock()
        # Mocking a site with English and "Íslenskur" text
        mock_response.text = '<html><body>Link to English page. Link to Íslenskur page.</body></html>'
        mock_response.apparent_encoding = 'utf-8'
        mock_get.return_value = mock_response

        result = self.app.check_site_features("http://example.com")

        self.assertEqual(result['langs']['英語'], 1)
        self.assertEqual(result['langs']['アイスランド語'], 1)
        self.assertEqual(result['langs']['中国語（簡体字）'], 0)

if __name__ == "__main__":
    unittest.main()
