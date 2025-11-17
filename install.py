# install.py

import os
import sys
import shutil
import platform

def get_anki_addon_path():
    """
    Determines the Anki addon path based on the operating system.
    """
    system = platform.system()

    if system == "Windows":
        # Path is typically in AppData/Roaming/Anki2/addons21
        return os.path.join(os.getenv("APPDATA"), "Anki2", "addons21")
    elif system == "Darwin": # macOS
        # Path is in user's Library/Application Support
        return os.path.expanduser("~/Library/Application Support/Anki2/addons21")
    elif system == "Linux":
        # Path follows XDG Base Directory Specification for data files
        xdg_data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return os.path.join(xdg_data_home, "Anki2", "addons21")
    else:
        return None

def main():
    """
    Main function to run the installation process.
    """
    print("--- CARS Addon Installer ---")

    # 1. Define source and destination
    source_dir = os.path.join(os.path.dirname(__file__), "src", "cars_addon")
    addon_name = "cars_addon" # The name of the folder inside the addons directory

    if not os.path.isdir(source_dir):
        print(f"❌ Error: Source directory not found at '{source_dir}'")
        sys.exit(1)

    print(f"🔍 Source directory found at: {source_dir}")

    # 2. Get Anki addon path
    print(" B Detecting Anki addon path for your operating system...")
    anki_path = get_anki_addon_path()

    if not anki_path:
        print("❌ Error: Could not determine Anki addon path for this operating system.")
        sys.exit(1)

    if not os.path.isdir(anki_path):
         print(f"Anki addons path not found at '{anki_path}', creating it now...")
         try:
            os.makedirs(anki_path)
            print("✅ Successfully created addons directory.")
         except OSError as e:
            print(f"❌ Error: Could not create Anki addon path: {e}")
            sys.exit(1)

    print(f"✅ Anki addon path detected: {anki_path}")

    destination_path = os.path.join(anki_path, addon_name)
    print(f"Destination will be: {destination_path}")

    # 3. Copy files
    print("\n Copying addon files...")

    try:
        # If the addon is already installed, remove it first to ensure a clean install
        if os.path.exists(destination_path):
            print(f" Found existing installation. Removing it first...")
            shutil.rmtree(destination_path)
            print("✅ Old version removed.")

        # Copy the entire addon folder
        shutil.copytree(source_dir, destination_path)

        print("\n🎉 --- Installation Complete! --- 🎉")
        print("The CARS addon has been successfully installed.")
        print("Please restart Anki to activate it.")

    except Exception as e:
        print(f"\n❌ An error occurred during installation: {e}")
        print("Please check file permissions and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
