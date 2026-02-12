"""데이터 모델 정의."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PostType(str, Enum):
    GENERAL = "general"
    REVIEW = "review"
    LISTICLE = "listicle"


class Persona(BaseModel):
    id: int | None = None
    name: str
    description: str
    system_prompt: str
    is_preset: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class Generation(BaseModel):
    id: int | None = None
    topic: str
    persona_name: str
    llm_model: str
    post_type: PostType = PostType.GENERAL
    search_context: str | None = None
    prompt_used: str = ""
    output_markdown: str = ""
    output_html: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    tags: list[str] = Field(default_factory=list)


class SkillConfig(BaseModel):
    name: str
    enabled: bool = True
    config: dict = Field(default_factory=dict)
