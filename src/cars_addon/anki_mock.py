# src/cars_addon/anki_mock.py

"""
This module provides mock objects that simulate the behavior of Anki's internal
classes (like Card, Note, Collection). This allows for the development and
testing of addon logic in an environment where Anki itself is not running.
"""

class MockNote:
    """Mocks an Anki Note object."""
    def __init__(self, fields):
        """
        Initializes the note with its fields.
        :param fields: A list of strings, representing the content of the note's fields (e.g., ['Front', 'Back']).
        """
        self.fields = fields
        self._fmap = {str(i): (i, v) for i, v in enumerate(fields)}

    def __getitem__(self, key):
        return self.fields[int(key)]

    def items(self):
        return [(str(i), v) for i, v in enumerate(self.fields)]


class MockCard:
    """Mocks an Anki Card object."""
    def __init__(self, card_id, note):
        """
        Initializes the card.
        :param card_id: The card's unique ID.
        :param note: The MockNote object associated with this card.
        """
        self.id = card_id
        self._note = note

    def note(self):
        return self._note


class MockCollection:
    """Mocks the Anki Collection (mw.col)."""
    def __init__(self):
        self.cards = {}
        self.notes = {}

    def add_note(self, note_fields):
        """Adds a new note and a corresponding card to the mock collection."""
        note_id = len(self.notes) + 1000
        card_id = len(self.cards) + 2000

        note = MockNote(note_fields)
        card = MockCard(card_id, note)

        self.notes[note_id] = note
        self.cards[card_id] = card
        return card

    def get_card(self, card_id):
        """Retrieves a card by its ID."""
        return self.cards.get(card_id)

    def find_cards(self, query):
        """
        Simulates finding cards based on a query.
        For simplicity, this mock returns all card IDs.
        :param query: The search query (e.g., "deck:current").
        """
        # In a real scenario, this would parse the query. Here, we just return all card ids.
        return sorted(self.cards.keys())

# --- Sample Usage ---
def create_sample_deck():
    """Creates and returns a mock collection with some sample cards."""
    mw = MockCollection()
    mw.add_note(["What is the capital of Japan?", "Tokyo"])
    mw.add_note(["What is 2 + 2?", "Four"])
    mw.add_note(["What element has the symbol 'O'?", "Oxygen"])
    mw.add_note(["Explain photosynthesis.", "A process used by plants to convert light energy into chemical energy."])
    mw.add_note(["Who wrote 'Hamlet'?", "William Shakespeare"])
    return mw

if __name__ == '__main__':
    # Example of how to use the mock objects
    mock_mw = create_sample_deck()

    # Get all card IDs
    card_ids = mock_mw.find_cards("deck:some_deck")
    print(f"Found card IDs: {card_ids}")

    # Get a specific card and its note
    if card_ids:
        first_card = mock_mw.get_card(card_ids[0])
        note = first_card.note()
        print(f"Card ID: {first_card.id}")
        print(f"  Front: {note.fields[0]}")
        print(f"  Back: {note.fields[1]}")
