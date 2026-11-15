"""The real-provider adapters, tested with fake clients (no network, no API key)."""
import httpx
import pytest

anthropic = pytest.importorskip("anthropic")
openai = pytest.importorskip("openai")

from lesson_agent import llm as llm_mod  # noqa: E402


class _Block:
    type = "text"

    def __init__(self, text):
        self.text = text


class _AnthropicMessages:
    def __init__(self, reject_temperature=False):
        self.calls, self.reject = [], reject_temperature

    def create(self, **kw):
        self.calls.append(kw)
        if self.reject and "temperature" in kw:
            req = httpx.Request("POST", "http://x")
            raise anthropic.BadRequestError("temperature is not supported for this model",
                                            response=httpx.Response(400, request=req), body=None)
        return type("R", (), {"content": [_Block("hello "), _Block("world")]})()


def _anthropic_llm(monkeypatch, reject=False):
    msgs = _AnthropicMessages(reject)
    monkeypatch.setattr(anthropic, "Anthropic", lambda: type("C", (), {"messages": msgs})())
    return llm_mod.AnthropicLLM("some-model"), msgs


def test_anthropic_adapter_shapes_the_request(monkeypatch):
    llm, msgs = _anthropic_llm(monkeypatch)
    assert llm.complete("SYS", "USER", temperature=0.7) == "hello world"
    c = msgs.calls[0]
    assert c["system"] == "SYS" and c["messages"] == [{"role": "user", "content": "USER"}]
    assert c["model"] == "some-model" and c["temperature"] == 0.7


def test_anthropic_adapter_retries_without_temperature_if_model_rejects_it(monkeypatch):
    llm, msgs = _anthropic_llm(monkeypatch, reject=True)
    assert llm.complete("S", "U", temperature=0.0) == "hello world"
    assert "temperature" in msgs.calls[0] and "temperature" not in msgs.calls[1]


def test_openai_adapter_shapes_the_request(monkeypatch):
    calls = []

    class Completions:
        def create(self, **kw):
            calls.append(kw)
            msg = type("M", (), {"content": "ok"})()
            return type("R", (), {"choices": [type("Ch", (), {"message": msg})()]})()

    client = type("C", (), {"chat": type("Chat", (), {"completions": Completions()})()})()
    monkeypatch.setattr(openai, "OpenAI", lambda: client)
    out = llm_mod.OpenAILLM("m").complete("SYS", "USER", temperature=0.2)
    assert out == "ok"
    assert calls[0]["messages"][0] == {"role": "system", "content": "SYS"}
    assert calls[0]["messages"][1] == {"role": "user", "content": "USER"}


def test_judge_can_use_a_different_model_than_the_writer(monkeypatch):
    from lesson_agent.config import Settings
    from pathlib import Path

    made = []
    monkeypatch.setattr(llm_mod, "AnthropicLLM", lambda model: made.append(model) or object())
    s = Settings("anthropic", "writer-model", "judge-model", 2, 2, Path("."), Path("."))
    llm_mod.get_llm(s, "generator")
    llm_mod.get_llm(s, "evaluator")
    assert made == ["writer-model", "judge-model"]
