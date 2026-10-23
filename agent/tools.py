
from datetime import datetime
import ctypes
import json
import os
import subprocess
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import pyautogui
from langchain_core.tools import tool


# ----------------------- APPLICATIONS -----------------------

APPLICATIONS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
}


# ----------------------- WINDOWS HELPERS -----------------------

def _find_window(title_keyword):
    """Return visible Windows whose title contains the keyword."""
    user32 = ctypes.windll.user32
    found = []
    callback_type = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
    )

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value

        if title_keyword.casefold() in title.casefold():
            found.append((hwnd, title))

        return True

    user32.EnumWindows(callback_type(callback), 0)
    return found


def _activate_window(hwnd):
    """Restore and focus a Windows window."""
    user32 = ctypes.windll.user32
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.8)



def _get_foreground_window_title():
    """Return the title of the currently active Windows window."""
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()

    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""

    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _focus_whatsapp():
    """Focus a visible WhatsApp Desktop window, not Chrome."""
    user32 = ctypes.windll.user32
    matches = []

    for hwnd, title in _find_window("WhatsApp"):
        class_buffer = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buffer, 256)
        class_name = class_buffer.value

        # Exclude Chrome browser windows.
        if "Chrome" in class_name or "Chrome" in title:
            continue

        matches.append((hwnd, title))

    if not matches:
        return False, "WhatsApp Desktop window was not found."

    _activate_window(matches[0][0])
    return True, f"Focused WhatsApp Desktop window: {matches[0][1]}"


def _chrome_path():
    """Find the installed Chrome executable."""
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Google/Chrome/Application/chrome.exe",
    ]

    return next((p for p in candidates if p.is_file()), None)


def _get_chrome_profiles():
    """Read local Chrome profile names and account names."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return []

    local_state = (
        Path(local_app_data) / "Google/Chrome/User Data/Local State"
    )

    if not local_state.is_file():
        return []

    try:
        data = json.loads(local_state.read_text(encoding="utf-8"))
        cache = data.get("profile", {}).get("info_cache", {})
        results = []

        for directory, info in cache.items():
            results.append({
                "directory": directory,
                "profile_name": info.get("name", directory),
                "account_name": (
                    info.get("gaia_name")
                    or info.get("user_name")
                    or info.get("name")
                    or directory
                ),
                "email": info.get("user_name", ""),
            })

        return results
    except (OSError, json.JSONDecodeError):
        return []


def _match_chrome_profile(profile_name):
    profiles = _get_chrome_profiles()
    target = profile_name.strip().casefold()

    matches = [
        p for p in profiles
        if target in {
            p["profile_name"].casefold(),
            p["account_name"].casefold(),
            p["email"].casefold(),
            p["directory"].casefold(),
        }
    ]

    return matches


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
    app = APPLICATIONS.get(app_name.strip().lower())
    if not app:
        return "Supported applications: Notepad, Calculator, Paint."

    try:
        subprocess.Popen([app])
        return f"Opened {app_name}."
    except OSError as exc:
        return f"Could not open {app_name}: {exc}"


# ----------------------- CLOSE APPLICATION -----------------------

@tool
def close_application(app_name: str) -> str:
    """Close Notepad, Calculator, or Paint."""
    name = app_name.strip().lower()
    process_names = {
        "notepad": ["notepad.exe"],
        "calculator": ["Calculator.exe", "CalculatorApp.exe"],
        "paint": ["mspaint.exe"],
    }

    if name not in process_names:
        return "Supported applications: Notepad, Calculator, Paint."

    errors = []
    for process in process_names[name]:
        try:
            result = subprocess.run(
                ["taskkill", "/IM", process, "/T", "/F"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                return f"Closed {name}."
            errors.append((result.stderr or result.stdout).strip())
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(str(exc))

    return f"Could not confirm closing {name}: {'; '.join(errors)}"


# ----------------------- WRITE IN NOTEPAD -----------------------

@tool
def write_in_notepad(text: str) -> str:
    """Write text in Notepad, opening it if necessary."""
    if not text.strip():
        return "Please provide text to write."

    try:
        windows = pyautogui.getWindowsWithTitle("Notepad")
        if windows:
            window = windows[0]
            if window.isMinimized:
                window.restore()
            window.activate()
        else:
            subprocess.Popen(["notepad.exe"])
            time.sleep(2)
            windows = pyautogui.getWindowsWithTitle("Notepad")
            if not windows:
                return "Could not find the Notepad window."
            windows[0].activate()

        time.sleep(0.5)
        pyautogui.write(text, interval=0.02)
        return "Typed the text in Notepad."
    except Exception as exc:
        return f"Could not write in Notepad: {exc}"


# ----------------------- CHROME PROFILES -----------------------

@tool
def list_chrome_profiles() -> str:
    """List Chrome profiles so the user can select one."""
    profiles = _get_chrome_profiles()
    if not profiles:
        return "No Chrome profiles were found."

    lines = ["Available Chrome profiles:"]
    for i, p in enumerate(profiles, start=1):
        lines.append(
            f'{i}. {p["account_name"]} | {p["email"] or "No email shown"} '
            f'| directory: {p["directory"]}'
        )

    return "\n".join(lines)


@tool
def search_in_chrome(
    query: str, profile_name: str, platform: str = "google"
) -> str:
    """Search Google or YouTube using a specifically selected Chrome profile."""
    if not query.strip():
        return "Please provide a search query."

    platform = platform.strip().lower()
    if platform not in ("google", "youtube"):
        return "Platform must be Google or YouTube."

    matches = _match_chrome_profile(profile_name)
    if len(matches) != 1:
        return "Chrome profile is missing or ambiguous. List profiles and ask the user to select one."

    executable = _chrome_path()
    if not executable:
        return "Chrome executable was not found."

    if platform == "youtube":
        url = "https://www.youtube.com/results?search_query=" + quote_plus(query)
    else:
        url = "https://www.google.com/search?q=" + quote_plus(query)

    try:
        subprocess.Popen([
            str(executable),
            f'--profile-directory={matches[0]["directory"]}',
            url,
        ])
        return f"Opened {platform.title()} search for '{query}'."
    except OSError as exc:
        return f"Could not start Chrome: {exc}"


@tool
def open_website(url: str, profile_name: str) -> str:
    """Open an HTTP or HTTPS website in the selected Chrome profile."""
    if "://" not in url:
        url = "https://" + url.strip()

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return "Please provide a valid HTTP or HTTPS URL."

    matches = _match_chrome_profile(profile_name)
    if len(matches) != 1:
        return "Chrome profile is missing or ambiguous. Ask the user to select one."

    executable = _chrome_path()
    if not executable:
        return "Chrome executable was not found."

    try:
        subprocess.Popen([
            str(executable),
            f'--profile-directory={matches[0]["directory"]}',
            url,
        ])
        return f"Opened {url} in the selected Chrome profile."
    except OSError as exc:
        return f"Could not open website: {exc}"


# ----------------------- WHATSAPP DESKTOP -----------------------

@tool
def open_whatsapp(use_web: bool = False) -> str:
    """Open WhatsApp Desktop by default. Use web only if requested."""
    try:
        if use_web:
            webbrowser.open("https://web.whatsapp.com/")
            return "Opened WhatsApp Web."

        os.startfile("whatsapp:")
        time.sleep(2)
        focused, result = _focus_whatsapp()
        return result if focused else (
            "Requested WhatsApp Desktop to open. Its window was not detected; "
            "open it manually and try again."
        )
    except Exception as exc:
        return f"Could not open WhatsApp Desktop: {type(exc).__name__}: {exc}"



@tool
def read_whatsapp_visible_text() -> str:
    """Read text exposed by the WhatsApp Desktop Windows accessibility interface.
    Use this to inspect visible chat names, previews, and messages.
    """
    try:
        from pywinauto import Desktop

        windows = Desktop(backend="uia").windows()
        whatsapp_windows = [
            window for window in windows
            if "whatsapp" in window.window_text().casefold()
            and window.is_visible()
        ]

        if not whatsapp_windows:
            return (
                "WhatsApp Desktop was not found. Open the desktop app "
                "and try again."
            )

        window = whatsapp_windows[0]
        lines = []

        for control in window.descendants():
            try:
                text = control.window_text().strip()
                if text and text not in lines:
                    lines.append(text)
            except Exception:
                continue

        if not lines:
            return (
                "WhatsApp was detected, but Windows did not expose readable "
                "text. We may need a screenshot/OCR fallback."
            )

        return (
            "Text exposed by the WhatsApp Desktop accessibility interface "
            "(this may be incomplete):\n"
            + "\n".join(lines[:150])
        )

    except Exception as exc:
        return (
            "Could not read WhatsApp accessibility text: "
            f"{type(exc).__name__}: {exc}"
        )



@tool
def search_whatsapp_contact(contact_name: str) -> str:
    """Search WhatsApp Desktop and attempt to open the matching contact chat."""
    if not contact_name.strip():
        return "Please provide a contact name."

    focused, result = _focus_whatsapp()
    if not focused:
        return result + " Use open_whatsapp first."

    try:
        pyautogui.hotkey("ctrl", "f")
        time.sleep(1)

        pyautogui.hotkey("ctrl", "a")
        pyautogui.write(contact_name.strip(), interval=0.08)
        time.sleep(2)

        # Attempt to open the highlighted search result.
        pyautogui.press("down")
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(1.5)

        title = _get_foreground_window_title()

        if "whatsapp" not in title.casefold():
            return (
                "Could not verify that WhatsApp Desktop is active after "
                "the search. No further action was taken."
            )

        return (
            f"Selected a WhatsApp search result for '{contact_name}'. "
            f"Current window title: '{title}'. Check that this is the "
            "correct contact before preparing a message."
        )

    except Exception as exc:
        return f"WhatsApp contact search failed: {type(exc).__name__}: {exc}"



@tool
def prepare_whatsapp_message(message: str) -> str:
    """Type a draft into WhatsApp Desktop without sending it."""
    if not message.strip():
        return "The message is empty."

    focused, result = _focus_whatsapp()
    if not focused:
        return result

    try:
        title = _get_foreground_window_title()

        if "whatsapp" not in title.casefold():
            return "WhatsApp Desktop is not the active window. No text was typed."

        # Type only; never press Enter in this tool.
        pyautogui.write(message, interval=0.03)
        return (
            "Typed the message into the active WhatsApp Desktop window. "
            "It was not sent. Verify the recipient and draft before sending."
        )

    except Exception as exc:
        return f"Could not type the message: {type(exc).__name__}: {exc}"




@tool
def send_whatsapp_message() -> str:
    """Send a prepared WhatsApp message after an explicit user request."""
    focused, result = _focus_whatsapp()
    if not focused:
        return result

    try:
        title = _get_foreground_window_title()

        if "whatsapp" not in title.casefold():
            return "WhatsApp Desktop is not active. Nothing was sent."

        # Only call this tool when the user explicitly asks to send.
        pyautogui.press("enter")
        time.sleep(1)

        return (
            "Pressed Enter in WhatsApp Desktop. "
            "Verify that the message appears as sent in the chat."
        )

    except Exception as exc:
        return f"Could not attempt to send the message: {type(exc).__name__}: {exc}"



@tool
def open_whatsapp_status() -> str:
    """Focus WhatsApp Desktop and explain if Status needs manual navigation."""
    focused, result = _focus_whatsapp()
    if not focused:
        return result

    return (
        "WhatsApp Desktop is now focused. Status/Updates navigation differs "
        "by app version, and this tool will not click an unverified location. "
        "Select Status or Updates in the WhatsApp window."
    )


@tool
def close_whatsapp() -> str:
    """Close WhatsApp Desktop only when it can be identified and focused."""
    focused, result = _focus_whatsapp()
    if not focused:
        return result

    try:
        pyautogui.hotkey("alt", "f4")
        time.sleep(1)
        return "Sent the close-window shortcut to WhatsApp Desktop."
    except Exception as exc:
        return f"Could not close WhatsApp: {type(exc).__name__}: {exc}"


# ----------------------- CLOSE CHROME TAB / WINDOW -----------------------

@tool
def close_current_chrome_tab() -> str:
    """Close the current Chrome tab only if a Chrome window is focused."""
    windows = _find_window("Chrome")
    if not windows:
        return "No Chrome window was detected. No tab was closed."

    try:
        _activate_window(windows[0][0])
        pyautogui.hotkey("ctrl", "w")
        return "Sent Ctrl+W to the focused Chrome window."
    except Exception as exc:
        return f"Could not close Chrome tab: {type(exc).__name__}: {exc}"


@tool
def close_chrome() -> str:
    """Close the focused Chrome window gracefully."""
    windows = _find_window("Chrome")
    if not windows:
        return "No Chrome window was detected."

    try:
        _activate_window(windows[0][0])
        pyautogui.hotkey("alt", "f4")
        return "Sent Alt+F4 to the focused Chrome window."
    except Exception as exc:
        return f"Could not close Chrome: {type(exc).__name__}: {exc}"


# ----------------------- REGISTER TOOLS -----------------------

tools = [
    get_current_datetime,
    open_application,
    close_application,
    write_in_notepad,
    list_chrome_profiles,
    search_in_chrome,
    open_website,
    open_whatsapp,
    search_whatsapp_contact,
    prepare_whatsapp_message,
    open_whatsapp_status,
    close_whatsapp,
    close_current_chrome_tab,
    close_chrome,
    send_whatsapp_message,
    read_whatsapp_visible_text,
]
