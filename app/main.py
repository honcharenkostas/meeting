import sys
import os
import time
from datetime import datetime
import shutil
import subprocess
import logging
import tempfile
import psutil
from models.db import SessionLocal, UserLogs


logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s"
)
db = SessionLocal()


class App:
    CHROME_CDP_PORT=9222 # http://localhost:9222 must be not in use on User's machine
    CHECK_INTERVAL = 1 # 1sec

    ACTIVITY_STATUS_SAFE = "safe"
    ACTIVITY_STATUS_WARNING = "warning"
    ACTIVITY_STATUS_DANGER = "danger"

    is_running = False
    log_id = 0

    def __init__(self):
        chrome_path = self.find_chrome_executable()
        chrome_path = self.find_chrome_executable()
        process = subprocess.Popen([
            chrome_path,
            f"--remote-debugging-port={self.CHROME_CDP_PORT}",
            f"--user-data-dir={self.get_user_data_dir()}"
        ])
        time.sleep(5)
        if process:
            logging.info("Chrome launched")
        else:
            raise Exception("Chrome launching failed")
    
    def run(self):
        self.is_running = True
        self.run_checker()
    
    def check_for_cheating_software(self):
        for proc in psutil.process_iter(attrs=["name"]):
            if "cluely" in proc.info["name"].lower():
                return True
        
        return False

    def run_checker(self):
        self.log_id = 0 # reset log_id
        while self.is_running:
            self.log_id += 1 # incremet log_id
            
            cheating_detected = self.check_for_cheating_software()
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

            time.sleep(self.CHECK_INTERVAL)
        
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
        app = App()
        app.run()
    except KeyboardInterrupt:
        logging.info("Shutting down ...")