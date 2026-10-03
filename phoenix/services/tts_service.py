"""TTS service: speaks text in order on one long-lived engine.

POST /speak            {"text", "request_id"}  -> queued, returns immediately
POST /finish           {"request_id"}          -> marks the end of a reply
GET  /wait/<request_id>?timeout=  -> blocks until that reply has been spoken
GET  /status/<request_id>         -> timing info without blocking
"""
from flask import jsonify, request

from phoenix.services.common import create_app, run
from phoenix.speech import Speaker


def create_tts_app(speaker=None):
    app = create_app("tts")
    speaker = speaker or Speaker()

    @app.post("/speak")
    def speak():
        body = request.get_json(force=True)
        speaker.say(body["text"], body["request_id"])
        return jsonify(status="queued")

    @app.post("/finish")
    def finish():
        speaker.finish(request.get_json(force=True)["request_id"])
        return jsonify(status="ok")

    @app.get("/wait/<request_id>")
    def wait(request_id):
        return jsonify(speaker.wait(request_id, timeout=float(request.args.get("timeout", 120))))

    @app.get("/status/<request_id>")
    def status(request_id):
        result = speaker.status(request_id)
        if result is None:
            return jsonify(error="unknown request_id"), 404
        return jsonify(result)

    return app


if __name__ == "__main__":
    run(create_tts_app(), "tts")
