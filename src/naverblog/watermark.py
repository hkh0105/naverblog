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


# ─── 이미지 워터마크 ───

def watermark_image(
    image_data: bytes,
    text: str = "보보쌤 | byhur99",
    opacity: int = 80,
    position: str = "bottom-right",
) -> bytes:
    """이미지에 텍스트 워터마크 삽입.

    Args:
        image_data: 원본 이미지 바이트
        text: 워터마크 텍스트
        opacity: 불투명도 (0~255)
        position: 위치 (bottom-right, bottom-left, center)

    Returns:
        워터마크가 적용된 이미지 바이트 (PNG)
    """
    img = Image.open(io.BytesIO(image_data)).convert("RGBA")
    w, h = img.size

    # 폰트 크기: 이미지 너비 기준
    font_size = max(16, w // 30)
    font = _find_korean_font(font_size)

    # 워터마크 레이어
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    margin = max(10, w // 50)
    if position == "bottom-right":
        x, y = w - tw - margin, h - th - margin
    elif position == "bottom-left":
        x, y = margin, h - th - margin
    elif position == "center":
        x, y = (w - tw) // 2, (h - th) // 2
    else:
        x, y = w - tw - margin, h - th - margin

    # 배경 박스 (가독성)
    pad = max(4, font_size // 6)
    draw.rounded_rectangle(
        [x - pad, y - pad, x + tw + pad, y + th + pad],
        radius=pad,
        fill=(0, 0, 0, opacity // 2),
    )
    # 텍스트
    draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))

    result = Image.alpha_composite(img, overlay).convert("RGB")

    buf = io.BytesIO()
    result.save(buf, format="PNG", quality=95)
    return buf.getvalue()


# ─── PDF 워터마크 ───

def watermark_pdf(
    pdf_data: bytes,
    text: str = "보보쌤 | byhur99",
    opacity: float = 0.15,
    font_size: int = 60,
) -> bytes:
    """PDF 각 페이지에 대각선 텍스트 워터마크 삽입.

    Args:
        pdf_data: 원본 PDF 바이트
        text: 워터마크 텍스트
        opacity: 불투명도 (0.0~1.0)
        font_size: 폰트 크기

    Returns:
        워터마크가 적용된 PDF 바이트
    """
    from pypdf import PdfReader, PdfWriter

    # 워터마크 이미지를 각 페이지 크기에 맞게 생성
    reader = PdfReader(io.BytesIO(pdf_data))
    writer = PdfWriter()

    for page in reader.pages:
        # 페이지 크기
        media = page.mediabox
        pw = float(media.width)
        ph = float(media.height)

        # 워터마크 이미지 생성 (투명 배경)
        scale = 3  # 해상도 배율
        img_w, img_h = int(pw * scale), int(ph * scale)
        wm_img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(wm_img)

        font = _find_korean_font(font_size * scale)
        alpha = int(255 * opacity)

        # 대각선 반복 패턴
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        spacing_x = tw + 100 * scale
        spacing_y = th + 150 * scale

        for yi in range(-img_h, img_h * 2, spacing_y):
            for xi in range(-img_w, img_w * 2, spacing_x):
                # 회전된 텍스트를 위한 임시 이미지
                txt_img = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
                txt_draw = ImageDraw.Draw(txt_img)
                txt_draw.text((10, 10), text, font=font, fill=(128, 128, 128, alpha))
                txt_rotated = txt_img.rotate(30, expand=True, fillcolor=(0, 0, 0, 0))

                if 0 <= xi < img_w and 0 <= yi < img_h:
                    wm_img.paste(txt_rotated, (xi, yi), txt_rotated)

        # 워터마크 이미지를 PDF 페이지에 합성
        wm_img_rgb = wm_img.convert("RGB")
        wm_pdf_buf = io.BytesIO()
        wm_img_rgb.save(wm_pdf_buf, format="PDF", resolution=72 * scale)
        wm_pdf_buf.seek(0)

        wm_reader = PdfReader(wm_pdf_buf)
        wm_page = wm_reader.pages[0]

        # 원본 위에 워터마크 오버레이
        page.merge_page(wm_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
