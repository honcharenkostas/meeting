import sys
import os
import shutil


class App:
    def __init__(self):
        chrome_path = self.find_chrome_executable()
        print(chrome_path)
        
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
