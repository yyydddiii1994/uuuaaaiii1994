# src/lector_ts_addon/deck_options_ui.py

from aqt.qt import QWidget, QVBoxLayout, QPushButton, QLabel
from aqt import gui_hooks

def on_deck_options_did_load(deck_options_dialog):
    """
    This function is hooked into Anki's deck options screen.
    It will be used to add our custom UI section for LECTOR-TS.
    """
    print("DEBUG: Deck options loaded. LECTOR-TS UI setup would go here.")

    # --- Placeholder for the UI ---
    # In a future step, we will:
    # 1. Create a new QGroupBox or QWidget for our settings.
    # 2. Add a title like "LECTOR-TS Optimization".
    # 3. Add the "Overwhelmingly Optimize! (Using local RTX 4070)" button.
    # 4. Add a QLabel to show progress during optimization.
    # 5. Add this new widget to the layout of the deck_options_dialog.

    # Example of what the code might look like:
    #
    # lector_groupbox = QGroupBox("LECTOR-TS (Next-Gen Scheduling)")
    # lector_layout = QVBoxLayout()
    #
    # optimize_button = QPushButton("Overwhelmingly Optimize! (Using local RTX 4070)")
    # optimize_button.clicked.connect(trigger_optimization) # trigger_optimization would be another function
    #
    # status_label = QLabel("Status: Ready to optimize.")
    #
    # lector_layout.addWidget(optimize_button)
    # lector_layout.addWidget(status_label)
    # lector_groupbox.setLayout(lector_layout)
    #
    # deck_options_dialog.form.vLayout.addWidget(lector_groupbox)
    pass

def trigger_optimization():
    """
    This function will be called when the user clicks the optimize button.
    It will start the LECTOR-TS fine-tuning process in a background thread.
    """
    print("DEBUG: Optimization process triggered (placeholder).")
    # This will involve:
    # - Grabbing the current deck/profile's data.
    # - Kicking off the data pipeline and fine-tuning process.
    # - Updating the status_label with progress.
    pass

def init_deck_options_ui():
    """
    Initializes the hook to add our UI to the deck options screen.
    """
    gui_hooks.deck_options_did_load.append(on_deck_options_did_load)

# This file is not meant to be run directly.
# The init_deck_options_ui() function will be called from __init__.py
