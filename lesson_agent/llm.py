
from __future__ import annotations

from .config import Settings


class LLMError(RuntimeError):
    pass


class BaseLLM:
    name = "base"

    def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> str:
        raise NotImplementedError


class AnthropicLLM(BaseLLM):
    name = "anthropic"

    def __init__(self, model: str):
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.model = model

    def complete(self, system, user, temperature=0.0, max_tokens=4000):
        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        r = self.client.messages.create(**kwargs)

        return "".join(
            b.text for b in r.content
            if getattr(b, "type", "") == "text"
        )


class OpenAILLM(BaseLLM):
    name = "openai"

    def __init__(self, model: str):
        import openai

        self._openai = openai
        self.client = openai.OpenAI()
        self.model = model

    def complete(self, system, user, temperature=0.0, max_tokens=4000):
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
        )

        try:
            r = self.client.chat.completions.create(
                temperature=temperature, **kwargs
            )
        except self._openai.BadRequestError as e:
            if "temperature" in str(e).lower():
                r = self.client.chat.completions.create(**kwargs)
            else:
                raise

        return r.choices[0].message.content or ""


class OllamaLLM(BaseLLM):
    name = "ollama"

    def __init__(self, model: str):
        from langchain_ollama import ChatOllama

        self.model = model
        self.client = ChatOllama(
            model=self.model,
            temperature=0.0,
        )

    def complete(self, system, user, temperature=0.0, max_tokens=4000):
        from langchain_core.messages import SystemMessage, HumanMessage

        self.client.temperature = temperature
        self.client.num_predict = max_tokens

        response = self.client.invoke([
            SystemMessage(content=system),
            HumanMessage(content=user),
        ])

        content = response.content

        if isinstance(content, str):
            return content

        return str(content)


def get_llm(settings: Settings, role: str) -> BaseLLM:
    """
    role: generator | evaluator | evolver.

    The evaluator can use a different model from the generator.
    """

    if settings.provider == "mock":
        from .mock import MockLLM

        return MockLLM(
            role=role,
            mode=settings.mock_mode
        )

    model = (
        settings.evaluator_model
        if role == "evaluator"
        else settings.generator_model
    )

    if settings.provider == "anthropic":
        return AnthropicLLM(model)

    if settings.provider == "openai":
        return OpenAILLM(model)

    if settings.provider == "ollama":
        return OllamaLLM(model)

    raise LLMError(f"Unknown provider: {settings.provider}")
