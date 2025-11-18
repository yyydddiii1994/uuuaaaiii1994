# src/lector_ts_addon/data_pipeline.py

import pandas as pd
from typing import List, Dict

# This will be replaced by the actual Anki collection object (mw.col)
# when the addon is running. For now, we use 'None' as a placeholder.
AnkiCollection = "typing.Any"

def get_all_revlog_entries(col: AnkiCollection) -> pd.DataFrame:
    """
    Extracts the entire review history (revlog) from the Anki collection
    and returns it as a pandas DataFrame.

    :param col: The Anki collection object (mw.col).
    :return: A DataFrame with columns like ['id', 'cid', 'usn', 'ease', 'ivl', 'lastIvl', 'factor', 'time', 'type'].
    """
    print("DEBUG: Fetching all revlog entries...")
    # In a real implementation, this would be:
    # return pd.DataFrame(col.db.all("SELECT * FROM revlog"))

    # For now, return a dummy DataFrame for testing
    dummy_data = {
        'id': [1609459200000 + i*86400000 for i in range(5)],
        'cid': [1500000000000 + i for i in range(5)],
        'ease': [3, 3, 1, 3, 3],
        'ivl': [1, 4, 0, 1, 4],
    }
    return pd.DataFrame(dummy_data)

def get_all_notes(col: AnkiCollection) -> Dict[int, str]:
    """
    Extracts the content (all fields combined) for every note in the collection.

    :param col: The Anki collection object (mw.col).
    :return: A dictionary mapping note_id (nid) to its combined text content.
    """
    print("DEBUG: Fetching all note contents...")
    # In a real implementation, this would involve querying the 'notes' and 'cards' tables
    # and stripping HTML.

    # For now, return a dummy dictionary
    return {
        1500000000001: "Q: What is the capital of France? A: Paris",
        1500000000002: "Q: What is 2 + 2? A: 4",
        1500000000003: "Q: Who wrote Hamlet? A: William Shakespeare",
    }

def preprocess_data(revlog: pd.DataFrame, notes: Dict[int, str]) -> "torch.utils.data.Dataset":
    """
    The main function that will eventually:
    1.  Merge revlog and note content.
    2.  Create text embeddings for LECTOR.
    3.  Calculate semantic interference features.
    4.  Build time-series sequences for the RWKV model.
    5.  Return a PyTorch-compatible Dataset.
    """
    print("DEBUG: Preprocessing data (placeholder)...")
    # This will be the core of the ML data preparation logic.

    # For now, just print the shapes of the inputs
    print(f"  - Received revlog with shape: {revlog.shape}")
    print(f"  - Received {len(notes)} notes.")

    # Placeholder for the final dataset
    return None

if __name__ == "__main__":
    print("--- Running data_pipeline.py standalone test ---")
    # We pass 'None' for the collection object, as our dummy functions don't use it.
    revlog_df = get_all_revlog_entries(None)
    notes_dict = get_all_notes(None)

    print("\n--- Revlog DataFrame ---")
    print(revlog_df.head())

    print("\n--- Notes Dictionary ---")
    print(notes_dict)

    print("\n--- Preprocessing ---")
    preprocess_data(revlog_df, notes_dict)

    print("\n✅ data_pipeline.py skeleton runs successfully.")
