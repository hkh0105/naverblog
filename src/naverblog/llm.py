"""LiteLLM 기반 Multi-LLM 추상화."""

from __future__ import annotations

import os

from litellm import completion

MODEL_REGISTRY: dict[str, str] = {
    "Claude Opus 4.8": "claude-opus-4-8",
    "Claude Opus 4.6": "claude-opus-4-6",
    "Claude Opus 4.5": "claude-opus-4-20250514",
    "Claude Sonnet": "claude-sonnet-4-20250514",
    "Claude Haiku": "claude-haiku-4-20250414",
    "GPT-5.5": "gpt-5.5",
    "GPT-4o": "gpt-4o",
    "GPT-4o Mini": "gpt-4o-mini",
    "Gemini Pro": "gemini/gemini-2.5-pro",
    "Gemini Flash": "gemini/gemini-2.5-flash",
}

DEFAULT_MODEL_NAME = "Claude Opus 4.8"
VERIFIED_GPT55_MODEL_NAME = "GPT-5.5"
GPT55_VERIFIED_ENV = "NAVERBLOG_GPT55_VERIFIED"
DEFAULT_MODEL_ENV = "NAVERBLOG_DEFAULT_MODEL"


def resolve_model(name: str) -> str:
    """표시 이름을 LiteLLM 모델 문자열로 변환."""
    if "/" in name or name in MODEL_REGISTRY.values():
        return name
    if name in MODEL_REGISTRY:
        return MODEL_REGISTRY[name]
    raise ValueError(f"알 수 없는 모델: '{name}'. 사용 가능: {list(MODEL_REGISTRY.keys())}")


def get_default_model_name() -> str:
    """앱 기본 모델을 반환.

    GPT-5.5는 실제 호출 검증 후 NAVERBLOG_GPT55_VERIFIED=1일 때만 기본값으로 사용합니다.
    """
    explicit = os.environ.get(DEFAULT_MODEL_ENV, "").strip()
    if explicit in MODEL_REGISTRY:
        return explicit

    gpt55_verified = os.environ.get(GPT55_VERIFIED_ENV, "").strip().lower()
    if gpt55_verified in {"1", "true", "yes", "y", "on"}:
        return VERIFIED_GPT55_MODEL_NAME

    return DEFAULT_MODEL_NAME


def _should_omit_sampling_params(model_id: str) -> bool:
    """일부 Claude 모델은 비기본 sampling parameter를 거부합니다."""
    return model_id.startswith("claude-opus-4-8")


def generate(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4000,
) -> str:
    """LLM을 호출하여 텍스트를 생성."""
    model_id = resolve_model(model)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    kwargs = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if not _should_omit_sampling_params(model_id):
        kwargs["temperature"] = temperature

    response = completion(**kwargs)
    return response.choices[0].message.content


def list_model_names() -> list[str]:
    """사용 가능한 모델의 표시 이름 목록 반환."""
    return list(MODEL_REGISTRY.keys())
