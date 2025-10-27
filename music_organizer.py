import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import queue
import shutil
import re
from concurrent.futures import ThreadPoolExecutor

try:
    from mutagen import File
    from mutagen.easyid3 import EasyID3
except ImportError:
    # アプリケーション起動時にエラーダイアログを表示する
    # この時点ではTkのメインループが始まっていないため、一時的なウィンドウを作成して表示
    root = tk.Tk()
    root.withdraw() # メインウィンドウは表示しない
    messagebox.showerror("ライブラリ不足エラー", "mutagenライブラリが見つかりません。\nターミナルで `pip install mutagen` を実行してインストールしてください。")
    root.destroy()
    exit() # アプリケーションを終了


class MusicOrganizerApp(tk.Tk):
    SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.m4a', '.mp4', '.flac')

    def __init__(self):
        super().__init__()
        self.title("音楽フォルダ整理アプリ")
        self.geometry("1400x800")

        self.source_folder = ""
        self.destination_folder = ""

        self.executor = ThreadPoolExecutor(max_workers=4)
        self.queue = queue.Queue()

        self.create_widgets()
        self.process_queue()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- フォルダ選択フレーム ---
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=5)

        self.select_source_button = ttk.Button(folder_frame, text="整理するフォルダを選択...", command=self.select_source_folder)
        self.select_source_button.pack(side=tk.LEFT, padx=(0, 5))
        self.source_folder_label = ttk.Label(folder_frame, text="フォルダが選択されていません", width=50)
        self.source_folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.select_dest_button = ttk.Button(folder_frame, text="保存先フォルダを選択...", command=self.select_destination_folder)
        self.select_dest_button.pack(side=tk.LEFT, padx=(10, 5))
        self.dest_folder_label = ttk.Label(folder_frame, text="フォルダが選択されていません", width=50)
        self.dest_folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- ファイルリストフレーム ---
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.file_list_tree = ttk.Treeview(
            middle_frame,
            columns=("original_path", "artist", "album", "track", "title", "new_path"),
            show="headings"
        )
        self.file_list_tree.heading("original_path", text="元の場所")
        self.file_list_tree.heading("artist", text="アーティスト")
        self.file_list_tree.heading("album", text="アルバム")
        self.file_list_tree.heading("track", text="トラック")
        self.file_list_tree.heading("title", text="曲名")
        self.file_list_tree.heading("new_path", text="整理後の場所")

        self.file_list_tree.column("original_path", width=300)
        self.file_list_tree.column("artist", width=150)
        self.file_list_tree.column("album", width=200)
        self.file_list_tree.column("track", width=50, anchor='center')
        self.file_list_tree.column("title", width=200)
        self.file_list_tree.column("new_path", width=300)

        vsb = ttk.Scrollbar(middle_frame, orient="vertical", command=self.file_list_tree.yview)
        hsb = ttk.Scrollbar(middle_frame, orient="horizontal", command=self.file_list_tree.xview)
        self.file_list_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_list_tree.pack(fill=tk.BOTH, expand=True)

        # --- 下部フレーム ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=5)
        self.organize_button = ttk.Button(bottom_frame, text="整理開始", command=self.start_organization, state=tk.DISABLED)
        self.organize_button.pack(side=tk.LEFT)
        self.progress_bar = ttk.Progressbar(bottom_frame, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        self.status_label = ttk.Label(bottom_frame, text="準備完了")
        self.status_label.pack(side=tk.LEFT, padx=10)

    def select_source_folder(self):
        folder = filedialog.askdirectory()
        if not folder: return
        self.source_folder = folder
        self.source_folder_label.config(text=self.source_folder)
        self.toggle_organize_button()
        self.set_ui_state(False)
        self.file_list_tree.delete(*self.file_list_tree.get_children())
        self.status_label.config(text="ファイルのスキャンを開始します...")
        self.executor.submit(self.scan_folder_worker, self.source_folder)

    def select_destination_folder(self):
        folder = filedialog.askdirectory()
        if not folder: return
        self.destination_folder = folder
        self.dest_folder_label.config(text=self.destination_folder)
        self.toggle_organize_button()

    def toggle_organize_button(self):
        if self.source_folder and self.destination_folder:
            self.organize_button.config(state=tk.NORMAL)
        else:
            self.organize_button.config(state=tk.DISABLED)

    def set_ui_state(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.select_source_button.config(state=state)
        self.select_dest_button.config(state=state)
        self.organize_button.config(state=state)

    def scan_folder_worker(self, folder_path):
        self.queue.put(("status", "フォルダをスキャン中..."))
        try:
            file_paths = [os.path.join(r, f) for r, _, fs in os.walk(folder_path) for f in fs if f.lower().endswith(self.SUPPORTED_EXTENSIONS)]
            self.queue.put(("scan_total", len(file_paths)))
            for file_path in file_paths:
                self.executor.submit(self.read_metadata_worker, file_path)
        except Exception as e:
            self.queue.put(("error", f"フォルダスキャン中にエラーが発生しました: {e}"))
        if not file_paths: # ファイルが見つからなかった場合
             self.queue.put(("scan_complete", "対象ファイルが見つかりませんでした。"))


    def read_metadata_worker(self, file_path):
        try:
            audio = File(file_path, easy=True)
            if not audio:
                 self.queue.put(("file_found", (file_path, "不明", "不明", "", os.path.basename(file_path), "")))
                 return

            artist = audio.get('artist', ['不明'])[0]
            album = audio.get('album', ['不明'])[0]
            title = audio.get('title', [os.path.splitext(os.path.basename(file_path))[0]])[0]
            track = audio.get('tracknumber', [''])[0].split('/')[0] # '1/12'のような形式に対応

            self.queue.put(("file_found", (file_path, artist, album, track, title, "")))
        except Exception as e:
            self.queue.put(("error", f"メタデータ読み取りエラー: {os.path.basename(file_path)} - {e}"))
            self.queue.put(("file_found", (file_path, "エラー", "エラー", "", os.path.basename(file_path), "")))

    def start_organization(self):
        if not self.source_folder or not self.destination_folder:
            messagebox.showwarning("確認", "整理するフォルダと保存先フォルダの両方を選択してください。")
            return
        if self.source_folder == self.destination_folder:
            if not messagebox.askyesno("警告", "整理元と保存先が同じフォルダです。ファイルを上書きする可能性がありますが、よろしいですか？"):
                return

        self.set_ui_state(False)
        self.status_label.config(text="整理を開始します...")

        items = self.file_list_tree.get_children()
        self.progress_bar['maximum'] = len(items)
        self.progress_bar['value'] = 0

        for item_id in items:
            values = self.file_list_tree.item(item_id, 'values')
            self.executor.submit(self.organize_file_worker, item_id, values)

    def sanitize_filename(self, name):
        # ファイル名やフォルダ名として使えない文字を置換
        return re.sub(r'[\\/*?:"<>|]', '_', name)

    def organize_file_worker(self, item_id, values):
        try:
            original_path, artist, album, track, title, _ = values

            # フォルダとファイル名を生成
            s_artist = self.sanitize_filename(artist)
            s_album = self.sanitize_filename(album)

            ext = os.path.splitext(original_path)[1]
            if track:
                s_title = self.sanitize_filename(f"{int(track):02d} - {title}{ext}")
            else:
                s_title = self.sanitize_filename(f"{title}{ext}")

            # 新しいパスを作成
            target_dir = os.path.join(self.destination_folder, s_artist, s_album)
            os.makedirs(target_dir, exist_ok=True)
            new_path = os.path.join(target_dir, s_title)

            # ファイルを移動
            shutil.move(original_path, new_path)

            self.queue.put(("organize_progress", (item_id, new_path)))
        except Exception as e:
            self.queue.put(("error", f"ファイル整理エラー: {os.path.basename(original_path)} - {e}"))
            self.queue.put(("organize_progress", (item_id, f"エラー: {e}")))

    def process_queue(self):
        try:
            while not self.queue.empty():
                msg_type, data = self.queue.get_nowait()
                if msg_type == "status":
                    self.status_label.config(text=data)
                elif msg_type == "scan_total":
                    self.progress_bar['maximum'] = data if data > 0 else 1
                    self.progress_bar['value'] = 0
                elif msg_type == "file_found":
                    self.file_list_tree.insert("", "end", values=data, iid=data[0])
                    self.progress_bar['value'] += 1
                    if self.progress_bar['value'] >= self.progress_bar['maximum']:
                         self.queue.put(("scan_complete", f"{self.progress_bar['maximum']}個のファイルのメタデータ読み取り完了。"))
                elif msg_type == "scan_complete":
                    self.status_label.config(text=data)
                    self.set_ui_state(True)
                    self.toggle_organize_button()
                elif msg_type == "organize_progress":
                    item_id, new_path = data
                    self.file_list_tree.set(item_id, "new_path", new_path)
                    self.progress_bar['value'] += 1
                    if self.progress_bar['value'] >= self.progress_bar['maximum']:
                        self.queue.put(("organize_complete", f"{self.progress_bar['maximum']}個のファイルの整理が完了しました。"))
                elif msg_type == "organize_complete":
                    self.status_label.config(text=data)
                    self.set_ui_state(True)
                elif msg_type == "error":
                    print(data) # コンソールにエラー出力
        finally:
            self.after(100, self.process_queue)

    def on_closing(self):
        if messagebox.askokcancel("終了", "アプリケーションを終了しますか？\n処理中の場合、中断されます。"):
            self.executor.shutdown(wait=False, cancel_futures=True)
            self.destroy()

if __name__ == "__main__":
    app = MusicOrganizerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
