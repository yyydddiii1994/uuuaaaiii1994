# src/cars_addon/reviewer_ui.py

from aqt import gui_hooks
from aqt.reviewer import Reviewer

# --- CSS to hide default buttons and style new ones ---
HAR_CSS = """
<style>
  /* Hide Anki's default answer buttons */
  #answer-buttons {
    display: none !important;
  }

  /* Container for HAR buttons */
  #har-buttons-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    padding: 10px;
  }

  #har-perception-container {
    grid-template-columns: 1fr 1fr 1fr;
  }

  .har-btn {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 40px;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    border: none;
    color: white;
  }

  .har-incorrect-btn { background-color: #D32F2F; } /* Red */
  .har-correct-btn { background-color: #388E3C; } /* Green */

  .har-hard-btn { background-color: #FBC02D; color: #212121;} /* Yellow */
  .har-normal-btn { background-color: #1976D2; } /* Blue */
  .har-easy-btn { background-color: #7B1FA2; } /* Purple */

  #har-perception-prompt {
      grid-column: 1 / -1; /* Span all columns */
      text-align: center;
      font-size: 14px;
      padding-bottom: 5px;
  }
</style>
"""

# --- HTML structure for the new buttons ---
HAR_HTML = """
<div id="har-buttons-container">
  <button class="har-btn har-incorrect-btn" onclick="har_answer('incorrect');">🔴 不正解</button>
  <button class="har-btn har-correct-btn" onclick="har_show_perception();">🟢 正解</button>
</div>

<div id="har-perception-container" style="display:none;">
    <div id="har-perception-prompt">このカードの体感難易度は？</div>
    <button class="har-btn har-hard-btn" onclick="har_answer('correct:hard');">難しい</button>
    <button class="har-btn har-normal-btn" onclick="har_answer('correct:normal');">普通</button>
    <button class="har-btn har-easy-btn" onclick="har_answer('correct:easy');">簡単</button>
</div>
"""

# --- JavaScript to handle button logic ---
HAR_JS = """
<script>
  function har_show_perception() {
    // Hide the Correct/Incorrect buttons and show the perception buttons
    document.getElementById('har-buttons-container').style.display = 'none';
    document.getElementById('har-perception-container').style.display = 'grid';
  }

  function har_answer(payload) {
    // Send the answer back to Python
    pycmd(`HAR:answer:${payload}`);
  }

  // Hook into Anki's showAnswer event to ensure the buttons are ready
  onShownHook.push(function() {
    // Reset UI to the initial state (Correct/Incorrect)
    document.getElementById('har-buttons-container').style.display = 'grid';
    document.getElementById('har-perception-container').style.display = 'none';
  });
</script>
"""

def inject_har_ui(web_content, context):
    """
    This hook function is called by Anki when the reviewer content is being prepared.
    It injects the custom HTML, CSS, and JavaScript for the HAR UI.
    """
    if not isinstance(context, Reviewer):
        return

    # Append our custom UI elements to the web content
    web_content.body += HAR_CSS
    web_content.body += HAR_HTML
    web_content.body += HAR_JS

def init_reviewer_ui():
    """Initializes the reviewer UI hooks."""
    gui_hooks.webview_will_set_content.append(inject_har_ui)

# This file is not meant to be run directly.
# The init_reviewer_ui() function will be called from __init__.py
