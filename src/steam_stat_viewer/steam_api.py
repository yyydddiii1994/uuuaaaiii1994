import requests
import time

class SteamClient:
    def __init__(self, api_key, steam_id):
        self.api_key = api_key
        self.steam_id = steam_id
        self.base_url = "https://api.steampowered.com"

    def _get(self, interface, method, version, params=None):
        if params is None:
            params = {}
        params['key'] = self.api_key
        params['steamid'] = self.steam_id  # Some endpoints use 'steamid', others 'steamids'

        url = f"{self.base_url}/{interface}/{method}/{version}/"
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error ({method}): {e}")
            return None

    def get_player_summary(self):
        # ISteamUser/GetPlayerSummaries/v0002/
        params = {'steamids': self.steam_id}
        data = self._get("ISteamUser", "GetPlayerSummaries", "v0002", params)
        if data and 'response' in data and 'players' in data['response']:
            players = data['response']['players']
            if players:
                return players[0]
        return None

    def get_owned_games(self):
        # IPlayerService/GetOwnedGames/v0001/
        params = {
            'include_appinfo': 1,
            'include_played_free_games': 1
        }
        data = self._get("IPlayerService", "GetOwnedGames", "v0001", params)
        if data and 'response' in data and 'games' in data['response']:
            return data['response']['games']
        return []

    def get_player_achievements(self, app_id):
        # ISteamUserStats/GetPlayerAchievements/v0001/
        params = {
            'appid': app_id
        }
        # Note: This endpoint often fails if the game has no stats/achievements
        # or if the user's game stats are private.
        data = self._get("ISteamUserStats", "GetPlayerAchievements", "v0001", params)
        if data and 'playerstats' in data:
            return data['playerstats']
        return None

    def get_schema_for_game(self, app_id):
        # ISteamUserStats/GetSchemaForGame/v2/
        # Useful to get achievement names/descriptions if needed, but might be overkill for just counting.
        params = {
            'appid': app_id
        }
        data = self._get("ISteamUserStats", "GetSchemaForGame", "v2", params)
        if data and 'game' in data:
            return data['game']
        return None
