import tkinter as tk
from tkhtmlview import HTMLScrolledText
import cloudscraper
from bs4 import BeautifulSoup
import threading
import queue
import time
import os

class ContentViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Content Viewer")
        self.geometry("800x600")

        self.scraper = cloudscraper.create_scraper()
        self.failed_chapters_lock = threading.Lock()

        self.url_frame = tk.Frame(self)
        self.url_frame.pack(fill=tk.X, padx=10, pady=5)
        self.url_label = tk.Label(self.url_frame, text="URL:")
        self.url_label.pack(side=tk.LEFT)
        self.url_entry = tk.Entry(self.url_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.url_entry.insert(0, "https://w.atwiki.jp/kwskp4/pages/166.html")
        self.fetch_button = tk.Button(self.url_frame, text="Fetch", command=self.fetch_content)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        self.text_area = HTMLScrolledText(self, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.queue = queue.Queue()
        self.after(100, self.process_queue)

        self.download_frame = tk.Frame(self)
        self.download_frame.pack(fill=tk.X, padx=10, pady=5)
        self.rezero_button = tk.Button(self.download_frame, text="Download Re:Zero All Chapters", command=self.download_rezero)
        self.rezero_button.pack(side=tk.LEFT)
        self.status_label = tk.Label(self.download_frame, text="Status: Idle")
        self.status_label.pack(side=tk.LEFT, padx=5)

    def chunk_list(self, lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def download_rezero(self):
        self.rezero_button.config(state=tk.DISABLED)
        thread = threading.Thread(target=self.rezero_download_thread)
        thread.start()

    def rezero_download_thread(self):
        failed_chapters = []
        try:
            self.queue.put(("download_status", "Status: Bypassing Cloudflare..."))
            base_url = "https://ncode.syosetu.com"
            toc_url = f"{base_url}/n2267be/"
            response = self.scraper.get(toc_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            chapter_elements = soup.select('.p-eplist__sublist a.p-eplist__subtitle')
            if not chapter_elements:
                self.queue.put(("download_status", "Status: Error - Could not find chapter links."))
                return

            chapter_urls = [f"{base_url}{a['href']}" for a in chapter_elements]
            self.queue.put(("download_status", f"Status: Found {len(chapter_urls)} chapters. Starting download..."))

            num_threads = 4
            chunk_size = (len(chapter_urls) + num_threads - 1) // num_threads
            url_chunks = list(self.chunk_list(chapter_urls, chunk_size))
            output_dir = "rezero_chapters"
            os.makedirs(output_dir, exist_ok=True)
            download_threads = []
            for i, chunk in enumerate(url_chunks):
                output_filename = os.path.join(output_dir, f"rezero_part_{i+1}.txt")
                with open(output_filename, "w") as f: f.write("")
                thread = threading.Thread(target=self.download_chapter_chunk, args=(chunk, output_filename, i + 1, failed_chapters))
                download_threads.append(thread)
                thread.start()
            for thread in download_threads:
                thread.join()
            if failed_chapters:
                self.queue.put(("download_status", f"Status: Complete with {len(failed_chapters)} errors. See failed_chapters.txt"))
                with open("failed_chapters.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(failed_chapters))
            else:
                self.queue.put(("download_status", f"Status: Download complete! Files in '{output_dir}' directory."))
        except Exception as e:
            self.queue.put(("download_status", f"Status: An unexpected error occurred: {e}"))
        finally:
            self.queue.put(("enable_button", None))

    def download_chapter_chunk(self, urls, output_filename, chunk_num, failed_list):
        for i, url in enumerate(urls, 1):
            try:
                if i % 10 == 0:
                    self.queue.put(("download_status", f"Status: Chunk {chunk_num}: Chapter {i}/{len(urls)}..."))
                response = self.scraper.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                title = soup.find('p', class_='novel_subtitle').get_text(strip=True)
                honbun = soup.find('div', id='novel_honbun').get_text(strip=False)
                with open(output_filename, "a", encoding="utf-8") as f:
                    f.write(f"\n--- {title} ---\n\n")
                    f.write(honbun)
                if i % 10 == 0:
                    time.sleep(1)
            except Exception:
                with self.failed_chapters_lock:
                    failed_list.append(url)
                continue

    def process_queue(self):
        try:
            msg_type, content = self.queue.get_nowait()
            if msg_type == "status": self.text_area.set_html(f"<i>{content}</i>")
            elif msg_type == "content": self.text_area.set_html(content)
            elif msg_type == "download_status": self.status_label.config(text=content)
            elif msg_type == "enable_button": self.rezero_button.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def fetch_content(self):
        url = self.url_entry.get()
        if not url:
            self.queue.put(("status", "Please enter a URL."))
            return
        self.queue.put(("status", "Fetching content..."))
        thread = threading.Thread(target=self.fetch_content_thread, args=(url,))
        thread.start()

    def fetch_content_thread(self, url):
        try:
            response = self.scraper.get(url)
            response.raise_for_status()
            self.queue.put(("content", response.text))
        except Exception as e:
            self.queue.put(("status", f"Failed to fetch content: {e}"))

if __name__ == "__main__":
    app = ContentViewer()
    app.mainloop()
