"""네이버 블로그 글 생성기 - Streamlit 웹 앱."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from naverblog.database import Database
from naverblog.image_gen import (
    generate_blog_images,
    get_image_model_id,
    list_image_model_names,
)
from naverblog.llm import list_model_names
from naverblog.models import Persona, PostType
from naverblog.pipeline import run_pipeline
from naverblog.skills import SkillRegistry
from naverblog.skills.blog_style import AVAILABLE_CATEGORIES, get_available_categories, seed_default_styles

# ─── 카테고리별 스킬 프리셋 ───
CATEGORY_SKILL_PRESETS: dict[str, dict] = {
    "과목별 공부 로직": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False,
        "note": "📚 교재/학습법 최신 정보 + 기존 글 참조",
    },
    "입시 파이널 : 면접": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False,
        "note": "🎤 면접 기출 트렌드 + 기존 글 참조",
    },
    "입시 파이널 : 자기소개서": {
        "search": False, "blog_style": True, "reference_posts": True, "image_gen": False,
        "note": "✏️ 스타일 가이드 + 기존 글 참조",
    },
    "생기부 : 수시의 모든 것": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False,
        "note": "📋 최신 세특 트렌드 + 기존 글 참조",
    },
    "77일만에 의대 가기": {
        "search": False, "blog_style": True, "reference_posts": True, "image_gen": True,
        "note": "💪 개인 경험 스토리 + 기존 글 참조 + 이미지",
    },
    "[전략] 입시 설계의 정석": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False,
        "note": "📊 최신 입시 데이터 + 기존 글 참조",
    },
    "시기별 로드맵": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False,
        "note": "🗓️ 시기별 최신 정보 + 기존 글 참조",
    },
    "학원 / 과외의 모든 것": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False,
        "note": "💰 학원 정보 + 기존 글 참조",
    },
    "블로그 활용법 (후기 zip)": {
        "search": False, "blog_style": True, "reference_posts": True, "image_gen": False,
        "note": "⭐ 후기 정리 + 기존 글 참조",
    },
    "입시 정보 모음": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False,
        "note": "🔍 입시 데이터 + 기존 글 참조",
    },
}

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="보보쌤 블로그 글 생성기 | 보윤공주",
    page_icon="👸",
    layout="wide",
)

# ─── CSS 커스텀 스타일 ───
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white !important; margin: 0; font-size: 2rem; }
    .main-header p { color: rgba(255,255,255,0.85); margin: 0.5rem 0 0 0; }
    .main-header .boyun-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        border-radius: 2rem;
        padding: 0.3rem 0.8rem;
        font-size: 0.75rem;
        margin-top: 0.5rem;
        color: #ffe0f0;
    }
    [data-testid="stSidebar"] { background-color: #f8f9fc; }
    .skill-preset-note {
        background: #eef2ff;
        border-left: 3px solid #667eea;
        border-radius: 0 0.5rem 0.5rem 0;
        padding: 0.6rem 0.8rem;
        font-size: 0.82rem;
        color: #4338ca;
        margin: 0.3rem 0 0.8rem 0;
    }
    [data-testid="stForm"] { border: none !important; padding: 0 !important; }
    .boyun-footer {
        text-align: center;
        padding: 1rem;
        color: #9ca3af;
        font-size: 0.8rem;
    }
    .boyun-footer .highlight { color: #a78bfa; font-weight: 600; }
    .image-placement-hint {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 0.5rem;
        padding: 0.8rem;
        font-size: 0.82rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ─── 초기화 (캐시) ───
@st.cache_resource
def get_db() -> Database:
    return Database()


@st.cache_resource
def get_skill_registry(_db: Database) -> SkillRegistry:
    registry = SkillRegistry(_db)
    registry.discover()
    return registry


db = get_db()
seed_default_styles(db)  # DB에 기본 스타일 시드
registry = get_skill_registry(db)


# ═══════════════════════════════════════
# 사이드바
# ═══════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ 설정")

    # ─ 글 생성 모델 ─
    model_names = list_model_names()
    selected_model = st.selectbox(
        "AI 모델 (글 생성)", model_names, index=0,
        help="글을 생성할 AI 모델. Claude가 한국어 품질이 가장 좋습니다.",
    )

    st.divider()

    # ─ 블로그 카테고리 ─
    db_categories = get_available_categories(db)
    category_options = ["(선택 안함)"] + (db_categories or AVAILABLE_CATEGORIES) + ["직접 입력"]
    selected_category_label = st.selectbox(
        "블로그 카테고리", category_options, index=0,
        help="카테고리 선택 시 해당 문체/구조 + 추천 스킬이 자동 적용됩니다",
    )
    custom_category = ""
    if selected_category_label == "직접 입력":
        custom_category = st.text_input("카테고리 이름", placeholder="예: 의대 입시 전략")
    selected_category = (
        custom_category if selected_category_label == "직접 입력"
        else "" if selected_category_label == "(선택 안함)"
        else selected_category_label
    )

    preset = CATEGORY_SKILL_PRESETS.get(selected_category, None)
    if preset:
        st.markdown(
            f'<div class="skill-preset-note">{preset["note"]}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ─ 페르소나 ─
    personas = db.list_personas()
    persona_names = [p.name for p in personas] + ["직접 입력"]
    selected_persona_name = st.selectbox(
        "대상 독자", persona_names, index=0, help="글의 대상 독자층",
    )
    custom_persona_text = ""
    if selected_persona_name == "직접 입력":
        custom_persona_text = st.text_input("독자 설명", placeholder="예: IT에 관심 있는 50대 남성")

    st.divider()

    # ─ 글 유형 ─
    post_type_options = {
        "일반 정보": PostType.GENERAL,
        "리뷰": PostType.REVIEW,
        "리스트형": PostType.LISTICLE,
    }
    selected_type_label = st.selectbox("글 유형", list(post_type_options.keys()))
    selected_post_type = post_type_options[selected_type_label]

    st.divider()

    # ─ 스킬 토글 ─
    st.markdown("### 🧩 스킬 설정")
    if preset:
        st.caption("카테고리 추천값 적용됨 (변경 가능)")

    default_search = preset["search"] if preset else True
    default_style = preset["blog_style"] if preset else True
    default_ref = preset.get("reference_posts", True) if preset else True

    use_search = st.toggle("🔍 웹 검색 (최신 정보)", value=default_search)
    use_blog_style = st.toggle("📝 보보쌤 스타일 적용", value=default_style)
    use_ref_posts = st.toggle(
        "📖 기존 글 참조",
        value=default_ref,
        help=f"보보쌤의 실제 블로그 글 {db.count_blog_posts()}개를 참조하여 문체를 더 정확하게 재현",
    )

    ref_post_count = 3
    if use_ref_posts:
        total_posts = db.count_blog_posts()
        ref_post_count = st.slider(
            "참조할 글 수",
            min_value=1,
            max_value=total_posts if total_posts > 0 else 50,
            value=min(total_posts, 50) if total_posts > 0 else 3,
            help="전체를 넣으면 문체를 더 정확하게 따라하지만 비용이 증가합니다",
        )
        # 토큰 예상
        if ref_post_count <= 3:
            est_tokens = ref_post_count * 750
        elif ref_post_count <= 10:
            est_tokens = ref_post_count * 500
        elif ref_post_count <= 20:
            est_tokens = ref_post_count * 375
        else:
            est_tokens = ref_post_count * 250
        est_cost_krw = int(est_tokens * 0.003 * 1450)  # ~$3/M tokens * KRW
        st.caption(f"예상 토큰: ~{est_tokens:,} ({est_cost_krw}원 추가)")

    st.divider()

    # ─ 비용 안내 ─
    with st.expander("💰 비용 안내"):
        st.markdown("""
**글 생성** (1회, ~2000자)

| 모델 | 비용 |
|------|------|
| Claude Sonnet | ~25원 |
| Claude Haiku | ~7원 |
| GPT-4o | ~40원 |
| GPT-4o Mini | ~7원 |
| Gemini Pro | ~25원 |
| Gemini Flash | ~7원 |

**이미지 생성** (1장): ~13~25원
**웹 검색**: Tavily 무료 1000회/월
        """)

    with st.expander("🔑 API 키 설정"):
        st.markdown("""
`.env` 파일에 설정:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
TAVILY_API_KEY=tvly-...
```
        """)

    st.markdown("---")
    st.markdown(
        '<p style="text-align:center; color:#a78bfa; font-size:0.75rem;">'
        "👸 보윤공주 & 보윤 빗취가 응원해요!</p>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════
# 메인 영역
# ═══════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>✍️ 보보쌤 블로그 글 생성기</h1>
    <p>주제를 입력하면 보보쌤 스타일로 네이버 블로그 글을 자동 생성합니다</p>
    <span class="boyun-badge">👸 보윤공주 에디션</span>
</div>
""", unsafe_allow_html=True)

# ─── 이미지 설정 (선택사항, form 바깥) ───
with st.expander("🖼️ 이미지 설정 (선택)", expanded=False):
    default_image = preset["image_gen"] if preset else False

    img_col1, img_col2 = st.columns(2)

    with img_col1:
        st.markdown("##### 📎 내 이미지 업로드")
        uploaded_files = st.file_uploader(
            "이미지 파일 선택",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        image_instructions = ""
        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)}장** 업로드됨")
            for i, f in enumerate(uploaded_files, 1):
                st.image(f, caption=f"이미지 {i}: {f.name}", width=150)
            image_instructions = st.text_area(
                "이미지 배치 지시",
                placeholder="예: 이미지 1은 서론에, 이미지 2는 본론 중간에 넣어줘",
                height=68,
            )
            st.markdown("""
<div class="image-placement-hint">
💡 <b>팁</b>: 글 생성 후 미리보기에서 [이미지 1], [이미지 2] 위치를 확인하세요.
네이버 에디터에서 해당 위치에 이미지를 직접 삽입하면 됩니다.
</div>
            """, unsafe_allow_html=True)

    with img_col2:
        st.markdown("##### 🎨 AI 이미지 생성")
        use_image_gen = st.toggle("AI로 이미지 생성하기", value=default_image)
        if use_image_gen:
            image_model_names = list_image_model_names()
            selected_image_model_name = st.selectbox(
                "이미지 모델", image_model_names, index=0,
                help="GEMINI_API_KEY 필요",
            )
            num_images = st.slider("생성할 이미지 수", 1, 4, 2)
        else:
            selected_image_model_name = "Imagen 3"
            num_images = 2


# ─── 입력 폼 (st.form으로 한글 입력 깨짐 해결) ───
with st.form("generate_form"):
    topic = st.text_area(
        "📌 블로그 주제",
        placeholder="예: 독학재수 3개월 수능 국어 공부법, 에어팟 프로 2 솔직 리뷰",
        height=68,
    )
    extra = st.text_area(
        "📝 추가 지시사항 (선택)",
        placeholder="예: 가성비 위주로 작성해줘, 구체적인 교재 추천 포함",
        height=68,
    )
    submitted = st.form_submit_button(
        "🚀 블로그 글 생성하기",
        type="primary",
        use_container_width=True,
    )


# ─── 생성 로직 ───
if submitted and topic.strip():
    # 페르소나 결정
    if selected_persona_name == "직접 입력":
        if not custom_persona_text.strip():
            st.error("대상 독자 설명을 입력해주세요.")
            st.stop()
        persona = Persona(
            name="커스텀",
            description=custom_persona_text,
            system_prompt=(
                f"당신은 다음 대상을 위한 네이버 블로그 전문가입니다: {custom_persona_text}. "
                "이 독자층에 맞는 문체, 어휘, 톤으로 작성합니다."
            ),
        )
    else:
        persona = db.get_persona(selected_persona_name)
        if persona is None:
            st.error(f"페르소나 '{selected_persona_name}'를 찾을 수 없습니다.")
            st.stop()

    # 스킬 토글
    if not use_blog_style:
        registry.disable("blog_style")
    else:
        registry.enable("blog_style")

    if not use_ref_posts:
        registry.disable("reference_posts")
    else:
        registry.enable("reference_posts")

    # 이미지 배치 지시를 extra_instructions에 추가
    full_extra = extra or ""
    if uploaded_files and image_instructions:
        img_list = "\n".join(
            f"- [이미지 {i}]: {f.name}" for i, f in enumerate(uploaded_files, 1)
        )
        full_extra += (
            f"\n\n## 이미지 배치\n"
            f"사용자가 {len(uploaded_files)}장의 이미지를 제공했습니다.\n"
            f"글 본문의 적절한 위치에 [이미지 1], [이미지 2] 등의 마커를 넣어주세요.\n"
            f"{img_list}\n"
            f"배치 지시: {image_instructions}"
        )
    elif uploaded_files:
        img_list = "\n".join(
            f"- [이미지 {i}]: {f.name}" for i, f in enumerate(uploaded_files, 1)
        )
        full_extra += (
            f"\n\n## 이미지 배치\n"
            f"사용자가 {len(uploaded_files)}장의 이미지를 제공했습니다.\n"
            f"글 본문의 적절한 위치에 [이미지 1], [이미지 2] 등의 마커를 넣어주세요.\n"
            f"{img_list}"
        )

    # ── 글 생성 ──
    with st.spinner("블로그 글을 생성하고 있습니다... ✨ (30초~1분 소요)"):
        try:
            generation = run_pipeline(
                topic=topic.strip(),
                persona=persona,
                model=selected_model,
                post_type=selected_post_type,
                skill_registry=registry,
                db=db,
                extra_instructions=full_extra.strip(),
                skip_search=not use_search,
                category=selected_category,
                ref_post_count=ref_post_count if use_ref_posts else 0,
            )
        except Exception as e:
            st.error(f"글 생성 중 오류가 발생했습니다: {e}")
            st.stop()

    # ── AI 이미지 생성 ──
    generated_images = []
    if use_image_gen:
        with st.spinner("보윤공주가 이미지를 그리고 있어요... 🎨"):
            try:
                image_model_id = get_image_model_id(selected_image_model_name)
                generated_images = generate_blog_images(
                    topic=topic.strip(),
                    num_images=num_images,
                    model=image_model_id,
                )
            except Exception as e:
                st.warning(f"이미지 생성 실패: {e}")

    # ── 결과 표시 ──
    st.success(f"생성 완료! (ID: #{generation.id})")

    # 탭 구성
    tab_names = ["📖 미리보기", "📋 HTML (복사용)", "📝 Markdown"]
    has_any_images = bool(generated_images) or bool(uploaded_files)
    if has_any_images:
        tab_names.append("🖼️ 이미지")
    tab_names.append("📊 참조 데이터")
    tab_names.append("🔧 프롬프트")

    tabs = st.tabs(tab_names)
    tab_idx = 0

    # 미리보기
    with tabs[tab_idx]:
        # 업로드 이미지 + AI 이미지 모두 표시
        if generated_images:
            st.image(
                generated_images[0].data,
                caption="AI 생성 대표 이미지",
                use_container_width=True,
            )
        elif uploaded_files:
            st.image(
                uploaded_files[0],
                caption=f"업로드 이미지: {uploaded_files[0].name}",
                use_container_width=True,
            )
        st.markdown(generation.output_markdown)
    tab_idx += 1

    # HTML
    with tabs[tab_idx]:
        st.markdown("##### 아래 HTML을 복사 → 네이버 에디터 → HTML 모드에 붙여넣기")
        st.code(generation.output_html, language="html")
    tab_idx += 1

    # Markdown
    with tabs[tab_idx]:
        st.markdown("##### Markdown 원문")
        st.code(generation.output_markdown, language="markdown")
    tab_idx += 1

    # 이미지 탭
    if has_any_images:
        with tabs[tab_idx]:
            st.markdown("##### 블로그에 사용할 이미지")
            st.caption(
                "네이버 블로그 에디터에서 '사진' 버튼으로 이미지를 업로드하세요. "
                "글에서 [이미지 N] 마커가 있는 위치에 삽입하면 됩니다."
            )

            # 업로드 이미지
            if uploaded_files:
                st.markdown("**📎 업로드한 이미지**")
                upload_cols = st.columns(min(len(uploaded_files), 3))
                for idx, f in enumerate(uploaded_files):
                    with upload_cols[idx % 3]:
                        st.image(f, caption=f"[이미지 {idx + 1}] {f.name}", use_container_width=True)
                        st.download_button(
                            f"💾 다운로드 ({idx + 1})",
                            data=f.getvalue(),
                            file_name=f.name,
                            mime=f.type,
                            key=f"dl_upload_{idx}",
                        )

            # AI 생성 이미지
            if generated_images:
                st.markdown("**🎨 AI 생성 이미지**")
                gen_cols = st.columns(min(len(generated_images), 3))
                for idx, img in enumerate(generated_images):
                    with gen_cols[idx % 3]:
                        label = ["대표 (썸네일)", "본문 삽입용", "추가", "추가"][idx]
                        st.image(img.data, caption=f"{idx + 1}. {label}", use_container_width=True)
                        st.download_button(
                            f"💾 다운로드 ({idx + 1})",
                            data=img.data,
                            file_name=f"ai_image_{idx + 1}.png",
                            mime="image/png",
                            key=f"dl_gen_{idx}",
                        )
                        with st.expander("프롬프트"):
                            st.caption(img.prompt)
        tab_idx += 1

    # 참조 데이터
    with tabs[tab_idx]:
        st.markdown("##### AI에게 전달된 참조 데이터")
        st.caption("글 생성 시 LLM에게 주입된 컨텍스트를 확인합니다.")

        # 스타일 가이드 데이터
        if use_blog_style:
            with st.expander("📝 스타일 가이드", expanded=False):
                prompt_text = generation.prompt_used
                style_start = prompt_text.find("## 블로그 스타일 가이드")
                if style_start >= 0:
                    style_end = prompt_text.find("\n## ", style_start + 10)
                    if style_end < 0:
                        style_end = style_start + 3000
                    st.text(prompt_text[style_start:style_end])
                else:
                    st.info("스타일 가이드 데이터 없음")

        # 레퍼런스 글 데이터
        if use_ref_posts:
            with st.expander(f"📖 레퍼런스 글 ({ref_post_count}개)", expanded=True):
                prompt_text = generation.prompt_used
                ref_start = prompt_text.find("## 보보쌤 기존 블로그 글 레퍼런스")
                if ref_start >= 0:
                    ref_end = prompt_text.find("\n## ", ref_start + 10)
                    if ref_end < 0:
                        ref_end = len(prompt_text)
                    ref_data = prompt_text[ref_start:ref_end]
                    st.markdown(f"**총 글자 수**: {len(ref_data):,}자 / **예상 토큰**: ~{len(ref_data)//4:,}")
                    st.text(ref_data[:5000] + ("\n... (더 있음)" if len(ref_data) > 5000 else ""))
                else:
                    st.info("레퍼런스 글 데이터 없음")

        # 검색 데이터
        if use_search:
            with st.expander("🔍 웹 검색 결과", expanded=False):
                prompt_text = generation.prompt_used
                search_start = prompt_text.find("## 참고할 최신 정보")
                if search_start >= 0:
                    search_end = prompt_text.find("\n## ", search_start + 10)
                    if search_end < 0:
                        search_end = search_start + 3000
                    st.text(prompt_text[search_start:search_end])
                else:
                    st.info("검색 데이터 없음")

        # 전체 프롬프트 길이 요약
        total_len = len(generation.prompt_used)
        st.metric("전체 프롬프트 길이", f"{total_len:,}자 (~{total_len//4:,} 토큰)")
    tab_idx += 1

    # 프롬프트
    with tabs[tab_idx]:
        st.caption("AI에게 전달된 전체 프롬프트 (디버깅/확인용)")
        st.text(generation.prompt_used)

elif submitted:
    st.warning("주제를 입력해주세요!")

st.divider()

# ─── 이전 생성 기록 ───
st.markdown("### 📚 이전 생성 기록")

history = db.list_generations(limit=10)

if not history:
    st.info("아직 생성된 글이 없습니다. 위에서 주제를 입력하고 생성해보세요!")
else:
    for gen in history:
        with st.expander(
            f"#{gen.id}  ·  {gen.topic}  ·  {gen.llm_model}  ·  "
            f"{gen.created_at.strftime('%m/%d %H:%M')}"
        ):
            tab1, tab2 = st.tabs(["미리보기", "HTML"])
            with tab1:
                st.markdown(gen.output_markdown)
            with tab2:
                st.code(gen.output_html, language="html")

# ─── 푸터 ───
st.divider()
st.markdown("""
<div class="boyun-footer">
    Made with Streamlit + LiteLLM + Imagen · 보보쌤 블로그 스타일 기반<br>
    <span class="highlight">👸 보윤공주</span> · <span class="highlight">보윤 빗취</span> · with love 💜
</div>
""", unsafe_allow_html=True)
