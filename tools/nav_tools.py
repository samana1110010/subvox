import os
import subprocess
import time

os.environ["YDOTOOL_SOCKET"] = "/run/user/1000/.ydotool_socket"

def up():
    time.sleep(2)
    os.system("wtype -k Prior")

def down():
    time.sleep(2)
    os.system("wtype -k Next")
    
def left():
    os.system("ydotool mousemove -- -100 0")

def right():
    os.system("ydotool mousemove -- 100 0")

def select():
    time.sleep(2)
    os.system("echo 'click left' | dotool")

# Focus Spotify
os.system("wmctrl -a Spotify")

# Focus Chrome/Brave
os.system("wmctrl -a Brave")

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