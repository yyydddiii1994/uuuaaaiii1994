# src/cars_addon/reviewer_ui.py

from aqt import gui_hooks
from aqt.reviewer import Reviewer

# --- CSS to hide default buttons and style new ones ---
HAR_CSS = """
<style>
  /* Hide Anki's default answer buttons */
  #answer-buttons { display: none !important; }

  /* Main container for our UI */
  #har-ui-wrapper {
    display: none; /* Hidden by default */
    padding: 8px;
    border-top: 1px solid #e0e0e0;
  }

  /* Shared button container styles */
  .har-buttons-container {
    display: grid;
    gap: 8px;
    max-width: 400px; /* Limit width on larger screens */
    margin: 0 auto;
  }

  #har-step1-container { grid-template-columns: 1fr 1fr; }
  #har-step2-container { grid-template-columns: 1fr 1fr 1fr; }

  .har-btn {
    height: 35px; /* Slightly smaller */
    border-radius: 5px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.2s ease;
  }

  /* More subtle colors */
  .har-incorrect-btn { background-color: #fbe9e7; color: #c62828; border-color: #ffcdd2; }
  .har-correct-btn { background-color: #e8f5e9; color: #2e7d32; border-color: #c8e6c9; }
  .har-hard-btn { background-color: #fffde7; color: #f9a825; border-color: #fff59d; }
  .har-normal-btn { background-color: #e3f2fd; color: #1565c0; border-color: #bbdefb; }
  .har-easy-btn { background-color: #f3e5f5; color: #6a1b9a; border-color: #e1bee7; }

  .har-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  #har-perception-prompt {
      grid-column: 1 / -1;
      text-align: center;
      font-size: 13px;
      color: #757575;
      padding-bottom: 4px;
  }
</style>
"""

# --- HTML structure ---
HAR_HTML = """
<div id="har-ui-wrapper">
  <div id="har-step1-container" class="har-buttons-container">
    <button class="har-btn har-incorrect-btn" onclick="har_answer('incorrect');">🔴 不正解</button>
    <button class="har-btn har-correct-btn" onclick="har_show_perception();">🟢 正解</button>
  </div>
  <div id="har-step2-container" class="har-buttons-container" style="display:none;">
      <div id="har-perception-prompt">このカードの体感難易度は？</div>
      <button class="har-btn har-hard-btn" onclick="har_answer('correct:hard');">難しい</button>
      <button class="har-btn har-normal-btn" onclick="har_answer('correct:normal');">普通</button>
      <button class="har-btn har-easy-btn" onclick="har_answer('correct:easy');">簡単</button>
  </div>
</div>
"""

# --- JavaScript to handle button logic ---
HAR_JS = """
<script>
  // --- DOM Elements ---
  const harWrapper = document.getElementById('har-ui-wrapper');
  const step1Container = document.getElementById('har-step1-container');
  const step2Container = document.getElementById('har-step2-container');

  // --- Core Functions ---
  function har_show_perception() {
    step1Container.style.display = 'none';
    step2Container.style.display = 'grid';
  }

  function har_answer(payload) {
    harWrapper.style.display = 'none'; // Hide immediately after any answer
    pycmd(`HAR:answer:${payload}`);
  }

  // --- Anki Hook Logic ---
  // This hook is called when the question is shown
  onUpdateHook.push(function() {
    if (harWrapper) {
      harWrapper.style.display = 'none'; // Hide when question is shown
    }
  });

  // This hook is called when the answer is shown
  onShownHook.push(function() {
    if (harWrapper) {
      // Reset to initial state (step 1)
      step1Container.style.display = 'grid';
      step2Container.style.display = 'none';
      // Show the UI
      harWrapper.style.display = 'block';
    }
  });
</script>
"""

def inject_har_ui(web_content, context):
    if not isinstance(context, Reviewer):
        return
    web_content.body += HAR_CSS
    web_content.body += HAR_HTML
    web_content.body += HAR_JS

def init_reviewer_ui():
    gui_hooks.webview_will_set_content.append(inject_har_ui)
