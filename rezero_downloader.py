import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import requests
from bs4 import BeautifulSoup
import textwrap
from concurrent.futures import ThreadPoolExecutor
import os
import random

class RezeroDownloaderApp:
    BASE_URL = "https://ncode.syosetu.com"
    NOVEL_ID = "n2267be"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/5.0 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Referer': f'https://ncode.syosetu.com/n2267be/',
        'Upgrade-Insecure-Requests': '1'
    }

    def __init__(self, root):
        self.root = root
        self.root.title("リゼロダウンローダー")
        self.root.geometry("700x500")

        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)

        self.start_button = ttk.Button(control_frame, text="ダウンロード開始", command=self.start_download_thread)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.progress = ttk.Progressbar(control_frame, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=20)
        self.log_area.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)

        self.proxies = []

    def log(self, message):
        self.root.after(0, self._log_message, message)

    def _log_message(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def set_progress(self, value):
        self.root.after(0, self._set_progress, value)

    def _set_progress(self, value):
        self.progress["value"] = value

    def start_download_thread(self):
        self.start_button.config(state=tk.DISABLED)
        self.log("ダウンロードスレッドを開始します。")
        download_thread = threading.Thread(target=self.run_download_process)
        download_thread.daemon = True
        download_thread.start()

    def get_proxies_from_geonode(self):
        try:
            self.log("geonode.comからプロキシを取得中...")
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
            self.log(f"geonode.comから {len(proxies)} 個のプロキシを取得しました。")
            return proxies
        except Exception as e:
            self.log(f"geonode.comからのプロキシ取得に失敗: {e}")
            return []

    def get_proxies_from_freeproxylist(self):
        try:
            self.log("free-proxy-list.netからプロキシを取得中...")
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
            self.log(f"free-proxy-list.netから {len(proxies)} 個のプロキシを取得しました。")
            return proxies
        except Exception as e:
            self.log(f"free-proxy-list.netからのプロキシ取得に失敗: {e}")
            return []

    def get_free_proxies(self):
        self.log("プロキシリストの取得を開始します...")
        all_proxies = []
        source_funcs = [self.get_proxies_from_geonode, self.get_proxies_from_freeproxylist]

        with ThreadPoolExecutor(max_workers=len(source_funcs)) as executor:
            futures = [executor.submit(func) for func in source_funcs]
            for future in futures:
                all_proxies.extend(future.result())

        unique_proxies = list(set(all_proxies))
        self.log(f"合計 {len(unique_proxies)} 個のユニークなプロキシを取得しました。")
        self.proxies = unique_proxies
        return unique_proxies

    def get_chapter_urls(self, proxy):
        toc_url = f"{self.BASE_URL}/{self.NOVEL_ID}/"
        self.log(f"目次ページを取得中 (プロキシ: {proxy})...")
        try:
            response = requests.get(toc_url, headers=self.HEADERS, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.select('.index_box a')
            urls = [self.BASE_URL + link.get('href') for link in links]
            self.log(f"全 {len(urls)} 話のURLを取得しました。")
            return urls
        except requests.RequestException as e:
            self.log(f"URL取得エラー (プロキシ: {proxy}): {e}")
            return None

    def get_text_from_url_with_proxy(self, url):
        if not self.proxies:
            self.log("プロキシがありません。")
            return ""

        max_retries = 5
        for i in range(max_retries):
            proxy = random.choice(self.proxies)
            try:
                time.sleep(0.5)
                response = requests.get(url, headers=self.HEADERS, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('p', class_='novel_subtitle').text.strip()
                honbun = soup.find('div', id='novel_honbun').text.strip()
                return f"<h2>{title}</h2>\n{honbun}\n\n"
            except requests.RequestException:
                continue

        self.log(f"ダウンロード失敗: {url.split('/')[-2]} (すべてのリトライに失敗)")
        return ""

    def run_download_process(self):
        try:
            self.get_free_proxies()
            if not self.proxies:
                self.log("有効なプロキシが見つかりませんでした。処理を中断します。")
                self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
                return

            chapter_urls = None
            for i in range(10):
                proxy = random.choice(self.proxies)
                chapter_urls = self.get_chapter_urls(proxy)
                if chapter_urls:
                    break

            if not chapter_urls:
                self.log("章のURLが取得できませんでした。多くのプロキシがブロックされているようです。")
                self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
                return

            total_chapters = len(chapter_urls)
            self.log(f"{total_chapters} 話のダウンロードを開始します。")
            self.progress["maximum"] = total_chapters

            def split_list(lst, n):
                k, m = divmod(len(lst), n)
                return (lst[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

            url_parts = list(split_list(chapter_urls, 4))

            num_workers = 10
            self.log(f"並列ダウンロードを開始します (ワーカー数: {num_workers})。")

            completed_count = 0
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                for i, part_urls in enumerate(url_parts):
                    part_num = i + 1
                    filename = f"rezero_part_{part_num}.txt"
                    self.log(f"パート {part_num} の処理を開始、ファイル: '{filename}'")

                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            results = executor.map(self.get_text_from_url_with_proxy, part_urls)

                            for text_content in results:
                                if text_content:
                                    f.write(text_content)

                                completed_count += 1
                                self.set_progress(completed_count)

                                if completed_count % 100 == 0 or completed_count == total_chapters:
                                    self.log(f"進捗: {completed_count}/{total_chapters}")

                        self.log(f"パート {part_num} の書き込みが完了しました。")
                    except IOError as e:
                        self.log(f"ファイル書き込みエラー ({filename}): {e}")

            self.log("すべてのダウンロードとファイル保存が完了しました。")

        except Exception as e:
            self.log(f"ダウンロード処理全体でエラーが発生: {e}")
        finally:
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))


if __name__ == "__main__":
    root = tk.Tk()
    app = RezeroDownloaderApp(root)
    root.mainloop()
