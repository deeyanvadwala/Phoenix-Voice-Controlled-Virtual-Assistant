import unittest

from phoenix.speech import SentenceChunker, Speaker


class SentenceChunkerTests(unittest.TestCase):
    def test_emits_sentences_as_soon_as_they_end(self):
        chunker = SentenceChunker()
        out = []
        for token in ["Hel", "lo there", ". How", " are", " you? I am", " fine"]:
            out.append(chunker.feed(token))
        self.assertEqual(out, [[], [], ["Hello there."], [], ["How are you?"], []])
        self.assertEqual(chunker.flush(), ["I am fine"])

    def test_splits_very_long_sentences_at_a_comma(self):
        chunker = SentenceChunker()
        ready = chunker.feed("word " * 50 + ", and more")
        self.assertEqual(len(ready), 1)
        self.assertTrue(ready[0].endswith(","))


class FakeEngine:
    def __init__(self):
        self.spoken = []
        self._callbacks = []
        self._pending = []

    def connect(self, topic, callback):
        self._callbacks.append(callback)

    def say(self, text):
        self._pending.append(text)

    def runAndWait(self):
        for text in self._pending:
            for callback in self._callbacks:
                callback(name=None)
            self.spoken.append(text)
        self._pending = []


class SpeakerTests(unittest.TestCase):
    def test_speaks_in_order_and_reports_timing(self):
        engine = FakeEngine()
        speaker = Speaker(engine_factory=lambda: engine)
        speaker.say("one", "r1")
        speaker.say("two", "r1")
        speaker.finish("r1")
        status = speaker.wait("r1", timeout=5)
        self.assertTrue(status["done"])
        self.assertEqual(engine.spoken, ["one", "two"])
        self.assertLessEqual(status["first_audio_at"], status["done_at"])

    def test_unknown_request(self):
        speaker = Speaker(engine_factory=FakeEngine)
        self.assertIsNone(speaker.status("missing"))


if __name__ == "__main__":
    unittest.main()
