import time

from tools.stream_tools import stream
from tools.media_tools import music
from tools.social import social
from tools.nav_tools import up, down, left, right, select, focus_app

# ---------------- COMMAND REGISTRY ---------------- #

COMMANDS = {
    # navigation
    "up": up,
    "down": down,
    "left": left,
    "right": right,
    "select": select,

    # app workflows
    "social": social,      # WhatsApp workflow
    "stream": stream,      # YouTube
    "music": music,        # Spotify

    # aliases
    "spotify": music,
    "youtube": stream,
    "whatsapp": social,
}


# ---------------- COMMAND HANDLER ---------------- #

def execute_command(command: str):
    command = command.strip().lower()

    if command in ["exit", "quit", "q"]:
        print("Exiting SubVox controller...")
        return False

    if command in ["help", "commands"]:
        show_commands()
        return True

    if command.startswith("focus "):
        app_name = command.replace("focus ", "").strip()
        if app_name:
            print(f"Focusing {app_name}...")
            focus_app(app_name)
        else:
            print("Usage: focus <app name>")
        return True

    action = COMMANDS.get(command)

    if action is None:
        print(f"Unknown command: {command}")
        print("Type 'help' to see available commands.")
        return True

    print(f"Executing command: {command}")

    try:
        action()
    except Exception as e:
        print(f"Error while executing '{command}': {e}")

    return True


def show_commands():
    print("\nAvailable commands:")
    print("  up")
    print("  down")
    print("  left")
    print("  right")
    print("  select")
    print("  social / whatsapp")
    print("  stream / youtube")
    print("  music / spotify")
    print("  focus <app name>")
    print("  help")
    print("  exit\n")


# ---------------- MAIN LOOP ---------------- #

def main():
    print("SubVox Automation Controller Started")
    print("SubVox Automation Controller Started")
    show_commands()

    running = True

    while running:
        command = input("Enter command: ")
        running = execute_command(command)
        time.sleep(0.2)


if __name__ == "__main__":
    main()