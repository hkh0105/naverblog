"""핵심 파이프라인: 주제 → 스킬 → 프롬프트 → LLM → 포맷 → 저장."""

from __future__ import annotations

import json

from naverblog.database import Database
from naverblog.formatter import markdown_to_naver_html
from naverblog.llm import generate
from naverblog.models import Generation, Persona, PostType
from naverblog.prompts.builder import build_system_prompt, build_user_prompt
from naverblog.skills import SkillRegistry
from naverblog.skills.base import SkillContext, SkillResult


def run_pipeline(
    topic: str,
    persona: Persona,
    model: str,
    post_type: PostType,
    skill_registry: SkillRegistry,
    db: Database,
    extra_instructions: str = "",
    skip_search: bool = False,
    category: str = "",
    ref_post_count: int = 3,
) -> Generation:
    """전체 파이프라인 실행.

    1. 활성화된 스킬 실행 (검색 등)
    2. 시스템 프롬프트 생성 (페르소나 기반)
    3. 사용자 프롬프트 생성 (주제 + 검색 결과 + 글 유형)
    4. LLM 호출
    5. Markdown → 네이버 HTML 변환
    6. DB 저장
    """
    # 1. 스킬 실행
    skill_context = SkillContext(
        topic=topic,
        persona_name=persona.name,
        persona_prompt=persona.system_prompt,
        category=category,
        db=db,
        ref_post_count=ref_post_count,
    )
    skill_results: dict[str, SkillResult] = {}

    for skill in skill_registry.get_enabled():
        if skip_search and skill.name == "search":
            continue
        result = skill.execute(skill_context)
        skill_results[skill.name] = result
        skill_context.previous_results = skill_results

    # 2-3. 프롬프트 빌드
    system_prompt = build_system_prompt(persona)
    user_prompt = build_user_prompt(
        topic=topic,
        post_type=post_type,
        skill_results=skill_results,
        extra_instructions=extra_instructions,
    )

    # 4. LLM 호출
    output_markdown = generate(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    # 5. 포맷
    output_html = markdown_to_naver_html(output_markdown)

    # 6. 저장
    generation = Generation(
        topic=topic,
        persona_name=persona.name,
        llm_model=model,
        post_type=post_type,
        search_context=(
            json.dumps(
                {k: v.raw for k, v in skill_results.items()},
                ensure_ascii=False,
            )
            if skill_results
            else None
        ),
        prompt_used=f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}",
        output_markdown=output_markdown,
        output_html=output_html,
    )
    generation = db.save_generation(generation)

    return generation
