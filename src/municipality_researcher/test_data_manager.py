import unittest
import os
import pandas as pd
from data_manager import DataManager

class TestDataManager(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.languages_file = os.path.join(self.base_dir, "languages.txt")
        self.sample_csv = os.path.join(self.base_dir, "sample_data.csv")
        self.test_data_file = os.path.join(self.base_dir, "../../data/test_data.xlsx")

        # Ensure clean state
        if os.path.exists(self.test_data_file):
            os.remove(self.test_data_file)

    def tearDown(self):
        if os.path.exists(self.test_data_file):
            os.remove(self.test_data_file)

    def test_load_and_save(self):
        dm = DataManager(data_file=self.test_data_file, languages_file=self.languages_file, sample_csv=self.sample_csv)

        # Check if languages loaded
        self.assertTrue(len(dm.languages) > 0)
        self.assertIn("日本語", dm.languages)

        # Check data loaded
        self.assertFalse(dm.df.empty)

        # Check language columns exist
        self.assertIn("日本語", dm.df.columns)

        # Update record
        dm.update_record(0, {"日本語": 1, "備考": "Test Update"})

        # Verify update in memory
        record = dm.get_record(0)
        self.assertEqual(record['備考'], "Test Update")

        # Verify file creation
        self.assertTrue(os.path.exists(self.test_data_file))

if __name__ == "__main__":
    unittest.main()
