import time
import os
from typing import List, Dict, Callable

# pymobiledevice3のインポートを試みる
try:
    from pymobiledevice3.lockdown import LockdownClient
    from pymobiledevice3.services.afc import AfcService
    # 正しいモジュールパスに修正
    from pymobiledevice3.services.mobilebackup2 import MobileBackup2Service
    from pymobiledevice3.exceptions import NoDeviceConnectedError, PyMobileDevice3Exception
    PYMOBILEDEVICE3_AVAILABLE = True
except (ImportError, FileNotFoundError):
    PYMOBILEDEVICE3_AVAILABLE = False

class BackupError(Exception):
    """バックアップ処理中にエラーが発生した場合のカスタム例外"""
    pass

def get_device_info() -> Dict[str, str]:
    if not PYMOBILEDEVICE3_AVAILABLE:
        raise BackupError("pymobiledevice3ライブラリが利用できません。")
    try:
        # LockdownClientのコンストラクタでシリアル番号を渡すことも可能
        client = LockdownClient()
        return {
            'DeviceName': client.get_value('DeviceName'),
            'ProductVersion': client.get_value('ProductVersion'),
            'UniqueDeviceID': client.udid,
        }
    except (NoDeviceConnectedError, PyMobileDevice3Exception) as e:
        # NoDeviceConnectedErrorはより具体的なエラーメッセージを提供する
        if isinstance(e, NoDeviceConnectedError):
            raise BackupError("iPadが接続されていません。USB接続を確認してください。")
        raise BackupError(f"デバイスに接続できません: {e}")

def list_files_and_folders(path: str = '/') -> List[Dict]:
    if not PYMOBILEDEVICE3_AVAILABLE:
        raise BackupError("pymobiledevice3ライブラリが利用できません。")
    try:
        with AfcService() as afc:
            items = []
            for name in afc.listdir(path):
                if name in ['.', '..']: continue
                full_path = os.path.join(path, name).replace('\\', '/')
                try:
                    info = afc.get_file_info(full_path)
                    item_type = 'folder' if info.get('st_ifmt') == 'S_IFDIR' else 'file'
                    items.append({'name': name, 'path': full_path, 'type': item_type})
                except PyMobileDevice3Exception:
                    # アクセスできないファイルやシンボリックリンクなどはスキップ
                    continue
            return items
    except (NoDeviceConnectedError, PyMobileDevice3Exception) as e:
        if isinstance(e, NoDeviceConnectedError):
            raise BackupError("iPadが接続されていません。USB接続を確認してください。")
        raise BackupError(f"ファイルリストの取得に失敗しました ({path}): {e}")

def start_backup(backup_path: str, progress_callback: Callable[[int, str], None]):
    if not PYMOBILEDEVICE3_AVAILABLE:
        raise BackupError("pymobiledevice3ライブラリが利用できません。")
    if not os.path.isdir(backup_path):
        raise BackupError(f"指定されたパスが見つかりません: {backup_path}")

    try:
        # MobileBackup2Serviceのインスタンスを作成
        with MobileBackup2Service() as backup_service:
            last_progress = -1
            # backup_progressイテレータを使用
            for progress, state, msg in backup_service.backup_progress(backup_path):
                if progress is not None and progress != last_progress:
                    progress_callback(progress, f"{state}: {msg}")
                    last_progress = progress
            progress_callback(100, "バックアップが正常に完了しました。")

    except (NoDeviceConnectedError, PyMobileDevice3Exception) as e:
        if isinstance(e, NoDeviceConnectedError):
            raise BackupError("iPadが接続されていません。バックアップを開始できません。")
        raise BackupError(f"バックアップ中にエラーが発生しました: {e}")

if __name__ == '__main__':
    print("--- バックエンドロジック テスト ---")
    if not PYMOBILEDEVICE3_AVAILABLE:
        print("pymobiledevice3 が見つからないか、初期化に失敗しました。")
    else:
        try:
            print("\n--- デバイス情報 ---")
            info = get_device_info()
            print(info)
        except BackupError as e:
            print(f"エラー: {e}")
