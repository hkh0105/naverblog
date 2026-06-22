"""PDF 기반 영어 단어 테스트/답지 이미지 생성 유틸리티."""

from __future__ import annotations

import io
import json
import math
import re
import zipfile
from dataclasses import dataclass
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from naverblog.direct_reading import (
    PALETTE,
    PdfText,
    _font,
    _line_height,
    _text_size,
    _wrapped_lines,
)


@dataclass
class VocabularySourceSpec:
    """PDF별 단어장 생성 설정."""

    label: str
    display_title: str
    word_count: int
    phrase_count: int
    sentence_count: int
    difficulty: str


def build_vocabulary_prompts(
    sources: list[PdfText],
    specs: list[VocabularySourceSpec],
    question_start: int = 18,
    question_end: int = 45,
    extra_instructions: str = "",
) -> tuple[str, str]:
    """단어 테스트 JSON 생성을 위한 LLM 프롬프트를 만든다."""
    spec_by_label = {spec.label: spec for spec in specs}
    source_blocks = []
    for source in sources:
        spec = spec_by_label[source.label]
        title = spec.display_title.strip() or source.label
        source_blocks.append(
            f"""## PDF: {source.label}
표시 제목: {title}
설정:
- 단어/표현 문항 수: {spec.word_count}
- 동사구/숙어/구절 최소 포함 수: {spec.phrase_count}
- 문장 해석 문항 수: {spec.sentence_count}
- 난이도: {spec.difficulty}
- 문항 범위: {question_start}-{question_end}번

추출 텍스트:
{source.text}
"""
        )

    system_prompt = (
        "당신은 한국 고등학생용 영어 모의고사 어휘 테스트를 만드는 전문 영어 교사입니다. "
        "PDF 추출 텍스트에 실제로 있는 지문과 표현만 사용하고, 쉬운 단어보다 해석에 영향을 주는 난도 있는 어휘, "
        "동사구, 숙어, 구절을 우선 선별합니다. 출력은 반드시 유효한 JSON만 반환합니다."
    )
    user_prompt = f"""아래 PDF 추출 텍스트를 바탕으로 영어 단어 테스트와 답지를 만들 JSON을 작성하세요.

핵심 목표:
- PDF별 설정된 개수만큼 단어/표현을 선별합니다.
- 각 PDF의 단어/표현 문항 안에 동사구, 숙어, 구절을 최소 설정 개수 이상 포함합니다.
- 해석하면 좋을 난도 있는 문장도 PDF별 설정 개수만큼 고릅니다.
- 문장 문항은 직독직해 chunks를 반드시 포함합니다.

선별 기준:
- 단순한 초급 단어보다 지문 해석에 결정적인 고급 어휘, 추상 명사, 학술 어휘, 동사구, 숙어, 전치사구, 구문 표현을 우선합니다.
- 보기/선택지/듣기 안내문/저작권 문구는 제외하고 {question_start}-{question_end}번 독해 지문 본문에서 고릅니다.
- PDF에 없는 내용을 만들지 마세요.

반환 JSON 스키마:
{{
  "title": "영어 단어 테스트",
  "subtitle": "PDF 자료 기반 난도 높은 어휘와 표현",
  "sources": [
    {{
      "title": "PDF 파일명 또는 시험명",
      "items": [
        {{
          "term": "영어 단어 또는 표현",
          "meaning": "한국어 뜻",
          "kind": "word 또는 phrase",
          "source_question": "34번"
        }}
      ]
    }}
  ],
  "sentences": [
    {{
      "source": "PDF 파일명 또는 시험명",
      "source_question": "34번",
      "sentence": "원문 영어 문장",
      "chunks": [
        {{"en": "English chunk", "ko": "한국어 직독직해"}}
      ],
      "translation": "자연스러운 전체 해석"
    }}
  ]
}}

규칙:
- JSON 외의 설명, Markdown 코드펜스, 주석을 붙이지 마세요.
- items 개수는 PDF별 설정과 정확히 맞추세요.
- kind가 "phrase"인 항목은 동사구/숙어/구절입니다.
- sources[].title과 sentences[].source는 반드시 각 PDF의 "표시 제목"을 그대로 쓰세요.
- chunks는 영어 문장의 순서대로 의미 단위를 끊고, 한국어도 같은 순서로 대응시킵니다.
- source_question은 알 수 있으면 "34번"처럼 쓰고, 불명확하면 빈 문자열로 둡니다.

추가 지시:
{extra_instructions.strip() or "- 없음"}

PDF 추출 텍스트:

{chr(10).join(source_blocks)}
"""
    return system_prompt, user_prompt


def parse_vocabulary_json(raw_text: str) -> dict[str, Any]:
    """LLM JSON 응답을 파싱하고 렌더러가 기대하는 기본 구조로 보정한다."""
    text = raw_text.strip()
    fence_match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

    data = json.loads(text)
    data.setdefault("title", "영어 단어 테스트")
    data.setdefault("subtitle", "PDF 자료 기반 난도 높은 어휘와 표현")
    data.setdefault("sources", [])
    data.setdefault("sentences", [])

    normalized_sources = []
    for source in data["sources"]:
        items = []
        for item in source.get("items", []):
            term = str(item.get("term", "")).strip()
            meaning = str(item.get("meaning", "")).strip()
            if not term or not meaning:
                continue
            kind = str(item.get("kind", "word")).strip().lower()
            items.append(
                {
                    "term": term,
                    "meaning": meaning,
                    "kind": "phrase" if kind == "phrase" else "word",
                    "source_question": str(item.get("source_question", "")).strip(),
                }
            )
        if items:
            normalized_sources.append(
                {
                    "title": str(source.get("title", "PDF 자료")).strip() or "PDF 자료",
                    "items": items,
                }
            )
    data["sources"] = normalized_sources

    normalized_sentences = []
    for sentence in data["sentences"]:
        text_sentence = str(sentence.get("sentence", "")).strip()
        chunks = sentence.get("chunks", [])
        if not text_sentence or not chunks:
            continue
        normalized_chunks = []
        for chunk in chunks:
            en = str(chunk.get("en", "")).strip()
            ko = str(chunk.get("ko", "")).strip()
            if en and ko:
                normalized_chunks.append({"en": en, "ko": ko})
        if not normalized_chunks:
            continue
        normalized_sentences.append(
            {
                "source": str(sentence.get("source", "PDF 자료")).strip() or "PDF 자료",
                "source_question": str(sentence.get("source_question", "")).strip(),
                "sentence": text_sentence,
                "chunks": normalized_chunks,
                "translation": str(sentence.get("translation", "")).strip(),
            }
        )
    data["sentences"] = normalized_sentences
    return data


def render_vocabulary_test_images(data: dict[str, Any]) -> list[Image.Image]:
    """단어 테스트지를 이미지 페이지로 렌더링한다."""
    ctx = _CanvasContext("영어 단어 테스트", data.get("subtitle", "난도 높은 어휘와 표현"))
    draw = ctx.draw

    ctx.draw_main_title(data.get("title", "영어 단어 테스트"), "뜻을 쓰고, 아래 문장을 자연스럽게 해석하세요.")
    no = 1
    colors = [PALETTE["blue"], PALETTE["green"], PALETTE["coral"], PALETTE["gold"]]

    for source_idx, source in enumerate(data.get("sources", [])):
        items = source.get("items", [])
        if not items:
            continue
        color = colors[source_idx % len(colors)]
        chunks = _chunk_items_for_test(items, max_items=16)
        for chunk_idx, chunk in enumerate(chunks):
            no = _draw_vocab_test_section(
                ctx=ctx,
                title=source.get("title", "PDF 자료"),
                items=chunk,
                color=color,
                start_no=no,
                continued=chunk_idx > 0,
            )

    sentences = data.get("sentences", [])
    draw = ctx.draw
    if sentences:
        first_lines = _wrapped_lines(draw, sentences[0]["sentence"], _font(23), ctx.content_w - 60)
        first_box_h = 88 + len(first_lines) * 35 + 108
        ctx.ensure(74 + first_box_h + 22)
        draw = ctx.draw
        draw.text((ctx.margin_x, ctx.y), "문장 해석", font=_font(35, bold=True), fill=PALETTE["ink"])
        draw.text((ctx.margin_x + 190, ctx.y + 10), "난도 있는 문장을 자연스럽게 해석하세요.", font=_font(20), fill=PALETTE["muted"])
        ctx.y += 74

    for idx, sentence in enumerate(sentences, 1):
        source = sentence.get("source", "")
        q = sentence.get("source_question", "")
        label = f"{idx}. {source}" + (f" · {q}" if q else "")
        sentence_lines = _wrapped_lines(draw, sentence["sentence"], _font(23), ctx.content_w - 60)
        box_h = 88 + len(sentence_lines) * 35 + 108
        ctx.ensure(box_h + 22)
        draw = ctx.draw
        x0, y0, x1 = ctx.margin_x, ctx.y, ctx.page_w - ctx.margin_x
        draw.rounded_rectangle((x0, y0, x1, y0 + box_h), radius=16, fill=PALETTE["white"], outline=PALETTE["line"], width=2)
        draw.text((x0 + 28, y0 + 22), label, font=_font(21, bold=True), fill=PALETTE["blue"])
        text_y = y0 + 64
        for line in sentence_lines:
            draw.text((x0 + 30, text_y), line, font=_font(23), fill=PALETTE["ink"])
            text_y += 35
        line_y = y0 + box_h - 82
        draw.line((x0 + 30, line_y, x1 - 30, line_y), fill=(190, 198, 207), width=2)
        draw.line((x0 + 30, line_y + 46, x1 - 30, line_y + 46), fill=(215, 221, 228), width=1)
        ctx.y += box_h + 24

    return ctx.finish()


def render_vocabulary_answer_images(data: dict[str, Any]) -> list[Image.Image]:
    """단어 테스트 답지를 이미지 페이지로 렌더링한다."""
    ctx = _CanvasContext("영어 단어 테스트 답지", "어휘 뜻 + 문장 직독직해 해설")
    draw = ctx.draw
    ctx.draw_main_title("영어 단어 테스트 답지", "선별 어휘 뜻과 문장 직독직해")

    no = 1
    colors = [PALETTE["blue"], PALETTE["green"], PALETTE["coral"], PALETTE["gold"]]
    for source_idx, source in enumerate(data.get("sources", [])):
        items = source.get("items", [])
        if not items:
            continue
        color = colors[source_idx % len(colors)]
        ctx.ensure(74)
        draw = ctx.draw
        x0, x1 = ctx.margin_x, ctx.page_w - ctx.margin_x
        draw.rounded_rectangle((x0, ctx.y, x1, ctx.y + 54), radius=16, fill=color)
        draw.text((x0 + 26, ctx.y + 14), _short_label(source.get("title", "PDF 자료")), font=_font(23, bold=True), fill=PALETTE["white"])
        draw.text((x0 + 610, ctx.y + 15), "어휘 / 표현", font=_font(20, bold=True), fill=PALETTE["white"])
        draw.text((x0 + 1030, ctx.y + 15), "뜻", font=_font(20, bold=True), fill=PALETTE["white"])
        ctx.y += 54

        for item in items:
            term_lines = _wrapped_lines(draw, item["term"], _font(21, bold=True), 430)
            meaning_lines = _wrapped_lines(draw, item["meaning"], _font(21), 650)
            row_h = max(54, max(len(term_lines), len(meaning_lines)) * 31 + 22)
            ctx.ensure(row_h)
            draw = ctx.draw
            y0 = ctx.y
            fill = (255, 255, 255) if no % 2 else (248, 251, 250)
            draw.rectangle((x0, y0, x1, y0 + row_h), fill=fill)
            draw.line((x0, y0, x1, y0), fill=(229, 234, 239), width=1)
            draw.text((x0 + 24, y0 + 15), f"{no:02d}", font=_font(20, bold=True), fill=color)
            badge = "표현" if item.get("kind") == "phrase" else "단어"
            draw.text((x0 + 88, y0 + 15), badge, font=_font(17, bold=True), fill=PALETTE["muted"])
            _draw_lines(draw, term_lines, x0 + 190, y0 + 13, _font(21, bold=True), PALETTE["ink"], 31)
            _draw_lines(draw, meaning_lines, x0 + 700, y0 + 13, _font(21), PALETTE["ink"], 31)
            ctx.y += row_h
            no += 1
        ctx.y += 32

    sentences = data.get("sentences", [])
    if sentences:
        ctx.ensure(80)
        draw = ctx.draw
        draw.text((ctx.margin_x, ctx.y), "문장 직독직해", font=_font(35, bold=True), fill=PALETTE["ink"])
        ctx.y += 62

    for idx, sentence in enumerate(sentences, 1):
        source = sentence.get("source", "")
        q = sentence.get("source_question", "")
        label = f"{idx}. {source}" + (f" · {q}" if q else "")
        sent_lines = _wrapped_lines(draw, sentence["sentence"], _font(22), ctx.content_w - 60)
        chunk_lines = []
        for chunk in sentence.get("chunks", []):
            en_lines = _wrapped_lines(draw, f"/ {chunk['en']}", _font(20), 650)
            ko_lines = _wrapped_lines(draw, f"-> {chunk['ko']}", _font(20), 650)
            chunk_lines.append((en_lines, ko_lines))
        trans_lines = _wrapped_lines(draw, sentence.get("translation", ""), _font(20), ctx.content_w - 310)
        box_h = 76 + len(sent_lines) * 34 + 24
        box_h += sum(max(len(en), len(ko)) * 30 + 12 for en, ko in chunk_lines)
        box_h += 58 + len(trans_lines) * 30
        ctx.ensure(box_h + 28)
        draw = ctx.draw

        x0, y0, x1 = ctx.margin_x, ctx.y, ctx.page_w - ctx.margin_x
        draw.rounded_rectangle((x0, y0, x1, y0 + box_h), radius=16, fill=PALETTE["white"], outline=PALETTE["line"], width=2)
        draw.text((x0 + 30, y0 + 24), label, font=_font(22, bold=True), fill=PALETTE["blue"])
        y = y0 + 66
        _draw_lines(draw, sent_lines, x0 + 30, y, _font(22), PALETTE["ink"], 34)
        y += len(sent_lines) * 34 + 18
        draw.line((x0 + 30, y, x1 - 30, y), fill=(220, 226, 232), width=2)
        y += 20
        for en_lines, ko_lines in chunk_lines:
            _draw_lines(draw, en_lines, x0 + 46, y, _font(20), PALETTE["ink"], 30)
            _draw_lines(draw, ko_lines, x0 + 790, y, _font(20), PALETTE["muted"], 30)
            y += max(len(en_lines), len(ko_lines)) * 30 + 12
        if trans_lines:
            draw.text((x0 + 46, y + 13), "자연스러운 해석", font=_font(20, bold=True), fill=PALETTE["green"])
            _draw_lines(draw, trans_lines, x0 + 245, y + 12, _font(20), PALETTE["ink"], 30)
        ctx.y += box_h + 30

    return ctx.finish()


def vocabulary_images_to_zip_bytes(
    test_images: list[Image.Image],
    answer_images: list[Image.Image],
) -> bytes:
    """시험지/답지 PNG 이미지를 하나의 ZIP으로 묶는다."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for idx, image in enumerate(test_images, 1):
            png = io.BytesIO()
            image.save(png, format="PNG")
            zf.writestr(f"vocab_test_{idx:02d}.png", png.getvalue())
        for idx, image in enumerate(answer_images, 1):
            png = io.BytesIO()
            image.save(png, format="PNG")
            zf.writestr(f"vocab_answer_{idx:02d}.png", png.getvalue())
    return buf.getvalue()


def _chunk_items_for_test(items: list[dict[str, Any]], max_items: int) -> list[list[dict[str, Any]]]:
    return [items[idx : idx + max_items] for idx in range(0, len(items), max_items)]


def _draw_vocab_test_section(
    ctx: "_CanvasContext",
    title: str,
    items: list[dict[str, Any]],
    color: tuple[int, int, int],
    start_no: int,
    continued: bool = False,
) -> int:
    """긴 표현이 겹치지 않도록 단어 테스트 섹션을 동적 행 높이로 그린다."""
    draw = ctx.draw
    x0, x1 = ctx.margin_x, ctx.page_w - ctx.margin_x
    col_gap = 34
    inner_pad = 28
    col_w = (x1 - x0 - inner_pad * 2 - col_gap) // 2
    rows = math.ceil(len(items) / 2)
    term_font = _font(22, bold=True)
    no_font = _font(20, bold=True)
    badge_font = _font(14, bold=True)

    row_heights: list[int] = []
    for row in range(rows):
        row_items = [items[row]]
        second_idx = row + rows
        if second_idx < len(items):
            row_items.append(items[second_idx])
        max_lines = 1
        for item in row_items:
            term_width = col_w - 150
            max_lines = max(max_lines, len(_wrapped_lines(draw, item["term"], term_font, term_width)))
        row_heights.append(max(78, max_lines * 29 + 50))

    section_h = 70 + sum(row_heights) + 24
    ctx.ensure(section_h + 22)
    draw = ctx.draw
    y0 = ctx.y

    draw.rounded_rectangle((x0, y0, x1, y0 + section_h), radius=18, fill=PALETTE["white"], outline=PALETTE["line"], width=2)
    draw.rounded_rectangle((x0, y0, x1, y0 + 58), radius=18, fill=color)
    draw.rectangle((x0, y0 + 32, x1, y0 + 58), fill=color)
    label = _short_label(title)
    if continued:
        label = f"{label} (계속)"
    draw.text((x0 + 26, y0 + 15), label, font=_font(24, bold=True), fill=PALETTE["white"])
    draw.text((x1 - 190, y0 + 17), "뜻을 쓰시오", font=_font(20), fill=PALETTE["white"])

    no = start_no
    y = y0 + 78
    for row, row_h in enumerate(row_heights):
        row_entries = [(0, items[row])]
        second_idx = row + rows
        if second_idx < len(items):
            row_entries.append((1, items[second_idx]))

        for col, item in row_entries:
            x = x0 + inner_pad + col * (col_w + col_gap)
            badge = "표현" if item.get("kind") == "phrase" else "단어"
            term_lines = _wrapped_lines(draw, item["term"], term_font, col_w - 150)

            draw.text((x, y + 5), f"{no:02d}.", font=no_font, fill=color)
            _draw_lines(draw, term_lines, x + 52, y + 3, term_font, PALETTE["ink"], 29)
            badge_x = x + col_w - 74
            draw.rounded_rectangle((badge_x, y + 1, badge_x + 66, y + 30), radius=13, fill=PALETTE["soft_blue"])
            draw.text((badge_x + 17, y + 6), badge, font=badge_font, fill=PALETTE["blue"])
            line_y = y + row_h - 20
            draw.line((x + 52, line_y, x + col_w - 8, line_y), fill=(185, 194, 204), width=2)
            no += 1
        y += row_h

    ctx.y += section_h + 28
    return no


class _CanvasContext:
    """A4 비율 학습지 이미지를 페이지 단위로 그리는 헬퍼."""

    page_w = 1654
    page_h = 2339
    margin_x = 92
    bottom_margin = 96

    def __init__(self, header_title: str, header_subtitle: str) -> None:
        self.header_title = header_title
        self.header_subtitle = header_subtitle
        self.pages: list[Image.Image] = []
        self.image, self.draw, self.y = self._new_page()

    @property
    def content_w(self) -> int:
        return self.page_w - self.margin_x * 2

    def ensure(self, required: int) -> None:
        if self.y + required <= self.page_h - self.bottom_margin:
            return
        self._finish_current_page()
        self.image, self.draw, self.y = self._new_page()

    def draw_main_title(self, title: str, subtitle: str) -> None:
        self.ensure(132)
        self.draw.text((self.margin_x, self.y), title, font=_font(44, bold=True), fill=PALETTE["ink"])
        self.y += 62
        self.draw.rounded_rectangle(
            (self.margin_x, self.y, self.page_w - self.margin_x, self.y + 54),
            radius=14,
            fill=PALETTE["white"],
            outline=PALETTE["line"],
            width=1,
        )
        self.draw.text((self.margin_x + 24, self.y + 15), subtitle, font=_font(22), fill=PALETTE["muted"])
        self.y += 88
        self.draw.line((self.margin_x, self.y, self.page_w - self.margin_x, self.y), fill=PALETTE["line"], width=3)
        self.y += 46

    def finish(self) -> list[Image.Image]:
        self._finish_current_page()
        return self.pages

    def _new_page(self) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
        page_no = len(self.pages) + 1
        image = Image.new("RGB", (self.page_w, self.page_h), PALETTE["paper"])
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, self.page_w, 170), fill=PALETTE["soft"])
        draw.text((self.margin_x, 48), self.header_title, font=_font(40, bold=True), fill=PALETTE["ink"])
        draw.text((self.margin_x + 2, 108), self.header_subtitle, font=_font(21), fill=PALETTE["muted"])
        draw.rounded_rectangle((self.page_w - 265, 54, self.page_w - 92, 112), radius=29, fill=PALETTE["white"])
        draw.text((self.page_w - 224, 70), f"PAGE {page_no}", font=_font(20, bold=True), fill=PALETTE["teal"])
        draw.line((self.margin_x, 154, self.page_w - self.margin_x, 154), fill=(191, 207, 207), width=2)
        return image, draw, 210

    def _finish_current_page(self) -> None:
        page_no = len(self.pages) + 1
        self.draw.line((self.margin_x, self.page_h - 74, self.page_w - self.margin_x, self.page_h - 74), fill=PALETTE["line"], width=1)
        self.draw.text((self.margin_x, self.page_h - 50), "보보쌤 영어 단어 자료", font=_font(17), fill=PALETTE["muted"])
        self.draw.text((self.page_w - 154, self.page_h - 50), str(page_no), font=_font(17, bold=True), fill=PALETTE["muted"])
        self.pages.append(self.image)


def _draw_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    x: int,
    y: int,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    line_h: int,
) -> None:
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h


def _short_label(label: str, limit: int = 42) -> str:
    """긴 PDF 파일명을 학습지 헤더에 맞게 줄인다."""
    text = str(label).replace(".pdf", "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."
