
import subprocess
import platform
import time
import os

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

def music():
    if IS_LINUX:
        subprocess.Popen(["/usr/bin/spotify"])
        time.sleep(5)  # give spotify time to open
        os.system("playerctl play")

    elif IS_WINDOWS:
        # Open Spotify Liked Songs
        subprocess.Popen(
            ["start", "spotify:collection:tracks"],
            shell=True
        )

        # Wait for app to load
        time.sleep(5)

        # Send play command (media key)
        import pyautogui
        pyautogui.press("playpause")

if __name__ == "__main__":
    music()
