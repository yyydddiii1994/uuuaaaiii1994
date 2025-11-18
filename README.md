# LECTOR-TS (LLM-Enhanced Concept-based Test-Oriented Repetition - Time Series) Anki Addon

This is the official repository for the LECTOR-TS Anki addon, a next-generation scheduling algorithm designed to surpass FSRS by incorporating content-aware and context-aware learning principles.

## The LECTOR-TS Paradigm

FSRS (Free Spaced Repetition Scheduler) is a powerful content-agnostic scheduler. However, its blindness to the *content* of cards and the *context* of review sessions represents a fundamental limitation.

LECTOR-TS overcomes this by moving from a purely statistical model to a dual deep learning architecture:

1.  **LECTOR (Content-Aware Model):** Uses a lightweight Transformer model (like Sentence-BERT) to analyze the text of all cards. It builds a semantic interference graph to understand which cards are conceptually similar (e.g., "JFK's assassination in 1963" vs. "Celtic's European Cup win in 1967") and are therefore likely to cause memory interference.

2.  **TS (Context-Aware Model):** Utilizes a state-of-the-art RWKV (Receptance-weighted-Key-Value) time-series model to treat a user's review history not as independent events, but as a continuous sequence. This allows it to model factors FSRS ignores, such as learning load, fatigue, and the memory consolidation effects of sleep.

## "Overwhelming Optimization!" Button

The core of this addon is the **"Overwhelmingly Optimize! (Using local RTX 4070)"** button. When pressed, it will:

1.  **Pre-process** your entire Anki collection, extracting review logs and card content.
2.  **Fine-tune** a pre-trained LECTOR-TS neural network model on your personal data using your local GPU (e.g., RTX 4070) via QLoRA for efficient on-device training.
3.  **Deploy** the personalized model, which will then be used for all subsequent scheduling decisions.

This project is currently under heavy development.
