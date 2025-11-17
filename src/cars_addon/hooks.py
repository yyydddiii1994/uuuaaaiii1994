# src/cars_addon/hooks.py

import json
from aqt import mw, gui_hooks
from aqt.reviewer import Reviewer

from .har_scheduler import HAR_Scheduler

# This will hold the currently loaded preset from config.json
# It's populated by the logic in __init__.py
loaded_config = {}

def on_js_message(handled, message: str, context):
    """
    Handles messages sent from the HAR UI in the reviewer WebView.
    """
    # Only process messages that are for us and are coming from a Reviewer context
    if message.startswith("HAR:answer:") and isinstance(context, Reviewer):

        card = context.card
        if not card or not loaded_config.get("presets"):
            # Card might not be available, or config not loaded. Do nothing.
            return handled

        # 1. Parse the message payload
        try:
            parts = message.replace("HAR:answer:", "").split(":")
            was_correct = parts[0] == "correct"
            perception = parts[1] if len(parts) > 1 else "normal"
        except IndexError:
            # Malformed message, ignore it
            return handled

        # 2. Initialize the scheduler with the selected preset
        preset_name = loaded_config.get("selected_preset", "Long-Term Learning")
        preset = loaded_config["presets"].get(preset_name)
        if not preset:
            # Preset not found, should not happen if config is valid
            return handled

        scheduler = HAR_Scheduler(preset)

        # 3. Get current state from the card
        current_state = scheduler.get_state_from_card(card)

        # 4. Apply HAR logic to get the new state and interval
        new_state, new_interval_days = scheduler.schedule(current_state, was_correct, perception)

        # 5. Write the new state back to the card
        scheduler.write_state_to_card(card, new_state)

        # 6. Manually reschedule the card in Anki's collection
        # We need to tell Anki the card has been reviewed and set its due date.
        # This is a simplified approach; a real implementation needs more robust handling
        # of different queue types, but it demonstrates the core concept.
        if new_interval_days > 0:
            # Note: Anki's internal scheduling methods are complex.
            # `set_due_date` is a direct way to achieve the HAR goal for now.
            # The string format "YYYY-MM-DD" is also possible.
            due_date_str = f"{int(round(new_interval_days))}d"
            mw.col.sched.set_due_date([card.id], due_date_str)

        # Mark the card as answered to remove it from the current session's queue
        # This part requires deeper integration with the scheduler, for now we let Anki handle it
        # after we've set the due date.

        # 7. Tell the reviewer to show the next card
        context.nextCard()

        # We have handled the message, so we return True
        return (True, None)

    # If the message was not for us, pass it on
    return handled

def init_hooks():
    """Initializes all backend hooks."""
    gui_hooks.webview_did_receive_js_message.append(on_js_message)

# This file is not meant to be run directly.
# The init_hooks() and config loading will be managed from __init__.py
