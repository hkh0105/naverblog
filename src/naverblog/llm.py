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

DEFAULT_MODEL_NAME = "GPT-5.5"
DEFAULT_MODEL_ENV = "NAVERBLOG_DEFAULT_MODEL"
PROVIDER_ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def resolve_model(name: str) -> str:
    """표시 이름을 LiteLLM 모델 문자열로 변환."""
    if "/" in name or name in MODEL_REGISTRY.values():
        return name
    if name in MODEL_REGISTRY:
        return MODEL_REGISTRY[name]
    raise ValueError(f"알 수 없는 모델: '{name}'. 사용 가능: {list(MODEL_REGISTRY.keys())}")


def get_model_provider(name: str) -> str:
    """모델 이름에 필요한 provider를 반환."""
    model_id = resolve_model(name)
    if model_id.startswith("claude-") or model_id.startswith("anthropic/"):
        return "anthropic"
    if model_id.startswith("gemini/"):
        return "gemini"
    if model_id.startswith("gpt-") or model_id.startswith("openai/"):
        return "openai"
    return "openai"


def get_required_env_var(name: str) -> str:
    """모델 호출에 필요한 환경변수 이름."""
    provider = get_model_provider(name)
    return PROVIDER_ENV_VARS[provider]


def has_required_api_key(name: str) -> bool:
    """선택한 모델의 API 키가 설정되어 있는지 확인."""
    return bool(os.environ.get(get_required_env_var(name)))


def format_missing_api_key_message(name: str) -> str:
    """사용자에게 보여줄 API 키 누락 안내."""
    env_var = get_required_env_var(name)
    provider = get_model_provider(name)
    provider_label = {
        "anthropic": "Anthropic",
        "openai": "OpenAI",
        "gemini": "Google Gemini",
    }.get(provider, provider)
    return (
        f"{name} 모델을 사용하려면 {provider_label} API 키가 필요합니다. "
        f"Streamlit Cloud의 App settings > Secrets에 `{env_var}`를 등록한 뒤 앱을 재부팅해주세요."
    )


def format_llm_exception_message(name: str, exc: Exception) -> str:
    """Provider 오류를 사용자 친화적인 메시지로 변환."""
    message = str(exc)
    provider = get_model_provider(name)

    if provider == "openai" and "You exceeded your current quota" in message:
        return (
            "OpenAI API 키는 인식됐지만 현재 quota/크레딧/프로젝트 예산이 부족합니다. "
            "OpenAI Platform의 Billing, Usage, Limits에서 결제수단·크레딧·프로젝트 월 예산을 확인해주세요. "
            "해결 전에는 AI 모델을 `Claude Opus 4.8`로 바꿔 생성할 수 있습니다."
        )

    if provider == "openai" and "RateLimitError" in message:
        return (
            "OpenAI 요청 한도에 걸렸습니다. 잠시 후 다시 시도하거나 OpenAI Platform의 프로젝트 rate limit/budget을 확인해주세요. "
            "급하면 `Claude Opus 4.8`로 바꿔 생성하세요."
        )

    if provider == "openai" and "temperature" in message and "Only the default" in message:
        return (
            "이 OpenAI 모델은 temperature 기본값만 지원합니다. "
            "앱 호출 설정을 다시 확인한 뒤 재시도해주세요."
        )

    if "Missing credentials" in message:
        return format_missing_api_key_message(name)

    return f"{name} 호출에 실패했습니다: {message}"


def get_default_model_name() -> str:
    """앱 기본 모델을 반환.

    NAVERBLOG_DEFAULT_MODEL에 유효한 모델명을 지정하면 앱 기본값을 덮어쓸 수 있습니다.
    """
    explicit = os.environ.get(DEFAULT_MODEL_ENV, "").strip()
    if explicit in MODEL_REGISTRY:
        return explicit

    return DEFAULT_MODEL_NAME


def _should_omit_sampling_params(model_id: str) -> bool:
    """일부 최신 모델은 비기본 sampling parameter를 거부합니다."""
    return model_id.startswith(("claude-opus-4-8", "gpt-5"))


def generate(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4000,
) -> str:
    """LLM을 호출하여 텍스트를 생성."""
    model_id = resolve_model(model)
    if not has_required_api_key(model):
        raise RuntimeError(format_missing_api_key_message(model))

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

    try:
        response = completion(**kwargs)
    except Exception as exc:
        raise RuntimeError(format_llm_exception_message(model, exc)) from exc
    return response.choices[0].message.content


def list_model_names() -> list[str]:
    """사용 가능한 모델의 표시 이름 목록 반환."""
    return list(MODEL_REGISTRY.keys())
