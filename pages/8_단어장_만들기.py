"""PDF 기반 영어 단어 테스트/답지 만들기 페이지."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from naverblog.config import inject_secrets

inject_secrets()

from naverblog.direct_reading import extract_pdf_text, images_to_pdf_bytes
from naverblog.llm import (
    format_missing_api_key_message,
    generate,
    get_default_model_name,
    has_required_api_key,
    list_model_names,
)
from naverblog.vocabulary import (
    VocabularySourceSpec,
    build_vocabulary_prompts,
    parse_vocabulary_json,
    render_vocabulary_answer_images,
    render_vocabulary_test_images,
    vocabulary_images_to_zip_bytes,
)


st.set_page_config(
    page_title="단어장 만들기 | 보보쌤",
    page_icon="📝",
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
    <h1>📝 단어장 만들기</h1>
    <p>영어 문제지 PDF에서 난도 있는 어휘, 동사구/숙어, 해석 문장을 골라 테스트지와 답지를 이미지로 만듭니다</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hint-box">
PDF를 여러 개 넣으면 파일별로 단어/표현 개수, 숙어·동사구 개수, 문장 해석 개수, 난이도를 조절할 수 있습니다.
결과는 시험지 이미지, 답지 이미지, 인쇄용 PDF로 각각 다운로드됩니다.
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

model_names = list_model_names()
default_model = get_default_model_name()
default_index = model_names.index(default_model) if default_model in model_names else 0

top_col1, top_col2, top_col3 = st.columns([1, 1, 1])
with top_col1:
    selected_model = st.selectbox("생성 모델", model_names, index=default_index)
with top_col2:
    question_start = st.number_input("시작 문항", min_value=1, max_value=200, value=18, step=1)
with top_col3:
    question_end = st.number_input("끝 문항", min_value=1, max_value=200, value=45, step=1)

with st.expander("PDF별 출제 설정", expanded=True):
    source_specs: list[VocabularySourceSpec] = []
    if not uploaded_pdfs:
        st.caption("PDF를 업로드하면 파일별 설정이 나타납니다.")
    else:
        file_count = len(uploaded_pdfs)
        base_word_count = max(5, round(30 / file_count))
        base_phrase_count = max(1, round(10 / file_count))
        sentence_defaults = [0] * file_count
        remaining_sentences = 3
        idx = 0
        while remaining_sentences > 0:
            sentence_defaults[idx % file_count] += 1
            remaining_sentences -= 1
            idx += 1

        for idx, uploaded in enumerate(uploaded_pdfs):
            st.markdown(f"**{idx + 1}. {uploaded.name}**")
            title = st.text_input(
                "자료명",
                value=_default_source_title(uploaded.name),
                key=f"vocab_display_title_{idx}_{uploaded.name}",
                help="시험지/답지에 표시될 제목입니다. 긴 파일명이 깨져 보이면 여기서 짧게 바꾸세요.",
            )
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                word_count = st.number_input(
                    "단어/표현 수",
                    min_value=3,
                    max_value=50,
                    value=base_word_count,
                    step=1,
                    key=f"vocab_word_count_{idx}_{uploaded.name}",
                )
            with col2:
                phrase_count = st.number_input(
                    "숙어/동사구 최소",
                    min_value=0,
                    max_value=50,
                    value=min(base_phrase_count, word_count),
                    step=1,
                    key=f"vocab_phrase_count_{idx}_{uploaded.name}",
                )
            with col3:
                sentence_count = st.number_input(
                    "문장 해석 수",
                    min_value=0,
                    max_value=10,
                    value=sentence_defaults[idx],
                    step=1,
                    key=f"vocab_sentence_count_{idx}_{uploaded.name}",
                )
            with col4:
                difficulty = st.selectbox(
                    "난이도",
                    ["보통", "어려움", "매우 어려움"],
                    index=1,
                    key=f"vocab_difficulty_{idx}_{uploaded.name}",
                )
            source_specs.append(
                VocabularySourceSpec(
                    label=uploaded.name,
                    display_title=title,
                    word_count=int(word_count),
                    phrase_count=int(min(phrase_count, word_count)),
                    sentence_count=int(sentence_count),
                    difficulty=difficulty,
                )
            )
            st.divider()

with st.expander("고급 설정", expanded=False):
    page_col1, page_col2, page_col3 = st.columns(3)
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
    with page_col3:
        max_chars_per_pdf = st.slider(
            "PDF당 최대 글자 수",
            min_value=20_000,
            max_value=120_000,
            value=80_000,
            step=10_000,
        )
    extra_instructions = st.text_area(
        "추가 지시",
        placeholder="예: 수능 빈출 표현 위주로, 추상명사는 더 많이 포함, 문장 해석은 34~39번 중심",
        height=86,
    )

generate_clicked = st.button(
    "단어 테스트/답지 만들기",
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
                        label=uploaded.name,
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

    system_prompt, user_prompt = build_vocabulary_prompts(
        extracted_sources,
        source_specs,
        question_start=int(question_start),
        question_end=int(question_end),
        extra_instructions=extra_instructions,
    )

    with st.spinner("단어/표현과 문장 해석 문항을 선별하고 있습니다..."):
        try:
            raw_json = generate(
                model=selected_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.35,
                max_tokens=13_000,
            )
            vocab_data = parse_vocabulary_json(raw_json)
        except Exception as exc:
            st.error(f"단어장 생성 실패: {exc}")
            st.stop()

    if not vocab_data.get("sources"):
        st.error("생성된 단어/표현 항목이 없습니다. PDF 범위나 난이도를 조정해 다시 시도해주세요.")
        st.stop()

    with st.spinner("시험지/답지 이미지와 PDF를 만들고 있습니다..."):
        try:
            test_images = render_vocabulary_test_images(vocab_data)
            answer_images = render_vocabulary_answer_images(vocab_data)
            test_pdf = images_to_pdf_bytes(test_images)
            answer_pdf = images_to_pdf_bytes(answer_images)
            image_zip = vocabulary_images_to_zip_bytes(test_images, answer_images)
        except Exception as exc:
            st.error(f"파일 변환 실패: {exc}")
            st.stop()

    st.session_state["vocab_result"] = {
        "data": vocab_data,
        "test_images": test_images,
        "answer_images": answer_images,
        "test_pdf": test_pdf,
        "answer_pdf": answer_pdf,
        "image_zip": image_zip,
    }

result = st.session_state.get("vocab_result")
if result:
    vocab_data = result["data"]
    item_count = sum(len(source.get("items", [])) for source in vocab_data.get("sources", []))
    sentence_count = len(vocab_data.get("sentences", []))
    st.success(f"단어 테스트 생성 완료 · 어휘/표현 {item_count}개 · 문장 {sentence_count}개")

    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        st.download_button(
            "시험지 PDF 다운로드",
            data=result["test_pdf"],
            file_name="vocab_test.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            "답지 PDF 다운로드",
            data=result["answer_pdf"],
            file_name="vocab_answer.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with dl_col3:
        st.download_button(
            "시험지/답지 이미지 ZIP",
            data=result["image_zip"],
            file_name="vocab_images.zip",
            mime="application/zip",
            use_container_width=True,
        )

    with st.expander("원본 JSON 다운로드", expanded=False):
        st.download_button(
            "JSON 다운로드",
            data=json.dumps(vocab_data, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="vocab_data.json",
            mime="application/json",
            use_container_width=True,
        )
        st.code(json.dumps(vocab_data, ensure_ascii=False, indent=2), language="json")

    tab_test, tab_answer = st.tabs(["시험지 이미지", "답지 이미지"])
    with tab_test:
        for idx, image in enumerate(result["test_images"][:3], 1):
            st.image(image, caption=f"시험지 {idx}", use_container_width=True)
        if len(result["test_images"]) > 3:
            st.caption(f"나머지 {len(result['test_images']) - 3}쪽은 ZIP/PDF에서 확인하세요.")
    with tab_answer:
        for idx, image in enumerate(result["answer_images"][:3], 1):
            st.image(image, caption=f"답지 {idx}", use_container_width=True)
        if len(result["answer_images"]) > 3:
            st.caption(f"나머지 {len(result['answer_images']) - 3}쪽은 ZIP/PDF에서 확인하세요.")
else:
    st.info("PDF를 업로드하고 파일별 개수/난이도를 조정한 뒤 자료를 생성하세요.")
