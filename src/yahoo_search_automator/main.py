import sys
import os

# Add the src directory to sys.path to ensure local imports work even if run from different cwd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.yahoo_search_automator.gui import SearchApp

def main():
    try:
        app = SearchApp()
        app.mainloop()
    except Exception as e:
        print(f"Critical Error: {e}")
        # In case GUI fails to start
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
