"""블로그 글에 맞는 이미지 생성 (Google Imagen / Gemini)."""

from __future__ import annotations

import base64
import io
import os
from dataclasses import dataclass


# 이미지 생성 모델 레지스트리
IMAGE_MODEL_REGISTRY: dict[str, str] = {
    "Imagen 3": "imagen-3.0-generate-002",
    "Imagen 4": "imagen-4.0-generate-001",
    "Gemini Flash Image": "gemini-2.5-flash-image",
}


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

    # 1. 대표 썸네일 이미지
    prompts.append(
        f"Blog thumbnail image about '{topic}'. "
        "Clean, modern Korean blog style. Soft pastel colors, "
        "warm lighting, professional composition. "
        "No text or watermarks."
    )

    # 2. 본문 삽입 이미지
    if num_images >= 2:
        prompts.append(
            f"Illustrative photo for a blog post about '{topic}'. "
            "Warm, friendly atmosphere. Suitable for Korean education blog. "
            "Natural, authentic feel. No text overlay."
        )

    # 3. 마무리/요약 이미지
    if num_images >= 3:
        prompts.append(
            f"Supporting visual for Korean blog about '{topic}'. "
            "Concept illustration or flat design style. "
            "Minimalist, clean aesthetic. No text."
        )

    return prompts[:num_images]


def generate_blog_images(
    topic: str,
    num_images: int = 3,
    model: str = "imagen-3.0-generate-002",
) -> list[GeneratedImage]:
    """블로그 글에 맞는 이미지를 생성합니다.

    Args:
        topic: 블로그 주제
        num_images: 생성할 이미지 수 (1~4)
        model: 이미지 생성 모델 ID

    Returns:
        생성된 이미지 리스트
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY 또는 GOOGLE_API_KEY가 설정되지 않았습니다. "
            ".env 파일에 추가해주세요."
        )

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    prompts = _build_image_prompts(topic, num_images)
    images: list[GeneratedImage] = []

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
        except Exception as e:
            # 개별 이미지 실패 시 건너뛰고 계속 진행
            print(f"이미지 생성 실패 ({prompt[:30]}...): {e}")
            continue

    return images


def list_image_model_names() -> list[str]:
    """사용 가능한 이미지 모델 이름 목록."""
    return list(IMAGE_MODEL_REGISTRY.keys())


def get_image_model_id(name: str) -> str:
    """표시 이름 → 모델 ID."""
    return IMAGE_MODEL_REGISTRY.get(name, name)
