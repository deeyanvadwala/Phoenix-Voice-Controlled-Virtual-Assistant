"""LLM service: multi-turn conversation with LLaMA 3 through LangChain + Ollama.

POST /chat          {"session_id", "message"} -> {"reply"}
POST /chat/stream   {"session_id", "message"} -> streamed plain-text tokens
POST /reset         {"session_id"}            -> clears that conversation
"""
import threading

from flask import Response, jsonify, request, stream_with_context
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from phoenix import config
from phoenix.services.common import create_app, run


def build_model():
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        seed=config.LLM_SEED,
        keep_alive=config.LLM_KEEP_ALIVE,
    )


class TrimmedHistory(InMemoryChatMessageHistory):
    """Chat history that only keeps the most recent messages to bound prompt size."""

    max_messages: int = config.LLM_HISTORY_MESSAGES

    def add_messages(self, messages):
        super().add_messages(messages)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]


class Conversations:
    def __init__(self, model):
        self._histories = {}
        self._lock = threading.Lock()
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", config.SYSTEM_PROMPT),
                MessagesPlaceholder("history"),
                ("human", "{question}"),
            ]
        )
        self.base_chain = prompt | model
        self.chain = RunnableWithMessageHistory(
            self.base_chain,
            self.history,
            input_messages_key="question",
            history_messages_key="history",
        )

    def history(self, session_id):
        with self._lock:
            if session_id not in self._histories:
                self._histories[session_id] = TrimmedHistory()
            return self._histories[session_id]

    def reset(self, session_id):
        with self._lock:
            self._histories.pop(session_id, None)

    def _run_config(self, session_id):
        return {"configurable": {"session_id": session_id}}

    def ask(self, session_id, message):
        return self.chain.invoke({"question": message}, config=self._run_config(session_id)).content

    def stream(self, session_id, message):
        for chunk in self.chain.stream({"question": message}, config=self._run_config(session_id)):
            if chunk.content:
                yield chunk.content


def create_llm_app(model=None):
    app = create_app("llm")
    conversations = Conversations(model or build_model())
    app.config["conversations"] = conversations

    def _args():
        body = request.get_json(force=True)
        return body.get("session_id", "default"), body["message"]

    @app.post("/chat")
    def chat():
        session_id, message = _args()
        return jsonify(reply=conversations.ask(session_id, message))

    @app.post("/chat/stream")
    def chat_stream():
        session_id, message = _args()
        tokens = conversations.stream(session_id, message)
        return Response(stream_with_context(tokens), mimetype="text/plain; charset=utf-8")

    @app.post("/reset")
    def reset():
        conversations.reset(request.get_json(force=True).get("session_id", "default"))
        return jsonify(status="ok")

    return app


def warm_up(app):
    """Load the model into Ollama's memory so the first real question is not slow."""
    try:
        app.config["conversations"].base_chain.invoke({"question": "Hi", "history": []})
    except Exception as exc:  # The service still starts; the first request will just be slower.
        print(f"[llm] warm-up failed: {exc}")


if __name__ == "__main__":
    llm_app = create_llm_app()
    warm_up(llm_app)
    run(llm_app, "llm")
