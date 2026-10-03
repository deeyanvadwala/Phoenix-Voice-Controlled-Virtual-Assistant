"""System and web automation actions. The services expose these over HTTP; the
single-process baseline calls them directly."""
import datetime
import re
import subprocess
import time
import urllib.parse
import webbrowser

import requests

from phoenix import config

APP_COMMANDS = {
    "calculator": [r"C:\Windows\System32\calc.exe"],
    "notepad": [r"C:\Windows\System32\notepad.exe"],
    "cmd": ["cmd.exe", "/c", "start", "cmd.exe"],
    "explorer": ["explorer.exe"],
}

SITE_URLS = {
    "google": "https://www.google.com/",
    "youtube": "https://www.youtube.com/",
    "chatgpt": "https://chatgpt.com/",
    "mail": "https://mail.google.com/",
}

SEARCH_URLS = {
    "google": "https://www.google.com/search?q={}",
    "youtube": "https://www.youtube.com/results?search_query={}",
}


def current_time():
    return datetime.datetime.now().strftime("%I:%M %p").lstrip("0")


def open_app(app):
    subprocess.Popen(APP_COMMANDS[app])


def open_site(site):
    webbrowser.open_new_tab(SITE_URLS[site])


def search(engine, query):
    webbrowser.open_new_tab(SEARCH_URLS[engine].format(urllib.parse.quote_plus(query)))


def change_volume(direction, steps=5):
    from pynput.keyboard import Controller, Key

    keyboard = Controller()
    key = Key.media_volume_up if direction == "up" else Key.media_volume_down
    for _ in range(steps):
        keyboard.press(key)
        keyboard.release(key)
        time.sleep(0.05)


def fetch_weather(city):
    """Current conditions from wttr.in, e.g. 'Sunny, 31°C'."""
    response = requests.get(
        f"https://wttr.in/{urllib.parse.quote(city)}",
        params={"format": "%C, %t", "m": ""},
        timeout=config.HTTP_TIMEOUT,
    )
    response.raise_for_status()
    response.encoding = "utf-8"  # wttr.in omits the charset, so requests would guess Latin-1.
    return re.sub(r"\s+,", ",", response.text.strip()).replace("+", "")
