import threading
import queue
import time

try:
    from .steam_api import SteamClient
    from .local_scanner import get_local_data
except ImportError:
    from steam_api import SteamClient
    from local_scanner import get_local_data

class AppLogic:
    def __init__(self, log_callback):
        self.client = None
        self.log_callback = log_callback
        self.stop_event = threading.Event()

    def set_credentials(self, api_key, steam_id):
        self.client = SteamClient(api_key, steam_id)

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)

    def fetch_basic_info(self):
        """Fetches user profile and list of owned games."""
        self.log("基本情報を取得中...")
        profile = self.client.get_player_summary()
        if not profile:
            self.log("エラー: プロファイルを取得できませんでした。APIキーとSteam IDを確認してください。")
            return None, None

        self.log(f"ユーザー認識: {profile.get('personaname')} ({self.client.steam_id})")

        self.log("所有ゲーム一覧を取得中...")
        games = self.client.get_owned_games()
        self.log(f"所有ゲーム数: {len(games)}")

        # Sort games by playtime (descending)
        games.sort(key=lambda x: x.get('playtime_forever', 0), reverse=True)

        return profile, games

    def fetch_local_data(self):
        """Fetches data from local Steam installation."""
        self.log("ローカルのSteam設定ファイルをスキャン中...")
        try:
            user_id, games = get_local_data()
            self.log(f"ローカルユーザーID: {user_id}")
            self.log(f"検出されたゲーム数: {len(games)}")

            # Create a mock profile object
            profile = {
                "personaname": f"LocalUser ({user_id})",
                "avatarfull": "" # No avatar available locally
            }
            return profile, games
        except Exception as e:
            self.log(f"ローカルスキャンエラー: {e}")
            return None, None

    def fetch_achievements_background(self, games, progress_callback, completion_callback, game_update_callback=None):
        """
        Background task to fetch achievements for all games.
        """
        def worker():
            total_achievements = 0
            games_with_achievements = 0
            processed_count = 0
            total_games = len(games)

            if not self.client:
                self.log("注意: APIキーが設定されていないため、実績データは取得できません。")
                # Just finish immediately with 0 achievements
                if completion_callback:
                    completion_callback(0)
                return

            self.log("実績データの全件取得を開始します (これには時間がかかります)...")

            for game in games:
                if self.stop_event.is_set():
                    self.log("処理が中断されました。")
                    break

                app_id = game.get('appid')
                game_name = game.get('name', 'Unknown')

                try:
                    stats = self.client.get_player_achievements(app_id)
                    achieved_count = 0
                    total_count = 0

                    if stats and 'achievements' in stats:
                        achieved_count = sum(1 for a in stats['achievements'] if a.get('achieved') == 1)
                        total_count = len(stats['achievements'])

                        if achieved_count > 0:
                            total_achievements += achieved_count
                            games_with_achievements += 1

                    # Store in game dict
                    game['achieved_count'] = achieved_count
                    game['total_achievements'] = total_count

                    # Notify UI to update specific row
                    if game_update_callback:
                        game_update_callback(game)

                except Exception as e:
                    pass

                processed_count += 1
                if progress_callback:
                    progress_callback(processed_count, total_games)

                time.sleep(0.1)

            self.log(f"実績集計完了。実績ありゲーム数: {games_with_achievements}, 総解除実績数: {total_achievements}")
            if completion_callback:
                completion_callback(total_achievements)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def stop_processing(self):
        self.stop_event.set()
