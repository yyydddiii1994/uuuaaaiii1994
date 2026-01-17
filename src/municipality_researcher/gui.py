import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import platform

class MunicipalityApp:
    def __init__(self, root, data_manager):
        self.root = root
        self.root.title("自治体ウェブサイト調査ツール")
        self.root.geometry("1200x800")
        self.dm = data_manager

        self._setup_ui()
        self._load_list()

    def _setup_ui(self):
        # PanedWindow for split view
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left side: List
        self.frame_list = ttk.Frame(self.paned_window, width=300)
        self.paned_window.add(self.frame_list, weight=1)

        self.listbox = tk.Listbox(self.frame_list)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = ttk.Scrollbar(self.frame_list, orient="vertical", command=self.listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Right side: Details
        self.frame_detail = ttk.Frame(self.paned_window)
        self.paned_window.add(self.frame_detail, weight=3)

        # Scrollable Frame for Details (because of many languages)
        self.canvas = tk.Canvas(self.frame_detail)
        self.detail_scrollbar = ttk.Scrollbar(self.frame_detail, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.detail_scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.detail_scrollbar.pack(side="right", fill="y")

        # Mousewheel scrolling - Cross-platform support
        self._bind_mousewheel(self.canvas)

        self._build_detail_fields()

    def _bind_mousewheel(self, widget):
        system = platform.system()
        if system == "Linux":
            widget.bind_all("<Button-4>", self._on_mousewheel)
            widget.bind_all("<Button-5>", self._on_mousewheel)
        else:
            widget.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _build_detail_fields(self):
        # Header Info
        self.lbl_pref = ttk.Label(self.scrollable_frame, text="県名: ", font=("Arial", 12, "bold"))
        self.lbl_pref.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.lbl_muni = ttk.Label(self.scrollable_frame, text="自治体名: ", font=("Arial", 12, "bold"))
        self.lbl_muni.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # URL
        ttk.Label(self.scrollable_frame, text="公式サイト:").grid(row=1, column=0, sticky="w", padx=5)
        self.entry_url = ttk.Entry(self.scrollable_frame, width=50)
        self.entry_url.grid(row=1, column=1, columnspan=2, sticky="we", padx=5)
        ttk.Button(self.scrollable_frame, text="開く", command=self._open_url).grid(row=1, column=3, padx=5)

        # Furigana
        ttk.Label(self.scrollable_frame, text="ふりがな機能:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.var_furigana = tk.StringVar()
        self.cb_furigana = ttk.Combobox(self.scrollable_frame, textvariable=self.var_furigana, values=["有", "無"])
        self.cb_furigana.grid(row=2, column=1, sticky="w", padx=5)

        # Remarks
        ttk.Label(self.scrollable_frame, text="備考:").grid(row=3, column=0, sticky="w", padx=5)
        self.entry_remarks = ttk.Entry(self.scrollable_frame, width=50)
        self.entry_remarks.grid(row=3, column=1, columnspan=3, sticky="we", padx=5)

        # Translation
        ttk.Separator(self.scrollable_frame, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=4, sticky="ew", pady=10)
        ttk.Label(self.scrollable_frame, text="翻訳情報", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="w", padx=5)

        ttk.Label(self.scrollable_frame, text="翻訳の有無:").grid(row=6, column=0, sticky="w", padx=5)
        self.var_trans_presence = tk.StringVar()
        self.cb_trans_presence = ttk.Combobox(self.scrollable_frame, textvariable=self.var_trans_presence, values=["有", "無", "機械"])
        self.cb_trans_presence.grid(row=6, column=1, sticky="w", padx=5)

        ttk.Label(self.scrollable_frame, text="翻訳種類:").grid(row=7, column=0, sticky="w", padx=5)
        self.var_trans_type = tk.StringVar()
        self.cb_trans_type = ttk.Combobox(self.scrollable_frame, textvariable=self.var_trans_type, values=["Google翻訳サービス", "DeepL", "独自システム", "その他", ""])
        self.cb_trans_type.grid(row=7, column=1, sticky="w", padx=5)

        ttk.Label(self.scrollable_frame, text="提供言語数:").grid(row=8, column=0, sticky="w", padx=5)
        self.var_lang_count = tk.StringVar()
        ttk.Entry(self.scrollable_frame, textvariable=self.var_lang_count, width=10).grid(row=8, column=1, sticky="w", padx=5)

        # Languages
        ttk.Separator(self.scrollable_frame, orient=tk.HORIZONTAL).grid(row=9, column=0, columnspan=4, sticky="ew", pady=10)
        ttk.Label(self.scrollable_frame, text="対応言語", font=("Arial", 10, "bold")).grid(row=10, column=0, sticky="w", padx=5)

        self.lang_vars = {}
        row = 11
        col = 0
        for lang in self.dm.languages:
            var = tk.IntVar()
            self.lang_vars[lang] = var
            cb = ttk.Checkbutton(self.scrollable_frame, text=lang, variable=var)
            cb.grid(row=row, column=col, sticky="w", padx=2)

            col += 1
            if col > 3: # 4 columns
                col = 0
                row += 1

        # Save Button
        ttk.Button(self.scrollable_frame, text="保存 (Save)", command=self._save_record).grid(row=row+1, column=0, columnspan=4, pady=20)

    def _load_list(self):
        self.listbox.delete(0, tk.END)
        items = self.dm.get_municipalities_list()
        for item in items:
            self.listbox.insert(tk.END, item)

    def _on_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        index = sel[0]
        self.current_index = index
        self._load_record(index)

    def _load_record(self, index):
        record = self.dm.get_record(index)
        if record is None:
            return

        self.lbl_pref.config(text=f"県名: {record['県名']}")
        self.lbl_muni.config(text=f"自治体名: {record['自治体名']}")

        self.entry_url.delete(0, tk.END)
        if pd.notna(record['公式サイト']):
            self.entry_url.insert(0, str(record['公式サイト']))

        self.var_furigana.set(str(record['ふりがな機能']) if pd.notna(record['ふりがな機能']) else "")

        self.entry_remarks.delete(0, tk.END)
        if pd.notna(record['備考']):
            self.entry_remarks.insert(0, str(record['備考']))

        self.var_trans_presence.set(str(record['翻訳の有無']) if pd.notna(record['翻訳の有無']) else "")
        self.var_trans_type.set(str(record['翻訳種類']) if pd.notna(record['翻訳種類']) else "")
        self.var_lang_count.set(str(record['提供言語数']) if pd.notna(record['提供言語数']) else "")

        # Load languages
        for lang, var in self.lang_vars.items():
            val = record.get(lang, 0)
            if pd.isna(val): val = 0
            var.set(int(val))

    def _open_url(self):
        url = self.entry_url.get()
        if url:
            webbrowser.open(url)

    def _save_record(self):
        if not hasattr(self, 'current_index'):
            return

        data = {
            '公式サイト': self.entry_url.get(),
            'ふりがな機能': self.var_furigana.get(),
            '備考': self.entry_remarks.get(),
            '翻訳の有無': self.var_trans_presence.get(),
            '翻訳種類': self.var_trans_type.get(),
            '提供言語数': self.var_lang_count.get()
        }

        # Count selected languages
        count = 0
        for lang, var in self.lang_vars.items():
            val = var.get()
            data[lang] = val
            if val == 1:
                count += 1

        # Update language count in UI and data
        self.var_lang_count.set(str(count))
        data['提供言語数'] = count

        if self.dm.update_record(self.current_index, data):
            messagebox.showinfo("成功", "保存しました")
        else:
            messagebox.showerror("エラー", "保存に失敗しました")
