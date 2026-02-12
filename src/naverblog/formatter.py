"""Markdown → 네이버 블로그 호환 HTML 변환."""

from __future__ import annotations

import markdown as md


def markdown_to_naver_html(md_text: str) -> str:
    """Markdown을 네이버 블로그에 붙여넣기 가능한 HTML로 변환."""
    html = md.markdown(
        md_text,
        extensions=["extra", "nl2br", "sane_lists"],
    )

    # 네이버 블로그 호환 스타일 적용
    html = html.replace("<h1>", '<h1 style="font-size: 1.6em; margin: 1em 0 0.5em 0;">')
    html = html.replace("<h2>", '<h2 style="font-size: 1.3em; margin: 0.8em 0 0.4em 0;">')
    html = html.replace("<h3>", '<h3 style="font-size: 1.1em; margin: 0.6em 0 0.3em 0;">')
    html = html.replace("<p>", '<p style="margin-bottom: 1em; line-height: 1.8;">')
    html = html.replace("<li>", '<li style="margin-bottom: 0.3em; line-height: 1.6;">')
    html = html.replace("<strong>", '<strong style="color: #333;">')

    return html.strip()
