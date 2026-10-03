"""Central configuration. Every value can be overridden with an environment variable."""
import os


def _env(name, default):
    return os.environ.get(name, default)


HOST = _env("PHOENIX_HOST", "127.0.0.1")

# One port per microservice.
PORTS = {
    "gateway": int(_env("PHOENIX_GATEWAY_PORT", "5000")),
    "llm": int(_env("PHOENIX_LLM_PORT", "5001")),
    "web": int(_env("PHOENIX_WEB_PORT", "5002")),
    "system": int(_env("PHOENIX_SYSTEM_PORT", "5003")),
    "tts": int(_env("PHOENIX_TTS_PORT", "5004")),
}


def service_url(name):
    return f"http://{HOST}:{PORTS[name]}"


# LLM
LLM_MODEL = _env("PHOENIX_LLM_MODEL", "llama3")
LLM_TEMPERATURE = float(_env("PHOENIX_LLM_TEMPERATURE", "0"))
LLM_SEED = int(_env("PHOENIX_LLM_SEED", "42"))
LLM_KEEP_ALIVE = _env("PHOENIX_LLM_KEEP_ALIVE", "30m")
# Number of past messages (user + assistant) kept per conversation.
LLM_HISTORY_MESSAGES = int(_env("PHOENIX_LLM_HISTORY_MESSAGES", "20"))
SYSTEM_PROMPT = _env(
    "PHOENIX_SYSTEM_PROMPT",
    "You are Phoenix, a helpful voice assistant. Your answers are spoken aloud, "
    "so reply in plain sentences without markdown, lists or code blocks.",
)

# Speech
USER_NAME = _env("PHOENIX_USER_NAME", "Deeyan")
WAKE_WORD = _env("PHOENIX_WAKE_WORD", "phoenix")
TTS_RATE = int(_env("PHOENIX_TTS_RATE", "150"))
TTS_VOLUME = float(_env("PHOENIX_TTS_VOLUME", "1.0"))
TTS_VOICE_INDEX = int(_env("PHOENIX_TTS_VOICE_INDEX", "0"))

# Web
WEATHER_CITY = _env("PHOENIX_WEATHER_CITY", "Ahmedabad")
WEATHER_CACHE_SECONDS = int(_env("PHOENIX_WEATHER_CACHE_SECONDS", "600"))
HTTP_TIMEOUT = float(_env("PHOENIX_HTTP_TIMEOUT", "10"))
