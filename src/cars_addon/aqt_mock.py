# src/cars_addon/aqt_mock.py

"""
Mocks the 'aqt' module, which is part of Anki's core code.
This allows running and testing addon modules in an environment
where Anki is not installed.
"""

import os
import json

class MockAddonManager:
    def getConfig(self, module_name):
        """
        Simulates getConfig to read the config.json from the filesystem.
        """
        try:
            # Assume __name__ is 'cars_addon' and config is in the same dir
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: aqt_mock could not find config.json.")
            return None

class MockMainWindow:
    def __init__(self):
        self.addonManager = MockAddonManager()

# Create a global 'mw' instance to be imported by other modules
mw = MockMainWindow()
