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
]


def _find_korean_font(size: int = 24) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """한국어 지원 폰트 탐색."""
    for path in _FONT_SEARCH_PATHS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """#RRGGBB → (R, G, B)."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


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
    """이미지에 텍스트 워터마크 삽입.

    Args:
        image_data: 원본 이미지 바이트
        text: 워터마크 텍스트 (줄바꿈 지원)
        opacity: 불투명도 (0~255)
        position: bottom-right, bottom-left, center, diagonal-single, diagonal-tiled
        font_size: 폰트 크기 (0이면 이미지 크기에 맞게 자동 계산)
        color: (R, G, B) 텍스트 색상
        rotation: 대각선 회전 각도 (degrees)
        bg_box: 코너/중앙 모드에서 배경 박스 표시 여부

    Returns:
        워터마크가 적용된 이미지 바이트 (PNG)
    """
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
    w, h = overlay.size

    # 텍스트 크기 측정
    tmp = ImageDraw.Draw(overlay)
    bbox = tmp.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if tiled:
        spacing_x = tw + 80
        spacing_y = th + 120
        for yi in range(-h, h * 2, spacing_y):
            for xi in range(-w, w * 2, spacing_x):
                txt_img = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
                txt_draw = ImageDraw.Draw(txt_img)
                txt_draw.text((10, 10), text, font=font, fill=fill)
                txt_rotated = txt_img.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
                if 0 <= xi < w and 0 <= yi < h:
                    overlay.paste(txt_rotated, (xi, yi), txt_rotated)
    else:
        # 1줄 대각선 - 이미지 중앙에 큰 텍스트 하나
        txt_img = Image.new("RGBA", (tw + 40, th + 40), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        txt_draw.text((20, 20), text, font=font, fill=fill)
        txt_rotated = txt_img.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
        rw, rh = txt_rotated.size
        x = (w - rw) // 2
        y = (h - rh) // 2
        overlay.paste(txt_rotated, (x, y), txt_rotated)


# ─── PDF 워터마크 ───

def watermark_pdf(
    pdf_data: bytes,
    text: str = "보보쌤 | byhur99",
    opacity: float = 0.15,
    position: str = "diagonal-tiled",
    font_size: int = 50,
    color: tuple[int, int, int] = (128, 128, 128),
    rotation: int = 30,
) -> bytes:
    """PDF 각 페이지에 워터마크 삽입.

    Args:
        pdf_data: 원본 PDF 바이트
        text: 워터마크 텍스트
        opacity: 불투명도 (0.0~1.0)
        position: diagonal-tiled, diagonal-single, bottom-right, bottom-left, center, top-right, top-left
        font_size: 폰트 크기
        color: (R, G, B) 텍스트 색상
        rotation: 대각선 회전 각도

    Returns:
        워터마크가 적용된 PDF 바이트
    """
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(io.BytesIO(pdf_data))
    writer = PdfWriter()

    for page in reader.pages:
        media = page.mediabox
        pw = float(media.width)
        ph = float(media.height)

        scale = 3
        img_w, img_h = int(pw * scale), int(ph * scale)
        wm_img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))

        font = _find_korean_font(font_size * scale)
        alpha = int(255 * opacity)
        r, g, b = color
        fill = (r, g, b, alpha)

        if position in ("diagonal-tiled", "diagonal-single"):
            _draw_diagonal(wm_img, text, font, fill, rotation, position == "diagonal-tiled")
        else:
            draw = ImageDraw.Draw(wm_img)
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = 30 * scale

            if position == "bottom-right":
                x, y = img_w - tw - margin, img_h - th - margin
            elif position == "bottom-left":
                x, y = margin, img_h - th - margin
            elif position == "top-right":
                x, y = img_w - tw - margin, margin
            elif position == "top-left":
                x, y = margin, margin
            else:  # center
                x, y = (img_w - tw) // 2, (img_h - th) // 2

            draw.text((x, y), text, font=font, fill=fill)

        # 워터마크 이미지를 PDF로 변환
        wm_img_rgb = wm_img.convert("RGB")
        wm_pdf_buf = io.BytesIO()
        wm_img_rgb.save(wm_pdf_buf, format="PDF", resolution=72 * scale)
        wm_pdf_buf.seek(0)

        wm_reader = PdfReader(wm_pdf_buf)
        wm_page = wm_reader.pages[0]
        page.merge_page(wm_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
