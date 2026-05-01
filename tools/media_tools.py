import subprocess
import os
import time

def music():
    subprocess.Popen(["/usr/bin/spotify"])
    time.sleep(5)  # give spotify time to open
    os.system("playerctl play")

if __name__ == "__main__":
    music()