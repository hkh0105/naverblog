"""Tavily 웹 검색 스킬."""

from __future__ import annotations

import os

from naverblog.skills.base import SkillBase, SkillContext, SkillResult


class SearchSkill(SkillBase):
    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Tavily API를 사용한 웹 검색 (최신 정보 수집)"

    def execute(self, context: SkillContext) -> SkillResult:
        api_key = os.environ.get("TAVILY_API_KEY", "")
        if not api_key:
            return SkillResult(
                skill_name=self.name,
                data=[],
                summary="[검색 스킵: TAVILY_API_KEY가 설정되지 않았습니다]",
            )

        try:
            from tavily import TavilyClient
        except ImportError:
            return SkillResult(
                skill_name=self.name,
                data=[],
                summary="[검색 스킵: tavily-python 패키지가 설치되지 않았습니다]",
            )

        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=context.topic,
            search_depth="advanced",
            topic="general",
            max_results=5,
            include_answer=True,
        )

        results = response.get("results", [])
        answer = response.get("answer", "")

        summary_parts = []
        if answer:
            summary_parts.append(f"## 검색 요약\n{answer}\n")

        summary_parts.append("## 참고 자료")
        for i, r in enumerate(results, 1):
            content = r.get("content", "")[:300]
            summary_parts.append(
                f"{i}. **{r['title']}** (출처: {r['url']})\n   {content}"
            )

        summary = "\n\n".join(summary_parts)

        return SkillResult(
            skill_name=self.name,
            data=results,
            summary=summary,
            raw=response,
        )
