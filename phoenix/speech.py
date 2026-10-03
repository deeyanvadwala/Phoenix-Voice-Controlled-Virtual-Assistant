"""Text-to-speech worker and sentence chunking for streamed LLM output."""
import queue
import re
import threading
import time
from collections import OrderedDict

from phoenix import config

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
# Very long sentences are split at a comma so speech can start sooner.
MAX_CHUNK_CHARS = 220


class SentenceChunker:
    """Collects streamed tokens and emits complete sentences as soon as they are ready."""

    def __init__(self):
        self._buffer = ""

    def feed(self, token):
        self._buffer += token
        parts = _SENTENCE_END.split(self._buffer)
        self._buffer = parts.pop()
        ready = [p.strip() for p in parts if p.strip()]
        if len(self._buffer) > MAX_CHUNK_CHARS and "," in self._buffer:
            head, self._buffer = self._buffer.rsplit(",", 1)
            ready.append(head.strip() + ",")
        return ready

    def flush(self):
        rest, self._buffer = self._buffer.strip(), ""
        return [rest] if rest else []


def _default_engine_factory():
    import pyttsx3

    try:  # SAPI5 on Windows needs COM initialised on the thread that owns the engine.
        import comtypes

        comtypes.CoInitialize()
    except ImportError:
        pass
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    if voices:
        engine.setProperty("voice", voices[min(config.TTS_VOICE_INDEX, len(voices) - 1)].id)
    engine.setProperty("rate", config.TTS_RATE)
    engine.setProperty("volume", config.TTS_VOLUME)
    return engine


class Speaker:
    """Owns a single TTS engine on a dedicated thread and speaks queued text in order.

    Text is grouped by ``request_id`` so callers can wait for a whole reply and see
    when its first audio started (used for latency measurement).
    """

    MAX_TRACKED_REQUESTS = 200

    def __init__(self, engine_factory=_default_engine_factory):
        self._engine_factory = engine_factory
        self._queue = queue.Queue()
        self._requests = OrderedDict()
        self._lock = threading.Lock()
        self._current = None
        self._ready = threading.Event()
        threading.Thread(target=self._run, name="tts-worker", daemon=True).start()
        self._ready.wait(timeout=30)

    def say(self, text, request_id):
        self._record(request_id)
        self._queue.put(("say", text, request_id))

    def finish(self, request_id):
        """Mark that no more text will be queued for ``request_id``."""
        self._record(request_id)
        self._queue.put(("finish", None, request_id))

    def wait(self, request_id, timeout=120):
        record = self._record(request_id)
        record["done"].wait(timeout)
        return self.status(request_id)

    def status(self, request_id):
        with self._lock:
            record = self._requests.get(request_id)
            if record is None:
                return None
            return {
                "request_id": request_id,
                "first_audio_at": record["first_audio_at"],
                "done_at": record["done_at"],
                "done": record["done"].is_set(),
            }

    def _record(self, request_id):
        with self._lock:
            record = self._requests.get(request_id)
            if record is None:
                record = {"first_audio_at": None, "done_at": None, "done": threading.Event()}
                self._requests[request_id] = record
                while len(self._requests) > self.MAX_TRACKED_REQUESTS:
                    self._requests.popitem(last=False)
            return record

    def _on_start(self, name=None):
        with self._lock:
            record = self._requests.get(self._current)
            if record is not None and record["first_audio_at"] is None:
                record["first_audio_at"] = time.time()

    def _run(self):
        engine = self._engine_factory()
        engine.connect("started-utterance", self._on_start)
        self._ready.set()
        while True:
            kind, text, request_id = self._queue.get()
            if kind == "say":
                self._current = request_id
                engine.say(text)
                engine.runAndWait()
            else:
                record = self._record(request_id)
                with self._lock:
                    record["done_at"] = time.time()
                record["done"].set()
