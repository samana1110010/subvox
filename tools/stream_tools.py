import subprocess
import time
import platform

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

def stream():
    if IS_LINUX:
        # KEEPING THIS SAME (as you asked)
        subprocess.Popen(["brave", "--new-window", "https://www.youtube.com"])
        time.sleep(3)

    elif IS_WINDOWS:
        # Open YouTube in Chrome
        subprocess.Popen(
            ["start", "chrome", "https://www.youtube.com"],
            shell=True
        )
        time.sleep(3)

if __name__ == "__main__":
    stream()
