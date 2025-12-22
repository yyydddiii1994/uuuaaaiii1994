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

class TestAutoCheckerMarkVII(unittest.TestCase):
    def setUp(self):
        self.root = MagicMock()
        auto_checker.ttk.Style = MagicMock()
        self.app = auto_checker.MunicipalityCheckerApp(self.root)

    @patch('src.municipality_researcher.auto_checker.requests.get')
    def test_link_tracking_redirect(self, mock_get):
        """Test that the scraper follows links to find the translation tool (e.g. tracking redirect)"""

        # Mock Response 1: Main Page (No tool, but link to English)
        main_page = MagicMock()
        main_page.text = '<html><body><a href="http://example.com/redirect">English</a></body></html>'
        main_page.apparent_encoding = 'utf-8'

        # Mock Response 2: Redirected Page (Is Google Translate)
        redirected_page = MagicMock()
        redirected_page.url = "https://translate.google.co.jp/?sl=ja&tl=en"
        redirected_page.text = '<html><body>Google Translate</body></html>'
        redirected_page.apparent_encoding = 'utf-8'

        # side_effect: returns main_page first, then redirected_page
        mock_get.side_effect = [main_page, redirected_page]

        result = self.app.check_site_features("http://example.com")

        # Should detect Google Translate via tracking
        self.assertEqual(result['tool_name'], "Google翻訳サービス")
        self.assertEqual(result['lang_flags']['英語'], 1)

    @patch('src.municipality_researcher.auto_checker.requests.get')
    def test_link_tracking_direct(self, mock_get):
        """Test that the scraper identifies a direct link to a translation service"""

        # Mock Response 1: Main Page with direct link
        main_page = MagicMock()
        main_page.text = '<html><body><a href="http://j-server.com/sapporo">Foreign Language</a></body></html>'
        main_page.apparent_encoding = 'utf-8'

        # Mock Response 2: The J-Server page itself (if it clicks it, though the logic might short-circuit if href is obvious)
        jserver_page = MagicMock()
        jserver_page.url = "http://j-server.com/sapporo"
        jserver_page.text = '<html><body>J-SERVER</body></html>'
        jserver_page.apparent_encoding = 'utf-8'

        mock_get.side_effect = [main_page, jserver_page]

        result = self.app.check_site_features("http://example.com")

        # Logic should catch J-SERVER from the link href or by following it
        self.assertEqual(result['tool_name'], "J-SERVER")

if __name__ == "__main__":
    unittest.main()
