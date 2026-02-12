"""이미지/PDF 워터마크 유틸리티."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# ─── 폰트 탐색 ───

_FONT_SEARCH_PATHS = [
    # macOS
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/Library/Fonts/AppleSDGothicNeo.ttc",
    # Linux (Streamlit Cloud - packages.txt에서 fonts-noto-cjk 설치)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/OTF/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/NotoSansCJK-Regular.ttc",
]

_CACHED_FONT_PATH: str | None = None


def _find_korean_font(size: int = 24) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """한국어 지원 폰트 탐색 (Pillow용)."""
    global _CACHED_FONT_PATH

    # 캐시된 경로가 있으면 바로 사용
    if _CACHED_FONT_PATH:
        try:
            return ImageFont.truetype(_CACHED_FONT_PATH, size)
        except Exception:
            _CACHED_FONT_PATH = None

    # 1차: 알려진 경로 탐색
    for path in _FONT_SEARCH_PATHS:
        if Path(path).exists():
            try:
                font = ImageFont.truetype(path, size)
                _CACHED_FONT_PATH = path
                return font
            except Exception:
                continue

    # 2차: fc-list로 한국어 폰트 동적 탐색
    import subprocess
    try:
        result = subprocess.run(
            ["fc-list", ":lang=ko", "file"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().split("\n"):
            fpath = line.strip().rstrip(":")
            if fpath and Path(fpath).exists():
                try:
                    font = ImageFont.truetype(fpath, size)
                    _CACHED_FONT_PATH = fpath
                    return font
                except Exception:
                    continue
    except Exception:
        pass

    # 3차: /usr/share/fonts 전체에서 Noto CJK 검색
    for fonts_dir in [Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]:
        if fonts_dir.exists():
            for fpath in fonts_dir.rglob("*Noto*CJK*"):
                try:
                    font = ImageFont.truetype(str(fpath), size)
                    _CACHED_FONT_PATH = str(fpath)
                    return font
                except Exception:
                    continue

    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """#RRGGBB → (R, G, B)."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


# ─── reportlab 한국어 폰트 등록 ───

_RL_FONT_NAME: str | None = None


def _get_reportlab_font() -> str:
    """reportlab용 한국어 폰트 등록 후 폰트 이름 반환."""
    global _RL_FONT_NAME
    if _RL_FONT_NAME is not None:
        return _RL_FONT_NAME

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for path in _FONT_SEARCH_PATHS:
        if not Path(path).exists():
            continue
        # .ttc 파일: subfontIndex=0 시도
        for idx in (0, None):
            try:
                if idx is not None:
                    pdfmetrics.registerFont(TTFont("KoreanWM", path, subfontIndex=idx))
                else:
                    pdfmetrics.registerFont(TTFont("KoreanWM", path))
                _RL_FONT_NAME = "KoreanWM"
                return _RL_FONT_NAME
            except Exception:
                continue

    _RL_FONT_NAME = "Helvetica"
    return _RL_FONT_NAME


# ─── 이미지 워터마크 ───

def watermark_image(
    image_data: bytes,
    text: str = "보보쌤 | byhur99",
    opacity: int = 80,
    position: str = "bottom-right",
    font_size: int = 0,
    color: tuple[int, int, int] = (255, 255, 255),
    rotation: int = 30,
    bg_box: bool = True,
) -> bytes:
    """이미지에 텍스트 워터마크 삽입."""
    img = Image.open(io.BytesIO(image_data)).convert("RGBA")
    w, h = img.size

    if font_size <= 0:
        font_size = max(16, w // 30)
    font = _find_korean_font(font_size)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    r, g, b = color

    if position in ("diagonal-tiled", "diagonal-single"):
        _draw_diagonal(overlay, text, font, (r, g, b, opacity), rotation, position == "diagonal-tiled")
    else:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        margin = max(10, w // 50)

        if position == "bottom-right":
            x, y = w - tw - margin, h - th - margin
        elif position == "bottom-left":
            x, y = margin, h - th - margin
        elif position == "top-right":
            x, y = w - tw - margin, margin
        elif position == "top-left":
            x, y = margin, margin
        else:  # center
            x, y = (w - tw) // 2, (h - th) // 2

        if bg_box:
            pad = max(4, font_size // 6)
            draw.rounded_rectangle(
                [x - pad, y - pad, x + tw + pad, y + th + pad],
                radius=pad,
                fill=(0, 0, 0, opacity // 2),
            )
        draw.text((x, y), text, font=font, fill=(r, g, b, opacity))

    result = Image.alpha_composite(img, overlay).convert("RGB")
    buf = io.BytesIO()
    result.save(buf, format="PNG", quality=95)
    return buf.getvalue()


def _draw_diagonal(
    overlay: Image.Image,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int, int],
    rotation: int,
    tiled: bool,
) -> None:
    """대각선 워터마크 (1줄 또는 반복 타일)."""
    import math

    w, h = overlay.size
    tmp = ImageDraw.Draw(overlay)
    bbox = tmp.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if tiled:
        # 큰 캔버스에 텍스트 타일링 후 전체 회전
        diag = int(math.sqrt(w * w + h * h))
        big = Image.new("RGBA", (diag * 2, diag * 2), (0, 0, 0, 0))
        big_draw = ImageDraw.Draw(big)
        gap_x = max(tw + 60, int(tw * 1.3))
        gap_y = th + 80
        for y in range(0, diag * 2, gap_y):
            for x in range(0, diag * 2, gap_x):
                big_draw.text((x, y), text, font=font, fill=fill)
        big_rotated = big.rotate(rotation, expand=False, fillcolor=(0, 0, 0, 0))
        # 중앙 크롭
        bw, bh = big_rotated.size
        cx, cy = bw // 2, bh // 2
        crop = big_rotated.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))
        overlay.paste(crop, (0, 0), crop)
    else:
        # 텍스트가 이미지에 맞게 폰트 크기 자동 조정 (리사이즈 없이 선명하게)
        rad = math.radians(rotation)
        max_w = w * 0.85
        max_h = h * 0.85
        adjusted_font = font
        for _ in range(10):
            test_bbox = ImageDraw.Draw(overlay).textbbox((0, 0), text, font=adjusted_font)
            ttw, tth = test_bbox[2] - test_bbox[0], test_bbox[3] - test_bbox[1]
            rot_w = abs(ttw * math.cos(rad)) + abs(tth * math.sin(rad))
            rot_h = abs(ttw * math.sin(rad)) + abs(tth * math.cos(rad))
            if rot_w <= max_w and rot_h <= max_h:
                break
            new_size = int(adjusted_font.size * min(max_w / rot_w, max_h / rot_h))
            if new_size < 10:
                break
            adjusted_font = _find_korean_font(new_size)

        bbox2 = ImageDraw.Draw(overlay).textbbox((0, 0), text, font=adjusted_font)
        tw2, th2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
        txt_img = Image.new("RGBA", (tw2 + 40, th2 + 40), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        txt_draw.text((20, 20), text, font=adjusted_font, fill=fill)
        txt_rotated = txt_img.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
        rw, rh = txt_rotated.size
        overlay.paste(txt_rotated, ((w - rw) // 2, (h - rh) // 2), txt_rotated)


# ─── PDF 워터마크 (reportlab으로 투명 오버레이 생성) ───

def watermark_pdf(
    pdf_data: bytes,
    text: str = "보보쌤 | byhur99",
    opacity: float = 0.15,
    position: str = "diagonal-tiled",
    font_size: int = 50,
    color: tuple[int, int, int] = (128, 128, 128),
    rotation: int = 30,
) -> bytes:
    """PDF 각 페이지에 투명 워터마크 삽입 (원본 보존)."""
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.colors import Color

    font_name = _get_reportlab_font()

    reader = PdfReader(io.BytesIO(pdf_data))
    writer = PdfWriter()

    r_f, g_f, b_f = color[0] / 255, color[1] / 255, color[2] / 255
    fill_color = Color(r_f, g_f, b_f, alpha=opacity)

    for page in reader.pages:
        media = page.mediabox
        pw = float(media.width)
        ph = float(media.height)

        # reportlab으로 투명 워터마크 PDF 페이지 생성
        wm_buf = io.BytesIO()
        c = rl_canvas.Canvas(wm_buf, pagesize=(pw, ph))
        c.setFillColor(fill_color)
        c.setFont(font_name, font_size)

        if position == "diagonal-tiled":
            text_w = c.stringWidth(text, font_name, font_size)
            sp_x = int(text_w + 60)
            sp_y = int(font_size + 80)
            for y in range(-int(ph), int(ph) * 2, sp_y):
                for x in range(-int(pw), int(pw) * 2, sp_x):
                    c.saveState()
                    c.translate(x, y)
                    c.rotate(rotation)
                    c.drawString(0, 0, text)
                    c.restoreState()

        elif position == "diagonal-single":
            c.saveState()
            c.translate(pw / 2, ph / 2)
            c.rotate(rotation)
            c.drawCentredString(0, 0, text)
            c.restoreState()

        elif position == "center":
            c.drawCentredString(pw / 2, ph / 2, text)

        elif position == "bottom-right":
            text_w = c.stringWidth(text, font_name, font_size)
            c.drawString(pw - text_w - 30, 30, text)

        elif position == "bottom-left":
            c.drawString(30, 30, text)

        elif position == "top-right":
            text_w = c.stringWidth(text, font_name, font_size)
            c.drawString(pw - text_w - 30, ph - font_size - 30, text)

        elif position == "top-left":
            c.drawString(30, ph - font_size - 30, text)

        c.save()
        wm_buf.seek(0)

        # 투명 워터마크 PDF를 원본 위에 오버레이
        wm_reader = PdfReader(wm_buf)
        wm_page = wm_reader.pages[0]
        page.merge_page(wm_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
