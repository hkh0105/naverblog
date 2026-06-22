"""블로그 글에 맞는 이미지 생성 (OpenAI GPT Image / Google Imagen)."""

from __future__ import annotations

import base64
import io
import os
from dataclasses import dataclass


IMAGE_MODEL_REGISTRY: dict[str, str] = {
    "GPT Image 2 (덕테이프)": "openai/gpt-image-2",
    "GPT Image 2": "openai/gpt-image-2",
    "GPT Image 1.5": "openai/gpt-image-1.5",
    "GPT Image 1 Mini": "openai/gpt-image-1-mini",
    "Imagen 3": "imagen-3.0-generate-002",
    "Imagen 4": "imagen-4.0-generate-001",
    "Gemini Flash Image": "gemini-2.5-flash-image",
}


def _is_openai_image_model(model: str) -> bool:
    return model.startswith("openai/") or model.startswith("gpt-image-")


def _openai_image_model_id(model: str) -> str:
    return model.removeprefix("openai/")


def get_image_provider(model: str) -> str:
    """이미지 모델 ID에 필요한 provider를 반환."""
    return "openai" if _is_openai_image_model(model) else "google"


def get_required_image_env_var(model: str) -> str:
    """이미지 모델 호출에 필요한 대표 환경변수 이름."""
    return "OPENAI_API_KEY" if get_image_provider(model) == "openai" else "GEMINI_API_KEY"


def has_image_api_key(model: str = "openai/gpt-image-2") -> bool:
    """이미지 생성용 API 키가 있는지 확인."""
    if get_image_provider(model) == "openai":
        return bool(os.environ.get("OPENAI_API_KEY"))
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def format_missing_image_api_key_message(model: str = "openai/gpt-image-2") -> str:
    """이미지 생성 키 누락 안내."""
    if get_image_provider(model) == "openai":
        return (
            "AI 이미지 생성은 기본적으로 OpenAI GPT Image 2를 사용합니다. "
            "Streamlit Cloud의 App settings > Secrets에 `OPENAI_API_KEY`를 등록한 뒤 앱을 재부팅해주세요."
        )
    return (
        "선택한 Google 이미지 모델은 `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY`가 필요합니다. "
        "Streamlit Cloud의 App settings > Secrets에 키를 등록한 뒤 앱을 재부팅해주세요."
    )


def format_image_exception_message(model: str, exc: Exception) -> str:
    """이미지 생성 오류를 사용자 친화적으로 변환."""
    message = str(exc)
    if get_image_provider(model) == "openai" and "You exceeded your current quota" in message:
        return (
            "OpenAI 이미지 생성 키는 인식됐지만 quota/크레딧/프로젝트 예산이 부족합니다. "
            "OpenAI Platform의 Billing, Usage, Limits를 확인하거나 이미지 모델을 Google Imagen/Gemini로 바꿔주세요."
        )
    if get_image_provider(model) == "openai" and "RateLimitError" in message:
        return (
            "OpenAI 이미지 생성 요청 한도에 걸렸습니다. 잠시 후 다시 시도하거나 OpenAI Platform의 rate limit/budget을 확인해주세요."
        )
    if "Missing credentials" in message:
        return format_missing_image_api_key_message(model)
    return f"이미지 생성 실패: {message}"


@dataclass
class GeneratedImage:
    """생성된 이미지."""

    data: bytes  # PNG 바이트
    prompt: str  # 생성에 사용된 프롬프트

    @property
    def base64(self) -> str:
        return base64.b64encode(self.data).decode()


def _build_image_prompts(topic: str, num_images: int = 3) -> list[str]:
    """블로그 주제에서 이미지 프롬프트를 생성."""
    prompts = []
    shared_style = (
        "Korean education blog visual in Bobo teacher style. "
        "Warm cream paper background, torn duct tape / masking tape strips, "
        "handmade scrapbook memo-board feeling, subtle shadows, clean editorial composition. "
        "No readable text, no watermark, no logo."
    )

    # 1. 대표 썸네일 이미지
    prompts.append(
        f"Main blog thumbnail image about '{topic}'. {shared_style} "
        "Use two diagonal pieces of beige duct tape near the top like a taped note."
    )

    # 2. 본문 삽입 이미지
    if num_images >= 2:
        prompts.append(
            f"Second supporting image for a blog post about '{topic}'. {shared_style} "
            "Focus on the duct-tape memo-note look: paper card, tape corners, study planning objects, soft coral and mint accents."
        )

    # 3. 마무리/요약 이미지
    if num_images >= 3:
        prompts.append(
            f"Closing summary image for Korean education blog about '{topic}'. {shared_style} "
            "Minimal study desk scene with taped checklist cards, no readable text."
        )

    return prompts[:num_images]


def generate_blog_images(
    topic: str,
    num_images: int = 3,
    model: str = "openai/gpt-image-2",
) -> list[GeneratedImage]:
    """블로그 글에 맞는 이미지를 생성합니다.

    Args:
        topic: 블로그 주제
        num_images: 생성할 이미지 수 (1~4)
        model: 이미지 생성 모델 ID

    Returns:
        생성된 이미지 리스트
    """
    if not has_image_api_key(model):
        raise ValueError(format_missing_image_api_key_message(model))

    prompts = _build_image_prompts(topic, num_images)
    images: list[GeneratedImage] = []
    errors: list[str] = []

    if _is_openai_image_model(model):
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        model_id = _openai_image_model_id(model)

        for prompt in prompts:
            try:
                response = client.images.generate(
                    model=model_id,
                    prompt=prompt,
                    size="1024x1024",
                    quality="low",
                )
                image_base64 = response.data[0].b64_json
                images.append(
                    GeneratedImage(data=base64.b64decode(image_base64), prompt=prompt)
                )
            except Exception as exc:
                errors.append(format_image_exception_message(model, exc))

        if not images and errors:
            raise RuntimeError(errors[0])
        return images

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    for prompt in prompts:
        try:
            if "imagen" in model:
                # Imagen API (이미지 전용 모델)
                response = client.models.generate_images(
                    model=model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/png",
                    ),
                )
                if response.generated_images:
                    img = response.generated_images[0].image
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    images.append(
                        GeneratedImage(data=buf.getvalue(), prompt=prompt)
                    )
            else:
                # Gemini native 이미지 생성 (gemini-2.5-flash-image 등)
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                    ),
                )
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data is not None:
                            image_bytes = part.inline_data.data
                            images.append(
                                GeneratedImage(data=image_bytes, prompt=prompt)
                            )
                            break
        except Exception as exc:
            errors.append(format_image_exception_message(model, exc))
            continue

    if not images and errors:
        raise RuntimeError(errors[0])
    return images


def list_image_model_names() -> list[str]:
    """사용 가능한 이미지 모델 이름 목록."""
    return list(IMAGE_MODEL_REGISTRY.keys())


def get_image_model_id(name: str) -> str:
    """표시 이름 → 모델 ID."""
    return IMAGE_MODEL_REGISTRY.get(name, name)
