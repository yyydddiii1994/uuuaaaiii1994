# src/lector_ts_addon/anki_mock.py

import pandas as pd
from typing import List, Dict, Any

class MockDb:
    """Mocks the Anki database object (col.db)."""
    def all(self, sql: str) -> List[Dict[str, Any]]:
        """
        Mocks the 'all' method to return dummy data for specific queries.
        """
        if "revlog" in sql.lower():
            # Return dummy revlog data matching a real query's structure
            return [
                {'id': 1609459200000, 'cid': 1500000000001, 'ease': 3, 'ivl': 1},
                {'id': 1609545600000, 'cid': 1500000000002, 'ease': 3, 'ivl': 1},
                {'id': 1609632000000, 'cid': 1500000000001, 'ease': 1, 'ivl': 0},
                {'id': 1609718400000, 'cid': 1500000000003, 'ease': 3, 'ivl': 1},
                {'id': 1609804800000, 'cid': 1500000000001, 'ease': 3, 'ivl': 4},
            ]
        elif "notes" in sql.lower():
             # Mocks a JOIN between cards and notes
            return [
                {'nid': 1500000000001, 'flds': "Q: Capital of France?<br>A: <b>Paris</b>"},
                {'nid': 1500000000002, 'flds': "Q: 2 + 2?<br>A: <i>4</i>"},
                {'nid': 1500000000003, 'flds': "Q: Who wrote Hamlet?<br>A: William Shakespeare"},
            ]
        return []

class MockCollection:
    """Mocks the Anki Collection (mw.col)."""
    def __init__(self):
        self.db = MockDb()

# --- Sample Usage ---
if __name__ == '__main__':
    print("--- Testing Anki Mock Objects ---")
    mock_col = MockCollection()

    # Test revlog fetching
    revlog_data = mock_col.db.all("SELECT * FROM revlog")
    revlog_df = pd.DataFrame(revlog_data)
    print("\n--- Mock Revlog DataFrame ---")
    print(revlog_df)

    # Test notes fetching
    notes_data = mock_col.db.all("SELECT n.id as nid, n.flds FROM notes n JOIN cards c ON n.id = c.nid")
    print("\n--- Mock Notes Data ---")
    for note in notes_data:
        print(note)

    print("\n✅ Mock objects are working as expected.")
