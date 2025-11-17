# src/cars_addon/logger.py

import logging
import os
from aqt import mw

# Get the addon manager to find the addon's folder path
addon_path = os.path.dirname(__file__)

# Define the log file path
LOG_FILE = os.path.join(addon_path, "cars_addon.log")

# --- Setup the logger ---
# We get a logger instance named after our addon.
log = logging.getLogger(__name__)

# Configure the logger (only if it has no handlers yet, to avoid duplicate logs)
if not log.handlers:
    log.setLevel(logging.DEBUG)

    # Create a file handler to write logs to a file
    file_handler = logging.FileHandler(LOG_FILE, "a", "utf-8")
    file_handler.setLevel(logging.DEBUG)

    # Create a formatter to define the log message format
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Add the formatter to the handler
    file_handler.setFormatter(formatter)

    # Add the handler to the logger
    log.addHandler(file_handler)

    log.info("--- Logger initialized for CARS Addon ---")

# --- Example Usage ---
if __name__ == '__main__':
    # This block won't run inside Anki, but serves as a test
    log.debug("This is a debug message.")
    log.info("This is an info message.")
    log.warning("This is a warning.")
    log.error("This is an error.")
    try:
        1 / 0
    except ZeroDivisionError:
        log.exception("An exception occurred!")

    print(f"Log messages written to: {LOG_FILE}")
