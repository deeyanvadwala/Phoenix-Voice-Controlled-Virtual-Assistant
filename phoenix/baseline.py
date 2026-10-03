"""Single-process baseline that mirrors the original Phoenix.py design.

Used only by benchmark.py to measure what the microservice architecture changed.
It keeps the original behaviour: everything runs sequentially in one process,
``Speak`` initialises the TTS engine on every call, the LLM answer is generated
in full before any of it is spoken, and the weather is fetched on every request.
Model, prompt and actions are shared with the services so only the architecture differs.
"""
import time

from langchain_core.prompts import ChatPromptTemplate

from phoenix import actions, config, intents
from phoenix.services.gateway_service import APP_LABELS, SITE_LABELS
from phoenix.services.llm_service import build_model


class Baseline:
    def __init__(self, model=None):
        prompt = ChatPromptTemplate.from_messages([("system", config.SYSTEM_PROMPT), ("human", "{question}")])
        self.chain = prompt | (model or build_model())

    def speak(self, text, timing):
        import pyttsx3

        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[min(config.TTS_VOICE_INDEX, len(voices) - 1)].id)
        engine.setProperty("rate", config.TTS_RATE)
        engine.setProperty("volume", config.TTS_VOLUME)
        token = engine.connect("started-utterance", lambda name=None: timing.setdefault("first_audio_at", time.time()))
        engine.say(text)
        engine.runAndWait()
        engine.disconnect(token)

    def handle(self, text):
        """Run one command end to end. Returns the reply and its timestamps."""
        timing = {}
        intent = intents.parse(text)
        args = intent.args
        if intent.name == "reply":
            reply = args["text"]
        elif intent.name == "time":
            reply = f"The time is {actions.current_time()}."
        elif intent.name == "weather":
            city = args.get("city") or config.WEATHER_CITY
            reply = f"It is currently {actions.fetch_weather(city)} in {city.title()}."
        elif intent.name == "open_app":
            reply = f"Opening {APP_LABELS[args['app']]}."
            self.speak(reply, timing)
            actions.open_app(args["app"])
            reply = None
        elif intent.name == "open_site":
            reply = f"Opening {SITE_LABELS[args['site']]}."
            self.speak(reply, timing)
            actions.open_site(args["site"])
            reply = None
        elif intent.name == "chat":
            reply = self.chain.invoke({"question": args["message"]}).content.strip()
        else:
            reply = intent.name
        if reply:
            self.speak(reply, timing)
        timing["done_at"] = time.time()
        return timing
