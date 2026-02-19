"""네이버 블로그 글 생성기 - Streamlit 웹 앱."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from naverblog.config import inject_secrets
inject_secrets()

from naverblog.database import Database, create_database
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

__version__ = "0.2.0"

# ─── 카테고리별 스킬 프리셋 ───
CATEGORY_SKILL_PRESETS: dict[str, dict] = {
    "과목별 공부 로직": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False, "keyword_analysis": True,
        "note": "교재/학습법 최신 정보 + 기존 글 참조 + SEO",
    },
    "입시 파이널 : 면접": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False, "keyword_analysis": True,
        "note": "면접 기출 트렌드 + 기존 글 참조 + SEO",
    },
    "입시 파이널 : 자기소개서": {
        "search": False, "blog_style": True, "reference_posts": True, "image_gen": False, "keyword_analysis": True,
        "note": "스타일 가이드 + 기존 글 참조 + SEO",
    },
    "생기부 : 수시의 모든 것": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False, "keyword_analysis": True,
        "note": "최신 세특 트렌드 + 기존 글 참조 + SEO",
    },
    "77일만에 의대 가기": {
        "search": False, "blog_style": True, "reference_posts": True, "image_gen": True, "keyword_analysis": False,
        "note": "개인 경험 스토리 + 기존 글 참조 + 이미지",
    },
    "[전략] 입시 설계의 정석": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False, "keyword_analysis": True,
        "note": "최신 입시 데이터 + 기존 글 참조 + SEO",
    },
    "시기별 로드맵": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False, "keyword_analysis": True,
        "note": "시기별 최신 정보 + 기존 글 참조 + SEO",
    },
    "학원 / 과외의 모든 것": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False, "keyword_analysis": True,
        "note": "학원 정보 + 기존 글 참조 + SEO",
    },
    "블로그 활용법 (후기 zip)": {
        "search": False, "blog_style": True, "reference_posts": True, "image_gen": False, "keyword_analysis": False,
        "note": "후기 정리 + 기존 글 참조",
    },
    "입시 정보 모음": {
        "search": True, "blog_style": True, "reference_posts": True, "image_gen": False, "keyword_analysis": True,
        "note": "입시 데이터 + 기존 글 참조 + SEO",
    },
}

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="보보쌤 블로그 글 생성기",
    page_icon="✍️",
    layout="wide",
)

# ─── CSS ───
st.markdown("""
<style>
    /* 전역 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .block-container { max-width: 960px; padding-top: 1.5rem; }

    /* 헤더 */
    .hero {
        background: linear-gradient(135deg, #7c3aed 0%, #a78bfa 50%, #c4b5fd 100%);
        padding: 2.5rem 2.5rem 2rem;
        border-radius: 1.25rem;
        color: white;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute; top: -50%; right: -20%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero h1 {
        color: white !important;
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.02em;
    }
    .hero .subtitle {
        color: rgba(255,255,255,0.88);
        font-size: 0.92rem;
        font-weight: 300;
        margin: 0;
        line-height: 1.5;
    }
    .hero .meta {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-top: 1rem;
        flex-wrap: wrap;
    }
    .hero .badge {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 2rem;
        padding: 0.25rem 0.75rem;
        font-size: 0.72rem;
        font-weight: 500;
        color: white;
    }
    .hero .love {
        font-size: 0.72rem;
        color: #fde68a;
        font-weight: 400;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f5f3ff 0%, #faf5ff 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        font-size: 1.05rem;
        font-weight: 600;
        color: #4c1d95;
        letter-spacing: -0.01em;
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-size: 0.88rem;
        font-weight: 600;
        color: #6d28d9;
    }
    .sidebar-section-label {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8b5cf6;
        margin-bottom: 0.25rem;
    }
    .skill-preset-note {
        background: linear-gradient(90deg, #ede9fe, #f5f3ff);
        border-left: 3px solid #8b5cf6;
        border-radius: 0 0.5rem 0.5rem 0;
        padding: 0.5rem 0.7rem;
        font-size: 0.78rem;
        color: #5b21b6;
        margin: 0.25rem 0 0.6rem 0;
        font-weight: 400;
    }

    /* 폼 */
    [data-testid="stForm"] {
        border: 1px solid #e9e5f5 !important;
        border-radius: 1rem !important;
        padding: 1.25rem !important;
        background: white;
    }

    /* 카드 스타일 expander */
    .streamlit-expanderHeader {
        font-weight: 500 !important;
        font-size: 0.88rem !important;
    }

    /* 이미지 힌트 */
    .image-placement-hint {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 0.75rem;
        padding: 0.75rem 1rem;
        font-size: 0.8rem;
        margin: 0.5rem 0;
        color: #166534;
    }

    /* 결과 성공 */
    .result-success {
        background: linear-gradient(90deg, #f0fdf4, #ecfdf5);
        border: 1px solid #86efac;
        border-radius: 0.75rem;
        padding: 0.8rem 1rem;
        font-size: 0.88rem;
        color: #166534;
        font-weight: 500;
        margin-bottom: 1rem;
    }

    /* 푸터 */
    .app-footer {
        text-align: center;
        padding: 1.5rem 0;
        color: #a1a1aa;
        font-size: 0.75rem;
        line-height: 1.8;
    }
    .app-footer a {
        color: #8b5cf6;
        text-decoration: none;
        font-weight: 500;
    }
    .app-footer .love-msg {
        color: #c084fc;
        font-weight: 500;
        font-size: 0.78rem;
    }
    .app-footer .ver {
        display: inline-block;
        background: #f4f4f5;
        border-radius: 1rem;
        padding: 0.1rem 0.5rem;
        font-size: 0.65rem;
        color: #a1a1aa;
        font-weight: 500;
    }

    /* 히스토리 */
    .history-label {
        font-size: 0.92rem;
        font-weight: 600;
        color: #3f3f46;
        margin-bottom: 0.5rem;
    }

    /* 토글/슬라이더 라벨 */
    [data-testid="stSidebar"] label {
        font-size: 0.82rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── 초기화 (캐시) ───
@st.cache_resource
def get_db() -> Database:
    return create_database()


@st.cache_resource
def get_skill_registry(_db: Database) -> SkillRegistry:
    registry = SkillRegistry(_db)
    registry.discover()
    return registry


db = get_db()
seed_default_styles(db)
registry = get_skill_registry(db)

# ─── 자동 크롤링 ───
if db.count_blog_posts() == 0:
    from naverblog.crawler import crawl_blog
    with st.spinner("첫 실행: 보보쌤 블로그 글 50개를 수집하고 있습니다..."):
        result = crawl_blog(db)
    if result["success"] > 0:
        st.toast(f"블로그 글 {result['success']}개 자동 수집 완료!", icon="✅")
        st.cache_resource.clear()
        st.rerun()


# ═══════════════════════════════════════
# 사이드바
# ═══════════════════════════════════════
with st.sidebar:
    st.markdown("## ✍️ 글 설정")

    # ─ 모델 ─
    st.markdown('<p class="sidebar-section-label">AI 모델</p>', unsafe_allow_html=True)
    model_names = list_model_names()
    selected_model = st.selectbox(
        "AI 모델", model_names, index=0, label_visibility="collapsed",
        help="글을 생성할 AI 모델. Claude가 한국어 품질이 가장 좋습니다.",
    )

    st.markdown("")

    # ─ 카테고리 ─
    st.markdown('<p class="sidebar-section-label">카테고리</p>', unsafe_allow_html=True)
    db_categories = get_available_categories(db)
    category_options = ["선택 안함"] + (db_categories or AVAILABLE_CATEGORIES) + ["직접 입력"]
    selected_category_label = st.selectbox(
        "블로그 카테고리", category_options, index=0, label_visibility="collapsed",
        help="카테고리 선택 시 해당 문체/구조 + 추천 스킬이 자동 적용됩니다",
    )
    custom_category = ""
    if selected_category_label == "직접 입력":
        custom_category = st.text_input("카테고리 이름", placeholder="예: 의대 입시 전략")
    selected_category = (
        custom_category if selected_category_label == "직접 입력"
        else "" if selected_category_label == "선택 안함"
        else selected_category_label
    )

    preset = CATEGORY_SKILL_PRESETS.get(selected_category, None)
    if preset:
        st.markdown(
            f'<div class="skill-preset-note">{preset["note"]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ─ 페르소나 ─
    st.markdown('<p class="sidebar-section-label">대상 독자</p>', unsafe_allow_html=True)
    personas = db.list_personas()
    persona_names = [p.name for p in personas] + ["직접 입력"]
    selected_persona_name = st.selectbox(
        "대상 독자", persona_names, index=0, label_visibility="collapsed",
        help="글의 대상 독자층",
    )
    custom_persona_text = ""
    if selected_persona_name == "직접 입력":
        custom_persona_text = st.text_input("독자 설명", placeholder="예: IT에 관심 있는 50대 남성")

    st.markdown("")

    # ─ 글 유형 ─
    st.markdown('<p class="sidebar-section-label">글 유형</p>', unsafe_allow_html=True)
    post_type_options = {
        "일반 정보": PostType.GENERAL,
        "리뷰": PostType.REVIEW,
        "리스트형": PostType.LISTICLE,
    }
    selected_type_label = st.selectbox(
        "글 유형", list(post_type_options.keys()), label_visibility="collapsed",
    )
    selected_post_type = post_type_options[selected_type_label]

    st.divider()

    # ─ 스킬 ─
    st.markdown("### 스킬")
    if preset:
        st.caption("카테고리 추천값 적용됨")

    default_search = preset["search"] if preset else True
    default_style = preset["blog_style"] if preset else True
    default_ref = preset.get("reference_posts", True) if preset else True
    default_keyword = preset.get("keyword_analysis", False) if preset else False

    use_search = st.toggle("웹 검색", value=default_search, help="Tavily API로 최신 정보 검색")
    use_blog_style = st.toggle("보보쌤 스타일", value=default_style, help="카테고리별 문체/구조 적용")
    use_ref_posts = st.toggle(
        "기존 글 참조", value=default_ref,
        help=f"보보쌤 블로그 글 {db.count_blog_posts()}개를 참조",
    )
    use_keyword = st.toggle(
        "키워드 분석", value=default_keyword,
        help="네이버 검색량/경쟁도 데이터를 글에 반영 (NAVER_AD_API_KEY 필요)",
    )

    ref_post_count = 3
    if use_ref_posts:
        total_posts = db.count_blog_posts()
        ref_post_count = st.slider(
            "참조할 글 수", min_value=1,
            max_value=total_posts if total_posts > 0 else 50,
            value=3,
        )
        if ref_post_count <= 3:
            est_chars = ref_post_count * 3000
        elif ref_post_count <= 10:
            est_chars = ref_post_count * 2000
        elif ref_post_count <= 20:
            est_chars = ref_post_count * 1500
        else:
            est_chars = ref_post_count * 1000
        est_tokens = est_chars // 4
        est_cost_krw = max(1, int(est_tokens * 3 / 1000000 * 1450))
        st.caption(f"~{est_tokens:,} 토큰 (+{est_cost_krw}원)")

    st.divider()

    with st.expander("비용 안내"):
        st.markdown("""
| 모델 | 비용/회 |
|------|---------|
| Claude Sonnet | ~25원 |
| Claude Haiku | ~7원 |
| GPT-4o | ~40원 |
| GPT-4o Mini | ~7원 |
| Gemini Pro | ~25원 |
| Gemini Flash | ~7원 |

이미지 1장: ~13~25원 · 웹 검색: 무료 1000회/월
        """)

    with st.expander("API 키 설정"):
        st.code(
            "ANTHROPIC_API_KEY=sk-ant-...\n"
            "OPENAI_API_KEY=sk-...\n"
            "GEMINI_API_KEY=AI...\n"
            "TAVILY_API_KEY=tvly-...",
            language="bash",
        )


# ═══════════════════════════════════════
# 메인 영역
# ═══════════════════════════════════════

# ─── 헤더 ───
st.markdown(f"""
<div class="hero">
    <h1>보보쌤 블로그 글 생성기</h1>
    <p class="subtitle">주제를 입력하면 보보쌤 스타일로 네이버 블로그 글을 자동 생성합니다</p>
    <div class="meta">
        <span class="badge">v{__version__}</span>
        <span class="badge">👸 보윤공주 에디션</span>
        <span class="love">자기 사랑해 💕</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── 이미지 설정 ───
with st.expander("🖼️ 이미지 설정", expanded=False):
    default_image = preset["image_gen"] if preset else False

    img_col1, img_col2 = st.columns(2)

    with img_col1:
        st.markdown("**내 이미지 업로드**")
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
💡 글 생성 후 미리보기에서 [이미지 1], [이미지 2] 위치를 확인하세요.
네이버 에디터에서 해당 위치에 이미지를 직접 삽입하면 됩니다.
</div>
            """, unsafe_allow_html=True)

    with img_col2:
        st.markdown("**AI 이미지 생성**")
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

        st.markdown("**워터마크**")
        use_watermark = st.toggle("이미지에 워터마크 넣기", value=False)
        wm_text = "보보쌤 | byhur99"
        if use_watermark:
            wm_text = st.text_input("워터마크 텍스트", value=wm_text, key="main_wm_text")


# ─── 입력 폼 ───
with st.form("generate_form"):
    topic = st.text_area(
        "블로그 주제",
        placeholder="예: 독학재수 3개월 수능 국어 공부법, 에어팟 프로 2 솔직 리뷰",
        height=68,
    )
    extra = st.text_area(
        "추가 지시사항 (선택)",
        placeholder="예: 가성비 위주로 작성해줘, 구체적인 교재 추천 포함",
        height=68,
    )
    submitted = st.form_submit_button(
        "블로그 글 생성하기",
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
                f"당신은 '보보쌤'입니다. 서울대를 졸업하고 직장 생활을 하다가 77일 만에 의대에 합격한 "
                f"20대 중후반 여성 입시 전문가입니다.\n\n"
                f"다음 대상을 위해 블로그 글을 작성합니다: {custom_persona_text}. "
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

    if not use_keyword:
        registry.disable("keyword_analysis")
    else:
        registry.enable("keyword_analysis")

    # 이미지 배치 지시
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
    with st.spinner("블로그 글을 생성하고 있습니다... (30초~1분)"):
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

    # session_state에 저장 (리런 시 레퍼런스 추가용)
    st.session_state["last_generation"] = {
        "id": generation.id,
        "topic": topic.strip(),
        "output_markdown": generation.output_markdown,
        "category": selected_category,
    }

    # ── AI 이미지 생성 ──
    generated_images = []
    if use_image_gen:
        with st.spinner("이미지를 생성하고 있습니다..."):
            try:
                image_model_id = get_image_model_id(selected_image_model_name)
                generated_images = generate_blog_images(
                    topic=topic.strip(),
                    num_images=num_images,
                    model=image_model_id,
                )
            except Exception as e:
                st.warning(f"이미지 생성 실패: {e}")

    # ── 결과 ──
    st.markdown(
        f'<div class="result-success">생성 완료 · ID #{generation.id} · {selected_model}</div>',
        unsafe_allow_html=True,
    )

    # 탭
    tab_names = ["미리보기", "HTML 복사", "Markdown"]
    has_any_images = bool(generated_images) or bool(uploaded_files)
    if has_any_images:
        tab_names.append("이미지")
    tab_names.append("참조 데이터")
    tab_names.append("프롬프트")

    tabs = st.tabs(tab_names)
    tab_idx = 0

    with tabs[tab_idx]:
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

    with tabs[tab_idx]:
        st.caption("아래 HTML을 복사해서 네이버 에디터의 HTML 모드에 붙여넣으세요")
        st.code(generation.output_html, language="html")
    tab_idx += 1

    with tabs[tab_idx]:
        st.caption("Markdown 원문")
        st.code(generation.output_markdown, language="markdown")
    tab_idx += 1

    if has_any_images:
        with tabs[tab_idx]:
            st.caption(
                "네이버 블로그 에디터에서 '사진' 버튼으로 업로드하세요. "
                "[이미지 N] 마커 위치에 삽입하면 됩니다."
            )

            if uploaded_files:
                st.markdown("**업로드한 이미지**")
                upload_cols = st.columns(min(len(uploaded_files), 3))
                for idx, f in enumerate(uploaded_files):
                    with upload_cols[idx % 3]:
                        img_data = f.getvalue()
                        if use_watermark:
                            from naverblog.watermark import watermark_image
                            img_data = watermark_image(img_data, text=wm_text)
                        st.image(img_data, caption=f"[이미지 {idx + 1}] {f.name}", use_container_width=True)
                        st.download_button(
                            f"다운로드 ({idx + 1})",
                            data=img_data,
                            file_name=f"wm_{f.name}" if use_watermark else f.name,
                            mime="image/png" if use_watermark else f.type,
                            key=f"dl_upload_{idx}",
                        )

            if generated_images:
                st.markdown("**AI 생성 이미지**")
                gen_cols = st.columns(min(len(generated_images), 3))
                for idx, img in enumerate(generated_images):
                    with gen_cols[idx % 3]:
                        label = ["대표 (썸네일)", "본문 삽입용", "추가", "추가"][idx]
                        img_data = img.data
                        if use_watermark:
                            from naverblog.watermark import watermark_image
                            img_data = watermark_image(img_data, text=wm_text)
                        st.image(img_data, caption=f"{idx + 1}. {label}", use_container_width=True)
                        st.download_button(
                            f"다운로드 ({idx + 1})",
                            data=img_data,
                            file_name=f"ai_image_{idx + 1}.png",
                            mime="image/png",
                            key=f"dl_gen_{idx}",
                        )
                        with st.expander("프롬프트"):
                            st.caption(img.prompt)
        tab_idx += 1

    with tabs[tab_idx]:
        st.caption("글 생성 시 LLM에게 주입된 컨텍스트를 확인합니다.")

        if use_blog_style:
            with st.expander("스타일 가이드", expanded=False):
                prompt_text = generation.prompt_used
                style_start = prompt_text.find("## 블로그 스타일 가이드")
                if style_start >= 0:
                    style_end = prompt_text.find("\n## ", style_start + 10)
                    if style_end < 0:
                        style_end = style_start + 3000
                    st.text(prompt_text[style_start:style_end])
                else:
                    st.info("스타일 가이드 데이터 없음")

        if use_ref_posts:
            with st.expander(f"레퍼런스 글 ({ref_post_count}개)", expanded=True):
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

        if use_search:
            with st.expander("웹 검색 결과", expanded=False):
                prompt_text = generation.prompt_used
                search_start = prompt_text.find("## 참고할 최신 정보")
                if search_start >= 0:
                    search_end = prompt_text.find("\n## ", search_start + 10)
                    if search_end < 0:
                        search_end = search_start + 3000
                    st.text(prompt_text[search_start:search_end])
                else:
                    st.info("검색 데이터 없음")

        total_len = len(generation.prompt_used)
        st.metric("전체 프롬프트 길이", f"{total_len:,}자 (~{total_len//4:,} 토큰)")
    tab_idx += 1

    with tabs[tab_idx]:
        st.caption("AI에게 전달된 전체 프롬프트 (디버깅용)")
        st.text(generation.prompt_used)

elif submitted:
    st.warning("주제를 입력해주세요!")

# ── 레퍼런스에 추가 (session_state 기반) ──
last_gen = st.session_state.get("last_generation")
if last_gen:
    st.divider()
    st.markdown("#### 이 글을 레퍼런스에 추가하시겠습니까?")
    st.caption("추가하면 다음 글 생성 시 이 글이 참조 컨텍스트로 사용됩니다.")

    ref_col1, ref_col2 = st.columns([1, 1])
    with ref_col1:
        cat_options = (
            [last_gen["category"]] + [c for c in (db_categories or AVAILABLE_CATEGORIES) if c != last_gen["category"]]
            if last_gen.get("category")
            else db_categories or AVAILABLE_CATEGORIES
        )
        ref_category = st.selectbox("레퍼런스 카테고리", cat_options, index=0, key="ref_save_cat")
    with ref_col2:
        if st.button("📥 레퍼런스에 추가", type="primary", key="save_to_ref"):
            import time as _time
            post_id = f"gen_{last_gen['id']}_{int(_time.time())}"
            db.save_blog_post(
                post_id=post_id,
                title=last_gen["topic"],
                category=ref_category,
                content=last_gen["output_markdown"],
            )
            st.success(f"레퍼런스에 추가됨! (카테고리: {ref_category})")
            del st.session_state["last_generation"]
            st.cache_resource.clear()

st.divider()

# ─── 이전 생성 기록 ───
st.markdown('<p class="history-label">이전 생성 기록</p>', unsafe_allow_html=True)

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
st.markdown("")
st.markdown(f"""
<div class="app-footer">
    보보쌤 블로그 스타일 기반 · Streamlit + LiteLLM + Imagen<br>
    👸 <span class="love-msg">보윤공주</span> · <span class="love-msg">보윤 빗취</span><br>
    <span class="love-msg">자기 사랑해 💕</span><br>
    <span class="ver">v{__version__}</span>
</div>
""", unsafe_allow_html=True)
