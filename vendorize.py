# vendorize.py

import os
import sys
import shutil
import subprocess

def main():
    """
    Installs all dependencies from requirements.txt into the addon's 'vendor' directory.
    This allows the addon to be self-contained and not interfere with other Python environments.
    """
    print("--- Starting Vendorization Process ---")

    # --- Configuration ---
    addon_dir = os.path.join("src", "lector_ts_addon")
    vendor_dir = os.path.join(addon_dir, "vendor")
    requirements_file = "requirements.txt"

    if not os.path.exists(requirements_file):
        print(f"❌ Error: '{requirements_file}' not found.")
        sys.exit(1)

    # --- Clean up existing vendor directory ---
    if os.path.exists(vendor_dir):
        print(f"🧹 Found existing vendor directory. Removing it for a clean install...")
        try:
            shutil.rmtree(vendor_dir)
            print("✅ Successfully removed old vendor directory.")
        except OSError as e:
            print(f"❌ Error removing directory '{vendor_dir}': {e}")
            sys.exit(1)

    print(f"📦 Creating new vendor directory at: {vendor_dir}")
    os.makedirs(vendor_dir, exist_ok=True)

    # --- Install dependencies using pip ---
    print(f"\\n🐍 Installing dependencies from '{requirements_file}' into '{vendor_dir}'...")

    # We use subprocess to run pip. The '-t' flag directs the installation to our vendor folder.
    pip_command = [
        sys.executable,  # Use the same python interpreter that is running this script
        "-m", "pip",
        "install",
        "--requirement", requirements_file,
        "--target", vendor_dir,
    ]

    try:
        # We stream the output of the subprocess to give real-time feedback
        process = subprocess.Popen(pip_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, pip_command)

        print("\n🎉 --- Vendorization Complete! --- 🎉")
        print("All dependencies have been installed into the 'vendor' directory.")
        print("The addon is now self-contained.")

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\\n❌ An error occurred during pip installation: {e}")
        print("Please ensure pip is installed and your requirements.txt is valid.")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
