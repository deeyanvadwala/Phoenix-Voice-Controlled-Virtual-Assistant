"""Web service: opens sites, runs searches and fetches the weather.

POST /open     {"site"}
POST /search   {"engine", "query"}
GET  /weather  ?city=   -> {"city", "conditions", "cached"}
"""
import threading
import time

from flask import jsonify, request

from phoenix import actions, config
from phoenix.services.common import create_app, run


class WeatherCache:
    def __init__(self, fetch=actions.fetch_weather, ttl=config.WEATHER_CACHE_SECONDS):
        self._fetch = fetch
        self._ttl = ttl
        self._entries = {}
        self._lock = threading.Lock()

    def get(self, city):
        key = city.lower()
        with self._lock:
            entry = self._entries.get(key)
            if entry and time.monotonic() - entry[0] < self._ttl:
                return entry[1], True
        conditions = self._fetch(city)
        with self._lock:
            self._entries[key] = (time.monotonic(), conditions)
        return conditions, False


def create_web_app(weather_cache=None):
    app = create_app("web")
    weather = weather_cache or WeatherCache()

    @app.post("/open")
    def open_site():
        site = request.get_json(force=True)["site"]
        if site not in actions.SITE_URLS:
            return jsonify(error=f"unknown site {site!r}"), 400
        actions.open_site(site)
        return jsonify(status="ok")

    @app.post("/search")
    def search():
        body = request.get_json(force=True)
        if body["engine"] not in actions.SEARCH_URLS:
            return jsonify(error=f"unknown engine {body['engine']!r}"), 400
        actions.search(body["engine"], body["query"])
        return jsonify(status="ok")

    @app.get("/weather")
    def get_weather():
        city = request.args.get("city") or config.WEATHER_CITY
        try:
            conditions, cached = weather.get(city)
        except Exception as exc:
            return jsonify(error=f"weather lookup failed: {exc}"), 502
        return jsonify(city=city, conditions=conditions, cached=cached)

    return app


if __name__ == "__main__":
    run(create_web_app(), "web")
