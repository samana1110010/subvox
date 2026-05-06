
import os
import platform
import shutil
import subprocess
import sys


PROJECT_NAME = "SubVox"


def run(command, check=False):
    print(f"\n> {command}")
    try:
        subprocess.run(command, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")


def command_exists(command):
    return shutil.which(command) is not None


def install_python_requirements():
    print("\nInstalling Python requirements...")

    if not os.path.exists("requirements.txt"):
        print("requirements.txt not found. Skipping Python package install.")
        return

    run(f"{sys.executable} -m pip install -r requirements.txt")


def install_playwright():
    print("\nInstalling Playwright browser files...")
    run(f"{sys.executable} -m playwright install chromium")


def setup_ollama_for_windows():
    print("\nSetting up Ollama model for Windows...")

    if not command_exists("ollama"):
        print("Ollama is not installed or not added to PATH.")
        print("Install Ollama first, then run this setup again.")
        print("After installing Ollama, run: ollama pull tinyllama")
        return

    run("ollama pull tinyllama")


def setup_ollama_for_linux():
    print("\nSetting up Ollama model for Linux...")

    if not command_exists("ollama"):
        print("Ollama is not installed.")
        print("Install Ollama first, then run this setup again.")
        print("After installing Ollama, run: ollama pull qwen2.5:7b")
        return

    run("ollama pull qwen2.5:7b")


def setup_windows():
    print("\nDetected Windows setup.")

    print("\nWindows requirements:")
    print("- Google Chrome should be installed.")
    print("- Ollama should be installed and running.")
    print("- This setup will pull TinyLlama for lighter Windows usage.")

    setup_ollama_for_windows()


def setup_linux():
    print("\nDetected Linux setup.")

    print("\nInstalling common Linux system packages if available...")

    if command_exists("pacman"):
        run("sudo pacman -S --needed wmctrl playerctl")
    elif command_exists("apt"):
        run("sudo apt update")
        run("sudo apt install -y wmctrl playerctl")
    else:
        print("Could not detect pacman or apt.")
        print("Please install these manually if needed:")
        print("- wmctrl")
        print("- playerctl")

    print("\nExtra Linux navigation tools used by this project:")
    print("- wtype")
    print("- ydotool")
    print("- dotool")
    print("\nOn Arch, you may need:")
    print("yay -S wtype ydotool dotool")

    setup_ollama_for_linux()


def main():
    print("=" * 50)
    print(f"{PROJECT_NAME} Setup")
    print("=" * 50)

    os_name = platform.system()
    print(f"Detected OS: {os_name}")

    install_python_requirements()
    install_playwright()

    if os_name == "Windows":
        setup_windows()
    elif os_name == "Linux":
        setup_linux()
    else:
        print(f"\nUnsupported or untested OS: {os_name}")
        print("You may need to install dependencies manually.")

    print("\nSetup completed.")
    print("\nRun the project with:")
    print("python main.py")


if __name__ == "__main__":
    main()