"""LiteLLM 기반 Multi-LLM 추상화."""

from __future__ import annotations

from litellm import completion

MODEL_REGISTRY: dict[str, str] = {
    "Claude Sonnet": "claude-sonnet-4-20250514",
    "Claude Haiku": "claude-haiku-4-20250414",
    "GPT-4o": "gpt-4o",
    "GPT-4o Mini": "gpt-4o-mini",
    "Gemini Pro": "gemini/gemini-2.5-pro",
    "Gemini Flash": "gemini/gemini-2.5-flash",
}


def resolve_model(name: str) -> str:
    """표시 이름을 LiteLLM 모델 문자열로 변환."""
    if "/" in name or name in MODEL_REGISTRY.values():
        return name
    if name in MODEL_REGISTRY:
        return MODEL_REGISTRY[name]
    raise ValueError(f"알 수 없는 모델: '{name}'. 사용 가능: {list(MODEL_REGISTRY.keys())}")


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
    response = completion(
        model=model_id,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def list_model_names() -> list[str]:
    """사용 가능한 모델의 표시 이름 목록 반환."""
    return list(MODEL_REGISTRY.keys())
