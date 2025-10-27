import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import sys  # sysモジュールをインポート
import pyscreenshot as ImageGrab # pyscreenshotをインポート
import backup_logic as be

class BackupApp(tk.Tk):
    def __init__(self, test_mode=False): # test_mode引数を追加
        super().__init__()
        self.title("iPad Backup Utility")
        self.geometry("700x550")

        self.queue = queue.Queue()
        self._create_widgets()
        self.after(100, self.process_queue)

        if test_mode:
            self.after(2000, self.take_screenshot_and_exit) # 2秒後にスクリーンショット撮影

    def take_screenshot_and_exit(self):
        print("Taking screenshot...")
        # アプリケーションのウィンドウを含むスクリーンショットを撮る
        # x, y, w, h を指定してウィンドウの領域だけを撮ることも可能だが、
        # xvfb環境ではウィンドウ位置の特定が難しいため、フルスクリーンで代用する
        screenshot = ImageGrab.grab()
        screenshot_path = "verification.png"
        screenshot.save(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        self.destroy() # アプリケーションを終了

    def _create_widgets(self):
        # (ウィジェットの作成コードは変更なし)
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        device_frame = ttk.LabelFrame(main_frame, text="Device Information", padding="10")
        device_frame.pack(fill=tk.X, pady=5)

        self.device_info_label = ttk.Label(device_frame, text="Press 'Refresh' to get device info.", justify=tk.LEFT)
        self.device_info_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        refresh_button = ttk.Button(device_frame, text="Refresh", command=self.get_device_info)
        refresh_button.pack(side=tk.RIGHT, padx=5)

        content_frame = ttk.LabelFrame(main_frame, text="Backup Contents", padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tree = ttk.Treeview(content_frame, columns=("type", "path"), show="tree headings")
        self.tree.heading("#0", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("path", text="Path")
        self.tree.column("#0", width=250)
        self.tree.column("type", width=80)
        self.tree.column("path", width=300)

        ysb = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        xsb = ttk.Scrollbar(content_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)

        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        xsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", self.on_item_double_click)
        self.tree.bind("<Return>", self.on_item_double_click)

        list_files_button = ttk.Button(main_frame, text="Check Root Contents", command=lambda: self.list_files('/'))
        list_files_button.pack(pady=5)

        backup_frame = ttk.LabelFrame(main_frame, text="Backup Execution", padding="10")
        backup_frame.pack(fill=tk.X, pady=5)

        self.backup_path = tk.StringVar()
        path_entry = ttk.Entry(backup_frame, textvariable=self.backup_path, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        path_entry.insert(0, "Enter backup path here")

        browse_button = ttk.Button(backup_frame, text="Browse...", command=self.browse_folder)
        browse_button.pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(backup_frame, text="Start Backup", command=self.start_backup)
        self.start_button.pack(side=tk.RIGHT, padx=5)

        # --- 復元フレーム ---
        restore_frame = ttk.LabelFrame(main_frame, text="Restore from Backup", padding="10")
        restore_frame.pack(fill=tk.X, pady=5)

        self.restore_path = tk.StringVar()
        restore_path_entry = ttk.Entry(restore_frame, textvariable=self.restore_path, width=50)
        restore_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        restore_path_entry.insert(0, "Enter restore path here")

        restore_browse_button = ttk.Button(restore_frame, text="Browse...", command=self.browse_restore_folder)
        restore_browse_button.pack(side=tk.LEFT, padx=5)

        self.restore_button = ttk.Button(restore_frame, text="Start Restore", command=self.start_restore)
        self.restore_button.pack(side=tk.RIGHT, padx=5)


        progress_frame = ttk.Frame(main_frame, padding=(0, 5))
        progress_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=(0,5))

        self.status_label = ttk.Label(progress_frame, text="Ready", anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

    # (以降のメソッドは変更なし)
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder: self.backup_path.set(folder)

    def browse_restore_folder(self):
        folder = filedialog.askdirectory()
        if folder: self.restore_path.set(folder)

    def start_threaded_task(self, task, *args):
        self.status_label.config(text="Processing...")
        self.progress_bar["value"] = 0
        threading.Thread(target=task, args=args, daemon=True).start()

    def get_device_info(self):
        self.device_info_label.config(text="Getting device info...")
        self.start_threaded_task(self._get_device_info_worker)

    def _get_device_info_worker(self):
        try:
            info = be.get_device_info()
            self.queue.put(("device_info", info))
        except be.BackupError as e:
            self.queue.put(("error", str(e)))

    def list_files(self, path):
        self.status_label.config(text=f"Fetching file list for {path}...")
        self.start_threaded_task(self._list_files_worker, path)

    def _list_files_worker(self, path):
        try:
            files = be.list_files_and_folders(path)
            self.queue.put(("file_list", (path, files)))
        except be.BackupError as e:
            self.queue.put(("error", str(e)))

    def on_item_double_click(self, event):
        item_id = self.tree.focus()
        if not item_id: return
        item = self.tree.item(item_id)
        item_type = item["values"][0]
        item_path = item["values"][1]
        if item_type == "folder":
            if not self.tree.get_children(item_id):
                self.list_files(item_path)

    def start_backup(self):
        path = self.backup_path.get()
        if not path or path == "Enter backup path here":
            messagebox.showwarning("Warning", "Please select a backup destination folder.")
            return
        self.start_button.config(state=tk.DISABLED)
        self.start_threaded_task(self._start_backup_worker, path)

    def _start_backup_worker(self, path):
        try:
            be.start_backup(path, self.update_progress)
        except be.BackupError as e:
            self.queue.put(("error", str(e)))

    def start_restore(self):
        path = self.restore_path.get()
        if not path or path == "Enter restore path here":
            messagebox.showwarning("Warning", "Please select a restore source folder.")
            return

        if messagebox.askyesno("Confirm Restore",
                                "WARNING: This will overwrite data on your iPad. "
                                "Are you sure you want to proceed?"):
            self.restore_button.config(state=tk.DISABLED)
            self.start_threaded_task(self._start_restore_worker, path)

    def _start_restore_worker(self, path):
        try:
            be.start_restore(path, self.update_progress)
        except be.BackupError as e:
            self.queue.put(("error", str(e)))

    def update_progress(self, progress, message):
        self.queue.put(("progress", (progress, message)))

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                if msg_type == "device_info":
                    info_text = "\n".join(f"{k}: {v}" for k, v in data.items())
                    self.device_info_label.config(text=info_text)
                    self.status_label.config(text="Device info updated.")
                elif msg_type == "file_list":
                    path, files = data
                    self.populate_tree(path, files)
                    self.status_label.config(text=f"Contents of {path} listed.")
                elif msg_type == "progress":
                    progress, message = data
                    self.progress_bar["value"] = progress
                    self.status_label.config(text=message)
                    if progress == 100:
                        self.start_button.config(state=tk.NORMAL)
                        self.restore_button.config(state=tk.NORMAL)
                        if "successfully" in message.lower():
                            messagebox.showinfo("Success", message)
                elif msg_type == "error":
                    self.status_label.config(text=f"Error: {data}")
                    messagebox.showerror("Error", data)
                    self.start_button.config(state=tk.NORMAL)
                    self.restore_button.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def populate_tree(self, path, files):
        parent_node_id = ""
        if path != '/':
             for item_id in self.tree.get_children(""): # ルートから探索
                 if self.tree.item(item_id)["values"][1] == path:
                     parent_node_id = item_id
                     break
        if parent_node_id:
            for child in self.tree.get_children(parent_node_id): self.tree.delete(child)
        else:
             for child in self.tree.get_children(): self.tree.delete(child)

        for item in files:
            self.tree.insert(parent_node_id, "end", text=item["name"], values=(item["type"], item["path"]))

if __name__ == "__main__":
    # コマンドライン引数 '--test' をチェック
    is_test_mode = "--test" in sys.argv
    app = BackupApp(test_mode=is_test_mode)
    app.mainloop()
