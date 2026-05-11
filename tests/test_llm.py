import json
from http.client import RemoteDisconnected
from types import SimpleNamespace

from podcast_pipeline.llm import MiniMaxChatLLM, build_llm_client


def test_build_llm_client_uses_minimax_provider_by_default(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    config = SimpleNamespace(
        llm_provider="minimax",
        llm_model="MiniMax-M2.7",
        llm_api_key_env="MINIMAX_API_KEY",
        llm_base_url="https://api.minimaxi.com/v1",
        openai_api_key_env="OPENAI_API_KEY",
        text_model="gpt-5.5",
    )

    llm = build_llm_client(config)

    assert isinstance(llm, MiniMaxChatLLM)
    assert llm.model == "MiniMax-M2.7"
    assert llm.base_url == "https://api.minimaxi.com/v1"


def test_minimax_generate_json_posts_chat_completion(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "{\"ok\": true}"}}]}).encode("utf-8")

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("podcast_pipeline.llm.request.urlopen", fake_urlopen)
    llm = MiniMaxChatLLM("MiniMax-M2.7", "test-key", "https://api.minimaxi.com/v1")

    result = llm.generate_json("system", "user")

    assert result == {"ok": True}
    assert captured["url"] == "https://api.minimaxi.com/v1/chat/completions"
    assert captured["body"]["model"] == "MiniMax-M2.7"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert captured["headers"]["Authorization"] == "Bearer test-key"


def test_minimax_generate_json_ignores_thinking_prefix(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            content = '<think>The model reasons before answering.</think>\n\n{"ok": true}'
            return json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")

    monkeypatch.setattr("podcast_pipeline.llm.request.urlopen", lambda request, timeout: FakeResponse())
    llm = MiniMaxChatLLM("MiniMax-M2.7", "test-key", "https://api.minimaxi.com/v1")

    assert llm.generate_json("system", "user") == {"ok": True}


def test_minimax_generate_json_retries_remote_disconnect(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "{\"ok\": true}"}}]}).encode("utf-8")

    attempts = {"count": 0}

    def flaky_urlopen(request, timeout):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RemoteDisconnected("closed")
        return FakeResponse()

    monkeypatch.setattr("podcast_pipeline.llm.request.urlopen", flaky_urlopen)
    monkeypatch.setattr("podcast_pipeline.llm.time.sleep", lambda seconds: None)
    llm = MiniMaxChatLLM("MiniMax-M2.7", "test-key", "https://api.minimaxi.com/v1")

    assert llm.generate_json("system", "user") == {"ok": True}
    assert attempts["count"] == 2
