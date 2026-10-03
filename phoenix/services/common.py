"""Helpers shared by all Phoenix microservices."""
import logging

import requests
from flask import Flask, jsonify

from phoenix import config


def create_app(name):
    app = Flask(name)

    @app.get("/health")
    def health():
        return jsonify(service=name, status="ok")

    return app


def run(app, name):
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    # threaded=True lets a service handle several requests at once (e.g. a TTS
    # /speak call while a /wait call is blocked) and streams responses unbuffered.
    app.run(host=config.HOST, port=config.PORTS[name], threaded=True, use_reloader=False)


class ServiceClient:
    """Thin JSON client for one service. Reuses a keep-alive HTTP connection."""

    def __init__(self, name, base_url=None, timeout=config.HTTP_TIMEOUT):
        self.name = name
        self.base_url = base_url or config.service_url(name)
        self.timeout = timeout
        self._session = requests.Session()

    def get(self, path, timeout=None, **params):
        response = self._session.get(self.base_url + path, params=params, timeout=timeout or self.timeout)
        response.raise_for_status()
        return response.json()

    def post(self, path, payload=None, timeout=None):
        response = self._session.post(self.base_url + path, json=payload or {}, timeout=timeout or self.timeout)
        response.raise_for_status()
        return response.json()

    def stream(self, path, payload, timeout=None):
        """POST and yield the response body as text chunks while it arrives."""
        with self._session.post(
            self.base_url + path, json=payload, stream=True, timeout=timeout or self.timeout
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    yield chunk
