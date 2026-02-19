"""보보쌤 네이버 블로그 RSS 크롤링 → DB 저장.

Usage:
    python scripts/crawl_blog.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from naverblog.crawler import crawl_blog
from naverblog.database import create_database


def main():
    db = create_database()
    print(f"📊 현재 DB에 저장된 포스트: {db.count_blog_posts()}개\n")

    result = crawl_blog(db, progress_callback=lambda msg: print(f"  {msg}"))

    print(f"\n{'='*50}")
    print(f"📊 크롤링 결과:")
    print(f"  ✅ 성공: {result['success']}개")
    print(f"  ⏭️ 이미 저장됨: {result['skip']}개")
    print(f"  ❌ 실패: {result['fail']}개")
    print(f"  📦 총 DB 포스트: {db.count_blog_posts()}개")

    print(f"\n📂 카테고리별 저장된 글 수:")
    for cat in db.get_blog_post_categories():
        posts_in_cat = db.list_blog_posts(category=cat)
        print(f"  - {cat}: {len(posts_in_cat)}개")


if __name__ == "__main__":
    main()
