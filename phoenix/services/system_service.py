"""System service: launches local apps, controls volume and reports the time.

POST /open    {"app"}
POST /volume  {"direction": "up" | "down"}
GET  /time    -> {"time"}
"""
from flask import jsonify, request

from phoenix import actions
from phoenix.services.common import create_app, run


def create_system_app():
    app = create_app("system")

    @app.post("/open")
    def open_app():
        name = request.get_json(force=True)["app"]
        if name not in actions.APP_COMMANDS:
            return jsonify(error=f"unknown app {name!r}"), 400
        actions.open_app(name)
        return jsonify(status="ok")

    @app.post("/volume")
    def volume():
        direction = request.get_json(force=True)["direction"]
        if direction not in ("up", "down"):
            return jsonify(error="direction must be 'up' or 'down'"), 400
        actions.change_volume(direction)
        return jsonify(status="ok")

    @app.get("/time")
    def get_time():
        return jsonify(time=actions.current_time())

    return app


if __name__ == "__main__":
    run(create_system_app(), "system")
