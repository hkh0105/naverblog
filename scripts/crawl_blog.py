"""보보쌤 네이버 블로그 RSS 크롤링 → DB 저장.

Usage:
    python scripts/crawl_blog.py
"""
from __future__ import annotations

import re
import sys
import time
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen

# 프로젝트 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from naverblog.database import Database

BLOG_ID = "byhur99"
RSS_URL = f"https://rss.blog.naver.com/{BLOG_ID}.xml"
# 네이버 블로그 본문 API (비공개 API지만 읽기 가능)
POST_VIEW_URL = "https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={post_id}&directAccess=false"


def fetch_url(url: str) -> str:
    """URL에서 텍스트 가져오기."""
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    })
    with urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_rss(xml_text: str) -> list[dict]:
    """RSS XML 파싱 → 포스트 메타데이터 리스트."""
    root = ET.fromstring(xml_text)
    posts = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        desc = item.findtext("description", "").strip()
        pub_date = item.findtext("pubDate", "").strip()
        category = item.findtext("category", "").strip()

        # postId 추출 (URL: /byhur99/224153699867?fromRss=...)
        post_id = ""
        if link:
            m = re.search(r"/(\d{10,})", link)
            if m:
                post_id = m.group(1)

        posts.append({
            "post_id": post_id,
            "title": unescape(title),
            "category": unescape(category),
            "link": link,
            "description": unescape(desc),
            "pub_date": pub_date,
        })
    return posts


def strip_html(html: str) -> str:
    """HTML 태그 제거 후 텍스트만 추출."""
    # script, style 태그 제거
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # HTML 태그 제거
    text = re.sub(r"<[^>]+>", "\n", text)
    # HTML 엔티티
    text = unescape(text)
    # 연속 공백/줄바꿈 정리
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def fetch_post_content(blog_id: str, post_id: str) -> str:
    """네이버 블로그 포스트 본문 텍스트 추출."""
    url = POST_VIEW_URL.format(blog_id=blog_id, post_id=post_id)
    try:
        html = fetch_url(url)
    except Exception as e:
        print(f"  ⚠️ HTTP 실패: {e}")
        return ""

    # 방법 1: se-main-container 영역 찾기
    start_marker = '<div class="se-main-container">'
    start_idx = html.find(start_marker)
    if start_idx >= 0:
        # se-main-container 이후의 본문 영역 추출
        region = html[start_idx:start_idx + 200000]  # 최대 200KB
        # 텍스트 단락 추출 (se-text-paragraph)
        paragraphs = re.findall(
            r'<p[^>]*class="[^"]*se-text-paragraph[^"]*"[^>]*>(.*?)</p>',
            region, re.DOTALL,
        )
        if paragraphs:
            texts = [strip_html(p) for p in paragraphs]
            return "\n".join(t for t in texts if t.strip())

        # se-text-paragraph이 없으면 전체 영역에서 텍스트 추출
        # SE_DOC_FOOTER_START 또는 다음 큰 div까지
        end_marker = "<!-- SE_DOC_FOOTER"
        end_idx = region.find(end_marker)
        if end_idx > 0:
            content = region[:end_idx]
        else:
            content = region[:100000]
        return strip_html(content)

    # 방법 2: postViewArea (구형 에디터)
    m = re.search(
        r'<div[^>]*id="postViewArea"[^>]*>(.*?)<!-- // -->',
        html, re.DOTALL,
    )
    if m:
        return strip_html(m.group(1))

    # 방법 3: body 전체에서 추출 (최후 수단)
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL)
    if m:
        text = strip_html(m.group(1))
        if len(text) > 200:
            return text[:8000]

    return ""


def fetch_post_via_mobile(blog_id: str, post_id: str) -> str:
    """모바일 페이지에서 본문 추출 (대안)."""
    url = f"https://m.blog.naver.com/{blog_id}/{post_id}"
    try:
        html = fetch_url(url)
    except Exception:
        return ""

    # 모바일 본문 영역
    m = re.search(
        r'<div[^>]*class="[^"]*se-main-container[^"]*"[^>]*>(.*?)<div[^>]*class="[^"]*post_footer',
        html, re.DOTALL,
    )
    if m:
        return strip_html(m.group(1))

    m = re.search(r'<div[^>]*id="viewTypeSelector"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    if m:
        return strip_html(m.group(1))

    return ""


def main():
    db = Database()
    existing_count = db.count_blog_posts()
    print(f"📊 현재 DB에 저장된 포스트: {existing_count}개")

    # 1. RSS 가져오기
    print(f"\n📡 RSS 피드 가져오는 중: {RSS_URL}")
    rss_xml = fetch_url(RSS_URL)
    posts = parse_rss(rss_xml)
    print(f"✅ RSS에서 {len(posts)}개 포스트 발견")

    # 2. 각 포스트 본문 크롤링
    success = 0
    skip = 0
    fail = 0

    for i, post in enumerate(posts, 1):
        post_id = post["post_id"]
        if not post_id:
            print(f"  [{i}/{len(posts)}] ⚠️ postId 없음: {post['title']}")
            fail += 1
            continue

        # 이미 DB에 있으면 스킵
        if db.get_blog_post(post_id):
            print(f"  [{i}/{len(posts)}] ⏭️ 이미 저장됨: {post['title'][:30]}")
            skip += 1
            continue

        print(f"  [{i}/{len(posts)}] 📥 크롤링: {post['title'][:40]}...", end=" ")

        # 데스크톱 버전 먼저 시도
        content = fetch_post_content(BLOG_ID, post_id)

        # 실패하면 모바일 버전 시도
        if not content or len(content) < 100:
            content = fetch_post_via_mobile(BLOG_ID, post_id)

        if content and len(content) >= 50:
            db.save_blog_post(
                post_id=post_id,
                title=post["title"],
                category=post["category"],
                content=content,
                pub_date=post["pub_date"],
                link=post["link"],
            )
            print(f"✅ ({len(content)}자)")
            success += 1
        else:
            # description이라도 저장
            if post["description"] and len(post["description"]) > 20:
                db.save_blog_post(
                    post_id=post_id,
                    title=post["title"],
                    category=post["category"],
                    content=post["description"],
                    pub_date=post["pub_date"],
                    link=post["link"],
                )
                print(f"⚠️ description만 저장 ({len(post['description'])}자)")
                success += 1
            else:
                print("❌ 본문 추출 실패")
                fail += 1

        # rate limit 방지
        time.sleep(0.5)

    # 3. 결과 요약
    print(f"\n{'='*50}")
    print(f"📊 크롤링 결과:")
    print(f"  ✅ 성공: {success}개")
    print(f"  ⏭️ 이미 저장됨: {skip}개")
    print(f"  ❌ 실패: {fail}개")
    print(f"  📦 총 DB 포스트: {db.count_blog_posts()}개")

    # 카테고리별 통계
    print(f"\n📂 카테고리별 저장된 글 수:")
    for cat in db.get_blog_post_categories():
        posts_in_cat = db.list_blog_posts(category=cat)
        print(f"  - {cat}: {len(posts_in_cat)}개")


if __name__ == "__main__":
    main()
