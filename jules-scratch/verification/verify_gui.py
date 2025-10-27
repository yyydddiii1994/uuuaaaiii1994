import asyncio
import subprocess
import time
from playwright.async_api import async_playwright

async def main():
    command = ["xvfb-run", "-a", "python3", "main_app.py"]
    app_process = subprocess.Popen(command)

    try:
        print("Waiting for application to launch (10 seconds)...")
        time.sleep(10)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            screenshot_path = "jules-scratch/verification/verification.png"
            print(f"Taking screenshot of the entire screen...")
            # Take a screenshot of the entire screen
            await page.screenshot(path=screenshot_path, full_page=True)

            await browser.close()
            print("Screenshot taken successfully.")

    finally:
        print("Terminating application process.")
        app_process.terminate()
        await asyncio.sleep(1)
        if app_process.poll() is None:
            print("Forcing termination.")
            app_process.kill()

if __name__ == "__main__":
    asyncio.run(main())
