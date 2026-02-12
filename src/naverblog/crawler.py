"""보보쌤 네이버 블로그 RSS 크롤링 모듈.

app.py 시작 시 DB가 비어있으면 자동 실행됩니다.
"""
from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from html import unescape
from urllib.request import Request, urlopen

from naverblog.database import Database

BLOG_ID = "byhur99"
RSS_URL = f"https://rss.blog.naver.com/{BLOG_ID}.xml"
POST_VIEW_URL = "https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={post_id}&directAccess=false"


def fetch_url(url: str) -> str:
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    })
    with urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_rss(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    posts = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        desc = item.findtext("description", "").strip()
        pub_date = item.findtext("pubDate", "").strip()
        category = item.findtext("category", "").strip()

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
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def fetch_post_content(blog_id: str, post_id: str) -> str:
    url = POST_VIEW_URL.format(blog_id=blog_id, post_id=post_id)
    try:
        html = fetch_url(url)
    except Exception:
        return ""

    start_marker = '<div class="se-main-container">'
    start_idx = html.find(start_marker)
    if start_idx >= 0:
        region = html[start_idx:start_idx + 200000]
        paragraphs = re.findall(
            r'<p[^>]*class="[^"]*se-text-paragraph[^"]*"[^>]*>(.*?)</p>',
            region, re.DOTALL,
        )
        if paragraphs:
            texts = [strip_html(p) for p in paragraphs]
            return "\n".join(t for t in texts if t.strip())

        end_marker = "<!-- SE_DOC_FOOTER"
        end_idx = region.find(end_marker)
        if end_idx > 0:
            content = region[:end_idx]
        else:
            content = region[:100000]
        return strip_html(content)

    m = re.search(
        r'<div[^>]*id="postViewArea"[^>]*>(.*?)<!-- // -->',
        html, re.DOTALL,
    )
    if m:
        return strip_html(m.group(1))

    m = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL)
    if m:
        text = strip_html(m.group(1))
        if len(text) > 200:
            return text[:8000]

    return ""


def crawl_blog(db: Database, progress_callback=None) -> dict:
    """블로그 크롤링 실행. progress_callback(message)로 진행 상황 전달."""
    def log(msg: str):
        if progress_callback:
            progress_callback(msg)

    log("RSS 피드 가져오는 중...")
    try:
        rss_xml = fetch_url(RSS_URL)
    except Exception as e:
        log(f"RSS 가져오기 실패: {e}")
        return {"success": 0, "skip": 0, "fail": 0}

    posts = parse_rss(rss_xml)
    log(f"RSS에서 {len(posts)}개 포스트 발견")

    success = 0
    skip = 0
    fail = 0

    for i, post in enumerate(posts, 1):
        post_id = post["post_id"]
        if not post_id:
            fail += 1
            continue

        if db.get_blog_post(post_id):
            skip += 1
            continue

        log(f"[{i}/{len(posts)}] 크롤링: {post['title'][:30]}...")

        content = fetch_post_content(BLOG_ID, post_id)

        if content and len(content) >= 50:
            db.save_blog_post(
                post_id=post_id,
                title=post["title"],
                category=post["category"],
                content=content,
                pub_date=post["pub_date"],
                link=post["link"],
            )
            success += 1
        elif post["description"] and len(post["description"]) > 20:
            db.save_blog_post(
                post_id=post_id,
                title=post["title"],
                category=post["category"],
                content=post["description"],
                pub_date=post["pub_date"],
                link=post["link"],
            )
            success += 1
        else:
            fail += 1

        time.sleep(0.5)

    log(f"완료! 성공: {success}, 스킵: {skip}, 실패: {fail}")
    return {"success": success, "skip": skip, "fail": fail}
