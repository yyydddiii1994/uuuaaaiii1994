# run_tests.py
import sys
import os

# 1. Add the 'src' directory to the Python path
# This allows us to import 'cars_addon' as a top-level package.
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)
print(f"✅ Added '{src_path}' to system path.")

# 2. Create a mock for the 'aqt' module *before* importing any addon code
class MockAqt:
    def __init__(self):
        # This class will be the 'aqt' module
        from cars_addon import aqt_mock
        self.mw = aqt_mock.mw

# Add the mock to sys.modules. Any 'from aqt import ...' will now use this.
sys.modules['aqt'] = MockAqt()
print("✅ Successfully mocked the 'aqt' module.")

# 3. Now that the mock is in place, we can safely run the tests.
print("\n--- Running har_scheduler.py tests ---")
try:
    from cars_addon import har_scheduler
    print("✅ har_scheduler.py passed.")
except Exception as e:
    print(f"❌ Error in har_scheduler.py: {e}")

print("\n--- Running logger.py tests ---")
try:
    from cars_addon import logger
    print("✅ logger.py passed.")
    # Verify log file was created
    log_file = os.path.join("src", "cars_addon", "cars_addon.log")
    if os.path.exists(log_file):
        print(f"✅ Log file found at: {log_file}")
    else:
        print(f"❌ Log file was not created.")
except Exception as e:
    print(f"❌ Error in logger.py: {e}")

print("\n--- All tests finished ---")
