"""레퍼런스 글 관리 페이지 - 크롤링된 보보쌤 블로그 글 조회/추가/삭제."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from naverblog.config import inject_secrets
inject_secrets()

from naverblog.database import Database

st.set_page_config(
    page_title="레퍼런스 글 관리 | 보보쌤",
    page_icon="📖",
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
    return Database()


db = get_db()

st.markdown("""
<div class="page-header">
    <h1>레퍼런스 글 관리</h1>
    <p>보보쌤 블로그에서 크롤링한 글을 확인하고 관리합니다. 이 글들이 새 글 생성 시 참조됩니다.</p>
</div>
""", unsafe_allow_html=True)

# ─── 통계 ───
total = db.count_blog_posts()
categories = db.get_blog_post_categories()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("총 저장된 글", f"{total}개")
with col2:
    st.metric("카테고리 수", f"{len(categories)}개")
with col3:
    total_chars = sum(len(p["content"]) for p in db.list_blog_posts())
    st.metric("총 글자 수", f"{total_chars:,}자")

st.divider()

# ─── 탭: 글 목록 / 글 추가 / 일괄 관리 ───
tab_list, tab_add, tab_bulk = st.tabs(["📚 글 목록", "➕ 글 추가", "🔧 일괄 관리"])

# ═══════════════════════════════════════
# 글 목록 + 삭제/편집
# ═══════════════════════════════════════
with tab_list:
    if total == 0:
        st.info("저장된 레퍼런스 글이 없습니다. '글 추가' 탭에서 추가하거나 크롤링 스크립트를 실행해주세요.")
    else:
        filter_options = ["전체"] + categories
        selected_filter = st.selectbox("카테고리 필터", filter_options)

        if selected_filter == "전체":
            posts = db.list_blog_posts()
        else:
            posts = db.list_blog_posts(category=selected_filter)

        st.markdown(f"### {selected_filter} ({len(posts)}개)")

        for post in posts:
            with st.expander(f"📝 {post['title']} | {post['category']} ({len(post['content']):,}자)"):
                # 메타 정보
                meta_cols = st.columns([2, 2, 1, 1])
                with meta_cols[0]:
                    st.caption(f"카테고리: {post['category']}")
                with meta_cols[1]:
                    st.caption(f"글자 수: {len(post['content']):,}자")
                with meta_cols[2]:
                    if post.get("link"):
                        st.markdown(f"[원문 보기]({post['link']})")
                with meta_cols[3]:
                    if st.button("🗑️ 삭제", key=f"del_{post['post_id']}", type="secondary"):
                        with db._get_conn() as conn:
                            conn.execute("DELETE FROM blog_posts WHERE post_id = ?", (post["post_id"],))
                        st.success(f"'{post['title'][:20]}...' 삭제됨")
                        st.rerun()

                st.markdown("---")

                # 내용 편집
                with st.form(f"edit_{post['post_id']}"):
                    new_title = st.text_input("제목", value=post["title"], key=f"title_{post['post_id']}")
                    new_category = st.text_input("카테고리", value=post["category"], key=f"cat_{post['post_id']}")
                    new_content = st.text_area(
                        "본문",
                        value=post["content"],
                        height=300,
                        key=f"content_{post['post_id']}",
                    )
                    save_btn = st.form_submit_button("💾 수정 저장", type="primary")

                if save_btn:
                    db.save_blog_post(
                        post_id=post["post_id"],
                        title=new_title,
                        category=new_category,
                        content=new_content,
                        pub_date=post.get("pub_date", ""),
                        link=post.get("link", ""),
                    )
                    st.success(f"'{new_title[:30]}' 수정 저장됨!")
                    st.rerun()

# ═══════════════════════════════════════
# 글 추가
# ═══════════════════════════════════════
with tab_add:
    st.markdown("### 새 레퍼런스 글 추가")
    st.caption("보보쌤이 작성한 글이나 참고할 글을 직접 추가합니다.")

    with st.form("add_post"):
        add_title = st.text_input("제목", placeholder="예: 수능 국어 공부법 - 현대시 분석 꿀팁")
        add_category = st.selectbox(
            "카테고리",
            categories + ["직접 입력"],
            index=0 if categories else 0,
        )
        custom_cat = ""
        if add_category == "직접 입력":
            custom_cat = st.text_input("카테고리 이름", placeholder="예: 의대 면접 준비")

        add_content = st.text_area(
            "본문",
            height=400,
            placeholder="블로그 글 본문을 붙여넣으세요...",
        )
        add_link = st.text_input("원문 링크 (선택)", placeholder="https://blog.naver.com/byhur99/...")

        add_btn = st.form_submit_button("➕ 레퍼런스 글 추가", type="primary")

    if add_btn:
        if not add_title.strip():
            st.error("제목을 입력해주세요.")
        elif not add_content.strip() or len(add_content.strip()) < 50:
            st.error("본문을 50자 이상 입력해주세요.")
        else:
            final_cat = custom_cat.strip() if add_category == "직접 입력" else add_category
            # 고유 ID 생성
            import time
            post_id = f"manual_{int(time.time())}"
            db.save_blog_post(
                post_id=post_id,
                title=add_title.strip(),
                category=final_cat,
                content=add_content.strip(),
                link=add_link.strip(),
            )
            st.success(f"'{add_title.strip()[:30]}' 추가됨! ({len(add_content):,}자)")
            st.balloons()
            st.rerun()

# ═══════════════════════════════════════
# 일괄 관리
# ═══════════════════════════════════════
with tab_bulk:
    st.markdown("### 일괄 관리")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 카테고리별 현황")
        for cat in categories:
            cat_posts = db.list_blog_posts(category=cat)
            cat_chars = sum(len(p["content"]) for p in cat_posts)
            st.markdown(f"- **{cat}**: {len(cat_posts)}개 ({cat_chars:,}자)")

    with col2:
        st.markdown("#### 도구")

        # 카테고리별 전체 삭제
        if categories:
            del_cat = st.selectbox("삭제할 카테고리", categories, key="bulk_del_cat")
            if st.button(f"🗑️ '{del_cat}' 카테고리 전체 삭제", type="secondary"):
                with db._get_conn() as conn:
                    cnt = conn.execute(
                        "SELECT COUNT(*) as cnt FROM blog_posts WHERE category = ?",
                        (del_cat,),
                    ).fetchone()["cnt"]
                    conn.execute("DELETE FROM blog_posts WHERE category = ?", (del_cat,))
                st.success(f"'{del_cat}' 카테고리 {cnt}개 글 삭제됨")
                st.rerun()

        st.divider()

        # 크롤링 안내
        st.markdown("#### 블로그 재크롤링")
        st.caption("새 글이 추가되었거나 기존 글을 업데이트하려면 크롤링을 다시 실행하세요.")
        st.code("python scripts/crawl_blog.py", language="bash")
        st.caption("이미 저장된 글은 건너뛰고 새 글만 추가됩니다.")
