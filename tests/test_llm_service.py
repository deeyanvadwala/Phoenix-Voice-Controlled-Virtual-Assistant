import unittest

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from phoenix.services.llm_service import create_llm_app


def echo_model(prompt_value):
    """Fake LLM that reports which earlier user messages it was given."""
    messages = prompt_value.to_messages()
    earlier = [m.content for m in messages[1:-1] if m.type == "human"]
    return AIMessage(content=f"Q: {messages[-1].content}. Remembered: {earlier}.")


class LlmServiceTests(unittest.TestCase):
    def setUp(self):
        self.client = create_llm_app(model=RunnableLambda(echo_model)).test_client()

    def chat(self, message, session_id="s1"):
        return self.client.post("/chat", json={"session_id": session_id, "message": message}).get_json()["reply"]

    def test_multi_turn_memory(self):
        self.chat("my name is priya")
        reply = self.chat("what is my name")
        self.assertIn("Remembered: ['my name is priya']", reply)

    def test_sessions_are_isolated_and_resettable(self):
        self.chat("first")
        self.assertIn("Remembered: []", self.chat("hello", session_id="other"))
        self.client.post("/reset", json={"session_id": "s1"})
        self.assertIn("Remembered: []", self.chat("again"))

    def test_stream_returns_text_and_updates_history(self):
        response = self.client.post("/chat/stream", json={"session_id": "s2", "message": "hi"})
        self.assertIn("Q: hi.", response.get_data(as_text=True))
        self.assertIn("Remembered: ['hi']", self.chat("next", session_id="s2"))

    def test_history_is_trimmed(self):
        for i in range(30):
            self.chat(f"m{i}")
        history = self.client.application.config["conversations"].history("s1")
        self.assertLessEqual(len(history.messages), history.max_messages)


if __name__ == "__main__":
    unittest.main()
