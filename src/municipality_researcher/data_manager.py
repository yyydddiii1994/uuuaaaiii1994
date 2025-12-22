import pandas as pd
import os
import shutil

class DataManager:
    def __init__(self, data_file="data.xlsx", languages_file="src/municipality_researcher/languages.txt", sample_csv="src/municipality_researcher/sample_data.csv"):
        self.data_file = data_file
        self.languages = self._load_languages(languages_file)
        self.df = self._load_data(sample_csv)

    def _load_languages(self, languages_file):
        with open(languages_file, "r", encoding="utf-8") as f:
            # Clean and deduplicate languages
            langs = [line.strip() for line in f if line.strip()]
            return sorted(list(set(langs)), key=langs.index) # Keep order but unique

    def _load_data(self, sample_csv):
        if os.path.exists(self.data_file):
            try:
                return pd.read_excel(self.data_file, index_col=None)
            except Exception as e:
                print(f"Error loading Excel: {e}")
                # Fallback to creating new from sample if load fails (or handle appropriately)

        # Initialize from sample csv
        df = pd.read_csv(sample_csv, encoding='utf-8')

        # Ensure all language columns exist
        missing_langs = [lang for lang in self.languages if lang not in df.columns]
        if missing_langs:
            new_cols = pd.DataFrame(0, index=df.index, columns=missing_langs)
            df = pd.concat([df, new_cols], axis=1)

        return df

    def save_data(self):
        self.df.to_excel(self.data_file, index=False)

    def get_municipalities_list(self):
        # Return a list of strings or tuples for the listbox
        # "Prefecture - Municipality"
        return self.df.apply(lambda row: f"{row['県名']} - {row['自治体名']}", axis=1).tolist()

    def get_record(self, index):
        if 0 <= index < len(self.df):
            return self.df.iloc[index]
        return None

    def update_record(self, index, data):
        """
        data: dict of column -> value
        """
        if 0 <= index < len(self.df):
            for col, val in data.items():
                if col in self.df.columns:
                    self.df.at[index, col] = val
            self.save_data()
            return True
        return False
