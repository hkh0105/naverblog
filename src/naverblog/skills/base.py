"""스킬 시스템 기본 인터페이스."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillContext:
    """스킬에 전달되는 입력 컨텍스트."""

    topic: str
    persona_name: str
    persona_prompt: str
    category: str = ""
    db: Any = None  # Database 인스턴스 (스킬에서 DB 접근용)
    ref_post_count: int = 3  # 레퍼런스 글 수 (0=전부)
    previous_results: dict[str, SkillResult] = field(default_factory=dict)


@dataclass
class SkillResult:
    """스킬 실행 결과."""

    skill_name: str
    data: Any
    summary: str
    raw: dict = field(default_factory=dict)


class SkillBase(ABC):
    """모든 스킬의 추상 베이스 클래스."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def execute(self, context: SkillContext) -> SkillResult: ...
