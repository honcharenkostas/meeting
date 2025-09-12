import sys
import os
import time
from datetime import datetime
import shutil
import subprocess
import logging
import tempfile
import psutil
import threading
import tkinter as tk
from playwright.sync_api import sync_playwright
from models.db import SessionLocal, UserLogs


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

db = SessionLocal()


class App:
    ACTIVITY_STATUS_SAFE = "safe"
    ACTIVITY_STATUS_WARNING = "warning"
    ACTIVITY_STATUS_DANGER = "danger"
    ZOOM_URL = "https://app.zoom.us/wc/6810523567/join?fromPWA=1&pwd=hfuKvvkIOuTNlESTRNWZJ8jI6YSaie.1"
    CHROME_CDP_PORT=9222 # http://localhost:9222 must be not in use on User's machine
    CHECK_INTERVAL = 1 # 1sec

    running = False
    log_id = 0

    def __init__(self, root):
        self.root = root
        root.title("Corporate Meeting")
        root.geometry("300x150")

        self.status_label = tk.Label(root, text="Status: Not running")
        self.status_label.pack(pady=10)

        self.start_btn = tk.Button(root, text="Start Monitoring", command=self.start_monitor)
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(root, text="Stop Monitoring", command=self.stop_monitor, state=tk.DISABLED)
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

        self.thread = threading.Thread(target=self.run)
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

    def run(self):
        self.log_id = 0 # reset log_id
        try:
            # launch browser
            user_data_dir = os.path.join(tempfile.gettempdir(), "chrome_profile")
            os.makedirs(user_data_dir, exist_ok=True)
            chrome_path = self.find_chrome_executable()
            process = subprocess.Popen([
                chrome_path,
                "--remote-debugging-address=127.0.0.1",
                f"--remote-debugging-port={self.CHROME_CDP_PORT}",
                f"--user-data-dir={user_data_dir}"  # self.get_user_data_dir()
            ])
            time.sleep(20)
            if process:
                logging.info("Chrome launched")
            else:
                raise Exception("Chrome launching failed")

            self.status_label.config(text="Status: Connecting to Chrome...")

            with sync_playwright() as p:
                # connect over cdp
                self.browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{self.CHROME_CDP_PORT}")
                self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
                self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
                self.page.goto(self.ZOOM_URL)
                logging.info(f"Navigated to Zoom URL: {self.ZOOM_URL}")

                self.status_label.config(text="Status: Monitoring Zoom page")
                time.sleep(10)

                while self.running:
                    try:
                        pages = self.context.pages
                        log_msg = ""
                        if not pages:
                            log_msg = "❌ No open browser pages"
                            self.status_label.config(text=log_msg)
                            logging.info(log_msg)

                        page = pages[0]
                        current_url = page.url
                        page.locator("title").inner_text() # hack for refreshing page.url

                        if not log_msg:
                            if current_url.startswith("https://app.zoom.us/wc/6810523567"):
                                self.status_label.config(text="✅ Zoom page open")
                            else:
                                log_msg = "⚠️ URL changed"
                                self.status_label.config(text=log_msg)

                        if log_msg:
                            self.log_id += 1 # incremet log_id
                            self.status_label.config(text=log_msg)
                            log_datetime = datetime.now()
                            logging.info(log_msg)

                            user_log = UserLogs()
                            user_log.user_id = "test-user"
                            user_log.user_fingerprint = "test-fingerprint"
                            user_log.meeting_id = "test-meeting"
                            user_log.log_id = self.log_id
                            user_log.log = log_msg
                            user_log.activity_status = self.ACTIVITY_STATUS_WARNING
                            user_log.logged_at = log_datetime
                            user_log.created_at = log_datetime
                            db.add(user_log)
                            db.commit()

                        self.check_for_cheating_software()
                        time.sleep(self.CHECK_INTERVAL)
                    except Exception as e:
                        logging.error(f"Page monitoring error: {e}")
                        pass

        except Exception as e:
            self.status_label.config(text=f"Error: {e}")
            logging.error(f"Error: {e}")
        finally:
            if self.browser:
                self.browser.close()
            if self.chrome_process:
                self.chrome_process.terminate()
            logging.error("Chrome and Playwright closed")
    
    
    @staticmethod
    def check_for_software(software):
        for proc in psutil.process_iter(attrs=["name"]):
            if software in proc.info["name"].lower():
                return True
        
        return False

    def check_for_cheating_software(self):
        self.log_id += 1 # incremet log_id
        
        cheating_detected = self.check_for_software("cluely")
        log_datetime = datetime.now()
        if cheating_detected:
            activity_status = self.ACTIVITY_STATUS_DANGER
            msg = "❌ Cluely is running"
        else:
            activity_status = self.ACTIVITY_STATUS_SAFE
            msg = "✅ Cheating software in not running"

        # output log for debug
        logging.info(msg)

        # show log in the software
        # self.status_label.config(text=msg)

        # save log
        user_log = UserLogs()
        user_log.user_id = "test-user"
        user_log.user_fingerprint = "test-fingerprint"
        user_log.meeting_id = "test-meeting"
        user_log.log_id = self.log_id
        user_log.log = msg
        user_log.activity_status = activity_status
        user_log.logged_at = log_datetime
        user_log.created_at = log_datetime
        db.add(user_log)
        db.commit()
        
    @staticmethod
    def get_user_data_dir():
        if sys.platform.startswith("win"):
            return os.path.join(os.environ["LOCALAPPDATA"], "Google", "Chrome", "User Data")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/Google/Chrome")
        else:  # Linux / Unix
            return os.path.expanduser("~/.config/google-chrome")
        
    @staticmethod
    def find_chrome_executable():
        candidates = []
        if sys.platform == "darwin":  # macOS
            candidates = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            ]
        elif sys.platform.startswith("win"):  # Windows
            candidates = [
                os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            ]

        for c in candidates:
            path = shutil.which(c) if not os.path.isabs(c) else (c if os.path.exists(c) else None)
            if path:
                return path

        raise Exception("Chrome executable not found")
    

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = App(root)
        root.protocol("WM_DELETE_WINDOW", app.stop_monitor)
        root.mainloop()
    except KeyboardInterrupt:
        logging.info("Shutting down ...")