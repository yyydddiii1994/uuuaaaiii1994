import tkinter as tk
from tkhtmlview import HTMLScrolledText
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

        self.text_area = HTMLScrolledText(self, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.queue = queue.Queue()
        self.after(100, self.process_queue)

    def process_queue(self):
        try:
            msg_type, content = self.queue.get_nowait()
            if msg_type == "status":
                self.text_area.set_html(f"<i>{content}</i>")
            elif msg_type == "content":
                self.text_area.set_html(content)
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def fetch_content(self):
        url = self.url_entry.get()
        if not url:
            self.queue.put(("status", "Please enter a URL."))
            return

        self.queue.put(("status", "Fetching proxy list from multiple sources..."))
        thread = threading.Thread(target=self.fetch_content_thread, args=(url,))
        thread.start()

    def fetch_content_thread(self, url):
        proxies = []
        try:
            proxies = self.get_free_proxies()
        except Exception as e:
            self.queue.put(("status", f"Failed to fetch proxy lists: {e}"))
            return

        if not proxies:
            self.queue.put(("status", "No working proxies could be found from any source. Please try again later."))
            return

        random.shuffle(proxies)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        max_proxies_to_try = 20
        for i, proxy in enumerate(proxies[:max_proxies_to_try]):
            self.queue.put(("status", f"Trying proxy {i+1}/{max_proxies_to_try}: {proxy}..."))
            try:
                proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                response = requests.get(url, headers=headers, proxies=proxy_dict, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, "html.parser")
                main_content = soup.find('div', id='wikibody')

                if main_content:
                    self.queue.put(("content", str(main_content)))
                else:
                    self.queue.put(("content", response.text))
                return
            except Exception:
                continue

        self.queue.put(("status", "All tried proxies failed. The website might be down or blocking all available proxies."))

    def get_free_proxies(self):
        """Fetches proxies from multiple sources and returns a combined list."""
        all_proxies = []

        # We can run these in threads to make it faster, but for simplicity, we do it sequentially.
        source_funcs = [self.get_proxies_from_geonode, self.get_proxies_from_freeproxylist]

        for func in source_funcs:
            try:
                all_proxies.extend(func())
            except Exception:
                # If one source fails, we can continue to the next.
                continue

        return list(set(all_proxies)) # Return unique proxies

    def get_proxies_from_geonode(self):
        url = "https://geonode.com/free-proxy-list"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        proxies = []
        table = soup.find("table")
        if not table: return []
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

    def get_proxies_from_freeproxylist(self):
        url = "https://free-proxy-list.net/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        proxies = []
        table = soup.find("table", attrs={"class": "table-striped"})
        if not table: return []
        for row in table.find("tbody").find_all("tr"):
            try:
                tds = row.find_all("td")
                ip = tds[0].text.strip()
                port = tds[1].text.strip()
                is_https = tds[6].text.strip().lower() == 'yes'
                if ip and port.isdigit() and is_https:
                    proxies.append(f"{ip}:{port}")
            except (IndexError, AttributeError):
                continue
        return proxies

if __name__ == "__main__":
    app = ProxyViewer()
    app.mainloop()
