import unittest
import os
import json
import pandas as pd
from src.google_maps_scraper.data_manager import DataManager

class TestComponents(unittest.TestCase):
    def setUp(self):
        self.test_config = {
            "min_delay": 1,
            "max_delay": 2,
            "max_items_per_day": 10
        }
        self.dm = DataManager(self.test_config)
        self.test_csv = "test_keywords.csv"
        with open(self.test_csv, "w") as f:
            f.write("keyword1\nkeyword2")

    def tearDown(self):
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)
        if os.path.exists("progress.json"):
            os.remove("progress.json")
        if os.path.exists("error_log.txt"):
            os.remove("error_log.txt")
        # Cleanup output dir files created by tests
        if os.path.exists(self.dm.output_dir):
            for f in os.listdir(self.dm.output_dir):
                os.remove(os.path.join(self.dm.output_dir, f))

    def test_incremental_save(self):
        # Step 1: Save 1 item
        data1 = [{"Keyword": "k1", "Name": "Shop A", "Address": "Tokyo", "Phone": "03", "URL": "http"}]
        file1 = self.dm.save_results(data1)
        self.assertTrue(os.path.exists(file1))
        df1 = pd.read_excel(file1)
        self.assertEqual(len(df1), 1)

        # Step 2: Save 2 items (simulating incremental update)
        data2 = data1 + [{"Keyword": "k2", "Name": "Shop B", "Address": "Osaka", "Phone": "06", "URL": "http"}]
        file2 = self.dm.save_results(data2)
        self.assertEqual(file1, file2) # Same file
        df2 = pd.read_excel(file2)
        self.assertEqual(len(df2), 2)

if __name__ == '__main__':
    unittest.main()
