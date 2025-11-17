# src/cars_addon/logic.py
import re
import math
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from .anki_mock import MockCard, create_sample_deck

# Load the sentence transformer model. This will be downloaded from the internet on first run.
# Using a lightweight, multilingual model as suggested in the WBS.
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
model = SentenceTransformer(MODEL_NAME)

def strip_html(text: str) -> str:
    """Removes HTML tags from a string."""
    return re.sub('<[^<]+?>', '', text)

def extract_text_from_card(card: MockCard) -> str:
    """
    Extracts and combines all textual content from a card's note.
    HTML tags are stripped from the fields.

    :param card: An Anki card object (or a mock).
    :return: A single string containing the combined text of all fields.
    """
    note = card.note()
    # Combine text from all fields, stripping HTML
    text_parts = [strip_html(field) for field in note.fields]
    return " ".join(text_parts).strip()

def vectorize_texts(texts: list[str]) -> np.ndarray:
    """
    Converts a list of texts into a matrix of sentence embeddings.

    :param texts: A list of strings to be vectorized.
    :return: A numpy array where each row is the vector for the corresponding text.
    """
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings

def estimate_ideal_k(num_cards: int) -> int:
    """
    Estimates the ideal number of clusters (k) based on the total number of cards.
    Using the rule of thumb k ≈ sqrt(N/2).
    """
    if num_cards == 0:
        return 0
    k = math.ceil(math.sqrt(num_cards / 2))
    return max(2, k) # Ensure at least 2 clusters if there are cards

def cluster_vectors(vectors: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Performs K-means clustering on a set of vectors.

    :param vectors: A numpy array of vectors to be clustered.
    :param k: The number of clusters to form.
    :return: A tuple containing:
             - cluster_labels: An array where the index corresponds to the vector and the value is the cluster ID.
             - centroids: The center points of the clusters.
    """
    if k == 0 or len(vectors) < k:
        return np.array([]), np.array([])

    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(vectors)
    return kmeans.labels_, kmeans.cluster_centers_

def run_card_processing_pipeline(mw, query: str) -> dict:
    """
    Runs the full pipeline: finding cards, extracting text, vectorizing, and clustering.

    :param mw: The mock Anki collection object.
    :param query: The card query (e.g., "deck:current").
    :return: A dictionary containing the results, e.g.,
             {
                 'card_ids': [...],
                 'clusters': {0: [cid1, cid2], 1: [cid3, ...]}
             }
    """
    # 1. Find and extract
    print("--- Step 1: Finding cards and extracting text ---")
    card_ids = mw.find_cards(query)
    if not card_ids:
        print("No cards found.")
        return {'card_ids': [], 'clusters': {}}

    card_texts = [extract_text_from_card(mw.get_card(cid)) for cid in card_ids]
    print(f"Found and extracted text from {len(card_ids)} cards.")

    # 2. Vectorize
    print("\n--- Step 2: Vectorizing texts ---")
    vectors = vectorize_texts(card_texts)
    print(f"Successfully created vectors. Matrix shape: {vectors.shape}")

    # 3. Cluster
    print("\n--- Step 3: Clustering vectors ---")
    num_cards = len(card_ids)
    k = estimate_ideal_k(num_cards)
    print(f"Estimated number of clusters (k): {k}")

    cluster_labels, _ = cluster_vectors(vectors, k)

    # 4. Format results
    clusters = {i: [] for i in range(k)}
    if cluster_labels.any():
        for i, cid in enumerate(card_ids):
            cluster_id = cluster_labels[i]
            clusters[cluster_id].append(cid)

    return {
        'card_ids': card_ids,
        'clusters': clusters
    }

# --- Sample Usage ---
if __name__ == '__main__':
    mock_mw = create_sample_deck()

    results = run_card_processing_pipeline(mock_mw, "deck:all")

    print("\n--- 🧠 CARS Pipeline Finished ---")
    print(f"Processed {len(results['card_ids'])} cards into {len(results['clusters'])} clusters.")

    print("\n--- Cluster Details ---")
    for cluster_id, cards_in_cluster in results['clusters'].items():
        print(f"Cluster {cluster_id}:")
        for cid in cards_in_cluster:
            card = mock_mw.get_card(cid)
            text = extract_text_from_card(card)
            print(f"  - Card {cid}: {text}")
