"""워터마크 페이지 - 이미지/PDF에 보보쌤 워터마크 삽입."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from naverblog.config import inject_secrets
inject_secrets()

from naverblog.watermark import watermark_image, watermark_pdf

st.set_page_config(
    page_title="워터마크 | 보보쌤",
    page_icon="💧",
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

st.markdown("""
<div class="page-header">
    <h1>워터마크</h1>
    <p>이미지나 PDF에 보보쌤 워터마크를 삽입합니다</p>
</div>
""", unsafe_allow_html=True)

# ─── 설정 ───
col_settings1, col_settings2 = st.columns(2)
with col_settings1:
    wm_text = st.text_input("워터마크 텍스트", value="보보쌤 | byhur99")
with col_settings2:
    wm_opacity = st.slider("불투명도", 10, 100, 40, step=5, help="높을수록 진하게")

# ─── 탭 ───
tab_image, tab_pdf = st.tabs(["🖼️ 이미지 워터마크", "📄 PDF 워터마크"])

# ═══════════════════════════════════════
# 이미지 워터마크
# ═══════════════════════════════════════
with tab_image:
    st.caption("이미지에 워터마크를 삽입합니다. 여러 장 동시 처리 가능.")

    position = st.selectbox(
        "워터마크 위치",
        ["우하단", "좌하단", "중앙"],
    )
    pos_map = {"우하단": "bottom-right", "좌하단": "bottom-left", "중앙": "center"}

    img_files = st.file_uploader(
        "이미지 업로드",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="wm_images",
    )

    if img_files:
        st.markdown(f"**{len(img_files)}장** 업로드됨")

        if st.button("워터마크 적용", type="primary", use_container_width=True, key="apply_img"):
            results = []
            for f in img_files:
                with st.spinner(f"{f.name} 처리 중..."):
                    wm_data = watermark_image(
                        f.getvalue(),
                        text=wm_text,
                        opacity=int(wm_opacity * 255 / 100),
                        position=pos_map[position],
                    )
                    results.append((f.name, wm_data))

            st.success(f"{len(results)}장 워터마크 완료")

            cols = st.columns(min(len(results), 3))
            for idx, (name, data) in enumerate(results):
                with cols[idx % 3]:
                    st.image(data, caption=name, use_container_width=True)
                    st.download_button(
                        f"다운로드",
                        data=data,
                        file_name=f"wm_{name.rsplit('.', 1)[0]}.png",
                        mime="image/png",
                        key=f"dl_wm_img_{idx}",
                    )

# ═══════════════════════════════════════
# PDF 워터마크
# ═══════════════════════════════════════
with tab_pdf:
    st.caption("PDF 각 페이지에 대각선 워터마크를 삽입합니다.")

    pdf_font_size = st.slider("텍스트 크기", 20, 100, 50, step=5, key="pdf_fs")

    pdf_file = st.file_uploader(
        "PDF 업로드",
        type=["pdf"],
        key="wm_pdf",
    )

    if pdf_file:
        st.info(f"**{pdf_file.name}** ({pdf_file.size / 1024:.0f} KB)")

        if st.button("워터마크 적용", type="primary", use_container_width=True, key="apply_pdf"):
            with st.spinner("PDF 워터마크 처리 중..."):
                try:
                    wm_pdf_data = watermark_pdf(
                        pdf_file.getvalue(),
                        text=wm_text,
                        opacity=wm_opacity / 100,
                        font_size=pdf_font_size,
                    )
                    st.success("PDF 워터마크 완료")
                    st.download_button(
                        "워터마크 PDF 다운로드",
                        data=wm_pdf_data,
                        file_name=f"wm_{pdf_file.name}",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except ImportError:
                    st.error("pypdf 패키지가 필요합니다. `pip install pypdf`")
                except Exception as e:
                    st.error(f"PDF 처리 실패: {e}")
