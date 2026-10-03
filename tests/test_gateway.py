import unittest

import requests

from phoenix.services.gateway_service import create_gateway_app
from phoenix.services.web_service import WeatherCache


class FakeClient:
    def __init__(self, responses=None, tokens=None, fail=False):
        self.calls = []
        self.responses = responses or {}
        self.tokens = tokens or []
        self.fail = fail

    def _call(self, method, path, payload):
        self.calls.append((method, path, payload))
        if self.fail:
            raise requests.ConnectionError("service down")
        return self.responses.get(path, {"status": "ok"})

    def get(self, path, timeout=None, **params):
        return self._call("GET", path, params)

    def post(self, path, payload=None, timeout=None):
        return self._call("POST", path, payload)

    def stream(self, path, payload, timeout=None):
        self.calls.append(("STREAM", path, payload))
        for token in self.tokens:
            yield token


class GatewayTests(unittest.TestCase):
    def make(self, **overrides):
        self.clients = {
            "llm": FakeClient(tokens=["The sky ", "is blue. ", "It scatters ", "light."]),
            "web": FakeClient(responses={"/weather": {"city": "boston", "conditions": "Sunny, 20°C"}}),
            "system": FakeClient(responses={"/time": {"time": "3:15 PM"}}),
            "tts": FakeClient(),
        }
        self.clients.update(overrides)
        return create_gateway_app(self.clients).test_client()

    def spoken(self):
        return [c[2]["text"] for c in self.clients["tts"].calls if c[1] == "/speak"]

    def test_llm_answer_is_spoken_sentence_by_sentence(self):
        body = self.make().post("/command", json={"text": "why is the sky blue", "session_id": "s"}).get_json()
        self.assertEqual(body["intent"], "chat")
        self.assertEqual(body["reply"], "The sky is blue. It scatters light.")
        self.assertEqual(self.spoken(), ["The sky is blue.", "It scatters light."])
        self.assertEqual(self.clients["tts"].calls[-1][1], "/finish")
        self.assertEqual(self.clients["llm"].calls[0][2], {"session_id": "s", "message": "why is the sky blue"})

    def test_first_sentence_is_sent_to_tts_before_generation_finishes(self):
        tts = FakeClient()
        order = []
        llm = FakeClient()

        def stream(path, payload, timeout=None):
            for token in ["One. ", "Two. ", "Three."]:
                order.append(("token", token))
                yield token

        llm.stream = stream
        original_post = tts.post
        tts.post = lambda path, payload=None, timeout=None: (order.append(("tts", path)), original_post(path, payload))[1]
        self.make(llm=llm, tts=tts).post("/command", json={"text": "count"})
        self.assertLess(order.index(("tts", "/speak")), order.index(("token", "Three.")))

    def test_actions_are_routed_to_the_right_service(self):
        client = self.make()
        client.post("/command", json={"text": "open calculator"})
        client.post("/command", json={"text": "search google for flask"})
        self.assertIn(("POST", "/open", {"app": "calculator"}), self.clients["system"].calls)
        self.assertIn(("POST", "/search", {"engine": "google", "query": "flask"}), self.clients["web"].calls)

    def test_time_and_weather(self):
        client = self.make()
        self.assertEqual(client.post("/command", json={"text": "what time is it"}).get_json()["reply"], "The time is 3:15 PM.")
        reply = client.post("/command", json={"text": "weather in boston"}).get_json()["reply"]
        self.assertEqual(reply, "It is currently Sunny, 20°C in Boston.")

    def test_service_failure_is_reported_and_spoken(self):
        body = self.make(system=FakeClient(fail=True)).post("/command", json={"text": "what time is it"}).get_json()
        self.assertIn("service down", body["error"])
        self.assertTrue(self.spoken()[0].startswith("Sorry"))


class WeatherCacheTests(unittest.TestCase):
    def test_caches_per_city(self):
        calls = []
        cache = WeatherCache(fetch=lambda city: calls.append(city) or "Clear", ttl=60)
        self.assertEqual(cache.get("Boston"), ("Clear", False))
        self.assertEqual(cache.get("boston"), ("Clear", True))
        self.assertEqual(calls, ["Boston"])


if __name__ == "__main__":
    unittest.main()
