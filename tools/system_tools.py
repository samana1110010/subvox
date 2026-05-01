
import subprocess

def update():
    subprocess.Popen(["pkexec", "pacman", "-Syu", "--noconfirm"])
    print("update successful")

if __name__ == "__main__":
    update()