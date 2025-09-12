import sys
import os
import time
import shutil
import subprocess
import logging
import tempfile


class App:
    CHROME_CDP_PORT=9222 # http://localhost:9222 must be not in use on User's machine

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
    app = App()
