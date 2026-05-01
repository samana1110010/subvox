
import subprocess
import time

def stream():
    subprocess.Popen(["brave", "--new-window", "https://www.youtube.com"])
    time.sleep(3)

if __name__ == "__main__":
    stream()