
from datetime import datetime
import subprocess
import time
import pyautogui

from langchain_core.tools import tool


# ----------------------- APPLICATIONS -----------------------

APPLICATIONS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
}


# ----------------------- DATE AND TIME -----------------------

@tool
def get_current_datetime() -> str:
    """Get the current local date and time."""
    return datetime.now().astimezone().strftime(
        "%A, %B %d, %Y at %I:%M:%S %p %Z"
    )


# ----------------------- OPEN APPLICATION -----------------------

@tool
def open_application(app_name: str) -> str:
    """Open Notepad, Calculator, or Paint."""
    name = app_name.strip().lower()
    app = APPLICATIONS.get(name)

    if not app:
        return "Supported applications: Notepad, Calculator, Paint."

    try:
        subprocess.Popen([app])
        return f"Opened {name} successfully."
    except OSError as error:
        return f"Could not open {name}: {error}"


# ----------------------- CLOSE APPLICATION -----------------------

@tool
def close_application(app_name: str) -> str:
    """Close Notepad, Calculator, or Paint."""
    name = app_name.strip().lower()

    process_names = {
        "notepad": "notepad.exe",
        "calculator": "Calculator.exe",
        "paint": "mspaint.exe",
    }

    process = process_names.get(name)

    if not process:
        return "Supported applications: Notepad, Calculator, Paint."

    try:
        result = subprocess.run(
            ["taskkill", "/IM", process, "/T"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            return f"Closed {name}."
        return f"Could not close {name}. It may not be running."

    except (OSError, subprocess.TimeoutExpired) as error:
        return f"Could not close {name}: {error}"


# ----------------------- WRITE IN NOTEPAD -----------------------


@tool
def write_in_notepad(text: str) -> str:
    """Write text in the existing Notepad window, opening it only if needed."""
    if not text.strip():
        return "Please provide text to write."

    try:
        # Reuse an existing Notepad window if one is available.
        windows = pyautogui.getWindowsWithTitle("Notepad")

        if windows:
            window = windows[0]
            if window.isMinimized:
                window.restore()
            window.activate()
            time.sleep(0.5)
        else:
            subprocess.Popen(["notepad.exe"])
            time.sleep(2)

            windows = pyautogui.getWindowsWithTitle("Notepad")
            if windows:
                windows[0].activate()
                time.sleep(0.5)

        pyautogui.write(text, interval=0.02)
        return "I typed the requested text in Notepad."

    except Exception as error:
        return f"Could not write in Notepad: {error}"


# ----------------------- REGISTER TOOLS -----------------------

tools = [
    get_current_datetime,
    open_application,
    close_application,
    write_in_notepad,
]
