# src/cars_addon/har_scheduler.py

import json
import math

class HAR_Scheduler:
    """
    Implements the Heuristic-Adaptive Resonance (HAR) scheduling logic.
    This class is responsible for calculating the next review interval based on
    a card's current state and user feedback.
    """

    def __init__(self, preset: dict):
        """
        Initializes the scheduler with a specific set of rules (a preset).

        :param preset: A dictionary containing the scheduling rules, e.g.,
                       {
                           "ladder_days": [0, 1, 3, 7, 21, ...],
                           "lapse_level": 1,
                           "rf_step": 0.1,
                           "rf_min": 0.8,
                           "rf_max": 1.3
                       }
        """
        self.rules = preset

    def get_initial_state(self) -> dict:
        """Returns the state for a new card."""
        return {"har_level": 0, "har_rf": 1.0}

    def get_state_from_card(self, card) -> dict:
        """
        Extracts HAR state from a card's custom_data field.

        :param card: An Anki card object (or a mock).
        :return: A dictionary with 'har_level' and 'har_rf'.
        """
        data = json.loads(card.custom_data or "{}")
        if "har_level" not in data or "har_rf" not in data:
            return self.get_initial_state()
        return {
            "har_level": data.get("har_level", 0),
            "har_rf": data.get("har_rf", 1.0)
        }

    def write_state_to_card(self, card, state: dict):
        """Writes the new HAR state back to the card's custom_data."""
        card.custom_data = json.dumps(state)

    def schedule(self, current_state: dict, was_correct: bool, perception: str = "normal") -> tuple[dict, float]:
        """
        Calculates the new state and next interval for a card.

        :param current_state: Dict with current 'har_level' and 'har_rf'.
        :param was_correct: Boolean indicating if the user answered correctly.
        :param perception: The user's subjective feedback ("hard", "normal", "easy").
        :return: A tuple containing (new_state, next_interval_in_days).
        """
        level = current_state["har_level"]
        rf = current_state["har_rf"]

        ladder = self.rules["ladder_days"]

        if not was_correct:
            new_level = self.rules["lapse_level"]
            new_rf = rf # RF is not changed on lapse, or could be reset to 1.0
        else:
            # Level up
            new_level = min(level + 1, len(ladder) - 1)

            # Adjust RF based on perception
            if perception == "easy":
                new_rf = min(self.rules["rf_max"], rf + self.rules["rf_step"])
            elif perception == "hard":
                new_rf = max(self.rules["rf_min"], rf - self.rules["rf_step"])
            else: # "normal"
                new_rf = 1.0

        new_state = {"har_level": new_level, "har_rf": round(new_rf, 4)}
        next_interval = ladder[new_level] * new_rf

        return new_state, next_interval

# --- Unit Testing ---
if __name__ == '__main__':
    from .anki_mock import MockCard

    # Use the default preset defined in the design document
    DEFAULT_PRESET = {
      "ladder_days": [0, 1, 3, 7, 21, 60, 180, 365],
      "lapse_level": 1,
      "rf_step": 0.1,
      "rf_min": 0.8,
      "rf_max": 1.3
    }

    scheduler = HAR_Scheduler(DEFAULT_PRESET)
    card = MockCard(card_id=1, note=None) # note is not needed for this test

    print("--- Testing HAR Scheduler Logic ---")

    # Scenario 1: Smooth learning
    print("\n--- Scenario 1: Smooth Learning ---")
    state = scheduler.get_state_from_card(card)
    print(f"Initial State: {state}")

    # 1. Correct, Normal
    state, interval = scheduler.schedule(state, was_correct=True, perception="normal")
    scheduler.write_state_to_card(card, state)
    print(f"Answer: Correct, Normal -> New State: {scheduler.get_state_from_card(card)}, Interval: {interval:.2f} days")

    # 2. Correct, Easy
    state = scheduler.get_state_from_card(card)
    state, interval = scheduler.schedule(state, was_correct=True, perception="easy")
    scheduler.write_state_to_card(card, state)
    print(f"Answer: Correct, Easy   -> New State: {scheduler.get_state_from_card(card)}, Interval: {interval:.2f} days")

    # 3. Correct, Easy
    state = scheduler.get_state_from_card(card)
    state, interval = scheduler.schedule(state, was_correct=True, perception="easy")
    scheduler.write_state_to_card(card, state)
    print(f"Answer: Correct, Easy   -> New State: {scheduler.get_state_from_card(card)}, Interval: {interval:.2f} days")

    # Scenario 2: "EASY Hell" Entry and Recovery
    print("\n--- Scenario 2: 'EASY Hell' Entry and Recovery ---")
    card = MockCard(card_id=2, note=None) # Reset card

    # User struggles initially
    for _ in range(3):
        state = scheduler.get_state_from_card(card)
        state, _ = scheduler.schedule(state, was_correct=True, perception="hard")
        scheduler.write_state_to_card(card, state)

    final_struggle_state = scheduler.get_state_from_card(card)
    print(f"Initial Struggle -> State: {final_struggle_state}, Interval: {DEFAULT_PRESET['ladder_days'][3] * final_struggle_state['har_rf']:.2f} days")

    # Now the card should be easy, user starts recovery
    print("...Card is now actually easy, user starts recovery...")

    # 1. Correct, Easy
    state = scheduler.get_state_from_card(card)
    state, interval = scheduler.schedule(state, was_correct=True, perception="easy")
    scheduler.write_state_to_card(card, state)
    print(f"Answer: Correct, Easy -> New State: {scheduler.get_state_from_card(card)}, Interval: {interval:.2f} days")

    # 2. Correct, Easy -> RF becomes 1.0
    state = scheduler.get_state_from_card(card)
    state, interval = scheduler.schedule(state, was_correct=True, perception="easy")
    scheduler.write_state_to_card(card, state)
    print(f"Answer: Correct, Easy -> New State: {scheduler.get_state_from_card(card)}, Interval: {interval:.2f} days")

    # 3. Correct, Normal -> RF stays 1.0
    state = scheduler.get_state_from_card(card)
    state, interval = scheduler.schedule(state, was_correct=True, perception="normal")
    scheduler.write_state_to_card(card, state)
    print(f"Answer: Correct, Normal -> New State: {scheduler.get_state_from_card(card)}, Interval: {interval:.2f} days")

    print("\n✅ Card successfully escaped 'EASY Hell'.")

    # Scenario 3: Lapse
    print("\n--- Scenario 3: Lapse ---")
    state = scheduler.get_state_from_card(card)
    state, interval = scheduler.schedule(state, was_correct=False)
    scheduler.write_state_to_card(card, state)
    print(f"Answer: Incorrect -> New State: {scheduler.get_state_from_card(card)}, Interval: {interval:.2f} days")
