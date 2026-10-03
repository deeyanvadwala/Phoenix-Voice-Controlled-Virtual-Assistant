"""Voice client: wake word, speech recognition, and the conversation loop.

It turns speech into text and sends it to the gateway. All actions and speech
output are handled by the services.
"""
import datetime
import uuid

import requests
import speech_recognition as sr

from phoenix import config
from phoenix.services.common import ServiceClient


class VoiceClient:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.gateway = ServiceClient("gateway", timeout=300)
        self.tts = ServiceClient("tts", timeout=300)
        self.session_id = uuid.uuid4().hex

    def say(self, text):
        request_id = uuid.uuid4().hex
        self.tts.post("/speak", {"text": text, "request_id": request_id})
        self.tts.post("/finish", {"request_id": request_id})
        self.tts.get(f"/wait/{request_id}")

    def greet(self):
        hour = datetime.datetime.now().hour
        part = "Morning" if hour < 12 else "Afternoon" if hour < 18 else "Evening"
        self.say(f"Good {part}, {config.USER_NAME}. My name is Phoenix, I am your virtual assistant. How can I help you?")

    def listen(self, source):
        print("Listening...")
        audio = self.recognizer.listen(source)
        try:
            text = self.recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            return None
        print(f"You said: {text}")
        return text

    def run(self):
        awake = False
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Say '{config.WAKE_WORD}' to wake me up.")
            while True:
                try:
                    text = self.listen(source)
                except sr.RequestError as exc:
                    print(f"Speech recognition unavailable: {exc}")
                    continue
                if not awake:
                    if text and config.WAKE_WORD in text:
                        awake = True
                        self.greet()
                    continue
                if not text:
                    self.say("Sorry, I didn't get that.")
                    continue
                result = self.send(text)
                if result is None:
                    continue
                if result["intent"] == "terminate":
                    return
                if result["intent"] == "sleep":
                    awake = False

    def send(self, text):
        """Send one command to the gateway and wait until the reply has been spoken."""
        try:
            result = self.gateway.post("/command", {"text": text, "session_id": self.session_id})
            self.tts.get(f"/wait/{result['request_id']}")
        except requests.RequestException as exc:
            print(f"Gateway error: {exc}")
            return None
        print(f"Phoenix: {result['reply']}")
        return result

    def run_text(self, lines):
        """Typed commands instead of the microphone, e.g. for testing without audio input."""
        for line in lines:
            text = line.strip()
            if not text:
                continue
            print(f"You: {text}")
            result = self.send(text)
            if result and result["intent"] == "terminate":
                return


def main():
    VoiceClient().run()


if __name__ == "__main__":
    main()
