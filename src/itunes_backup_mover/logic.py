import os
import shutil
import subprocess
import ctypes
import platform
import logging
from pathlib import Path

# Logger setup
logger = logging.getLogger("BackupMover")
logger.setLevel(logging.INFO)

class BackupManager:
    def __init__(self):
        self.os_type = platform.system()
        self.default_paths = [
            # Standard iTunes
            os.path.expandvars(r"%APPDATA%\Apple Computer\MobileSync\Backup"),
            # Microsoft Store iTunes (Sandboxed) - approximate location
            os.path.expandvars(r"%USERPROFILE%\Apple\MobileSync\Backup"),
            # Older versions
            os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\Apple Computer\MobileSync\Backup")
        ]
        self.found_path = None

    def is_admin(self):
        """Check if the script is running with administrative privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def find_current_backup_folder(self):
        """Finds the existing backup folder from standard locations."""
        for path in self.default_paths:
            p = Path(path)
            # Check if it exists and is a directory (or a symlink to one)
            if p.exists():
                self.found_path = str(p)
                return self.found_path
        return None

    def validate_new_path(self, new_path):
        """Checks if the new path is valid."""
        p = Path(new_path)
        if not p.exists():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise Exception(f"保存先フォルダを作成できませんでした: {e}")

        # Check if it's writable
        if not os.access(new_path, os.W_OK):
            raise Exception("指定されたフォルダへの書き込み権限がありません。")

        return True

    def move_and_link(self, target_path, callback=None):
        """
        Moves the backup content to target_path and creates a junction.
        callback(message) is used for GUI updates.
        """
        def log(msg):
            if callback:
                callback(msg)
            else:
                print(msg)

        if self.os_type != "Windows":
            # For testing in non-Windows environment, we warn but allow proceed if mocked
            log("警告: Windows環境ではありません。動作が保証されません。")

        if not self.found_path:
            # Default to standard APPDATA location if nothing found
            default_location = Path(os.path.expandvars(r"%APPDATA%\Apple Computer\MobileSync\Backup"))
            if not default_location.parent.exists():
                 try:
                     default_location.parent.mkdir(parents=True, exist_ok=True)
                 except Exception as e:
                     raise Exception(f"iTunesの標準フォルダを作成できませんでした: {e}")
            self.found_path = str(default_location)
            log(f"既存のバックアップが見つからないため、標準パスを対象にします:\n{self.found_path}")

        src = Path(self.found_path)
        dst_root = Path(target_path)
        dst = dst_root / "Backup"

        log("処理を開始します...")

        # 1. Check if source is already a link
        if src.is_symlink() or self._is_junction(src):
            log(f"確認: 元のフォルダはすでにリンクのようです ({src})。")
            log("既存のリンクを解除します...")
            try:
                src.rmdir() # unlink for junctions
            except OSError:
                os.remove(src) # try remove for file-like symlinks

        # 2. Move data if it exists and is a real directory
        elif src.exists():
            log("既存のデータを新しい場所に移動しています... \n(データ量により時間がかかる場合があります)")
            try:
                # Check if destination already exists to avoid nesting
                if dst.exists():
                    log(f"警告: 移動先フォルダ ({dst}) が既に存在します。")
                    # If empty, delete it so we can move src there
                    if not any(dst.iterdir()):
                         dst.rmdir()
                    else:
                        raise Exception(f"移動先フォルダ {dst} が既に存在し、空ではありません。手動で削除するか別の場所を選択してください。")

                dst.parent.mkdir(parents=True, exist_ok=True)

                shutil.move(str(src), str(dst))
                log("データの移動が完了しました。")
            except Exception as e:
                raise Exception(f"データの移動中にエラーが発生しました: {e}")
        else:
            log("移動するデータはありません。新しい保存先フォルダを作成します。")
            dst.mkdir(parents=True, exist_ok=True)

        # 3. Create Junction
        log(f"シンボリックリンク(ジャンクション)を作成中...\n元: {src}\n先: {dst}")

        # Ensure source parent exists
        if not src.parent.exists():
            src.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Check if using Windows
            if self.os_type == "Windows":
                # Command: mklink /J "Link" "Target"
                # Shell=True is often required for mklink as it's a shell command
                cmd = f'mklink /J "{src}" "{dst}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                if result.returncode != 0:
                    raise Exception(f"リンク作成コマンドが失敗しました: {result.stderr}")
            else:
                # Fallback for non-Windows (e.g. Linux test)
                os.symlink(dst, src)

            log("成功: リンクが正常に作成されました。")
        except Exception as e:
            raise Exception(f"リンク作成エラー: {e}")

        log("すべての処理が正常に完了しました！\niTunesを起動して、設定 > デバイス でバックアップが表示されるか確認してください。")

    def _is_junction(self, path):
        """Helper to check if a path is specifically a junction."""
        try:
            return os.path.islink(path)
        except:
            return False
