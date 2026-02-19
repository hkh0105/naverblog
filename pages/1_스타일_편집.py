"""스타일 편집 페이지 - 보보쌤 블로그 스타일 가이드를 웹에서 수정."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from naverblog.config import inject_secrets
inject_secrets()

from naverblog.database import Database, create_database
from naverblog.skills.blog_style import (
    DEFAULT_CATEGORY_STYLES,
    DEFAULT_COMMON_STYLE,
    seed_default_styles,
)

st.set_page_config(
    page_title="스타일 편집 | 보보쌤",
    page_icon="🎨",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .block-container { max-width: 960px; padding-top: 1.5rem; }
    .page-header {
        background: linear-gradient(135deg, #7c3aed 0%, #a78bfa 50%, #c4b5fd 100%);
        padding: 2rem 2.5rem;
        border-radius: 1.25rem;
        color: white;
        margin-bottom: 2rem;
    }
    .page-header h1 { color: white !important; font-size: 1.5rem; font-weight: 700; margin: 0 0 0.3rem 0; }
    .page-header p { color: rgba(255,255,255,0.85); font-size: 0.88rem; margin: 0; font-weight: 300; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db() -> Database:
    return create_database()


db = get_db()

seed_default_styles(db)

st.markdown("""
<div class="page-header">
    <h1>스타일 가이드 편집</h1>
    <p>보보쌤 블로그 문체와 구조 규칙을 수정하세요. 수정 즉시 다음 글 생성에 반영됩니다.</p>
</div>
""", unsafe_allow_html=True)

# ─── 탭: 공통 스타일 / 카테고리별 / 새 카테고리 추가 ───
tab_common, tab_categories, tab_add = st.tabs([
    "📝 공통 스타일", "📂 카테고리별 스타일", "➕ 새 카테고리 추가"
])

# ═══════════════════════════════════════
# 공통 스타일 편집
# ═══════════════════════════════════════
with tab_common:
    st.markdown("### 공통 스타일 가이드")
    st.caption("모든 카테고리의 글에 공통으로 적용되는 문체, 구조, 표현 규칙입니다.")

    current_common = db.get_blog_style("common") or DEFAULT_COMMON_STYLE

    with st.form("edit_common"):
        edited_common = st.text_area(
            "공통 스타일 (Markdown)",
            value=current_common,
            height=500,
            help="이 내용이 모든 글 생성 시 LLM에게 전달됩니다.",
        )

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            save_common = st.form_submit_button("💾 저장", type="primary")
        with col2:
            reset_common = st.form_submit_button("🔄 기본값 복원")

    if save_common:
        db.save_blog_style("common", edited_common)
        st.success("공통 스타일이 저장되었습니다!")
        st.rerun()

    if reset_common:
        db.save_blog_style("common", DEFAULT_COMMON_STYLE)
        st.success("공통 스타일이 기본값으로 복원되었습니다!")
        st.rerun()

    # 미리보기
    with st.expander("👁️ 미리보기 (Markdown 렌더링)"):
        st.markdown(current_common)

# ═══════════════════════════════════════
# 카테고리별 스타일 편집
# ═══════════════════════════════════════
with tab_categories:
    st.markdown("### 카테고리별 스타일")
    st.caption("각 카테고리에 맞는 톤, 구조, 특징적 패턴을 편집합니다.")

    all_styles = db.list_blog_styles()
    categories = [k for k in all_styles if k != "common"]

    if not categories:
        st.info("카테고리가 없습니다. '새 카테고리 추가' 탭에서 추가해주세요.")
    else:
        selected_cat = st.selectbox(
            "편집할 카테고리", categories,
            format_func=lambda x: f"📂 {x}",
        )

        if selected_cat:
            current_cat_style = all_styles.get(selected_cat, "")
            default_cat_style = DEFAULT_CATEGORY_STYLES.get(selected_cat, "")

            with st.form(f"edit_cat_{selected_cat}"):
                edited_cat = st.text_area(
                    f"{selected_cat} 스타일",
                    value=current_cat_style,
                    height=350,
                )

                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    save_cat = st.form_submit_button("💾 저장", type="primary")
                with col2:
                    if default_cat_style:
                        reset_cat = st.form_submit_button("🔄 기본값 복원")
                    else:
                        reset_cat = False
                with col3:
                    delete_cat = st.form_submit_button("🗑️ 삭제", type="secondary")

            if save_cat:
                db.save_blog_style(selected_cat, edited_cat)
                st.success(f"'{selected_cat}' 스타일이 저장되었습니다!")
                st.rerun()

            if reset_cat and default_cat_style:
                db.save_blog_style(selected_cat, default_cat_style)
                st.success(f"'{selected_cat}' 스타일이 기본값으로 복원되었습니다!")
                st.rerun()

            if delete_cat:
                db.delete_blog_style(selected_cat)
                st.success(f"'{selected_cat}' 카테고리가 삭제되었습니다!")
                st.rerun()

            with st.expander("👁️ 미리보기"):
                st.markdown(current_cat_style)

# ═══════════════════════════════════════
# 새 카테고리 추가
# ═══════════════════════════════════════
with tab_add:
    st.markdown("### 새 카테고리 추가")
    st.caption("새로운 블로그 카테고리와 스타일 규칙을 추가합니다.")

    template = """\
### 카테고리: [카테고리명]
- **톤**:
- **구조**:
- **핵심 메시지**: ""
- **특징적 패턴**:
  -
  -
- **예시 도입부**: \"\""""

    with st.form("add_category"):
        new_cat_name = st.text_input(
            "카테고리 이름",
            placeholder="예: 의대 면접 준비",
        )
        new_cat_style = st.text_area(
            "스타일 규칙 (Markdown)",
            value=template,
            height=300,
            help="이 카테고리의 톤, 구조, 특징적 패턴 등을 정의하세요.",
        )
        add_btn = st.form_submit_button("➕ 카테고리 추가", type="primary")

    if add_btn:
        if not new_cat_name.strip():
            st.error("카테고리 이름을 입력해주세요.")
        elif db.get_blog_style(new_cat_name.strip()):
            st.error(f"'{new_cat_name}' 카테고리가 이미 존재합니다.")
        else:
            db.save_blog_style(new_cat_name.strip(), new_cat_style)
            st.success(f"'{new_cat_name}' 카테고리가 추가되었습니다!")
            st.balloons()
            st.rerun()

# ─── 전체 스타일 현황 ───
st.divider()
st.markdown("### 📊 현재 스타일 현황")
all_styles = db.list_blog_styles()
st.metric("총 스타일 수", f"{len(all_styles)}개 (공통 1 + 카테고리 {len(all_styles) - 1})")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**등록된 카테고리:**")
    for k in all_styles:
        if k != "common":
            st.markdown(f"- 📂 {k}")
with col2:
    st.markdown("**기본값과 다른 항목:**")
    modified = []
    if all_styles.get("common") != DEFAULT_COMMON_STYLE:
        modified.append("공통 스타일")
    for cat_name, cat_style in all_styles.items():
        if cat_name == "common":
            continue
        default = DEFAULT_CATEGORY_STYLES.get(cat_name)
        if default and cat_style != default:
            modified.append(cat_name)
    if modified:
        for m in modified:
            st.markdown(f"- ✏️ {m} (수정됨)")
    else:
        st.markdown("_모두 기본값 사용 중_")
