import os
import shutil
import subprocess
import ctypes
import platform
import logging
import stat
from pathlib import Path

# Logger setup
logger = logging.getLogger("BackupMover")
logger.setLevel(logging.INFO)

class BackupManager:
    def __init__(self):
        self.os_type = platform.system()
        # Expanded default paths to check
        self.default_paths = [
            # Standard iTunes
            os.path.expandvars(r"%APPDATA%\Apple Computer\MobileSync\Backup"),
            # Microsoft Store iTunes (Sandboxed) - approximate location
            os.path.expandvars(r"%USERPROFILE%\Apple\MobileSync\Backup"),
            # Older versions
            os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\Apple Computer\MobileSync\Backup")
        ]
        self.found_path = None

    def get_log_messages(self):
        pass

    def check_itunes_running(self):
        """Checks if iTunes is currently running using tasklist."""
        if self.os_type != "Windows":
            return False

        try:
            # cmd /c tasklist /FI "IMAGENAME eq iTunes.exe" /NH
            cmd = ['tasklist', '/FI', 'IMAGENAME eq iTunes.exe', '/NH']
            result = subprocess.run(cmd, capture_output=True, text=True)
            if "iTunes.exe" in result.stdout:
                return True
        except Exception as e:
            # If check fails, we assume false but log warning (not here, but logic wise)
            pass
        return False

    def find_current_backup_folder(self):
        """Finds the existing backup folder from standard locations."""
        for path in self.default_paths:
            p = Path(path)
            # Check if it exists
            if p.exists():
                self.found_path = str(p)
                return self.found_path
        return None

    def get_link_target(self, path):
        """Returns the target of the link if it is one."""
        p = Path(path)
        try:
            # os.readlink works for junctions on newer Python/Windows
            return os.readlink(p)
        except:
            return None

    def validate_new_path(self, new_path):
        """Checks if the new path is valid and writable."""
        p = Path(new_path)
        if not p.exists():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise Exception(f"保存先フォルダを作成できませんでした: {e}")

        # Robust write check
        test_file = p / ".write_test"
        try:
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
        except Exception as e:
            raise Exception(f"指定されたフォルダへの書き込み権限がありません (テスト書き込み失敗): {e}")

        return True

    def _is_reparse_point(self, p) -> bool:
        """Accurately checks if a path is a Reparse Point (Junction/Symlink) on Windows."""
        if isinstance(p, str):
            p = Path(p)

        try:
            # FILE_ATTRIBUTE_REPARSE_POINT = 0x400
            return bool(p.lstat().st_file_attributes & 0x400)
        except AttributeError:
            # Linux/Mac or older Python might not have st_file_attributes easily accessible
            return p.is_symlink()
        except Exception:
            return False

    def _remove_link_dir(self, p: Path):
        """Safely removes a link/junction without deleting target contents."""
        try:
            p.unlink() # Works for symbolic links
        except Exception:
            try:
                p.rmdir() # Works for junctions usually
            except Exception as e:
                raise Exception(f"リンクの解除に失敗しました: {e}")

    def move_and_link(self, target_path, callback=None):
        """
        Moves the backup content to target_path and creates a junction.
        Safely handles existing files and links.
        """
        def log(msg):
            if callback:
                callback(msg)
            else:
                print(msg)

        # 0. Environment Checks
        if self.os_type != "Windows":
            log("警告: Windows環境ではありません。")

        if self.check_itunes_running():
            raise Exception("iTunesが起動しています。終了してから再試行してください。")

        # 1. Determine Source
        if not self.found_path:
            # Force standard path if nothing found
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

        # 2. Handle Existing Source
        # Case A: Source is already a link
        if self._is_reparse_point(src):
            log(f"確認: 元のフォルダはすでにリンクのようです ({src})。")
            log("既存のリンクを解除します...")
            self._remove_link_dir(src)

        # Case B: Source is a real directory
        elif src.exists() and src.is_dir():
            log("既存のデータを新しい場所に移動しています... \n(データ量により時間がかかる場合があります)")

            # Prepare destination
            try:
                dst.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise Exception(f"移動先フォルダ作成エラー: {e}")

            # Move contents item by item (Safer than moving root)
            for item in src.iterdir():
                dest_item = dst / item.name
                if dest_item.exists():
                    log(f"スキップ (移動先に存在): {item.name}")
                    continue # Or handle overwrite? Safety first: skip/warn.

                try:
                    shutil.move(str(item), str(dest_item))
                except Exception as e:
                    raise Exception(f"ファイル移動エラー ({item.name}): {e}")

            log("データの移動が完了しました。")

            # Remove the now-empty source directory
            try:
                src.rmdir()
            except OSError as e:
                # If not empty (e.g. skipped files), we cannot proceed to link
                if any(src.iterdir()):
                     raise Exception("移動元フォルダが空になりませんでした（一部ファイルが残っています）。手動で確認してください。")
                else:
                    raise Exception(f"移動元フォルダの削除に失敗しました: {e}")

        else:
            # Case C: Source doesn't exist (fresh install or weird state)
            log("移動するデータはありません。新しい保存先フォルダを作成します。")
            dst.mkdir(parents=True, exist_ok=True)

        # 3. Create Junction
        log(f"シンボリックリンク(ジャンクション)を作成中...\n元: {src}\n先: {dst}")

        # Ensure source parent exists
        if not src.parent.exists():
            src.parent.mkdir(parents=True, exist_ok=True)

        try:
            if self.os_type == "Windows":
                # Command: mklink /J "Link" "Target"
                # using cmd /c is safer and clearer
                cmd = ["cmd", "/c", "mklink", "/J", str(src), str(dst)]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    raise Exception(f"リンク作成コマンドが失敗しました: {result.stderr}")
            else:
                # Fallback for non-Windows (e.g. Linux test)
                os.symlink(dst, src)

            log("成功: リンクが正常に作成されました。")
        except Exception as e:
            # Recovery/Advice
            log(f"!!! 重大エラー !!!: {e}")
            log(f"データは {dst} に移動されています。")
            log(f"手動でリンクを作成するか、データを {src} に戻してください。")
            raise e

        log("すべての処理が正常に完了しました！\niTunesを起動して、設定 > デバイス でバックアップが表示されるか確認してください。")
