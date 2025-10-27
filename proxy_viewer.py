import tkinter as tk
from tkinter import scrolledtext
import requests
from bs4 import BeautifulSoup
import random
import threading
import queue

class ProxyViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Proxy Viewer")
        self.geometry("800x600")

        self.url_frame = tk.Frame(self)
        self.url_frame.pack(fill=tk.X, padx=10, pady=5)

        self.url_label = tk.Label(self.url_frame, text="URL:")
        self.url_label.pack(side=tk.LEFT)

        self.url_entry = tk.Entry(self.url_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.url_entry.insert(0, "https://w.atwiki.jp/kwskp4/pages/166.html")

        self.fetch_button = tk.Button(self.url_frame, text="Fetch", command=self.fetch_content)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.queue = queue.Queue()
        self.after(100, self.process_queue)

    def process_queue(self):
        try:
            msg = self.queue.get_nowait()
            # To avoid flooding the text area with status updates,
            # we can check if the message is a status message or the final content.
            if "..." in msg or "failed" in msg or "error" in msg:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, msg)
            else:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, msg)
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def fetch_content(self):
        url = self.url_entry.get()
        if not url:
            self.queue.put("Please enter a URL.")
            return

        self.queue.put("Fetching proxy list...")
        thread = threading.Thread(target=self.fetch_content_thread, args=(url,))
        thread.start()

    def fetch_content_thread(self, url):
        proxies = []
        try:
            proxies = self.get_free_proxies()
        except Exception as e:
            self.queue.put(f"Failed to fetch proxy list: {e}")
            return

        if not proxies:
            self.queue.put("No working proxies found. Please try again later.")
            return

        random.shuffle(proxies)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        for i, proxy in enumerate(proxies[:20]): # Try up to 20 proxies
            self.queue.put(f"Trying proxy {i+1}/20: {proxy}...")
            try:
                proxy_dict = {
                    "http": f"http://{proxy}",
                    "https": f"http://{proxy}",
                }
                response = requests.get(url, headers=headers, proxies=proxy_dict, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, "html.parser")
                main_content = soup.find('div', id='wikibody')

                if main_content:
                    content_text = main_content.get_text(separator='\\n', strip=True)
                    self.queue.put(content_text)
                else:
                    self.queue.put(soup.get_text(separator='\\n', strip=True))
                return

            except (requests.exceptions.ProxyError, requests.exceptions.Timeout, requests.exceptions.RequestException):
                continue

        self.queue.put("All tried proxies failed. The website might be down or blocking all proxies.")

    def get_free_proxies(self):
        url = "https://geonode.com/free-proxy-list"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        proxies = []
        table = soup.find("table")
        if not table:
            return []
        for row in table.find_all("tr")[1:]:
            try:
                tds = row.find_all("td")
                ip = tds[0].text.strip()
                port = tds[1].text.strip()
                if ip and port.isdigit():
                    proxies.append(f"{ip}:{port}")
            except (IndexError, AttributeError):
                continue
        return proxies

if __name__ == "__main__":
    app = ProxyViewer()
    app.mainloop()
