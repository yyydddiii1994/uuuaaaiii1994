# src/cars_addon/menu.py

from aqt import mw
from aqt.qt import QAction

from .settings_dialog import SettingsDialog

def open_settings_dialog():
    """
    Creates and shows the settings dialog.
    It's kept alive by assigning it to a variable on mw.
    """
    # We assign the dialog to a variable on the main window (mw)
    # to prevent it from being garbage-collected immediately.
    mw.har_settings_dialog = SettingsDialog(mw)
    mw.har_settings_dialog.show()

def setup_menu():
    """
    Adds a menu item to Anki's "Tools" menu.
    """
    # Get the "Tools" menu from the main window
    tools_menu = mw.form.menuTools

    # Create a new action (menu item)
    action = QAction("HAR アルゴリズム設定＆仕様...", mw)

    # Connect the action's "triggered" signal to our function
    action.triggered.connect(open_settings_dialog)

    # Add a separator and the new action to the menu
    tools_menu.addSeparator()
    tools_menu.addAction(action)

def init_menu():
    """
    Initializes the menu setup.
    This function is called from __init__.py
    """
    # The menu needs to be set up after the main window is fully initialized.
    # The 'main_window_did_init' hook is the perfect place for this.
    from aqt import gui_hooks
    gui_hooks.main_window_did_init.append(setup_menu)
