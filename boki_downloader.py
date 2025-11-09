import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import time
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import queue
import os
import re

# --- Constants and Scraping Logic ---
EXAM_PAGE_URLS = [
    "https://www.kentei.ne.jp/48153", "https://www.kentei.ne.jp/46525",
    "https://www.kentei.ne.jp/45137", "https://www.kentei.ne.jp/43001",
    "https://www.kentei.ne.jp/40744", "https://www.kentei.ne.jp/38658",
    "https://www.kentei.ne.jp/37295", "https://www.kentei.ne.jp/35588",
    "https://www.kentei.ne.jp/34294",
]

def get_pdfs_from_page(session, url, log_callback):
    try:
        response = session.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'lxml')
        title_tag = soup.find('h1')
        title_prefix = title_tag.text.strip() if title_tag else "Unknown Exam"
        pdfs = []
        content = soup.find('article', class_='post-content') or soup.body
        for a_tag in content.find_all('a', href=lambda href: href and href.endswith('.pdf')):
            pdf_url = urljoin(url, a_tag['href'])
            description = f"{title_prefix} - {a_tag.text.strip()}"
            pdfs.append({'url': pdf_url, 'description': description})
        return pdfs
    except requests.exceptions.RequestException as e:
        log_callback(f"エラー: {url} の解析中に問題が発生しました - {e}")
        return []

# --- GUI Application ---
class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("日商簿記1級 過去問ダウンローダー")
        self.root.geometry("700x450")
        self.log_queue = queue.Queue()
        self.setup_ui()
        self.process_log_queue()

    def setup_ui(self):
        dir_frame = tk.Frame(self.root, padx=10, pady=10)
        dir_frame.pack(fill=tk.X)
        tk.Label(dir_frame, text="ダウンロード先:").pack(side=tk.LEFT)
        self.dir_entry = tk.Entry(dir_frame)
        self.dir_entry.insert(0, os.path.join(os.path.expanduser("~"), "Downloads"))
        self.dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(dir_frame, text="フォルダを選択", command=self.browse_directory).pack(side=tk.LEFT)

        self.download_button = tk.Button(self.root, text="ダウンロード開始", command=self.start_download, pady=5)
        self.download_button.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(self.root, text="進捗:", justify=tk.LEFT).pack(fill=tk.X, padx=10, pady=(5, 0))
        self.log_area = scrolledtext.ScrolledText(self.root, height=15, state='disabled')
        self.log_area.pack(padx=10, pady=5, expand=True, fill=tk.BOTH)

    def browse_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, dir_path)

    def log(self, message):
        self.log_queue.put(message)

    def process_log_queue(self):
        try:
            while not self.log_queue.empty():
                message = self.log_queue.get_nowait()
                self.log_area.config(state='normal')
                self.log_area.insert(tk.END, message + '\n')
                self.log_area.config(state='disabled')
                self.log_area.see(tk.END)
        finally:
            self.root.after(100, self.process_log_queue)

    def start_download(self):
        download_dir = self.dir_entry.get()
        if not os.path.isdir(download_dir):
            messagebox.showerror("エラー", "指定されたダウンロード先フォルダが存在しません。")
            return

        self.download_button.config(state='disabled', text='ダウンロード中...')
        threading.Thread(target=self.download_thread, args=(download_dir,), daemon=True).start()

    def sanitize_filename(self, text):
        text = re.sub(r'[\s/\\:\*\?"<>\|]', '_', text)
        return text[:150]

    def download_thread(self, download_dir):
        try:
            self.log("--- ダウンロードプロセス開始 ---")
            self.log("PDFリンクのリストを取得しています...")

            all_pdfs = []
            with requests.Session() as session:
                session.headers.update({'User-Agent': 'Mozilla/5.0'})
                for url in EXAM_PAGE_URLS:
                    all_pdfs.extend(get_pdfs_from_page(session, url, self.log))
                    time.sleep(1)

            if not all_pdfs:
                self.log("ダウンロード対象のPDFが見つかりませんでした。")
                return

            self.log(f"合計 {len(all_pdfs)} 件のPDFが見つかりました。ダウンロードを開始します。")
            self.log("-" * 20)

            for i, pdf in enumerate(all_pdfs):
                filename = self.sanitize_filename(pdf['description']) + '.pdf'
                filepath = os.path.join(download_dir, filename)
                self.log(f"({i+1}/{len(all_pdfs)}) ダウンロード中: {filename}")

                try:
                    response = requests.get(pdf['url'], stream=True)
                    response.raise_for_status()
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    self.log(f" -> 保存完了: {filepath}")
                except requests.exceptions.RequestException as e:
                    self.log(f" -> エラー: {filename} のダウンロードに失敗しました - {e}")

                if i < len(all_pdfs) - 1:
                    self.log("次のダウンロードまで5秒間待機します...")
                    time.sleep(5)

            self.log("-" * 20)
            self.log("--- すべてのダウンロードが完了しました ---")
            messagebox.showinfo("完了", "すべてのダウンロードが完了しました。")

        except Exception as e:
            self.log(f"致命的なエラーが発生しました: {e}")
            messagebox.showerror("エラー", f"ダウンロード中に予期せぬエラーが発生しました:\n{e}")
        finally:
            self.download_button.config(state='normal', text='ダウンロード開始')

if __name__ == '__main__':
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()
