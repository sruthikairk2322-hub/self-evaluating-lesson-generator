
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Load .env variables. Existing environment variables take priority."""
    f = ROOT / ".env"
    if not f.exists():
        return

    for line in f.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue

        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")

        if v and k not in os.environ:
            os.environ[k] = v


_load_dotenv()

DEFAULT_MODELS = {
    "anthropic": ("claude-sonnet-5-5", "claude-opus-5-5"),
    "openai": ("gpt-4o", "gpt-4o"),
    "ollama": ("llama3.2", "llama3.2"),
    "mock": ("mock", "mock"),
}


def detect_provider() -> str:
    p = os.getenv("LLM_PROVIDER", "").strip().lower()

    if p:
        return p

    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"

    if os.getenv("OPENAI_API_KEY"):
        return "openai"

    return "mock"


@dataclass
class Settings:
    provider: str
    generator_model: str
    evaluator_model: str
    max_retries: int
    evolve_threshold: int
    memory_dir: Path
    output_dir: Path
    mock_mode: str = "improve"


def load_settings(
    provider: str | None = None,
    memory_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    max_retries: int | None = None,
    mock_mode: str | None = None,
) -> Settings:

    provider = (provider or detect_provider()).lower()

    if provider not in DEFAULT_MODELS:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            "Use anthropic, openai, ollama or mock."
        )

    gen_default, eval_default = DEFAULT_MODELS[provider]

    retries = (
        max_retries
        if max_retries is not None
        else int(os.getenv("MAX_RETRIES", "2"))
    )

    retries = max(1, min(2, retries))

    return Settings(
        provider=provider,
        generator_model=(
            os.getenv("GENERATOR_MODEL", gen_default)
            if provider != "mock"
            else "mock"
        ),
        evaluator_model=(
            os.getenv("EVALUATOR_MODEL", eval_default)
            if provider != "mock"
            else "mock"
        ),
        max_retries=retries,
        evolve_threshold=int(os.getenv("EVOLVE_THRESHOLD", "2")),
        memory_dir=Path(memory_dir) if memory_dir else ROOT / "memory",
        output_dir=Path(output_dir) if output_dir else ROOT / "outputs",
        mock_mode=mock_mode or os.getenv("MOCK_MODE", "improve"),
    )
