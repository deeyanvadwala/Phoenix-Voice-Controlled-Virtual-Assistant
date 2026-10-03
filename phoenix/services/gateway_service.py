"""Gateway: the single entry point the voice client talks to.

POST /command  {"text", "session_id"?} -> {"request_id", "intent", "reply", "error"}
POST /reset    {"session_id"?}         -> clears the LLM conversation

The gateway parses the command, calls the service that owns the action, and sends
the spoken reply to the TTS service. TTS runs in its own process, so speech plays
while the gateway keeps working. For LLM answers the gateway streams tokens from
the LLM service and forwards each finished sentence to TTS right away, so Phoenix
starts talking after the first sentence instead of after the whole answer.
"""
import uuid

import requests
from flask import jsonify, request

from phoenix import intents
from phoenix.services.common import ServiceClient, create_app, run
from phoenix.speech import SentenceChunker

APP_LABELS = {"calculator": "Calculator", "notepad": "Notepad", "cmd": "Command Prompt", "explorer": "File Explorer"}
SITE_LABELS = {"google": "Google", "youtube": "YouTube", "chatgpt": "ChatGPT", "mail": "your mail"}


def default_clients():
    return {name: ServiceClient(name) for name in ("llm", "web", "system", "tts")}


class Pipeline:
    def __init__(self, clients):
        self.llm = clients["llm"]
        self.web = clients["web"]
        self.system = clients["system"]
        self.tts = clients["tts"]

    def speak(self, text, request_id):
        self.tts.post("/speak", {"text": text, "request_id": request_id})

    def say(self, text, request_id):
        self.speak(text, request_id)
        return text

    def chat(self, message, session_id, request_id):
        chunker = SentenceChunker()
        reply = []
        stream = self.llm.stream("/chat/stream", {"session_id": session_id, "message": message}, timeout=300)
        for token in stream:
            reply.append(token)
            for sentence in chunker.feed(token):
                self.speak(sentence, request_id)
        for sentence in chunker.flush():
            self.speak(sentence, request_id)
        return "".join(reply).strip()

    def handle(self, intent, session_id, request_id):
        args = intent.args
        if intent.name == "reply":
            return self.say(args["text"], request_id)
        if intent.name == "terminate":
            return self.say("Shutting down.", request_id)
        if intent.name == "sleep":
            return self.say("Going to sleep.", request_id)
        if intent.name == "time":
            return self.say(f"The time is {self.system.get('/time')['time']}.", request_id)
        if intent.name == "weather":
            params = {"city": args["city"]} if args.get("city") else {}
            data = self.web.get("/weather", **params)
            return self.say(f"It is currently {data['conditions']} in {data['city'].title()}.", request_id)
        if intent.name == "volume":
            reply = self.say(f"Turning the volume {args['direction']}.", request_id)
            self.system.post("/volume", {"direction": args["direction"]})
            return reply
        if intent.name == "open_app":
            reply = self.say(f"Opening {APP_LABELS[args['app']]}.", request_id)
            self.system.post("/open", {"app": args["app"]})
            return reply
        if intent.name == "open_site":
            reply = self.say(f"Opening {SITE_LABELS[args['site']]}.", request_id)
            self.web.post("/open", {"site": args["site"]})
            return reply
        if intent.name == "search":
            engine = "YouTube" if args["engine"] == "youtube" else "Google"
            reply = self.say(f"Here is what I found on {engine}.", request_id)
            self.web.post("/search", args)
            return reply
        return self.chat(args["message"], session_id, request_id)


def create_gateway_app(clients=None):
    app = create_app("gateway")
    pipeline = Pipeline(clients or default_clients())

    @app.post("/command")
    def command():
        body = request.get_json(force=True)
        session_id = body.get("session_id", "default")
        request_id = uuid.uuid4().hex
        intent = intents.parse(body["text"])
        error = None
        try:
            reply = pipeline.handle(intent, session_id, request_id)
        except requests.RequestException as exc:
            error = str(exc)
            reply = "Sorry, something went wrong while handling that."
            app.logger.error("command %r failed: %s", body["text"], exc)
            try:
                pipeline.speak(reply, request_id)
            except requests.RequestException:
                pass
        try:
            pipeline.tts.post("/finish", {"request_id": request_id})
        except requests.RequestException:
            pass
        return jsonify(request_id=request_id, intent=intent.name, reply=reply, error=error)

    @app.post("/reset")
    def reset():
        session_id = (request.get_json(silent=True) or {}).get("session_id", "default")
        pipeline.llm.post("/reset", {"session_id": session_id})
        return jsonify(status="ok")

    return app


if __name__ == "__main__":
    run(create_gateway_app(), "gateway")
