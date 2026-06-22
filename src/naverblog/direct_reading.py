"""PDF 기반 영어 지문 직독직해 자료 생성 유틸리티."""

from __future__ import annotations

import io
import re
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


@dataclass
class PdfText:
    """업로드된 PDF에서 추출한 텍스트."""

    label: str
    text: str
    page_count: int


PALETTE = {
    "ink": (28, 33, 40),
    "muted": (91, 101, 114),
    "line": (209, 218, 228),
    "paper": (252, 253, 249),
    "soft": (232, 241, 238),
    "soft_green": (239, 248, 244),
    "soft_blue": (239, 246, 255),
    "teal": (15, 118, 110),
    "coral": (200, 90, 58),
    "gold": (242, 166, 90),
    "blue": (38, 93, 150),
    "green": (35, 126, 106),
    "white": (255, 255, 255),
}


def extract_pdf_text(
    pdf_bytes: bytes,
    label: str,
    page_start: int | None = None,
    page_end: int | None = None,
    max_chars: int = 80_000,
) -> PdfText:
    """PDF 바이트에서 텍스트를 추출한다. page_start/page_end는 1-indexed."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)

    start_idx = max((page_start or 1) - 1, 0)
    end_idx = min(page_end or total_pages, total_pages)
    chunks: list[str] = []

    for page_no in range(start_idx, end_idx):
        page_text = reader.pages[page_no].extract_text() or ""
        page_text = _normalize_extracted_text(page_text)
        if page_text:
            chunks.append(f"[페이지 {page_no + 1}]\n{page_text}")
        if sum(len(chunk) for chunk in chunks) >= max_chars:
            chunks.append("\n[알림] 텍스트가 길어 여기서 일부만 사용했습니다.")
            break

    return PdfText(label=label, text="\n\n".join(chunks)[:max_chars], page_count=total_pages)


def _normalize_extracted_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_direct_reading_prompts(
    sources: list[PdfText],
    question_start: int,
    question_end: int,
    target_questions: str = "",
    extra_instructions: str = "",
) -> tuple[str, str]:
    """LLM에 전달할 직독직해 생성 프롬프트를 만든다."""
    target = target_questions.strip()
    target_desc = (
        f"특정 문항만 작성: {target}"
        if target
        else f"{question_start}번부터 {question_end}번까지 모든 영어 지문 문항 작성"
    )
    source_blocks = "\n\n".join(
        f"## PDF: {source.label}\n총 {source.page_count}쪽\n\n{source.text}"
        for source in sources
    )

    system_prompt = (
        "당신은 한국 고등학생용 영어 모의고사 지문을 문장별 직독직해 자료로 만드는 전문 교사입니다. "
        "제공된 PDF 추출 텍스트에 근거해서만 작성하고, 없는 문항은 없다고 표시합니다."
    )
    user_prompt = f"""아래 PDF 추출 텍스트를 바탕으로 직독직해 자료를 Markdown으로 작성하세요.

작업 범위:
- 문항 범위: {question_start}-{question_end}번
- {target_desc}

출력 형식은 반드시 아래 구조를 따르세요.

# {question_start}-{question_end}번 지문 직독직해

PDF 자료 기반 문장별 직독직해 정리

---

## PDF 파일명 또는 시험명

### 34번

English sentence chunk 1 / English sentence chunk 2 / English sentence chunk 3.
* 영어 청크 1의 직독직해 / 영어 청크 2의 직독직해 / 영어 청크 3의 직독직해.

규칙:
- 각 영어 문장은 의미 단위마다 " / "로 끊으세요.
- 바로 다음 줄에는 "* "로 시작하는 한국어 직독직해를 쓰세요.
- 한국어도 영어 청크 순서에 맞춰 " / "로 나누세요.
- 선택지, 안내문, 광고 문구, 저작권 문구는 제외하고 영어 지문 본문만 처리하세요.
- 표/도표 문항은 본문 문장이 있으면 처리하고, 문장형 본문이 없으면 짧게 제외 이유를 쓰세요.
- 문항을 찾지 못하면 "### N번" 아래에 "* PDF 추출 텍스트에서 해당 문항을 찾지 못했습니다."라고 쓰세요.
- 추측으로 지문을 새로 만들지 마세요.
- 답변에는 Markdown 본문만 출력하세요.

추가 지시:
{extra_instructions.strip() or "- 없음"}

PDF 추출 텍스트:

{source_blocks}
"""
    return system_prompt, user_prompt


def clean_markdown_response(markdown_text: str) -> str:
    """LLM이 Markdown 코드펜스로 감싼 경우 본문만 남긴다."""
    text = markdown_text.strip()
    fence_match = re.fullmatch(r"```(?:markdown|md)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()
    return text


def render_markdown_to_images(markdown_text: str) -> list[Image.Image]:
    """직독직해 Markdown을 PNG 페이지 이미지로 렌더링한다."""
    page_w, page_h = 1654, 2339
    margin_x = 92
    bottom_margin = 96
    content_w = page_w - margin_x * 2

    pages: list[Image.Image] = []
    image, draw, y = _new_page(page_w, page_h, page_no=1)

    def ensure_space(required: int) -> None:
        nonlocal image, draw, y
        if y + required <= page_h - bottom_margin:
            return
        _draw_footer(draw, page_w, page_h, len(pages) + 1)
        pages.append(image)
        image, draw, y = _new_page(page_w, page_h, page_no=len(pages) + 1)

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            y += 18
            continue

        if line.strip() == "---":
            ensure_space(42)
            draw.line((margin_x, y + 14, page_w - margin_x, y + 14), fill=PALETTE["line"], width=3)
            y += 42
            continue

        if line.startswith("# "):
            title = line[2:].strip()
            ensure_space(110)
            draw.text((margin_x, y), title, font=_font(44, bold=True), fill=PALETTE["ink"])
            y += 70
            continue

        if line.startswith("## "):
            section = line[3:].strip()
            ensure_space(82)
            draw.rounded_rectangle(
                (margin_x, y, page_w - margin_x, y + 58),
                radius=16,
                fill=PALETTE["teal"],
            )
            draw.text((margin_x + 26, y + 14), section, font=_font(25, bold=True), fill=PALETTE["white"])
            y += 82
            continue

        if line.startswith("### "):
            question = line[4:].strip()
            ensure_space(68)
            draw.rounded_rectangle(
                (margin_x, y, margin_x + 170, y + 48),
                radius=24,
                fill=PALETTE["soft_blue"],
                outline=PALETTE["blue"],
                width=2,
            )
            draw.text((margin_x + 28, y + 10), question, font=_font(25, bold=True), fill=PALETTE["blue"])
            y += 66
            continue

        is_translation = line.lstrip().startswith("* ")
        text = line.lstrip()[2:].strip() if is_translation else line.strip()
        font = _font(24 if is_translation else 26, bold=False)
        fill = PALETTE["green"] if is_translation else PALETTE["ink"]
        box_fill = PALETTE["soft_green"] if is_translation else PALETTE["white"]
        left_pad = 30 if is_translation else 24
        line_gap = 9 if is_translation else 10
        lines = _wrapped_lines(draw, text, font, content_w - left_pad * 2)
        box_h = max(58, len(lines) * (_line_height(draw, font) + line_gap) + 28)
        ensure_space(box_h + 18)

        draw.rounded_rectangle(
            (margin_x, y, page_w - margin_x, y + box_h),
            radius=14,
            fill=box_fill,
            outline=PALETTE["line"],
            width=1,
        )
        text_y = y + 16
        if is_translation:
            draw.text((margin_x + 18, text_y + 1), "*", font=_font(24, bold=True), fill=PALETTE["green"])
        for wrapped in lines:
            draw.text((margin_x + left_pad, text_y), wrapped, font=font, fill=fill)
            text_y += _line_height(draw, font) + line_gap
        y += box_h + 18

    _draw_footer(draw, page_w, page_h, len(pages) + 1)
    pages.append(image)
    return pages


def images_to_pdf_bytes(images: list[Image.Image]) -> bytes:
    """이미지 페이지들을 PDF 바이트로 변환한다."""
    if not images:
        raise ValueError("PDF로 변환할 이미지가 없습니다.")
    buf = io.BytesIO()
    rgb_images = [img.convert("RGB") for img in images]
    rgb_images[0].save(
        buf,
        format="PDF",
        resolution=150.0,
        save_all=True,
        append_images=rgb_images[1:],
    )
    return buf.getvalue()


def images_to_zip_bytes(images: list[Image.Image], basename: str = "direct_reading") -> bytes:
    """PNG 이미지들을 ZIP 바이트로 묶는다."""
    buf = io.BytesIO()
    safe_name = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", basename).strip("_") or "direct_reading"
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for idx, image in enumerate(images, 1):
            png = io.BytesIO()
            image.save(png, format="PNG")
            zf.writestr(f"{safe_name}_{idx:02d}.png", png.getvalue())
    return buf.getvalue()


def _new_page(page_w: int, page_h: int, page_no: int) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    image = Image.new("RGB", (page_w, page_h), PALETTE["paper"])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, page_w, 170), fill=PALETTE["soft"])
    draw.text((92, 48), "직독직해 파일", font=_font(42, bold=True), fill=PALETTE["ink"])
    draw.text(
        (94, 108),
        "PDF 자료 기반 문장별 영어 독해 정리",
        font=_font(21),
        fill=PALETTE["muted"],
    )
    draw.rounded_rectangle((page_w - 265, 54, page_w - 92, 112), radius=29, fill=PALETTE["white"])
    draw.text((page_w - 224, 70), f"PAGE {page_no}", font=_font(20, bold=True), fill=PALETTE["teal"])
    draw.line((92, 154, page_w - 92, 154), fill=(191, 207, 207), width=2)
    return image, draw, 210


def _draw_footer(draw: ImageDraw.ImageDraw, page_w: int, page_h: int, page_no: int) -> None:
    draw.line((92, page_h - 74, page_w - 92, page_h - 74), fill=PALETTE["line"], width=1)
    draw.text((92, page_h - 50), "보보쌤 직독직해 자료", font=_font(17), fill=PALETTE["muted"])
    draw.text((page_w - 154, page_h - 50), str(page_no), font=_font(17, bold=True), fill=PALETTE["muted"])


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    root = Path(__file__).resolve().parents[2]
    candidates = [
        root / "assets" / "fonts" / "NotoSansKR.ttf",
        Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size, index=1 if bold and path.suffix == ".ttc" else 0)
            except Exception:
                try:
                    return ImageFont.truetype(str(path), size=size)
                except Exception:
                    continue
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _line_height(draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont) -> int:
    return _text_size(draw, "Ag가", font)[1]


def _wrapped_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        tokens = paragraph.split(" ")
        line = ""
        for token in tokens:
            candidate = token if not line else f"{line} {token}"
            if _text_size(draw, candidate, font)[0] <= max_width:
                line = candidate
                continue
            if line:
                lines.append(line)
            if _text_size(draw, token, font)[0] <= max_width:
                line = token
            else:
                pieces = _break_long_token(draw, token, font, max_width)
                lines.extend(pieces[:-1])
                line = pieces[-1] if pieces else ""
        if line:
            lines.append(line)
    return lines


def _break_long_token(
    draw: ImageDraw.ImageDraw,
    token: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    if len(token) > 28 and re.fullmatch(r"[A-Za-z0-9_/.,;:'\"()\\-]+", token):
        rough = max(8, int(max_width / max(_text_size(draw, "m", font)[0], 1)))
        return textwrap.wrap(token, width=rough)

    pieces: list[str] = []
    current = ""
    for char in token:
        candidate = current + char
        if _text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
        else:
            if current:
                pieces.append(current)
            current = char
    if current:
        pieces.append(current)
    return pieces
