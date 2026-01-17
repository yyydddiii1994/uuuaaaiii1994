import tkinter as tk
from gui import MunicipalityApp
from data_manager import DataManager
import os

def main():
    root = tk.Tk()

    # Ensure directories exist
    os.makedirs("data", exist_ok=True)

    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(base_dir, "../../data/municipality_data.xlsx")
    languages_file = os.path.join(base_dir, "languages.txt")
    sample_csv = os.path.join(base_dir, "sample_data.csv")

    dm = DataManager(data_file=data_file, languages_file=languages_file, sample_csv=sample_csv)

    app = MunicipalityApp(root, dm)
    root.mainloop()

if __name__ == "__main__":
    main()
