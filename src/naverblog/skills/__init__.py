"""스킬 레지스트리 - 자동 발견 및 관리."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from naverblog.models import SkillConfig
from naverblog.skills.base import SkillBase


class SkillRegistry:
    """스킬 자동 발견, 등록, 생명주기 관리."""

    def __init__(self, db):
        self._skills: dict[str, SkillBase] = {}
        self._db = db

    def discover(self) -> None:
        """skills/ 패키지 내 모든 SkillBase 서브클래스를 자동 발견."""
        package_path = Path(__file__).parent
        for _importer, modname, _ispkg in pkgutil.iter_modules([str(package_path)]):
            if modname in ("base",):
                continue
            module = importlib.import_module(f"naverblog.skills.{modname}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, SkillBase)
                    and attr is not SkillBase
                ):
                    instance = attr()
                    self.register(instance)

    def register(self, skill: SkillBase) -> None:
        """스킬 인스턴스를 등록하고 DB에 설정 동기화."""
        self._skills[skill.name] = skill
        if self._db.get_skill_config(skill.name) is None:
            self._db.save_skill_config(SkillConfig(name=skill.name, enabled=True))

    def get_enabled(self) -> list[SkillBase]:
        """DB에서 활성화된 스킬만 반환."""
        enabled = []
        for name, skill in self._skills.items():
            cfg = self._db.get_skill_config(name)
            if cfg and cfg.enabled:
                enabled.append(skill)
        return enabled

    def get(self, name: str) -> SkillBase | None:
        return self._skills.get(name)

    def list_all(self) -> list[SkillBase]:
        return list(self._skills.values())

    def enable(self, name: str) -> None:
        cfg = self._db.get_skill_config(name)
        if cfg:
            cfg.enabled = True
            self._db.save_skill_config(cfg)

    def disable(self, name: str) -> None:
        cfg = self._db.get_skill_config(name)
        if cfg:
            cfg.enabled = False
            self._db.save_skill_config(cfg)
