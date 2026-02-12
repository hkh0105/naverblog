"""워터마크 페이지 - 이미지/PDF에 커스텀 워터마크 삽입."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from naverblog.config import inject_secrets
inject_secrets()

from naverblog.watermark import watermark_image, watermark_pdf, _hex_to_rgb

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
    .settings-section {
        background: #f8f7ff;
        border: 1px solid #e9e5ff;
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    }
    .settings-section h3 { font-size: 0.95rem; font-weight: 600; color: #5b21b6; margin: 0 0 0.75rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h1>워터마크</h1>
    <p>이미지나 PDF에 커스텀 워터마크를 삽입합니다</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# 공통 설정
# ═══════════════════════════════════════
st.markdown('<div class="settings-section"><h3>워터마크 설정</h3></div>', unsafe_allow_html=True)

POSITION_OPTIONS = {
    "대각선 반복 (타일)": "diagonal-tiled",
    "대각선 1줄": "diagonal-single",
    "우측 하단": "bottom-right",
    "좌측 하단": "bottom-left",
    "우측 상단": "top-right",
    "좌측 상단": "top-left",
    "중앙": "center",
}

col1, col2 = st.columns(2)
with col1:
    wm_text = st.text_area(
        "워터마크 텍스트",
        value="보보쌤 | byhur99",
        height=68,
        help="여러 줄 입력 가능",
    )
with col2:
    wm_position = st.selectbox(
        "배치 스타일",
        list(POSITION_OPTIONS.keys()),
        index=0,
    )

col3, col4, col5 = st.columns(3)
with col3:
    wm_opacity = st.slider("투명도", 5, 100, 30, step=5, help="낮을수록 투명, 높을수록 진하게")
with col4:
    wm_font_size = st.slider("글자 크기", 10, 200, 50, step=5)
with col5:
    wm_rotation = st.slider("회전 각도", 0, 90, 30, step=5, help="대각선 모드에서 사용")

col6, col7 = st.columns(2)
with col6:
    wm_color = st.color_picker("글자 색상", value="#808080")
with col7:
    wm_bg_box = st.checkbox("배경 박스 표시", value=False, help="코너/중앙 모드에서 텍스트 뒤에 반투명 배경")

position_value = POSITION_OPTIONS[wm_position]
color_rgb = _hex_to_rgb(wm_color)

st.divider()

# ─── 탭 ───
tab_image, tab_pdf = st.tabs(["🖼️ 이미지 워터마크", "📄 PDF 워터마크"])

# ═══════════════════════════════════════
# 이미지 워터마크
# ═══════════════════════════════════════
with tab_image:
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
                        position=position_value,
                        font_size=wm_font_size,
                        color=color_rgb,
                        rotation=wm_rotation,
                        bg_box=wm_bg_box,
                    )
                    results.append((f.name, wm_data))

            st.success(f"{len(results)}장 워터마크 완료")

            cols = st.columns(min(len(results), 3))
            for idx, (name, data) in enumerate(results):
                with cols[idx % 3]:
                    st.image(data, caption=name, use_container_width=True)
                    st.download_button(
                        "다운로드",
                        data=data,
                        file_name=f"wm_{name.rsplit('.', 1)[0]}.png",
                        mime="image/png",
                        key=f"dl_wm_img_{idx}",
                    )

# ═══════════════════════════════════════
# PDF 워터마크
# ═══════════════════════════════════════
with tab_pdf:
    pdf_files = st.file_uploader(
        "PDF 업로드",
        type=["pdf"],
        accept_multiple_files=True,
        key="wm_pdf",
    )

    if pdf_files:
        for pf in pdf_files:
            st.info(f"**{pf.name}** ({pf.size / 1024:.0f} KB)")

        if st.button("워터마크 적용", type="primary", use_container_width=True, key="apply_pdf"):
            for pf in pdf_files:
                with st.spinner(f"{pf.name} 처리 중..."):
                    try:
                        wm_pdf_data = watermark_pdf(
                            pf.getvalue(),
                            text=wm_text,
                            opacity=wm_opacity / 100,
                            position=position_value,
                            font_size=wm_font_size,
                            color=color_rgb,
                            rotation=wm_rotation,
                        )
                        st.success(f"{pf.name} 워터마크 완료")
                        st.download_button(
                            f"📥 {pf.name} 다운로드",
                            data=wm_pdf_data,
                            file_name=f"wm_{pf.name}",
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"dl_wm_pdf_{pf.name}",
                        )
                    except ImportError:
                        st.error("pypdf 패키지가 필요합니다. `pip install pypdf`")
                    except Exception as e:
                        st.error(f"PDF 처리 실패: {e}")
