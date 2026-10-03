"""Rule-based intent parser that maps a spoken command to an action.

Anything that does not match a rule becomes a ``chat`` intent and goes to the LLM.
"""
import re
from dataclasses import dataclass, field

# Phrase -> app name understood by the system service.
APPS = {
    "calculator": "calculator",
    "notepad": "notepad",
    "command prompt": "cmd",
    "cmd": "cmd",
    "source file": "explorer",
    "file explorer": "explorer",
}

# Phrase -> site name understood by the web service.
SITES = {
    "google": "google",
    "youtube": "youtube",
    "chatgpt": "chatgpt",
    "chat gpt": "chatgpt",
    "my mail": "mail",
    "gmail": "mail",
}

SMALL_TALK = {
    "how are you": "I'm fine, thank you.",
    "i am fine": "That's great. How can I help you today?",
    "i'm fine": "That's great. How can I help you today?",
    "thank you": "You're welcome.",
}


@dataclass
class Intent:
    name: str
    args: dict = field(default_factory=dict)


def _strip_wake_word(command):
    return re.sub(r"\bphoenix\b[,\s]*", "", command).strip()


def parse(command):
    text = _strip_wake_word(command.lower().strip())

    if text in ("terminate", "shut down", "shutdown", "exit", "quit"):
        return Intent("terminate")
    if text in ("sleep", "go to sleep"):
        return Intent("sleep")

    for phrase, reply in SMALL_TALK.items():
        if text.startswith(phrase):
            return Intent("reply", {"text": reply})

    if re.search(r"\bwhat(?:'s| is) the time\b|\bwhat time is it\b|^time$", text):
        return Intent("time")

    if re.search(r"\bweather\b", text) and len(text.split()) <= 6:
        match = re.search(r"\bweather (?:in|for|at) ([a-z .'-]+)$", text)
        return Intent("weather", {"city": match.group(1).strip() if match else None})

    match = re.match(r"^(?:volume|turn (?:the )?volume) (up|down)$", text)
    if match:
        return Intent("volume", {"direction": match.group(1)})

    match = re.match(r"^open (.+)$", text)
    if match:
        target = match.group(1).strip()
        if target in APPS:
            return Intent("open_app", {"app": APPS[target]})
        if target in SITES:
            return Intent("open_site", {"site": SITES[target]})

    # "search google for X", "google X", "search X on youtube", "play X on youtube"
    match = re.match(r"^(?:search )?(google|youtube)(?: for)? (.+)$", text) or re.match(
        r"^(?:search|play|find) (.+?) on (google|youtube)$", text
    )
    if match:
        groups = match.groups()
        engine, query = (groups[0], groups[1]) if groups[0] in ("google", "youtube") else (groups[1], groups[0])
        return Intent("search", {"engine": engine, "query": query.strip()})

    return Intent("chat", {"message": text})
