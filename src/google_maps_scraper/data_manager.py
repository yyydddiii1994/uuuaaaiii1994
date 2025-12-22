import pandas as pd
import json
import os
import csv
from datetime import datetime
import re

class DataManager:
    def __init__(self, config):
        self.config = config
        self.output_dir = "output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.progress_file = "progress.json"

        # セッションごとのファイル名を固定
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        self.current_excel_file = f"{self.output_dir}/結果_{timestamp}.xlsx"
        self.current_csv_file = f"{self.output_dir}/backup_{timestamp}.csv"

    def read_keywords(self, filepath):
        """TXTまたはCSVからキーワードを読み込む"""
        keywords = []
        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath, header=None)
                keywords = df.iloc[:, 0].dropna().astype(str).tolist()
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    keywords = [line.strip() for line in f if line.strip()]
            return keywords
        except Exception as e:
            print(f"キーワード読み込みエラー: {e}")
            return []

    def save_results(self, data):
        """結果をExcelに保存（上書き更新）"""
        if not data: return None

        df = pd.DataFrame(data, columns=["Keyword", "Name", "Address", "Phone", "URL"])

        # 重複除去 (店舗名 + 住所)
        df.drop_duplicates(subset=['Name', 'Address'], keep='first', inplace=True)

        try:
            # Excel保存
            df.to_excel(self.current_excel_file, index=False)
            return self.current_excel_file
        except Exception as e:
            print(f"Excel保存エラー: {e}")
            # バックアップCSV保存
            try:
                df.to_csv(self.current_csv_file, index=False, encoding='utf-8-sig')
                return self.current_csv_file
            except Exception as csv_e:
                print(f"CSV保存エラー: {csv_e}")
                return None

    def load_progress(self):
        """進捗状況を読み込む"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"processed_keywords": [], "last_run": None}
        return {"processed_keywords": [], "last_run": None}

    def save_progress(self, processed_keywords):
        """進捗状況を保存する"""
        data = {
            "processed_keywords": processed_keywords,
            "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def log_error(self, keyword, error_message):
        """エラーログを追記する"""
        with open("error_log.txt", "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] Keyword: {keyword} - Error: {error_message}\n")
