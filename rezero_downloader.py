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
    API_URL = "https://api.syosetu.com/novelapi/api/"
    NOVEL_ID = "n2267be"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/5.0 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Referer': f'https://ncode.syosetu.com/{NOVEL_ID}/',
        'Upgrade-Insecure-Requests': '1'
    }

    def __init__(self, root):
        self.root = root
        self.root.title("リゼロダウンローダー (API版)")
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

    def get_chapter_info_from_api(self):
        self.log("なろう小説APIから作品情報を取得中...")
        params = {"ncode": self.NOVEL_ID, "out": "json", "of": "ga"}
        try:
            response = requests.get(self.API_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            if len(data) > 1 and "general_all_no" in data[1]:
                total_chapters = data[1]["general_all_no"]
                self.log(f"APIから総話数を取得しました: {total_chapters} 話")
                return total_chapters
            else:
                self.log("APIレスポンスが不正です。")
                return None
        except requests.RequestException as e:
            self.log(f"APIからの情報取得に失敗: {e}")
            return None

    def get_proxies_from_geonode(self):
        try:
            self.log("geonode.comからプロキシを取得中...")
            url = "https://geonode.com/free-proxy-list"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            proxies = [f"{tds[0].text.strip()}:{tds[1].text.strip()}" for row in soup.find("table").find_all("tr")[1:] if (tds := row.find_all("td")) and len(tds) > 1 and tds[0].text.strip() and tds[1].text.strip().isdigit()]
            self.log(f"geonode.comから {len(proxies)} 個のプロキシを取得しました。")
            return proxies
        except Exception:
            self.log("geonode.comからのプロキシ取得に失敗しました。")
            return []

    def get_proxies_from_freeproxylist(self):
        try:
            self.log("free-proxy-list.netからプロキシを取得中...")
            url = "https://free-proxy-list.net/"
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            proxies = [f"{tds[0].text.strip()}:{tds[1].text.strip()}" for row in soup.find("table", class_="table-striped").find("tbody").find_all("tr") if (tds := row.find_all("td")) and len(tds) > 6 and tds[0].text.strip() and tds[1].text.strip().isdigit() and tds[6].text.strip().lower() == 'yes']
            self.log(f"free-proxy-list.netから {len(proxies)} 個のプロキシを取得しました。")
            return proxies
        except Exception:
            self.log("free-proxy-list.netからのプロキシ取得に失敗しました。")
            return []

    def get_free_proxies(self):
        self.log("プロキシリストの取得を開始します...")
        all_proxies = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.get_proxies_from_geonode), executor.submit(self.get_proxies_from_freeproxylist)]
            for future in futures:
                all_proxies.extend(future.result())
        self.proxies = list(set(all_proxies))
        self.log(f"合計 {len(self.proxies)} 個のユニークなプロキシを取得しました。")
        return self.proxies

    def get_text_from_url_with_proxy(self, url):
        if not self.proxies:
            return ""

        max_retries = 5
        for _ in range(max_retries):
            proxy = random.choice(self.proxies)
            try:
                time.sleep(0.5)
                response = requests.get(url, headers=self.HEADERS, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                title_tag = soup.find('p', class_='novel_subtitle')
                honbun_tag = soup.find('div', id='novel_honbun')

                if title_tag and honbun_tag:
                    title = title_tag.text.strip()
                    honbun = honbun_tag.text.strip()
                    return f"<h2>{title}</h2>\n{honbun}\n\n"
                else:
                    return ""
            except requests.RequestException:
                continue
        self.log(f"ダウンロード失敗: {url.split('/')[-2]} (すべてのリトライに失敗)")
        return ""

    def run_download_process(self):
        try:
            total_chapters = self.get_chapter_info_from_api()
            if not total_chapters:
                self.log("総話数が取得できず、処理を中断します。")
                self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
                return

            if not self.get_free_proxies():
                self.log("有効なプロキシが見つかりませんでした。本文のダウンロードはできません。")
                self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
                return

            chapter_urls = [f"{self.BASE_URL}/{self.NOVEL_ID}/{i}/" for i in range(1, total_chapters + 1)]
            self.log(f"{len(chapter_urls)} 話のダウンロードを開始します。")
            self.progress["maximum"] = len(chapter_urls)

            def split_list(lst, n):
                k, m = divmod(len(lst), n)
                return (lst[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))
            url_parts = list(split_list(chapter_urls, 4))

            num_workers = 10
            self.log(f"並列ダウンロードを開始します (ワーカー数: {num_workers})。")

            completed_count = 0
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                for i, part_urls in enumerate(url_parts):
                    filename = f"rezero_part_{i+1}.txt"
                    self.log(f"パート {i+1} の処理を開始、ファイル: '{filename}'")
                    with open(filename, 'w', encoding='utf-8') as f:
                        results = executor.map(self.get_text_from_url_with_proxy, part_urls)
                        for text_content in results:
                            if text_content:
                                f.write(text_content)
                            completed_count += 1
                            self.set_progress(completed_count)
                            if completed_count % 100 == 0 or completed_count == len(chapter_urls):
                                self.log(f"進捗: {completed_count}/{len(chapter_urls)}")
            self.log("すべてのダウンロードとファイル保存が完了しました。")

        except Exception as e:
            self.log(f"ダウンロード処理全体でエラーが発生: {e}")
        finally:
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))


if __name__ == "__main__":
    root = tk.Tk()
    app = RezeroDownloaderApp(root)
    root.mainloop()
