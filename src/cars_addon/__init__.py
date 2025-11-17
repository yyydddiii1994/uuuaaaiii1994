# src/cars_addon/__init__.py

try:
    # This will fail if Anki is not running, which is useful for testing.
    from aqt import mw
except ImportError:
    mw = None

if mw:
    from . import hooks
    from . import reviewer_ui
    from .logger import log

def initialize_addon():
    """
    Initializes all components of the CARS addon.
    """
    log.info("Initializing CARS Addon...")

    # 1. Load configuration
    try:
        config = mw.addonManager.getConfig(__name__)
        if not config or "presets" not in config:
            log.error("Failed to load or parse config.json. Addon may not work correctly.")
            return

        # Pass the loaded config to the hooks module so it can be used by the scheduler
        hooks.loaded_config = config
        log.info(f"Configuration loaded. Selected preset: {config.get('selected_preset')}")

    except Exception as e:
        log.exception("An error occurred while loading the configuration.", exc_info=True)
        return

    # 2. Initialize backend hooks
    try:
        hooks.init_hooks()
        log.info("Backend hooks initialized.")
    except Exception as e:
        log.exception("An error occurred while initializing backend hooks.", exc_info=True)

    # 3. Initialize reviewer UI modifications
    try:
        reviewer_ui.init_reviewer_ui()
        log.info("Reviewer UI initialized.")
    except Exception as e:
        log.exception("An error occurred while initializing the reviewer UI.", exc_info=True)

    log.info("CARS Addon initialization complete.")

# Run the initialization function only when Anki is running
if mw:
    initialize_addon()
