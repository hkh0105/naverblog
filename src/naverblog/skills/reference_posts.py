"""레퍼런스 포스트 스킬 - 보보쌤의 기존 글을 참조 컨텍스트로 제공.

DB에 크롤링된 실제 블로그 글 중 해당 카테고리의 글을 선별하여
LLM 프롬프트에 주입합니다. 글 생성 시 실제 문체/구조를 참고합니다.
"""
from __future__ import annotations

from naverblog.skills.base import SkillBase, SkillContext, SkillResult


class ReferencePostsSkill(SkillBase):
    """보보쌤 기존 글 레퍼런스 스킬."""

    @property
    def name(self) -> str:
        return "reference_posts"

    @property
    def description(self) -> str:
        return "보보쌤 기존 블로그 글 참조 (실제 글을 컨텍스트로 제공)"

    def execute(self, context: SkillContext) -> SkillResult:
        category = getattr(context, "category", None) or ""
        db = getattr(context, "db", None)
        max_posts = getattr(context, "ref_post_count", 3) or 0

        if not db:
            return SkillResult(
                skill_name=self.name,
                data={"posts": []},
                summary="(DB 연결 없음 - 레퍼런스 스킵)",
            )

        # 해당 카테고리의 글 가져오기
        posts = []
        if category:
            posts = db.list_blog_posts(category=category)

        # 카테고리 매치가 없으면 부분 매치 시도
        if not posts and category:
            all_posts = db.list_blog_posts()
            for p in all_posts:
                if category in p["category"] or p["category"] in category:
                    posts.append(p)

        # 그래도 없으면 전체에서
        if not posts:
            posts = db.list_blog_posts()

        # 글 수 제한 (0이면 전부)
        if max_posts > 0:
            selected = posts[:max_posts]
        else:
            selected = posts

        if not selected:
            return SkillResult(
                skill_name=self.name,
                data={"posts": []},
                summary="(저장된 레퍼런스 글이 없습니다)",
            )

        # 글 수에 따라 글당 최대 길이 조절 (토큰 예산 관리)
        n = len(selected)
        if n <= 3:
            max_len = 3000
        elif n <= 10:
            max_len = 2000
        elif n <= 20:
            max_len = 1500
        else:
            max_len = 1000

        # 프롬프트용 텍스트 생성
        parts = [
            "## 보보쌤 기존 블로그 글 레퍼런스\n"
            f"아래는 보보쌤이 실제로 작성한 블로그 글 {n}개입니다. "
            "이 글들의 문체, 구조, 표현 방식을 참고하여 새 글을 작성하세요.\n"
        ]

        post_data = []
        total_chars = 0
        for i, p in enumerate(selected, 1):
            content = p["content"]
            original_len = len(content)
            if len(content) > max_len:
                content = content[:max_len] + "\n... (이하 생략)"

            parts.append(
                f"### 레퍼런스 #{i}: {p['title']}\n"
                f"카테고리: {p['category']}\n\n"
                f"{content}\n"
            )
            total_chars += len(content)
            post_data.append({
                "title": p["title"],
                "category": p["category"],
                "post_id": p["post_id"],
                "content_length": original_len,
                "truncated_length": min(original_len, max_len),
            })

        summary = "\n---\n".join(parts)

        return SkillResult(
            skill_name=self.name,
            data={
                "posts": post_data,
                "total_available": len(posts),
                "selected_count": n,
                "total_chars": total_chars,
                "max_len_per_post": max_len,
                "estimated_tokens": total_chars // 4,
            },
            summary=summary,
        )
