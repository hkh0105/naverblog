"""SQLite 데이터베이스 관리."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from naverblog.config import DB_PATH, PRESETS_DIR, ensure_app_dir
from naverblog.models import Generation, Persona, SkillConfig

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    is_preset BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    persona_name TEXT NOT NULL,
    llm_model TEXT NOT NULL,
    post_type TEXT DEFAULT 'general',
    search_context TEXT,
    prompt_used TEXT NOT NULL,
    output_markdown TEXT NOT NULL,
    output_html TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS skills (
    name TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT 1,
    config TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS blog_styles (
    key TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blog_posts (
    post_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    pub_date TEXT,
    link TEXT,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        ensure_app_dir()
        self._db_path = db_path
        self._migrate()
        self._seed_presets()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _migrate(self) -> None:
        with self._get_conn() as conn:
            conn.executescript(SCHEMA_SQL)

    def _seed_presets(self) -> None:
        presets_file = PRESETS_DIR / "personas.json"
        if not presets_file.exists():
            return
        presets = json.loads(presets_file.read_text(encoding="utf-8"))
        preset_names = {p["name"] for p in presets}
        with self._get_conn() as conn:
            # 기존 프리셋 중 JSON에 없는 것 삭제
            conn.execute(
                "DELETE FROM personas WHERE is_preset = 1 AND name NOT IN ({})".format(
                    ",".join("?" for _ in preset_names)
                ),
                list(preset_names),
            )
            # 프리셋 upsert
            for p in presets:
                conn.execute(
                    "INSERT OR REPLACE INTO personas (name, description, system_prompt, is_preset) "
                    "VALUES (?, ?, ?, 1)",
                    (p["name"], p["description"], p["system_prompt"]),
                )

    # --- Persona ---

    def get_persona(self, name: str) -> Persona | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM personas WHERE name = ?", (name,)
            ).fetchone()
        if row is None:
            return None
        return Persona(**dict(row))

    def list_personas(self) -> list[Persona]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM personas ORDER BY is_preset DESC, name"
            ).fetchall()
        return [Persona(**dict(r)) for r in rows]

    def add_persona(self, persona: Persona) -> Persona:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO personas (name, description, system_prompt, is_preset) "
                "VALUES (?, ?, ?, ?)",
                (persona.name, persona.description, persona.system_prompt, persona.is_preset),
            )
            persona.id = cursor.lastrowid
        return persona

    def delete_persona(self, name: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM personas WHERE name = ? AND is_preset = 0", (name,))
        return cursor.rowcount > 0

    # --- Generation ---

    def save_generation(self, gen: Generation) -> Generation:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO generations "
                "(topic, persona_name, llm_model, post_type, search_context, "
                "prompt_used, output_markdown, output_html, tags) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    gen.topic,
                    gen.persona_name,
                    gen.llm_model,
                    gen.post_type.value,
                    gen.search_context,
                    gen.prompt_used,
                    gen.output_markdown,
                    gen.output_html,
                    json.dumps(gen.tags, ensure_ascii=False),
                ),
            )
            gen.id = cursor.lastrowid
        return gen

    def get_generation(self, gen_id: int) -> Generation | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM generations WHERE id = ?", (gen_id,)
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["tags"] = json.loads(data.get("tags", "[]"))
        return Generation(**data)

    def list_generations(self, limit: int = 20) -> list[Generation]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM generations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        results = []
        for r in rows:
            data = dict(r)
            data["tags"] = json.loads(data.get("tags", "[]"))
            results.append(Generation(**data))
        return results

    # --- Skill Config ---

    def get_skill_config(self, name: str) -> SkillConfig | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM skills WHERE name = ?", (name,)
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["config"] = json.loads(data.get("config", "{}"))
        return SkillConfig(**data)

    def save_skill_config(self, config: SkillConfig) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO skills (name, enabled, config) VALUES (?, ?, ?)",
                (config.name, config.enabled, json.dumps(config.config, ensure_ascii=False)),
            )

    def list_skill_configs(self) -> list[SkillConfig]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM skills").fetchall()
        results = []
        for r in rows:
            data = dict(r)
            data["config"] = json.loads(data.get("config", "{}"))
            results.append(SkillConfig(**data))
        return results

    # --- App Config ---

    def get_config(self, key: str, default: str = "") -> str:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM app_config WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return default
        return row["value"]

    def set_config(self, key: str, value: str) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)",
                (key, value),
            )

    # --- Blog Styles ---

    def get_blog_style(self, key: str) -> str | None:
        """키(common 또는 카테고리명)에 해당하는 스타일 텍스트 반환."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT content FROM blog_styles WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        return row["content"]

    def save_blog_style(self, key: str, content: str) -> None:
        """스타일 텍스트를 DB에 저장 (upsert)."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO blog_styles (key, content, updated_at) "
                "VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key, content),
            )

    def list_blog_styles(self) -> dict[str, str]:
        """모든 블로그 스타일을 {key: content} 형태로 반환."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT key, content FROM blog_styles").fetchall()
        return {row["key"]: row["content"] for row in rows}

    def delete_blog_style(self, key: str) -> bool:
        """스타일 삭제. common은 삭제 불가."""
        if key == "common":
            return False
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM blog_styles WHERE key = ?", (key,))
        return cursor.rowcount > 0

    # --- Blog Posts (크롤링된 원본 글) ---

    def save_blog_post(
        self, post_id: str, title: str, category: str, content: str,
        pub_date: str = "", link: str = "",
    ) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO blog_posts "
                "(post_id, title, category, content, pub_date, link, crawled_at) "
                "VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (post_id, title, category, content, pub_date, link),
            )

    def get_blog_post(self, post_id: str) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM blog_posts WHERE post_id = ?", (post_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_blog_posts(self, category: str = "") -> list[dict]:
        with self._get_conn() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM blog_posts WHERE category = ? ORDER BY pub_date DESC",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM blog_posts ORDER BY pub_date DESC"
                ).fetchall()
        return [dict(r) for r in rows]

    def count_blog_posts(self) -> int:
        with self._get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM blog_posts").fetchone()
        return row["cnt"]

    def get_blog_post_categories(self) -> list[str]:
        """크롤링된 포스트의 카테고리 목록."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT category FROM blog_posts WHERE category != '' ORDER BY category"
            ).fetchall()
        return [row["category"] for row in rows]
