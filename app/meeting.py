import sys, os
sys.path.append(os.path.dirname(__file__))  # add current dir
import subprocess
import time
import threading
import sys
import os
import shutil
import logging
import tkinter as tk
from playwright.sync_api import sync_playwright
from datetime import datetime
from models.db import SessionLocal, UserLogs


os.environ["DB_HOST"] = "34.70.21.253"
os.environ["DB_PORT"] = "5432"
os.environ["DB_USER"] = "sandbox"
os.environ["DB_PASSWORD"] = "ThisIsSandbox123$"
os.environ["DB_NAME"] = "sandbox"


CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"  # TODO
ZOOM_URL = "https://app.zoom.us/wc/6810523567/join?fromPWA=1&pwd=hfuKvvkIOuTNlESTRNWZJ8jI6YSaie.1"


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/Users/stas/code/meeting/app/app.log", mode="w", delay=False),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)


class ZoomMonitorApp:
    def __init__(self, root):
        self.root = root
        self.db = SessionLocal()
        root.title("Meeting App")
        root.geometry("300x150")

        self.status_label = tk.Label(root, text="Status: Not running")
        self.status_label.pack(pady=10)

        self.start_btn = tk.Button(root, text="Start Meeting", command=self.start_monitor)
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(root, text="Stop Meeting", command=self.stop_monitor, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

        self.running = False
        self.thread = None
        self.browser = None
        self.context = None
        self.page = None
        self.chrome_process = None

    def start_monitor(self):
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Starting Chrome...")
        logging.info("Starting Chrome for Zoom monitoring")

        self.thread = threading.Thread(target=self.monitor_zoom)
        self.thread.start()

    def stop_monitor(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Stopped")
        logging.info("Stopped monitoring")

        if self.browser:
            self.browser.close()
        if self.chrome_process:
            self.chrome_process.terminate()

    def monitor_zoom(self):
        try:
            # Launch Chrome with remote debugging
            self.chrome_process = subprocess.Popen([
                CHROME_PATH,
                "--remote-debugging-port=9222",
                "--user-data-dir=/tmp/chrome-profile"
            ])
            time.sleep(5)
            logging.info("Chrome launched")

            self.status_label.config(text="Status: Connecting to Chrome...")

            with sync_playwright() as p:
                self.browser = p.chromium.connect_over_cdp("http://localhost:9222")
                self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
                self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
                self.page.goto(ZOOM_URL)
                logging.info(f"Navigated to Zoom URL: {ZOOM_URL}")

                self.status_label.config(text="Status: Monitoring Zoom page")
                time.sleep(20)

                while self.running:
                    try:
                        pages = self.context.pages
                        if not pages:
                            self.status_label.config(text="❌ No open pages")
                            logging.info("No open pages detected")
                            # break

                        page = pages[0]
                        current_url = page.url
                        title = page.locator("title").inner_text()
                        logging.info(f"URL: {current_url} | Title: {title}")

                        if current_url.startswith("https://app.zoom.us/wc/6810523567"):
                            self.status_label.config(text="✅ Zoom page open")
                        else:
                            self.status_label.config(text=f"⚠️ URL changed")

                        time.sleep(1)
                    except Exception as e:
                        logging.info(f"Page monitoring error: {e}")
                        pass

        except Exception as e:
            self.status_label.config(text=f"Error: {e}")
            logging.info(f"Error: {e}")
        finally:
            if self.browser:
                self.browser.close()
            if self.chrome_process:
                self.chrome_process.terminate()
            logging.info("Chrome and Playwright closed")


if __name__ == "__main__":
    root = tk.Tk()
    app = ZoomMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.stop_monitor)
    root.mainloop()