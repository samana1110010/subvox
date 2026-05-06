import os
import time
import platform

# Detect OS
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# ---------------- LINUX SETUP (UNCHANGED) ----------------
if IS_LINUX:
    os.environ["YDOTOOL_SOCKET"] = "/run/user/1000/.ydotool_socket"

# ---------------- WINDOWS SETUP ----------------
if IS_WINDOWS:
    import pyautogui
    import pygetwindow as gw

# ---------------- FUNCTIONS ----------------

def up():
    time.sleep(2)
    if IS_LINUX:
        os.system("wtype -k Prior")
    elif IS_WINDOWS:
        pyautogui.press("pageup")

def down():
    time.sleep(2)
    if IS_LINUX:
        os.system("wtype -k Next")
    elif IS_WINDOWS:
        pyautogui.press("pagedown")

def left():
    if IS_LINUX:
        os.system("ydotool mousemove -- -100 0")
    elif IS_WINDOWS:
        x, y = pyautogui.position()
        pyautogui.moveTo(x - 100, y)

def right():
    if IS_LINUX:
        os.system("ydotool mousemove -- 100 0")
    elif IS_WINDOWS:
        x, y = pyautogui.position()
        pyautogui.moveTo(x + 100, y)

def select():
    time.sleep(2)
    if IS_LINUX:
        os.system("echo 'click left' | dotool")
    elif IS_WINDOWS:
        pyautogui.click()

# ---------------- WINDOW FOCUS ----------------

def focus_app(name):
    if IS_LINUX:
        os.system(f"wmctrl -a {name}")
    elif IS_WINDOWS:
        try:
            windows = gw.getWindowsWithTitle(name)
            if windows:
                windows[0].activate()
        except Exception:
            pass

# Focus Spotify
focus_app("Spotify")

# Focus Chrome/Brave
focus_app("Brave")

# ---------------- MAIN LOOP ----------------

if __name__ == "__main__":
    while True:
        command = input("Enter command (up/down/left/right/select): ")
        if command == "up":
            up()
        elif command == "down":
            down()
        elif command == "left":
            left()
        elif command == "right":
            right()
        elif command == "select":
            select()