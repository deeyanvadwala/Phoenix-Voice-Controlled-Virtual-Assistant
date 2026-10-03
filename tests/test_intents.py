import unittest

from phoenix.intents import parse


class ParseTests(unittest.TestCase):
    def check(self, text, name, **args):
        intent = parse(text)
        self.assertEqual(intent.name, name, text)
        for key, value in args.items():
            self.assertEqual(intent.args.get(key), value, text)

    def test_apps_and_sites(self):
        self.check("open calculator", "open_app", app="calculator")
        self.check("Phoenix, open command prompt", "open_app", app="cmd")
        self.check("open youtube", "open_site", site="youtube")
        self.check("open my mail", "open_site", site="mail")

    def test_search(self):
        self.check("search google for python decorators", "search", engine="google", query="python decorators")
        self.check("youtube lofi music", "search", engine="youtube", query="lofi music")
        self.check("play despacito on youtube", "search", engine="youtube", query="despacito")

    def test_questions_mentioning_keywords_go_to_the_llm(self):
        # The original keyword matching sent these to search / the clock by mistake.
        self.check("who founded google", "chat")
        self.check("how much time does it take to boil an egg", "chat")
        self.check("explain how weather forecasting models work in detail", "chat")

    def test_utilities(self):
        self.check("what time is it", "time")
        self.check("weather", "weather", city=None)
        self.check("what's the weather in boston", "weather", city="boston")
        self.check("volume up", "volume", direction="up")
        self.check("turn the volume down", "volume", direction="down")

    def test_control_and_small_talk(self):
        self.check("terminate", "terminate")
        self.check("go to sleep", "sleep")
        self.check("how are you", "reply")

    def test_everything_else_is_chat(self):
        self.check("tell me a joke", "chat", message="tell me a joke")


if __name__ == "__main__":
    unittest.main()
