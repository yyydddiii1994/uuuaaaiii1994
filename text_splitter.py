import tkinter as tk
from tkinter import messagebox
import traceback
import sys

from tkinter import filedialog
from tkinter import ttk
import os
import threading
import queue
import time
import math

class TextSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("テキストファイル分割ツール")
        self.root.geometry("500x400")

        self.filepath = tk.StringVar()
        self.split_count = tk.IntVar(value=2)
        self.instruction_text = tk.StringVar(value="次の行動: テキストファイルを選択してください")

        self.create_widgets()

    def create_widgets(self):
        # Instruction Label
        instruction_label = tk.Label(self.root, textvariable=self.instruction_text, font=("Arial", 12, "bold"), fg="blue")
        instruction_label.pack(pady=10)

        # File selection
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(file_frame, text="ファイル:").pack(side=tk.LEFT)
        tk.Entry(file_frame, textvariable=self.filepath, state='readonly', width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="参照", command=self.browse_file).pack(side=tk.LEFT)

        # Split count configuration
        split_frame = tk.Frame(self.root)
        split_frame.pack(pady=10)

        tk.Label(split_frame, text="分割数:").pack(side=tk.LEFT)
        tk.Spinbox(split_frame, from_=2, to=100, textvariable=self.split_count, width=5).pack(side=tk.LEFT, padx=5)

        # Execute button
        self.split_button = tk.Button(self.root, text="分割開始", command=self.start_split, state=tk.DISABLED)
        self.split_button.pack(pady=15)

        # Progress Display
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=20, pady=5)

        self.progress_label_text = tk.StringVar(value="進捗: 0%")
        self.progress_label = tk.Label(self.root, textvariable=self.progress_label_text)
        self.progress_label.pack(pady=5)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            self.filepath.set(filename)
            self.instruction_text.set("次の行動: 分割数を指定して「分割開始」をクリックしてください")
            self.split_button.config(state=tk.NORMAL)

    def start_split(self):
        self.split_button.config(state=tk.DISABLED)
        self.instruction_text.set("次の行動: 処理が完了するまでお待ちください...")
        self.progress_var.set(0)
        self.progress_label_text.set("進捗: 0%")

        filepath = self.filepath.get()
        num_parts = self.split_count.get()

        # Use queue for thread-safe UI updates
        self.q = queue.Queue()
        self.check_queue()

        # Start background thread
        thread = threading.Thread(target=self.split_file_thread, args=(filepath, num_parts))
        thread.daemon = True
        thread.start()

    def check_queue(self):
        try:
            while True:
                msg_type, data = self.q.get_nowait()
                if msg_type == "progress":
                    self.progress_var.set(data)
                    self.progress_label_text.set(f"進捗: {data:.1f}%")
                elif msg_type == "done":
                    self.instruction_text.set("次の行動: 処理が完了しました。別のファイルを選択するか終了してください")
                    self.split_button.config(state=tk.NORMAL)
                    messagebox.showinfo("完了", data)
                    return
                elif msg_type == "error":
                    self.instruction_text.set("次の行動: エラーが発生しました")
                    self.split_button.config(state=tk.NORMAL)
                    messagebox.showerror("エラー", data)
                    return
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def split_file_thread(self, filepath, num_parts):
        try:
            # Count total lines memory efficiently
            total_lines = 0
            with open(filepath, 'r', encoding='utf-8') as f:
                for _ in f:
                    total_lines += 1

            if total_lines == 0:
                self.q.put(("error", "ファイルが空です。"))
                return

            lines_per_part = math.ceil(total_lines / num_parts)
            base_name, ext = os.path.splitext(filepath)

            lines_written_total = 0
            actual_parts = 0

            with open(filepath, 'r', encoding='utf-8') as f:
                for i in range(num_parts):
                    output_filename = f"{base_name}_part{i+1}{ext}"

                    # Read lines_per_part for this chunk and write to output file
                    lines_in_this_part = 0

                    # Instead of buffering the whole part, we write line by line
                    # But we open the file only if there's at least one line to write
                    # Let's peek a line to see if we reached EOF
                    current_pos = f.tell()
                    first_line = f.readline()
                    if not first_line:
                        break # EOF reached

                    # Go back to start of line
                    f.seek(current_pos)

                    with open(output_filename, 'w', encoding='utf-8') as out_f:
                        for _ in range(lines_per_part):
                            line = f.readline()
                            if not line:
                                break
                            out_f.write(line)
                            lines_in_this_part += 1
                            lines_written_total += 1

                            if lines_written_total % 5000 == 0:
                                progress = (lines_written_total / total_lines) * 100
                                self.q.put(("progress", progress))

                    actual_parts += 1
                    progress = (lines_written_total / total_lines) * 100
                    self.q.put(("progress", progress))

                    time.sleep(0.1) # Small delay for smooth UI update

            self.q.put(("done", f"{actual_parts}個のファイルに分割しました。\n元のファイルと同じフォルダに保存されました。"))

        except Exception as e:
            self.q.put(("error", f"エラーが発生しました:\n{str(e)}"))

def main():
    try:
        root = tk.Tk()
        app = TextSplitterApp(root)
        root.mainloop()
    except Exception as e:
        error_msg = f"Application failed to start. Error:\n{e}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)

        # Fallback GUI
        error_root = tk.Tk()
        error_root.title("Startup Error")
        error_root.geometry("600x400")

        lbl = tk.Label(error_root, text="An unexpected error occurred during startup:", fg="red", font=("Arial", 12, "bold"))
        lbl.pack(pady=10)

        text_area = tk.Text(error_root, wrap=tk.WORD)
        text_area.insert(tk.END, error_msg)
        text_area.config(state=tk.DISABLED)
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        btn = tk.Button(error_root, text="Close", command=error_root.destroy)
        btn.pack(pady=10)

        error_root.mainloop()

if __name__ == "__main__":
    main()
