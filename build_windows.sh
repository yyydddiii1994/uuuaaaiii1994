#!/bin/bash
# Install wine if not present
if ! command -v wine &> /dev/null
then
    sudo apt-get update && sudo apt-get install -y wine
fi
# We can use PyInstaller in wine if we install windows python, but since it's complex, we can use wine to run a portable python or cross compilation.
# Alternatively, a much simpler approach is to tell the user to build it on their machine. Let me just provide a build_exe.py script.
