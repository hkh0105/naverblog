"""Jinja2 기반 프롬프트 조립."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from naverblog.models import Persona, PostType
from naverblog.skills.base import SkillResult

TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    trim_blocks=True,
    lstrip_blocks=True,
)


def build_system_prompt(persona: Persona) -> str:
    """페르소나 기반 시스템 프롬프트 생성."""
    template = _env.get_template("system.j2")
    return template.render(persona=persona)


def build_user_prompt(
    topic: str,
    post_type: PostType,
    skill_results: dict[str, SkillResult],
    extra_instructions: str = "",
) -> str:
    """주제 + 검색 결과 + 글 유형 기반 사용자 프롬프트 생성."""
    template_name = f"blog_{post_type.value}.j2"
    template = _env.get_template(template_name)
    return template.render(
        topic=topic,
        skill_results=skill_results,
        extra_instructions=extra_instructions,
    )
