import os
import winreg
import glob
from .vdf_parser import parse_vdf

def find_steam_path():
    """
    Attempts to find the Steam installation path via Windows Registry or default paths.
    """
    try:
        # Try Registry
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        path, _ = winreg.QueryValueEx(key, "SteamPath")
        # Registry path uses forward slashes often, normalize it
        return os.path.normpath(path)
    except Exception:
        pass

    # Try default paths
    candidates = [
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files\Steam",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def find_library_folders(steam_path):
    """
    Reads libraryfolders.vdf to find all Steam library paths (where games are installed).
    """
    libraries = [steam_path]
    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")

    if os.path.exists(vdf_path):
        try:
            with open(vdf_path, "r", encoding="utf-8") as f:
                data = parse_vdf(f.read())

            # The structure varies by version, but usually usually:
            # "libraryfolders" { "0" { "path" "..." } "1" { "path" "..." } }
            if "libraryfolders" in data:
                for k, v in data["libraryfolders"].items():
                    if isinstance(v, dict) and "path" in v:
                        libraries.append(os.path.normpath(v["path"]))
                    elif isinstance(v, str) and os.path.exists(v):
                         # Older format where value was just the path?
                         libraries.append(os.path.normpath(v))
        except Exception as e:
            print(f"Error reading libraryfolders: {e}")

    return list(set(libraries))

def scan_installed_games(steam_path):
    """
    Scans 'steamapps' folders for .acf files to get names of INSTALLED games.
    Returns dict: {appid (str): name (str)}
    """
    game_names = {}
    libraries = find_library_folders(steam_path)

    for lib in libraries:
        apps_path = os.path.join(lib, "steamapps")
        if not os.path.exists(apps_path):
            continue

        acf_files = glob.glob(os.path.join(apps_path, "appmanifest_*.acf"))
        for acf in acf_files:
            try:
                with open(acf, "r", encoding="utf-8") as f:
                    data = parse_vdf(f.read())

                if "AppState" in data:
                    app_id = data["AppState"].get("appid")
                    name = data["AppState"].get("name")
                    if app_id and name:
                        game_names[str(app_id)] = name
            except:
                continue

    return game_names

def scan_user_config(steam_path):
    """
    Finds localconfig.vdf for the user and extracts playtimes.
    Returns: (user_id, games_list)
    games_list is a list of dicts: {'appid': ..., 'playtime_forever': ...}
    """
    userdata_path = os.path.join(steam_path, "userdata")
    if not os.path.exists(userdata_path):
        return None, []

    # If multiple users, pick the one with the most recently modified localconfig.vdf
    users = []
    for entry in os.scandir(userdata_path):
        if entry.is_dir() and entry.name.isdigit():
            config_path = os.path.join(entry.path, "config", "localconfig.vdf")
            if os.path.exists(config_path):
                users.append((entry.name, config_path, os.path.getmtime(config_path)))

    if not users:
        return None, []

    # Sort by mtime desc
    users.sort(key=lambda x: x[2], reverse=True)
    user_id, config_file, _ = users[0]

    games = []
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            # This file can be huge, but our parser should handle it
            data = parse_vdf(f.read())

        # Path: UserLocalConfigStore -> Software -> Valve -> Steam -> apps
        # Structure varies, but traverse safely
        base = data.get("UserLocalConfigStore", {}).get("Software", {}).get("Valve", {}).get("Steam", {})
        apps = base.get("apps", {})

        for app_id, stats in apps.items():
            # stats is a dict like {"PlayTime": "123", ...}
            # PlayTime is in minutes
            playtime = int(stats.get("PlayTime", 0))
            if playtime > 0:
                games.append({
                    "appid": app_id,
                    "playtime_forever": playtime,
                    "name": f"AppID: {app_id}" # Placeholder
                })

    except Exception as e:
        print(f"Error parsing localconfig: {e}")
        return None, []

    return user_id, games

def get_local_data():
    """
    Main entry point.
    Returns: (user_id, games_list_with_names)
    """
    steam_path = find_steam_path()
    if not steam_path:
        raise FileNotFoundError("Steam installation not found.")

    user_id, games = scan_user_config(steam_path)
    if not games:
        raise FileNotFoundError("No user data found (localconfig.vdf missing or empty).")

    # Get names for installed games
    installed_names = scan_installed_games(steam_path)

    # Merge names
    for game in games:
        aid = str(game["appid"])
        if aid in installed_names:
            game["name"] = installed_names[aid]

    # Sort by playtime
    games.sort(key=lambda x: x.get('playtime_forever', 0), reverse=True)

    return user_id, games
