"""PDF 기반 직독직해 파일 만들기 페이지."""

from __future__ import annotations

import sys
import re
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from naverblog.config import inject_secrets

inject_secrets()

from naverblog.direct_reading import (
    build_direct_reading_prompts,
    clean_markdown_response,
    extract_pdf_text,
    images_to_pdf_bytes,
    images_to_zip_bytes,
    render_markdown_to_images,
)
from naverblog.llm import (
    format_missing_api_key_message,
    generate,
    get_default_model_name,
    has_required_api_key,
    list_model_names,
)


st.set_page_config(
    page_title="직독직해 파일 만들기 | 보보쌤",
    page_icon="📘",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .block-container { max-width: 1120px; padding-top: 1.2rem; }
    .page-header {
        background: linear-gradient(135deg, #0f766e 0%, #c85a3a 58%, #f2a65a 100%);
        padding: 1.7rem 2.1rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 1.3rem;
    }
    .page-header h1 { color: white !important; font-size: 1.35rem; font-weight: 700; margin: 0 0 0.25rem 0; }
    .page-header p { color: rgba(255,255,255,0.86); font-size: 0.86rem; margin: 0; font-weight: 300; }
    .hint-box {
        border: 1px solid #d7e3df;
        background: #f7fbf9;
        border-radius: 0.75rem;
        padding: 0.8rem 0.95rem;
        color: #36524e;
        font-size: 0.88rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h1>📘 직독직해 파일 만들기</h1>
    <p>영어 문제지 PDF를 넣고 문항 범위를 지정하면 문장별 직독직해 자료를 PDF와 이미지로 만듭니다</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hint-box">
PDF를 여러 개 올릴 수 있습니다. 예: 3월 고3 문제지와 6월 모의평가 문제지를 넣고
문항 범위를 18~45로 지정하면 각 PDF에서 해당 범위의 영어 지문을 찾아 직독직해 Markdown을 만든 뒤,
다운로드용 PDF와 PNG 이미지 묶음으로 변환합니다.
</div>
""", unsafe_allow_html=True)

uploaded_pdfs = st.file_uploader(
    "영어 문제지 PDF 업로드",
    type=["pdf", "application/pdf"],
    accept_multiple_files=True,
    help="PDF 텍스트 추출이 가능한 문제지 파일을 업로드하세요.",
)


def _default_source_title(filename: str) -> str:
    text = unicodedata.normalize("NFC", filename).replace(".pdf", "")
    text = re.sub(r"[_\\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:48]


source_titles: dict[str, str] = {}
if uploaded_pdfs:
    with st.expander("PDF 표시 제목", expanded=True):
        for idx, uploaded in enumerate(uploaded_pdfs):
            source_titles[uploaded.name] = st.text_input(
                f"{idx + 1}. 자료명",
                value=_default_source_title(uploaded.name),
                key=f"direct_display_title_{idx}_{uploaded.name}",
                help="직독직해 결과의 섹션 제목으로 표시됩니다.",
            )

range_col1, range_col2, range_col3 = st.columns([1, 1, 2])
with range_col1:
    question_start = st.number_input("시작 문항", min_value=1, max_value=200, value=18, step=1)
with range_col2:
    question_end = st.number_input("끝 문항", min_value=1, max_value=200, value=45, step=1)
with range_col3:
    target_questions = st.text_input(
        "특정 문항만 만들기 (선택)",
        placeholder="예: 34 또는 31, 34, 39",
        help="비워두면 시작~끝 문항 전체를 만듭니다.",
    )

model_names = list_model_names()
default_model = get_default_model_name()
default_index = model_names.index(default_model) if default_model in model_names else 0

setting_col1, setting_col2 = st.columns([1, 1])
with setting_col1:
    selected_model = st.selectbox("생성 모델", model_names, index=default_index)
with setting_col2:
    max_chars_per_pdf = st.slider(
        "PDF당 읽을 최대 글자 수",
        min_value=20_000,
        max_value=120_000,
        value=80_000,
        step=10_000,
        help="문항 범위가 넓으면 크게 두세요. 너무 크면 생성 시간이 길어질 수 있습니다.",
    )

with st.expander("고급 설정", expanded=False):
    page_col1, page_col2 = st.columns(2)
    with page_col1:
        page_start = st.number_input(
            "PDF 시작 페이지 (선택)",
            min_value=0,
            max_value=500,
            value=0,
            step=1,
            help="0이면 처음부터 읽습니다.",
        )
    with page_col2:
        page_end = st.number_input(
            "PDF 끝 페이지 (선택)",
            min_value=0,
            max_value=500,
            value=0,
            step=1,
            help="0이면 끝까지 읽습니다.",
        )
    extra_instructions = st.text_area(
        "추가 지시",
        placeholder="예: 34번만 아주 자세히, 청크를 더 촘촘하게 나눠줘",
        height=86,
    )

generate_clicked = st.button(
    "직독직해 자료 만들기",
    type="primary",
    use_container_width=True,
    disabled=not uploaded_pdfs,
)

if generate_clicked:
    if question_start > question_end:
        st.error("시작 문항은 끝 문항보다 작거나 같아야 합니다.")
        st.stop()

    if not has_required_api_key(selected_model):
        st.error(format_missing_api_key_message(selected_model))
        st.stop()

    extracted_sources = []
    with st.spinner("PDF 텍스트를 읽고 있습니다..."):
        for uploaded in uploaded_pdfs:
            try:
                extracted_sources.append(
                    extract_pdf_text(
                        uploaded.getvalue(),
                        label=source_titles.get(uploaded.name, uploaded.name),
                        page_start=page_start or None,
                        page_end=page_end or None,
                        max_chars=max_chars_per_pdf,
                    )
                )
            except Exception as exc:
                st.error(f"{uploaded.name} 텍스트 추출 실패: {exc}")
                st.stop()

    if not any(source.text.strip() for source in extracted_sources):
        st.error("PDF에서 텍스트를 추출하지 못했습니다. 스캔 이미지 PDF라면 OCR이 필요합니다.")
        st.stop()

    system_prompt, user_prompt = build_direct_reading_prompts(
        extracted_sources,
        question_start=int(question_start),
        question_end=int(question_end),
        target_questions=target_questions,
        extra_instructions=extra_instructions,
    )

    with st.spinner("직독직해 Markdown을 생성하고 있습니다..."):
        try:
            markdown_result = generate(
                model=selected_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4,
                max_tokens=14_000,
            )
            markdown_result = clean_markdown_response(markdown_result)
            if len(markdown_result.strip()) < 20:
                raise ValueError("모델 응답이 비어 있습니다. PDF 범위나 모델을 바꿔 다시 시도해주세요.")
        except Exception as exc:
            st.error(f"직독직해 생성 실패: {exc}")
            st.stop()

    with st.spinner("PDF와 PNG 이미지를 만들고 있습니다..."):
        try:
            images = render_markdown_to_images(markdown_result)
            pdf_bytes = images_to_pdf_bytes(images)
            zip_bytes = images_to_zip_bytes(images, basename="direct_reading")
        except Exception as exc:
            st.error(f"파일 변환 실패: {exc}")
            st.stop()

    st.session_state["direct_reading_result"] = {
        "markdown": markdown_result,
        "pdf": pdf_bytes,
        "zip": zip_bytes,
        "images": images,
        "source_count": len(extracted_sources),
    }

result = st.session_state.get("direct_reading_result")
if result:
    st.success(f"직독직해 자료 생성 완료 · PDF {result['source_count']}개 기반")

    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        st.download_button(
            "Markdown 다운로드",
            data=result["markdown"].encode("utf-8"),
            file_name="direct_reading.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            "PDF 다운로드",
            data=result["pdf"],
            file_name="direct_reading.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with dl_col3:
        st.download_button(
            "PNG 이미지 ZIP 다운로드",
            data=result["zip"],
            file_name="direct_reading_images.zip",
            mime="application/zip",
            use_container_width=True,
        )

    preview_tab, markdown_tab = st.tabs(["이미지 미리보기", "Markdown"])
    with preview_tab:
        preview_images = result["images"][:3]
        for idx, image in enumerate(preview_images, 1):
            st.image(image, caption=f"페이지 {idx}", use_container_width=True)
        if len(result["images"]) > 3:
            st.caption(f"나머지 {len(result['images']) - 3}쪽은 ZIP/PDF에서 확인하세요.")

    with markdown_tab:
        st.code(result["markdown"], language="markdown")
else:
    st.info("PDF를 업로드하고 문항 범위를 지정한 뒤 자료를 생성하세요.")
