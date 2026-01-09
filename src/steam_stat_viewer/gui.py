import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser

try:
    from .logic import AppLogic
except ImportError:
    from logic import AppLogic

class SteamStatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam プレイログ & 実績集計ツール")
        self.root.geometry("850x650") # Increased size slightly for new buttons

        self.logic = AppLogic(self.log_message)

        # UI Variables
        self.api_key_var = tk.StringVar()
        self.steam_id_var = tk.StringVar()
        self.total_playtime_var = tk.StringVar(value="0 時間")
        self.total_games_var = tk.StringVar(value="0 本")
        self.total_achievements_var = tk.StringVar(value="集計中...")
        self.progress_var = tk.DoubleVar()

        self.setup_ui()

    def setup_ui(self):
        # --- Top: Configuration ---
        config_frame = ttk.LabelFrame(self.root, text="設定")
        config_frame.pack(fill="x", padx=10, pady=5)

        # Row 0: Inputs
        ttk.Label(config_frame, text="Steam API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(config_frame, textvariable=self.api_key_var, width=35, show="*").grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(config_frame, text="Steam ID (64bit):").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        ttk.Entry(config_frame, textvariable=self.steam_id_var, width=20).grid(row=0, column=3, padx=5, pady=5)

        # Buttons Frame
        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=0, column=4, rowspan=2, padx=10, pady=5, sticky="ns")

        self.fetch_btn = ttk.Button(btn_frame, text="データ取得開始", command=self.start_fetching)
        self.fetch_btn.pack(side="top", pady=2, fill="x")

        # Local Scan Button
        self.local_btn = ttk.Button(btn_frame, text="ローカル読込", command=self.start_local_scan)
        self.local_btn.pack(side="top", pady=2, fill="x")

        # Row 1: Help Buttons
        def open_api_page():
            webbrowser.open("https://steamcommunity.com/dev/apikey")

        def open_id_page():
            webbrowser.open("https://store.steampowered.com/account/")

        btn_get_key = ttk.Button(config_frame, text="🔑 API Keyを取得 (Web)", command=open_api_page, width=20)
        btn_get_key.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        btn_check_id = ttk.Button(config_frame, text="🔍 IDを確認 (Web)", command=open_id_page, width=15)
        btn_check_id.grid(row=1, column=3, padx=5, pady=2, sticky="w")


        # --- Middle: Summary Dashboard ---
        summary_frame = ttk.LabelFrame(self.root, text="サマリー")
        summary_frame.pack(fill="x", padx=10, pady=5)

        # Grid layout for summary
        ttk.Label(summary_frame, text="総プレイ時間:").grid(row=0, column=0, padx=20, pady=10)
        ttk.Label(summary_frame, textvariable=self.total_playtime_var, font=("Helvetica", 14, "bold")).grid(row=0, column=1, padx=5, pady=10)

        ttk.Label(summary_frame, text="所有ゲーム数:").grid(row=0, column=2, padx=20, pady=10)
        ttk.Label(summary_frame, textvariable=self.total_games_var, font=("Helvetica", 14, "bold")).grid(row=0, column=3, padx=5, pady=10)

        ttk.Label(summary_frame, text="総解除実績数:").grid(row=0, column=4, padx=20, pady=10)
        ttk.Label(summary_frame, textvariable=self.total_achievements_var, font=("Helvetica", 14, "bold")).grid(row=0, column=5, padx=5, pady=10)

        # Progress bar for achievement scanning
        self.progress_bar = ttk.Progressbar(summary_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=5)

        # --- Bottom: Tabs ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Games List
        self.games_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.games_tab, text="ゲーム一覧")

        # Treeview for games
        columns = ("rank", "name", "playtime", "achievements")
        self.tree = ttk.Treeview(self.games_tab, columns=columns, show="headings")
        self.tree.heading("rank", text="順位")
        self.tree.heading("name", text="ゲーム名")
        self.tree.heading("playtime", text="プレイ時間 (時間)")
        self.tree.heading("achievements", text="実績 (解除/総数)")

        self.tree.column("rank", width=50, anchor="center")
        self.tree.column("name", width=400)
        self.tree.column("playtime", width=100, anchor="e")
        self.tree.column("achievements", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(self.games_tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Tab 2: Logs
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="ログ")

        self.log_text = tk.Text(self.log_tab, state="disabled", height=10)
        self.log_text.pack(fill="both", expand=True)

    def log_message(self, message):
        """Thread-safe logging to the text widget."""
        def _log():
            self.log_text.config(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.root.after(0, _log)

    def start_fetching(self):
        api_key = self.api_key_var.get().strip()
        steam_id = self.steam_id_var.get().strip()

        if not api_key or not steam_id:
            messagebox.showerror("エラー", "API KeyとSteam IDを入力してください。")
            return

        self.fetch_btn.config(state="disabled")
        self.local_btn.config(state="disabled")
        self.logic.set_credentials(api_key, steam_id)

        # Run in thread to not freeze UI
        threading.Thread(target=self.run_fetch_pipeline, daemon=True).start()

    def start_local_scan(self):
        self.fetch_btn.config(state="disabled")
        self.local_btn.config(state="disabled")

        threading.Thread(target=self.run_local_pipeline, daemon=True).start()

    def run_fetch_pipeline(self):
        self.log_message("データ取得を開始します (APIモード)...")

        profile, games = self.logic.fetch_basic_info()

        if not profile or games is None:
            self.root.after(0, lambda: self.enable_buttons())
            return

        # Update Summary UI
        total_minutes = sum(g.get('playtime_forever', 0) for g in games)
        total_hours = total_minutes / 60

        self.root.after(0, lambda: self.update_summary(len(games), total_hours))
        self.root.after(0, lambda: self.populate_games_list(games))

        # Start achievement fetching
        self.logic.fetch_achievements_background(
            games,
            self.update_progress,
            self.achievement_scan_complete,
            self.update_game_row_callback
        )

    def run_local_pipeline(self):
        self.log_message("データ取得を開始します (ローカルモード)...")
        self.log_message("※ 注意: ローカルモードでは実績の集計は行えません。")

        profile, games = self.logic.fetch_local_data()

        if not games:
            self.log_message("エラー: ローカルデータの取得に失敗しました。")
            self.root.after(0, lambda: self.enable_buttons())
            return

        total_minutes = sum(g.get('playtime_forever', 0) for g in games)
        total_hours = total_minutes / 60

        self.root.after(0, lambda: self.update_summary(len(games), total_hours))
        self.root.after(0, lambda: self.populate_games_list(games, local_mode=True))

        # In local mode, we skip achievement scanning or do a dummy pass
        # But since we have no API key, fetch_achievements_background will just finish immediately if we try call it without credentials
        # Or better, just finish here.
        self.root.after(0, lambda: self.achievement_scan_complete(0))


    def enable_buttons(self):
        self.fetch_btn.config(state="normal")
        self.local_btn.config(state="normal")

    def update_summary(self, count, hours):
        self.total_games_var.set(f"{count} 本")
        self.total_playtime_var.set(f"{hours:,.1f} 時間")

    def populate_games_list(self, games, local_mode=False):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, game in enumerate(games):
            minutes = game.get('playtime_forever', 0)
            hours = minutes / 60

            ach_str = "..." if not local_mode else "-"

            # rank, name, playtime, achievements (placeholder)
            # Store appid as iid to easily update it later
            self.tree.insert("", "end", iid=str(game.get('appid')), values=(
                idx + 1,
                game.get('name'),
                f"{hours:,.1f}",
                ach_str
            ))

    def update_progress(self, current, total):
        def _update():
            percent = (current / total) * 100
            self.progress_var.set(percent)
        self.root.after(0, _update)

    def update_game_row_callback(self, game):
        """Updates the treeview row for a specific game with achievement counts."""
        def _update_row():
            app_id = str(game.get('appid'))
            if self.tree.exists(app_id):
                # Get current values
                current_values = self.tree.item(app_id, "values")
                # rank(0), name(1), playtime(2), ach(3)

                achieved = game.get('achieved_count', 0)
                total = game.get('total_achievements', 0)

                ach_str = f"{achieved} / {total}" if total > 0 else "-"

                new_values = (current_values[0], current_values[1], current_values[2], ach_str)
                self.tree.item(app_id, values=new_values)

        self.root.after(0, _update_row)

    def achievement_scan_complete(self, total_achieved):
        def _finish():
            if total_achieved > 0:
                self.total_achievements_var.set(f"{total_achieved} 個")
            else:
                self.total_achievements_var.set("集計なし")

            self.enable_buttons()
            self.log_message("全ての処理が完了しました。")
        self.root.after(0, _finish)
