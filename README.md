# HAR (Heuristic-Adaptive Resonance) Anki Addon

**Tired of "Ease Hell"? Frustrated by FSRS's black box? This addon offers a new way.**

HAR is a next-generation scheduling algorithm for Anki that prioritizes **user comfort, transparency, and intuitive control** over pure mathematical optimization. It's designed to make your learning experience feel "effortless" by aligning with your perception of difficulty, not just a complex memory model.

This project implements the [Heuristic-Adaptive Resonance (HAR) algorithm](https://example.com/har-paper), a groundbreaking proposal that challenges the core design of traditional Spaced Repetition Systems (SRS).

## The HAR Philosophy

Traditional SRS like SM-2 and FSRS have known pain points:
- **SM-2's "Ease Hell"**: Cards that are initially difficult remain stuck in short review intervals forever, even after you've mastered them.
- **FSRS's "Black Box"**: A complex, parameter-heavy system that requires "optimization" and can produce unpredictable, unintuitive review schedules, causing user anxiety.

HAR solves these problems with three core principles:

1.  **Transparent "Interval Ladder"**: No more guessing. Your card's progress is tracked across simple, visible levels (L1 to L10), each with a clear base interval (e.g., L1=1d, L2=3d, L3=7d). This brings back the tangible sense of progress found in systems like Leitner.

2.  **Decoupled Two-Step Feedback**: HAR fixes a fundamental design flaw in other SRS. Instead of mixing "did I get it right?" with "how did it feel?" into one set of buttons, HAR separates them:
    *   **Step 1 (Performance)**: You first answer with a simple `🔴 Incorrect` or `🟢 Correct`.
    *   **Step 2 (Perception)**: Only if you were correct, you give optional feedback on how it *felt*: `Hard`, `Normal`, or `Easy`. This provides clean, unambiguous data.

3.  **The "Resonance Factor" (RF)**: This is how HAR escapes "Ease Hell" without FSRS's complexity. Your subjective feedback (`Hard`/`Easy`) adjusts a simple multiplier (the RF) on each card. If a card *feels* easier over time, its RF increases, gently lengthening its interval. If it feels harder, the RF decreases. It's an adaptive system that resonates with your personal learning experience.

## Features

- **User-Centric Scheduling**: Implements the full HAR algorithm.
- **Intuitive Two-Step UI**: Replaces Anki's default answer buttons with the new, unambiguous feedback system.
- **"One-Click" Goal Presets**: No complex parameters to tune. Simply choose your goal (e.g., "Long-Term Learning" or "Exam Cramming") from a dropdown, and the addon adjusts the interval ladder for you.
- **Easy Installation**: Comes with a simple command-line script (`install.py`) to automatically place the addon in the correct Anki folder.
- **Detailed Logging**: All addon activities are logged to `cars_addon.log` for easy troubleshooting.

## How to Install

1.  Ensure you have Python installed.
2.  Clone this repository.
3.  Run the installer from your terminal:
    ```bash
    python install.py
    ```
4.  Restart Anki.
5.  (Optional) Go to `Tools > Add-ons > CARS Addon > Config` to change your learning goal preset.
