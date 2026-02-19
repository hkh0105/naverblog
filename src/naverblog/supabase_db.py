"""Supabase PostgreSQL 데이터베이스 관리.

Database와 동일한 public 인터페이스를 제공.
SUPABASE_URL + SUPABASE_KEY 환경변수가 설정되어 있을 때 사용.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

from supabase import Client, create_client

from naverblog.config import PRESETS_DIR
from naverblog.models import Generation, Persona, PostType, SkillConfig


class SupabaseDatabase:
    def __init__(self) -> None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        self._client: Client = create_client(url, key)
        self._seed_presets()

    # --- Persona ---

    def _seed_presets(self) -> None:
        presets_file = PRESETS_DIR / "personas.json"
        if not presets_file.exists():
            return
        presets = json.loads(presets_file.read_text(encoding="utf-8"))
        preset_names = {p["name"] for p in presets}

        # 기존 프리셋 중 JSON에 없는 것 삭제
        existing = (
            self._client.table("personas")
            .select("name")
            .eq("is_preset", True)
            .execute()
        )
        for row in existing.data:
            if row["name"] not in preset_names:
                self._client.table("personas").delete().eq("name", row["name"]).execute()

        # 프리셋 upsert
        for p in presets:
            self._client.table("personas").upsert(
                {
                    "name": p["name"],
                    "description": p["description"],
                    "system_prompt": p["system_prompt"],
                    "is_preset": True,
                },
                on_conflict="name",
            ).execute()

    def get_persona(self, name: str) -> Persona | None:
        resp = (
            self._client.table("personas")
            .select("*")
            .eq("name", name)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        return self._row_to_persona(resp.data[0])

    def list_personas(self) -> list[Persona]:
        resp = (
            self._client.table("personas")
            .select("*")
            .order("is_preset", desc=True)
            .order("name")
            .execute()
        )
        return [self._row_to_persona(r) for r in resp.data]

    def add_persona(self, persona: Persona) -> Persona:
        resp = (
            self._client.table("personas")
            .insert(
                {
                    "name": persona.name,
                    "description": persona.description,
                    "system_prompt": persona.system_prompt,
                    "is_preset": persona.is_preset,
                }
            )
            .execute()
        )
        persona.id = resp.data[0]["id"]
        return persona

    def delete_persona(self, name: str) -> bool:
        resp = (
            self._client.table("personas")
            .delete()
            .eq("name", name)
            .eq("is_preset", False)
            .execute()
        )
        return len(resp.data) > 0

    @staticmethod
    def _row_to_persona(row: dict) -> Persona:
        return Persona(
            id=row.get("id"),
            name=row["name"],
            description=row["description"],
            system_prompt=row["system_prompt"],
            is_preset=row.get("is_preset", False),
            created_at=row.get("created_at", datetime.now()),
        )

    # --- Generation ---

    def save_generation(self, gen: Generation) -> Generation:
        resp = (
            self._client.table("generations")
            .insert(
                {
                    "topic": gen.topic,
                    "persona_name": gen.persona_name,
                    "llm_model": gen.llm_model,
                    "post_type": gen.post_type.value,
                    "search_context": gen.search_context,
                    "prompt_used": gen.prompt_used,
                    "output_markdown": gen.output_markdown,
                    "output_html": gen.output_html,
                    "tags": json.dumps(gen.tags, ensure_ascii=False),
                }
            )
            .execute()
        )
        gen.id = resp.data[0]["id"]
        return gen

    def get_generation(self, gen_id: int) -> Generation | None:
        resp = (
            self._client.table("generations")
            .select("*")
            .eq("id", gen_id)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        return self._row_to_generation(resp.data[0])

    def list_generations(self, limit: int = 20) -> list[Generation]:
        resp = (
            self._client.table("generations")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [self._row_to_generation(r) for r in resp.data]

    @staticmethod
    def _row_to_generation(row: dict) -> Generation:
        tags = row.get("tags", "[]")
        if isinstance(tags, str):
            tags = json.loads(tags)
        return Generation(
            id=row.get("id"),
            topic=row["topic"],
            persona_name=row["persona_name"],
            llm_model=row["llm_model"],
            post_type=row.get("post_type", "general"),
            search_context=row.get("search_context"),
            prompt_used=row.get("prompt_used", ""),
            output_markdown=row.get("output_markdown", ""),
            output_html=row.get("output_html", ""),
            created_at=row.get("created_at", datetime.now()),
            tags=tags,
        )

    # --- Skill Config ---

    def get_skill_config(self, name: str) -> SkillConfig | None:
        resp = (
            self._client.table("skills")
            .select("*")
            .eq("name", name)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        row = resp.data[0]
        config = row.get("config", "{}")
        if isinstance(config, str):
            config = json.loads(config)
        return SkillConfig(name=row["name"], enabled=row["enabled"], config=config)

    def save_skill_config(self, config: SkillConfig) -> None:
        self._client.table("skills").upsert(
            {
                "name": config.name,
                "enabled": config.enabled,
                "config": json.dumps(config.config, ensure_ascii=False),
            },
            on_conflict="name",
        ).execute()

    def list_skill_configs(self) -> list[SkillConfig]:
        resp = self._client.table("skills").select("*").execute()
        results = []
        for row in resp.data:
            config = row.get("config", "{}")
            if isinstance(config, str):
                config = json.loads(config)
            results.append(
                SkillConfig(name=row["name"], enabled=row["enabled"], config=config)
            )
        return results

    # --- App Config ---

    def get_config(self, key: str, default: str = "") -> str:
        resp = (
            self._client.table("app_config")
            .select("value")
            .eq("key", key)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return default
        return resp.data[0]["value"]

    def set_config(self, key: str, value: str) -> None:
        self._client.table("app_config").upsert(
            {"key": key, "value": value},
            on_conflict="key",
        ).execute()

    # --- Blog Styles ---

    def get_blog_style(self, key: str) -> str | None:
        resp = (
            self._client.table("blog_styles")
            .select("content")
            .eq("key", key)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        return resp.data[0]["content"]

    def save_blog_style(self, key: str, content: str) -> None:
        self._client.table("blog_styles").upsert(
            {
                "key": key,
                "content": content,
                "updated_at": datetime.now().isoformat(),
            },
            on_conflict="key",
        ).execute()

    def list_blog_styles(self) -> dict[str, str]:
        resp = self._client.table("blog_styles").select("key, content").execute()
        return {row["key"]: row["content"] for row in resp.data}

    def delete_blog_style(self, key: str) -> bool:
        if key == "common":
            return False
        resp = (
            self._client.table("blog_styles")
            .delete()
            .eq("key", key)
            .execute()
        )
        return len(resp.data) > 0

    # --- Blog Posts ---

    def save_blog_post(
        self,
        post_id: str,
        title: str,
        category: str,
        content: str,
        pub_date: str = "",
        link: str = "",
    ) -> None:
        self._client.table("blog_posts").upsert(
            {
                "post_id": post_id,
                "title": title,
                "category": category,
                "content": content,
                "pub_date": pub_date,
                "link": link,
                "crawled_at": datetime.now().isoformat(),
            },
            on_conflict="post_id",
        ).execute()

    def get_blog_post(self, post_id: str) -> dict | None:
        resp = (
            self._client.table("blog_posts")
            .select("*")
            .eq("post_id", post_id)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        return resp.data[0]

    def list_blog_posts(self, category: str = "") -> list[dict]:
        query = self._client.table("blog_posts").select("*")
        if category:
            query = query.eq("category", category)
        resp = query.order("pub_date", desc=True).execute()
        return resp.data

    def count_blog_posts(self) -> int:
        resp = (
            self._client.table("blog_posts")
            .select("post_id", count="exact")
            .execute()
        )
        return resp.count or 0

    def get_blog_post_categories(self) -> list[str]:
        resp = (
            self._client.table("blog_posts")
            .select("category")
            .neq("category", "")
            .execute()
        )
        categories = sorted({row["category"] for row in resp.data})
        return categories

    def delete_blog_post(self, post_id: str) -> bool:
        resp = (
            self._client.table("blog_posts")
            .delete()
            .eq("post_id", post_id)
            .execute()
        )
        return len(resp.data) > 0

    def delete_blog_posts_by_category(self, category: str) -> int:
        resp = (
            self._client.table("blog_posts")
            .delete()
            .eq("category", category)
            .execute()
        )
        return len(resp.data)

    # --- Keyword Cache ---

    def get_keyword_cache(self, keyword: str, data_type: str) -> dict | None:
        """캐시된 키워드 분석 결과를 반환. 만료된 경우 None."""
        resp = (
            self._client.table("keyword_cache")
            .select("result_json")
            .eq("keyword", keyword)
            .eq("data_type", data_type)
            .gte("expires_at", datetime.now().isoformat())
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        result = resp.data[0]["result_json"]
        if isinstance(result, str):
            return json.loads(result)
        return result

    def save_keyword_cache(
        self, keyword: str, data_type: str, result: dict, ttl_hours: int = 24,
    ) -> None:
        """키워드 분석 결과를 캐시에 저장."""
        expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        self._client.table("keyword_cache").upsert(
            {
                "keyword": keyword,
                "data_type": data_type,
                "result_json": json.dumps(result, ensure_ascii=False),
                "queried_at": datetime.now().isoformat(),
                "expires_at": expires_at,
            },
            on_conflict="keyword,data_type",
        ).execute()

    def clear_expired_cache(self) -> int:
        """만료된 캐시 항목 삭제."""
        resp = (
            self._client.table("keyword_cache")
            .delete()
            .lt("expires_at", datetime.now().isoformat())
            .execute()
        )
        return len(resp.data)

    def clear_keyword_cache(self, keyword: str = "") -> int:
        """특정 키워드 또는 전체 캐시 삭제."""
        query = self._client.table("keyword_cache").delete()
        if keyword:
            query = query.eq("keyword", keyword)
        else:
            query = query.neq("keyword", "")
        resp = query.execute()
        return len(resp.data)
