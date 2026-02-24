"""블로그 썸네일 이미지 생성 (Pillow) - 보보쌤 미리캔버스 스타일."""

from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont

from naverblog.watermark import _find_korean_font, _hex_to_rgb

# ─── 색상 프리셋 (보보쌤 블로그 실제 스타일 기반) ───

THUMBNAIL_PRESETS: dict[str, dict] = {
    "보보쌤 기본 (크림)": {
        "bg_color": "#FDF6EC",
        "text_color": "#1a1a1a",
        "highlight_color": "#FFE066",
        "accent_color": "#7c3aed",
        "branding_color": "#888888",
        "description": "보보쌤 블로그 실제 스타일",
    },
    "보보쌤 퍼플": {
        "bg_color": "#F5F0FF",
        "text_color": "#1a1a1a",
        "highlight_color": "#C4B5FD",
        "accent_color": "#7c3aed",
        "branding_color": "#7c3aed",
        "description": "보라색 포인트",
    },
    "화이트 클린": {
        "bg_color": "#FFFFFF",
        "text_color": "#1a1a1a",
        "highlight_color": "#FFE066",
        "accent_color": "#3B82F6",
        "branding_color": "#999999",
        "description": "깔끔한 화이트",
    },
    "소프트 핑크": {
        "bg_color": "#FFF0F5",
        "text_color": "#1a1a1a",
        "highlight_color": "#FBCFE8",
        "accent_color": "#EC4899",
        "branding_color": "#EC4899",
        "description": "따뜻한 핑크",
    },
    "네이비": {
        "bg_color": "#1E293B",
        "text_color": "#FFFFFF",
        "highlight_color": "#3B82F6",
        "accent_color": "#60A5FA",
        "branding_color": "#94A3B8",
        "description": "진한 네이비",
    },
    "다크": {
        "bg_color": "#18181B",
        "text_color": "#FFFFFF",
        "highlight_color": "#A78BFA",
        "accent_color": "#A78BFA",
        "branding_color": "#71717A",
        "description": "세련된 다크",
    },
    "민트": {
        "bg_color": "#F0FDF4",
        "text_color": "#1a1a1a",
        "highlight_color": "#86EFAC",
        "accent_color": "#059669",
        "branding_color": "#059669",
        "description": "상쾌한 민트",
    },
}

# ─── 글자 크기 프리셋 ───

FONT_SIZE_PRESETS: dict[str, dict[str, int]] = {
    "큰 제목": {"title": 80, "subtitle": 36, "category": 26, "branding": 24},
    "보통": {"title": 64, "subtitle": 32, "category": 24, "branding": 22},
    "작은 제목": {"title": 52, "subtitle": 28, "category": 22, "branding": 20},
}

# ─── 레이아웃 프리셋 ───

LAYOUT_PRESETS: dict[str, str] = {
    "가운데 정렬": "center",
    "왼쪽 정렬": "left",
    "하단 정렬": "bottom",
}


def _draw_gradient(
    img: Image.Image,
    start_hex: str,
    end_hex: str,
) -> None:
    """세로 방향 그라데이션."""
    sr, sg, sb = _hex_to_rgb(start_hex)
    er, eg, eb = _hex_to_rgb(end_hex)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for y in range(h):
        ratio = y / h
        r = int(sr + (er - sr) * ratio)
        g = int(sg + (eg - sg) * ratio)
        b = int(sb + (eb - sb) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    """텍스트를 max_width 픽셀 내로 줄바꿈."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            test = current + char
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width:
                if current:
                    lines.append(current)
                current = char
            else:
                current = test
        if current:
            lines.append(current)
    return lines


def _line_height(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    sample: str = "가Ay",
) -> int:
    bbox = draw.textbbox((0, 0), sample, font=font)
    return bbox[3] - bbox[1]


def _draw_highlight(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text_width: int,
    line_h: int,
    color_hex: str,
    opacity: int = 180,
) -> None:
    """형광펜 밑줄 효과 (텍스트 하단 40%)."""
    r, g, b = _hex_to_rgb(color_hex)
    highlight_h = max(int(line_h * 0.35), 8)
    highlight_y = y + line_h - highlight_h + 4
    draw.rectangle(
        [x - 4, highlight_y, x + text_width + 4, highlight_y + highlight_h],
        fill=(r, g, b),
    )


def _draw_separator(
    draw: ImageDraw.ImageDraw,
    y: int,
    width: int,
    color_hex: str,
    padding_x: int = 100,
) -> None:
    """가로 구분선."""
    r, g, b = _hex_to_rgb(color_hex)
    draw.line(
        [(padding_x, y), (width - padding_x, y)],
        fill=(r, g, b),
        width=2,
    )


def render_thumbnail(
    title: str = "",
    title_lines: list[dict] | None = None,
    subtitle: str = "",
    subtitle_color: str | None = None,
    category_label: str = "",
    branding_text: str = "보보쌤의 공부 & 입시 연구소",
    bg_color: str = "#FDF6EC",
    text_color: str = "#1a1a1a",
    highlight_color: str = "#FFE066",
    accent_color: str = "#7c3aed",
    branding_color: str = "#888888",
    title_font_size: int = 64,
    subtitle_font_size: int = 32,
    use_highlight: bool = True,
    highlight_line: int = -1,
    use_separator: bool = False,
    layout: str = "center",
    title_y_offset: int = 0,
    width: int = 1200,
    height: int = 628,
    gradient_end_color: str | None = None,
) -> bytes:
    """보보쌤 스타일 블로그 썸네일을 생성합니다.

    title_lines를 제공하면 줄별 개별 스타일링이 적용됩니다.
    title_lines 각 항목: {"text", "color", "highlight", "highlight_color", "y_offset"}

    title_lines가 없으면 title 문자열을 자동 줄바꿈합니다.
    """
    bg_rgb = _hex_to_rgb(bg_color)
    img = Image.new("RGB", (width, height), bg_rgb)

    if gradient_end_color:
        _draw_gradient(img, bg_color, gradient_end_color)

    draw = ImageDraw.Draw(img)
    txt_rgb = _hex_to_rgb(text_color)
    accent_rgb = _hex_to_rgb(accent_color)
    branding_rgb = _hex_to_rgb(branding_color)

    padding_x = 100
    max_text_width = width - 2 * padding_x

    # 폰트
    title_font = _find_korean_font(title_font_size)
    subtitle_font = _find_korean_font(subtitle_font_size)
    category_font = _find_korean_font(max(20, subtitle_font_size - 8))
    branding_font = _find_korean_font(max(18, subtitle_font_size - 10))

    # 줄 높이
    title_lh = _line_height(draw, title_font)
    subtitle_lh = _line_height(draw, subtitle_font)
    category_lh = _line_height(draw, category_font) if category_label else 0
    branding_lh = _line_height(draw, branding_font) if branding_text else 0

    title_gap = int(title_lh * 0.4)
    subtitle_gap = int(subtitle_lh * 0.3)

    # ─── 제목 줄 전처리 ───
    # title_lines가 제공되면 각 줄을 개별 스타일로 처리
    # 아니면 title 문자열을 자동 줄바꿈
    rendered_lines: list[dict] = []
    if title_lines:
        for line_cfg in title_lines:
            txt = line_cfg.get("text", "")
            if not txt.strip():
                continue
            wrapped = _wrap_text(draw, txt, title_font, max_text_width)
            for wl in wrapped:
                rendered_lines.append({
                    "text": wl,
                    "color": line_cfg.get("color"),
                    "highlight": line_cfg.get("highlight", False),
                    "highlight_color": line_cfg.get("highlight_color"),
                    "y_offset": line_cfg.get("y_offset", 0),
                })
    elif title:
        wrapped = _wrap_text(draw, title, title_font, max_text_width)
        hl_idx = len(wrapped) + highlight_line if highlight_line < 0 else highlight_line
        for i, wl in enumerate(wrapped):
            rendered_lines.append({
                "text": wl,
                "highlight": use_highlight and i == hl_idx,
            })

    if not rendered_lines:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # 부제목 줄바꿈
    subtitle_lines = _wrap_text(draw, subtitle, subtitle_font, max_text_width) if subtitle else []

    # 전체 블록 높이 계산
    total_h = 0
    if category_label:
        total_h += category_lh + 20
    total_h += title_lh * len(rendered_lines) + title_gap * max(0, len(rendered_lines) - 1)
    if subtitle_lines:
        total_h += 28 + subtitle_lh * len(subtitle_lines) + subtitle_gap * max(0, len(subtitle_lines) - 1)
    if branding_text:
        if use_separator:
            total_h += 40 + branding_lh
        else:
            total_h += 30 + branding_lh

    # Y 시작 위치
    if layout == "bottom":
        y = height - total_h - 60
    else:
        y = (height - total_h) // 2

    y += title_y_offset

    # ─── 카테고리 라벨 ───
    if category_label:
        cat_bbox = draw.textbbox((0, 0), category_label, font=category_font)
        cat_w = cat_bbox[2] - cat_bbox[0]
        if layout == "left":
            cat_x = padding_x
        else:
            cat_x = (width - cat_w) // 2
        draw.text((cat_x, y), category_label, font=category_font, fill=accent_rgb)
        y += category_lh + 20

    # ─── 제목 (줄별 개별 스타일 + 위치 오프셋) ───
    for line_cfg in rendered_lines:
        line_text = line_cfg["text"]
        line_color = _hex_to_rgb(line_cfg.get("color") or text_color)
        line_hl = line_cfg.get("highlight", False)
        line_hl_color = line_cfg.get("highlight_color") or highlight_color
        line_y_off = line_cfg.get("y_offset", 0)

        bbox = draw.textbbox((0, 0), line_text, font=title_font)
        tw = bbox[2] - bbox[0]
        if layout == "left":
            x = padding_x
        else:
            x = (width - tw) // 2

        draw_y = y + line_y_off

        if line_hl:
            _draw_highlight(draw, x, draw_y, tw, title_lh, line_hl_color)

        draw.text((x, draw_y), line_text, font=title_font, fill=line_color)
        y += title_lh + title_gap

    # ─── 부제목 ───
    if subtitle_lines:
        sub_rgb = _hex_to_rgb(subtitle_color) if subtitle_color else txt_rgb
        y += 28 - title_gap
        for line in subtitle_lines:
            bbox = draw.textbbox((0, 0), line, font=subtitle_font)
            tw = bbox[2] - bbox[0]
            if layout == "left":
                x = padding_x
            else:
                x = (width - tw) // 2
            draw.text((x, y), line, font=subtitle_font, fill=sub_rgb)
            y += subtitle_lh + subtitle_gap

    # ─── 구분선 + 브랜딩 ───
    if branding_text:
        if use_separator:
            y += 20
            _draw_separator(draw, y, width, branding_color, padding_x)
            y += 20
        else:
            y += 30

        br_bbox = draw.textbbox((0, 0), branding_text, font=branding_font)
        br_w = br_bbox[2] - br_bbox[0]
        if layout == "left":
            br_x = padding_x
        else:
            br_x = (width - br_w) // 2
        draw.text((br_x, y), branding_text, font=branding_font, fill=branding_rgb)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
