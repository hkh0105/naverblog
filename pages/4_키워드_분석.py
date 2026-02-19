"""키워드 분석 - 블랙키위 스타일 네이버 키워드 분석 도구."""

from __future__ import annotations

import io
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from naverblog.config import inject_secrets

inject_secrets()

import os
from difflib import SequenceMatcher

import pandas as pd

from naverblog.database import create_database
from naverblog.naver_api import (
    DetailedSaturation,
    KeywordGrade,
    KeywordMetrics,
    NaverDataLabClient,
    NaverSearchAdClient,
    calculate_detailed_saturation,
    calculate_keyword_grade,
    calculate_saturation,
)

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="키워드 분석",
    page_icon="🔍",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .block-container { max-width: 1100px; padding-top: 1.5rem; }

    .kw-hero {
        background: linear-gradient(135deg, #059669 0%, #34d399 50%, #6ee7b7 100%);
        padding: 2rem 2.5rem 1.5rem;
        border-radius: 1.25rem;
        color: white;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .kw-hero::before {
        content: '';
        position: absolute; top: -50%; right: -20%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .kw-hero h1 {
        color: white !important;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
    }
    .kw-hero .subtitle {
        color: rgba(255,255,255,0.88);
        font-size: 0.88rem;
        font-weight: 300;
    }

    .api-status {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 1rem;
        font-size: 0.72rem;
        font-weight: 600;
    }
    .api-ok { background: #d1fae5; color: #065f46; }
    .api-no { background: #fef3c7; color: #92400e; }

    /* 등급 뱃지 */
    .grade-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 56px; height: 56px;
        border-radius: 50%;
        font-size: 1.5rem; font-weight: 800;
        color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .grade-S { background: linear-gradient(135deg, #f59e0b, #f97316); }
    .grade-A { background: linear-gradient(135deg, #10b981, #059669); }
    .grade-B { background: linear-gradient(135deg, #3b82f6, #2563eb); }
    .grade-C { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
    .grade-D { background: linear-gradient(135deg, #ef4444, #dc2626); }

    /* 포화 레벨 뱃지 */
    .sat-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 0.4rem;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .sat-low { background: #d1fae5; color: #065f46; }
    .sat-mid { background: #fef3c7; color: #92400e; }
    .sat-high { background: #fee2e2; color: #991b1b; }
    .sat-na { background: #f3f4f6; color: #6b7280; }

    /* 점수 바 */
    .score-bar {
        height: 8px; border-radius: 4px;
        background: #e5e7eb;
        overflow: hidden;
        margin: 0.3rem 0;
    }
    .score-bar-fill {
        height: 100%; border-radius: 4px;
        transition: width 0.5s ease;
    }

    /* 워드 클라우드 태그 */
    .tag-cloud { display: flex; flex-wrap: wrap; gap: 6px; padding: 0.5rem 0; }
    .tag-item {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 1rem;
        background: #f0fdf4;
        color: #166534;
        font-size: 0.78rem;
        border: 1px solid #bbf7d0;
    }
    .tag-item-lg { font-size: 1rem; font-weight: 600; background: #dcfce7; }
    .tag-item-md { font-size: 0.88rem; font-weight: 500; }
    .tag-item-sm { font-size: 0.75rem; color: #4ade80; }

    /* 히스토리 */
    .history-chip {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        margin: 0.15rem;
        border-radius: 1rem;
        background: #f3f4f6;
        color: #374151;
        font-size: 0.75rem;
        cursor: pointer;
        border: 1px solid #e5e7eb;
    }
    .history-chip:hover { background: #e5e7eb; }
</style>
""", unsafe_allow_html=True)


# ─── 헬퍼 함수 ───


def safe_cache_get(db, keyword: str, data_type: str):
    """캐시 조회 (테이블 없어도 안전)."""
    try:
        return db.get_keyword_cache(keyword, data_type)
    except Exception:
        return None


def safe_cache_save(db, keyword: str, data_type: str, result: dict, ttl_hours: int = 24):
    """캐시 저장 (테이블 없어도 안전)."""
    try:
        db.save_keyword_cache(keyword, data_type, result, ttl_hours=ttl_hours)
    except Exception:
        pass


def sat_badge_html(level: str) -> str:
    """포화 레벨 → 뱃지 HTML."""
    cls_map = {"낮음": "sat-low", "보통": "sat-mid", "높음": "sat-high"}
    cls = cls_map.get(level, "sat-na")
    return f'<span class="sat-badge {cls}">{level}</span>'


def grade_badge_html(grade: str) -> str:
    """등급 → 뱃지 HTML."""
    return f'<span class="grade-badge grade-{grade}">{grade}</span>'


def score_bar_html(score: float, color: str = "#10b981") -> str:
    """점수 → 프로그레스 바 HTML."""
    return (
        f'<div class="score-bar">'
        f'<div class="score-bar-fill" style="width:{score}%;background:{color};"></div>'
        f'</div>'
    )


def spelling_similarity(a: str, b: str) -> float:
    """두 키워드 간 철자 유사도 (0~1)."""
    return SequenceMatcher(None, a.replace(" ", ""), b.replace(" ", "")).ratio()


def extract_hashtags(keywords: list[KeywordMetrics], top_n: int = 20) -> list[str]:
    """연관 키워드에서 해시태그 추출."""
    sorted_kw = sorted(keywords, key=lambda x: x.total_monthly_qc, reverse=True)
    return [f"#{m.keyword}" for m in sorted_kw[:top_n]]


def get_keyword_blog_counts(
    datalab: NaverDataLabClient, keywords: list[str], max_count: int = 15
) -> dict[str, int]:
    """키워드별 블로그 발행수 조회 (최대 max_count개)."""
    counts: dict[str, int] = {}
    for kw in keywords[:max_count]:
        try:
            counts[kw] = datalab.get_blog_count(kw)
        except Exception:
            counts[kw] = 0
    return counts


def build_topic_clusters(
    keywords: list[KeywordMetrics], main_keyword: str,
) -> dict[str, list[KeywordMetrics]]:
    """연관 키워드를 주제별 클러스터로 분류 (단어 기반 간단 클러스터링)."""
    # 메인 키워드에서 핵심 단어 추출
    main_words = set(main_keyword.replace(" ", ""))

    clusters: dict[str, list[KeywordMetrics]] = {}

    for kw in keywords:
        kw_text = kw.keyword
        # 공통 접두사/접미사 기반 클러스터링
        assigned = False
        for cluster_name, cluster_items in clusters.items():
            # 기존 클러스터와 2글자 이상 공통 부분 있으면 합류
            ref = cluster_items[0].keyword
            common = _longest_common_substring(kw_text, ref)
            if len(common) >= 2:
                cluster_items.append(kw)
                assigned = True
                break

        if not assigned:
            clusters[kw_text] = [kw]

    # 너무 작은 클러스터 → "기타"로 합치기
    final: dict[str, list[KeywordMetrics]] = {}
    etc_list: list[KeywordMetrics] = []
    for name, items in clusters.items():
        if len(items) >= 2:
            final[name] = items
        else:
            etc_list.extend(items)
    if etc_list:
        final["기타"] = etc_list

    return final


def _longest_common_substring(s1: str, s2: str) -> str:
    """두 문자열의 최장 공통 부분 문자열."""
    m = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
    longest, end_pos = 0, 0
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i - 1] == s2[j - 1]:
                m[i][j] = m[i - 1][j - 1] + 1
                if m[i][j] > longest:
                    longest = m[i][j]
                    end_pos = i
    return s1[end_pos - longest:end_pos]


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """DataFrame → CSV bytes (UTF-8 BOM)."""
    buf = io.BytesIO()
    buf.write(b"\xef\xbb\xbf")  # UTF-8 BOM for Excel
    df.to_csv(buf, index=False, encoding="utf-8")
    return buf.getvalue()


# ─── 초기화 ───
@st.cache_resource
def get_db():
    return create_database()


db = get_db()

ad_client = NaverSearchAdClient()
datalab_client = NaverDataLabClient()

# 검색 히스토리 초기화
if "keyword_history" not in st.session_state:
    st.session_state["keyword_history"] = []

# ─── 헤더 ───
st.markdown("""
<div class="kw-hero">
    <h1>🔍 키워드 분석</h1>
    <p class="subtitle">네이버 검색량, 경쟁도, 트렌드, 포화지수를 분석하여 최적의 블로그 키워드를 찾아보세요</p>
</div>
""", unsafe_allow_html=True)

# ─── API 상태 ───
col_status1, col_status2 = st.columns(2)
with col_status1:
    if ad_client.is_configured:
        st.markdown(
            '<span class="api-status api-ok">✅ 검색광고 API 연결됨</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="api-status api-no">⚠️ 검색광고 API 미설정</span>',
            unsafe_allow_html=True,
        )
with col_status2:
    if datalab_client.is_configured:
        st.markdown(
            '<span class="api-status api-ok">✅ 데이터랩 API 연결됨</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="api-status api-no">⚠️ 데이터랩 API 미설정</span>',
            unsafe_allow_html=True,
        )

if not ad_client.is_configured and not datalab_client.is_configured:
    st.warning(
        "API 키가 설정되지 않았습니다. `.env` 파일에 네이버 API 키를 추가해주세요.\n\n"
        "**검색광고 API** (검색량/경쟁도): https://searchad.naver.com\n"
        "- `NAVER_AD_API_KEY`, `NAVER_AD_SECRET_KEY`, `NAVER_AD_CUSTOMER_ID`\n\n"
        "**개발자 API** (트렌드/인구통계): https://developers.naver.com\n"
        "- `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`"
    )

# ─── 검색 히스토리 ───
history = st.session_state.get("keyword_history", [])
if history:
    st.markdown("**최근 검색:**")
    chips_html = " ".join(
        f'<span class="history-chip">{kw}</span>' for kw in history[-10:][::-1]
    )
    st.markdown(chips_html, unsafe_allow_html=True)
    st.markdown("")

# ─── 키워드 입력 ───
with st.form("keyword_form"):
    keyword_input = st.text_input(
        "분석할 키워드",
        placeholder="예: 수능 공부법, 의대 입시, 생기부 세특",
        help="쉼표로 구분하여 여러 키워드를 입력할 수 있습니다 (최대 5개)",
    )
    submitted = st.form_submit_button(
        "🔍 키워드 분석", type="primary", width="stretch",
    )

if submitted and keyword_input.strip():
    keywords = [kw.strip() for kw in keyword_input.split(",") if kw.strip()][:5]
    main_keyword = keywords[0]

    # 히스토리에 추가
    hist = st.session_state.get("keyword_history", [])
    if main_keyword not in hist:
        hist.append(main_keyword)
        if len(hist) > 20:
            hist = hist[-20:]
        st.session_state["keyword_history"] = hist

    # ═══════════════════════════════════════════════════
    # 데이터 수집
    # ═══════════════════════════════════════════════════
    metrics: list[KeywordMetrics] = []
    trends: list = []
    blog_count = 0
    cafe_count = 0

    # 검색광고 API: 검색량/경쟁도/연관 키워드
    if ad_client.is_configured:
        with st.spinner("검색량 데이터를 가져오는 중..."):
            try:
                cached = safe_cache_get(db, main_keyword, "search_volume")
                if cached and "metrics" in cached:
                    metrics = [KeywordMetrics(**m) for m in cached["metrics"]]
                else:
                    metrics = ad_client.get_keyword_metrics(keywords)
                    if metrics:
                        safe_cache_save(
                            db, main_keyword, "search_volume",
                            {"metrics": [m.model_dump() for m in metrics]},
                            ttl_hours=24,
                        )
            except Exception as e:
                st.error(f"검색광고 API 오류: {e}")

    # 데이터랩 API: 트렌드 + 블로그/카페 발행수
    if datalab_client.is_configured:
        with st.spinner("트렌드 및 콘텐츠 데이터를 가져오는 중..."):
            try:
                trends = datalab_client.get_search_trend(keywords[:5])
            except Exception as e:
                st.error(f"데이터랩 API 오류: {e}")

            try:
                blog_count = datalab_client.get_blog_count(main_keyword)
            except Exception:
                pass
            try:
                cafe_count = datalab_client.get_cafe_count(main_keyword)
            except Exception:
                pass

    if not metrics and not trends:
        st.warning("분석 결과가 없습니다. API 키를 확인해주세요.")
        st.stop()

    # 결과를 session_state에 저장
    st.session_state["keyword_analysis"] = {
        "keyword": main_keyword,
        "metrics": metrics,
        "trends": trends,
        "blog_count": blog_count,
        "cafe_count": cafe_count,
    }

    # 메인 키워드 데이터 준비
    main_kw = metrics[0] if metrics else None
    total_qc = main_kw.total_monthly_qc if main_kw else 0

    # 포화지수 계산
    detailed_sat = None
    kw_grade = None
    if main_kw and (blog_count or cafe_count):
        detailed_sat = calculate_detailed_saturation(
            main_keyword, blog_count, cafe_count, total_qc,
        )
        kw_grade = calculate_keyword_grade(
            main_keyword, total_qc,
            main_kw.comp_idx,
            detailed_sat.blog_saturation if detailed_sat else 0,
        )

    # ═══════════════════════════════════════════════════
    # 결과 탭
    # ═══════════════════════════════════════════════════
    tab_names = ["📊 키워드 개요"]
    if metrics:
        tab_names.append("🔗 연관 키워드")
    if trends or datalab_client.is_configured:
        tab_names.append("📈 검색 트렌드")
    if detailed_sat or (blog_count or cafe_count):
        tab_names.append("🎯 포화지수")
    if datalab_client.is_configured:
        tab_names.append("👥 인구통계")

    tabs = st.tabs(tab_names)
    tab_idx = 0

    # ═══════════════════════════════════════════════════
    # Tab 1: 키워드 개요
    # ═══════════════════════════════════════════════════
    with tabs[tab_idx]:
        st.markdown(f"### 「{main_keyword}」 키워드 분석 결과")

        # ── 등급 + 요약 ──
        if kw_grade:
            g_col1, g_col2 = st.columns([1, 5])
            with g_col1:
                st.markdown(grade_badge_html(kw_grade.grade), unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center;font-size:0.75rem;color:#6b7280;margin-top:4px;'>종합 {kw_grade.score}점</div>", unsafe_allow_html=True)
            with g_col2:
                st.markdown(f"**{kw_grade.summary}**")
                # 점수 상세
                s1, s2, s3 = st.columns(3)
                with s1:
                    st.caption("검색량 (40%)")
                    st.markdown(score_bar_html(kw_grade.search_volume_score, "#3b82f6"), unsafe_allow_html=True)
                    st.markdown(f"<span style='font-size:0.8rem;'>{kw_grade.search_volume_score:.0f}점</span>", unsafe_allow_html=True)
                with s2:
                    st.caption("경쟁도 (30%)")
                    st.markdown(score_bar_html(kw_grade.competition_score, "#10b981"), unsafe_allow_html=True)
                    st.markdown(f"<span style='font-size:0.8rem;'>{kw_grade.competition_score:.0f}점</span>", unsafe_allow_html=True)
                with s3:
                    st.caption("포화도 (30%)")
                    st.markdown(score_bar_html(kw_grade.saturation_score, "#f59e0b"), unsafe_allow_html=True)
                    st.markdown(f"<span style='font-size:0.8rem;'>{kw_grade.saturation_score:.0f}점</span>", unsafe_allow_html=True)

        st.markdown("---")

        # ── 월간 검색량 ──
        st.markdown("#### 월간 검색량")
        if main_kw:
            vc1, vc2, vc3 = st.columns(3)
            vc1.metric("PC", f"{main_kw.monthly_pc_qc:,}건")
            vc2.metric("모바일", f"{main_kw.monthly_mobile_qc:,}건")
            vc3.metric("합계", f"{total_qc:,}건")

            # 이번 달 예상 검색량 (트렌드 기반)
            if trends and trends[0].data:
                last_ratio = trends[0].data[-1].ratio
                prev_ratio = trends[0].data[-2].ratio if len(trends[0].data) >= 2 else last_ratio
                if prev_ratio > 0:
                    change_pct = ((last_ratio - prev_ratio) / prev_ratio) * 100
                    estimated = int(total_qc * (1 + change_pct / 100))
                    ec1, ec2 = st.columns(2)
                    ec1.metric(
                        "이번 달 예상 검색량",
                        f"{estimated:,}건",
                        delta=f"{change_pct:+.1f}% 전월 대비",
                    )

        st.markdown("")

        # ── 콘텐츠 발행수 ──
        st.markdown("#### 월간 콘텐츠 발행수")
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("블로그", f"{blog_count:,}건")
        pc2.metric("카페", f"{cafe_count:,}건")
        pc3.metric("전체", f"{blog_count + cafe_count:,}건")

        st.markdown("")

        # ── 콘텐츠 포화지수 요약 ──
        if detailed_sat:
            st.markdown("#### 콘텐츠 포화지수")
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                st.markdown("**블로그**")
                st.markdown(f"{detailed_sat.blog_saturation:.3f}")
                st.markdown(sat_badge_html(detailed_sat.blog_level), unsafe_allow_html=True)
            with sc2:
                st.markdown("**카페**")
                st.markdown(f"{detailed_sat.cafe_saturation:.3f}")
                st.markdown(sat_badge_html(detailed_sat.cafe_level), unsafe_allow_html=True)
            with sc3:
                st.markdown("**전체**")
                st.markdown(f"{detailed_sat.total_saturation:.3f}")
                st.markdown(sat_badge_html(detailed_sat.total_level), unsafe_allow_html=True)

        st.markdown("")

        # ── 경쟁도 ──
        if main_kw:
            st.markdown("#### 경쟁도")
            comp_labels = {"low": "낮음", "medium": "보통", "high": "높음"}
            comp_colors = {"low": "🟢", "medium": "🟡", "high": "🔴"}
            comp_label = comp_labels.get(main_kw.comp_idx, main_kw.comp_idx)
            comp_icon = comp_colors.get(main_kw.comp_idx, "⚪")

            cc1, cc2, cc3, cc4 = st.columns(4)
            cc1.metric("경쟁도", f"{comp_icon} {comp_label}")
            cc2.metric("PC 평균 CTR", f"{main_kw.monthly_pc_ctr:.2f}%")
            cc3.metric("모바일 평균 CTR", f"{main_kw.monthly_mobile_ctr:.2f}%")
            cc4.metric("노출 광고수", f"{main_kw.pl_avg_depth}개")

    tab_idx += 1

    # ═══════════════════════════════════════════════════
    # Tab 2: 연관 키워드
    # ═══════════════════════════════════════════════════
    if metrics:
        with tabs[tab_idx]:
            st.markdown("### 연관 키워드")

            related = sorted(
                metrics[1:], key=lambda x: x.total_monthly_qc, reverse=True
            )

            if related:
                # ── 연관 키워드별 블로그 발행수 조회 ──
                kw_blog_counts: dict[str, int] = {}
                if datalab_client.is_configured:
                    with st.spinner("연관 키워드별 블로그 발행수 조회 중..."):
                        kw_blog_counts = get_keyword_blog_counts(
                            datalab_client,
                            [m.keyword for m in related[:15]],
                        )

                # ── 메인 테이블 ──
                comp_labels = {"low": "낮음", "medium": "보통", "high": "높음"}
                df_related_data = []
                for m in related[:30]:
                    row = {
                        "키워드": m.keyword,
                        "월간 검색량": m.total_monthly_qc,
                        "PC": m.monthly_pc_qc,
                        "모바일": m.monthly_mobile_qc,
                        "경쟁도": comp_labels.get(m.comp_idx, m.comp_idx),
                        "PC CTR": round(m.monthly_pc_ctr, 2),
                        "모바일 CTR": round(m.monthly_mobile_ctr, 2),
                    }
                    if kw_blog_counts:
                        row["블로그 발행수"] = kw_blog_counts.get(m.keyword, "-")
                    row["철자 유사도"] = f"{spelling_similarity(main_keyword, m.keyword) * 100:.0f}%"
                    df_related_data.append(row)

                df_related = pd.DataFrame(df_related_data)
                st.dataframe(
                    df_related,
                    width="stretch",
                    hide_index=True,
                    height=min(len(df_related_data) * 38 + 40, 500),
                )

                # CSV 다운로드
                csv_data = to_csv_bytes(df_related)
                st.download_button(
                    "📥 CSV 다운로드",
                    data=csv_data,
                    file_name=f"연관키워드_{main_keyword}.csv",
                    mime="text/csv",
                )

                st.markdown("---")

                # ── 주제 클러스터 ──
                st.markdown("#### 주제 클러스터")
                clusters = build_topic_clusters(related, main_keyword)
                for cluster_name, cluster_items in sorted(
                    clusters.items(),
                    key=lambda x: sum(m.total_monthly_qc for m in x[1]),
                    reverse=True,
                ):
                    total_vol = sum(m.total_monthly_qc for m in cluster_items)
                    with st.expander(
                        f"🏷️ {cluster_name} ({len(cluster_items)}개 키워드, 총 {total_vol:,}건/월)"
                    ):
                        for m in sorted(cluster_items, key=lambda x: x.total_monthly_qc, reverse=True):
                            st.markdown(
                                f"- **{m.keyword}** — 월 {m.total_monthly_qc:,}건 "
                                f"({comp_labels.get(m.comp_idx, m.comp_idx)})"
                            )

                st.markdown("---")

                # ── 해시태그 ──
                st.markdown("#### 해시태그 추출")
                hashtags = extract_hashtags(related, top_n=20)
                if hashtags:
                    ht_text = " ".join(hashtags)
                    st.code(ht_text, language=None)
                    st.caption("위 해시태그를 복사하여 블로그에 활용하세요.")

                st.markdown("---")

                # ── 워드 클라우드 ──
                st.markdown("#### 키워드 워드 클라우드")
                max_vol = max(m.total_monthly_qc for m in related) if related else 1
                tags_html = '<div class="tag-cloud">'
                for m in related[:25]:
                    ratio = m.total_monthly_qc / max_vol if max_vol > 0 else 0
                    if ratio > 0.6:
                        cls = "tag-item tag-item-lg"
                    elif ratio > 0.3:
                        cls = "tag-item tag-item-md"
                    else:
                        cls = "tag-item tag-item-sm"
                    tags_html += f'<span class="{cls}">{m.keyword} ({m.total_monthly_qc:,})</span>'
                tags_html += '</div>'
                st.markdown(tags_html, unsafe_allow_html=True)

                st.markdown("---")

                # ── 글 생성 연동 ──
                st.markdown("#### 글 생성에 활용")
                selected_keywords = st.multiselect(
                    "글 생성에 사용할 키워드 선택",
                    [m.keyword for m in related],
                    default=[related[0].keyword] if related else [],
                )
                if selected_keywords and st.button(
                    "📝 선택한 키워드로 글 생성 페이지로 이동",
                    type="primary",
                ):
                    st.session_state["keyword_for_generation"] = {
                        "keyword": main_keyword,
                        "related": selected_keywords,
                    }
                    st.success(
                        f"키워드가 저장되었습니다! 메인 페이지에서 글을 생성해주세요.\n\n"
                        f"메인 키워드: **{main_keyword}**\n"
                        f"연관 키워드: {', '.join(selected_keywords)}"
                    )
            else:
                st.info("연관 키워드가 없습니다.")

        tab_idx += 1

    # ═══════════════════════════════════════════════════
    # Tab 3: 검색 트렌드
    # ═══════════════════════════════════════════════════
    if trends or datalab_client.is_configured:
        with tabs[tab_idx]:
            st.markdown("### 검색 트렌드")

            # ── 필터 옵션 ──
            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                time_unit = st.selectbox(
                    "기간 단위",
                    ["month", "week", "date"],
                    format_func=lambda x: {"month": "월별", "week": "주별", "date": "일별"}[x],
                    index=0,
                )
            with fc2:
                device_filter = st.selectbox(
                    "기기",
                    ["", "pc", "mo"],
                    format_func=lambda x: {"": "전체", "pc": "PC", "mo": "모바일"}[x],
                )
            with fc3:
                gender_filter = st.selectbox(
                    "성별",
                    ["", "m", "f"],
                    format_func=lambda x: {"": "전체", "m": "남성", "f": "여성"}[x],
                )
            with fc4:
                age_options = {
                    "": "전체",
                    "1": "0~12세", "2": "13~18세", "3": "19~24세",
                    "4": "25~29세", "5": "30~34세", "6": "35~39세",
                    "7": "40~44세", "8": "45~49세", "9": "50~54세",
                    "10": "55~59세", "11": "60세 이상",
                }
                age_filter = st.selectbox(
                    "연령대",
                    list(age_options.keys()),
                    format_func=lambda x: age_options[x],
                )

            # ── 비교 키워드 ──
            compare_input = st.text_input(
                "비교 키워드 (쉼표 구분, 최대 4개 추가)",
                placeholder="예: 수시, 정시, 내신",
                help="메인 키워드와 비교할 키워드를 입력하세요",
            )

            compare_keywords = [main_keyword]
            if compare_input.strip():
                extra = [kw.strip() for kw in compare_input.split(",") if kw.strip()][:4]
                compare_keywords.extend(extra)

            # ── 트렌드 조회 ──
            if st.button("📈 트렌드 조회", type="primary"):
                with st.spinner("트렌드 데이터를 가져오는 중..."):
                    try:
                        trend_kwargs = {
                            "keywords": compare_keywords,
                            "time_unit": time_unit,
                        }
                        if device_filter:
                            trend_kwargs["device"] = device_filter
                        if gender_filter:
                            trend_kwargs["gender"] = gender_filter
                        if age_filter:
                            trend_kwargs["ages"] = [age_filter]

                        filtered_trends = datalab_client.get_search_trend(**trend_kwargs)
                        if filtered_trends:
                            trends = filtered_trends
                    except Exception as e:
                        st.error(f"트렌드 조회 오류: {e}")

            # ── 트렌드 차트 ──
            if trends:
                trend_frames = {}
                for trend in trends:
                    if trend.data:
                        trend_frames[trend.title] = {
                            d.period: d.ratio for d in trend.data
                        }

                if trend_frames:
                    df_trend = pd.DataFrame(trend_frames)
                    df_trend.index.name = "기간"
                    st.line_chart(df_trend)

                    # 최근 트렌드 요약
                    if len(trends) >= 1 and trends[0].data:
                        data_points = trends[0].data
                        recent = data_points[-1].ratio
                        peak = max(d.ratio for d in data_points)
                        avg = sum(d.ratio for d in data_points) / len(data_points)

                        tc1, tc2, tc3 = st.columns(3)
                        tc1.metric("최근 지수", f"{recent:.1f}")
                        tc2.metric("최고 지수", f"{peak:.1f}")
                        tc3.metric("평균 지수", f"{avg:.1f}")

                    with st.expander("원본 데이터"):
                        st.dataframe(df_trend, width="stretch")
                        csv_trend = to_csv_bytes(df_trend.reset_index())
                        st.download_button(
                            "📥 트렌드 CSV 다운로드",
                            data=csv_trend,
                            file_name=f"트렌드_{main_keyword}.csv",
                            mime="text/csv",
                        )
            else:
                st.info("트렌드 데이터가 없습니다. 위의 '트렌드 조회' 버튼을 눌러주세요.")

        tab_idx += 1

    # ═══════════════════════════════════════════════════
    # Tab 4: 포화지수
    # ═══════════════════════════════════════════════════
    if detailed_sat or (blog_count or cafe_count):
        with tabs[tab_idx]:
            st.markdown("### 콘텐츠 포화지수 상세")
            st.caption("포화지수 = 콘텐츠 발행수 / 월간 검색량 (낮을수록 블루오션)")

            if detailed_sat:
                st.markdown("---")

                # ── 블로그 포화지수 ──
                st.markdown("#### 📝 블로그 포화지수")
                bc1, bc2, bc3 = st.columns(3)
                bc1.metric("블로그 발행수", f"{detailed_sat.blog_count:,}건")
                bc2.metric("포화지수", f"{detailed_sat.blog_saturation:.3f}")
                with bc3:
                    st.markdown("**포화 수준**")
                    st.markdown(sat_badge_html(detailed_sat.blog_level), unsafe_allow_html=True)

                # 시각적 바
                blog_pct = min(detailed_sat.blog_saturation * 100, 100)
                blog_color = {"낮음": "#10b981", "보통": "#f59e0b", "높음": "#ef4444"}.get(detailed_sat.blog_level, "#6b7280")
                st.markdown(score_bar_html(blog_pct, blog_color), unsafe_allow_html=True)

                st.markdown("")

                # ── 카페 포화지수 ──
                st.markdown("#### ☕ 카페 포화지수")
                kc1, kc2, kc3 = st.columns(3)
                kc1.metric("카페 발행수", f"{detailed_sat.cafe_count:,}건")
                kc2.metric("포화지수", f"{detailed_sat.cafe_saturation:.3f}")
                with kc3:
                    st.markdown("**포화 수준**")
                    st.markdown(sat_badge_html(detailed_sat.cafe_level), unsafe_allow_html=True)

                cafe_pct = min(detailed_sat.cafe_saturation * 100, 100)
                cafe_color = {"낮음": "#10b981", "보통": "#f59e0b", "높음": "#ef4444"}.get(detailed_sat.cafe_level, "#6b7280")
                st.markdown(score_bar_html(cafe_pct, cafe_color), unsafe_allow_html=True)

                st.markdown("")

                # ── 전체 포화지수 ──
                st.markdown("#### 📊 전체 포화지수")
                tc1, tc2, tc3 = st.columns(3)
                tc1.metric("전체 발행수", f"{detailed_sat.blog_count + detailed_sat.cafe_count:,}건")
                tc2.metric("포화지수", f"{detailed_sat.total_saturation:.3f}")
                with tc3:
                    st.markdown("**포화 수준**")
                    st.markdown(sat_badge_html(detailed_sat.total_level), unsafe_allow_html=True)

                total_pct = min(detailed_sat.total_saturation * 100, 100)
                total_color = {"낮음": "#10b981", "보통": "#f59e0b", "높음": "#ef4444"}.get(detailed_sat.total_level, "#6b7280")
                st.markdown(score_bar_html(total_pct, total_color), unsafe_allow_html=True)

                st.markdown("---")

                # 포화지수 비교 테이블
                sat_df = pd.DataFrame([
                    {"플랫폼": "블로그", "발행수": detailed_sat.blog_count,
                     "포화지수": detailed_sat.blog_saturation, "수준": detailed_sat.blog_level},
                    {"플랫폼": "카페", "발행수": detailed_sat.cafe_count,
                     "포화지수": detailed_sat.cafe_saturation, "수준": detailed_sat.cafe_level},
                    {"플랫폼": "전체", "발행수": detailed_sat.blog_count + detailed_sat.cafe_count,
                     "포화지수": detailed_sat.total_saturation, "수준": detailed_sat.total_level},
                ])
                st.dataframe(sat_df, width="stretch", hide_index=True)

            # ── 해석 가이드 ──
            with st.expander("포화지수 해석 가이드"):
                st.markdown("""
| 포화지수 | 수준 | 해석 |
|---------|------|------|
| ≤ 0.3 | 🟢 낮음 | 콘텐츠 부족. 지금 진입하면 상위 노출 유리 |
| 0.3 ~ 0.7 | 🟡 보통 | 적절한 경쟁. 양질의 콘텐츠로 승부 가능 |
| > 0.7 | 🔴 높음 | 콘텐츠 과잉. 롱테일 키워드 전환 추천 |

**블로그 vs 카페 전략:**
- 블로그 포화 높음 + 카페 포화 낮음 → 카페 콘텐츠로 진입 고려
- 블로그 포화 낮음 → 블로그 집중 공략
- 전체 포화 낮음 → 블루오션! 적극 진입 추천
                """)

        tab_idx += 1

    # ═══════════════════════════════════════════════════
    # Tab 5: 인구통계
    # ═══════════════════════════════════════════════════
    if datalab_client.is_configured:
        with tabs[tab_idx]:
            st.markdown("### 인구통계 분석")
            st.caption("네이버 데이터랩 기반 검색 비율 (상대값)")

            # ── 성별 분석 ──
            st.markdown("#### 성별 검색 비율")
            try:
                male_trend = datalab_client.get_search_trend(
                    [main_keyword], gender="m"
                )
                female_trend = datalab_client.get_search_trend(
                    [main_keyword], gender="f"
                )

                male_avg = 0.0
                female_avg = 0.0
                if male_trend and male_trend[0].data:
                    male_avg = sum(d.ratio for d in male_trend[0].data) / len(
                        male_trend[0].data
                    )
                if female_trend and female_trend[0].data:
                    female_avg = sum(d.ratio for d in female_trend[0].data) / len(
                        female_trend[0].data
                    )

                total = male_avg + female_avg
                if total > 0:
                    male_pct = male_avg / total * 100
                    female_pct = female_avg / total * 100

                    gc1, gc2 = st.columns(2)
                    gc1.metric("👨 남성", f"{male_pct:.1f}%")
                    gc2.metric("👩 여성", f"{female_pct:.1f}%")

                    # 시각적 바
                    st.markdown(
                        f'<div style="display:flex;height:30px;border-radius:8px;overflow:hidden;">'
                        f'<div style="width:{male_pct}%;background:#3b82f6;display:flex;align-items:center;justify-content:center;color:white;font-size:0.8rem;font-weight:600;">남 {male_pct:.0f}%</div>'
                        f'<div style="width:{female_pct}%;background:#ec4899;display:flex;align-items:center;justify-content:center;color:white;font-size:0.8rem;font-weight:600;">여 {female_pct:.0f}%</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    st.markdown("")

                    # 성별 트렌드 비교 차트
                    if male_trend and male_trend[0].data and female_trend and female_trend[0].data:
                        gender_trend_df = pd.DataFrame({
                            "남성": {d.period: d.ratio for d in male_trend[0].data},
                            "여성": {d.period: d.ratio for d in female_trend[0].data},
                        })
                        st.line_chart(gender_trend_df)
                else:
                    st.info("성별 데이터를 가져올 수 없습니다.")
            except Exception as e:
                st.warning(f"성별 분석 오류: {e}")

            st.markdown("---")

            # ── 연령별 분석 ──
            st.markdown("#### 연령별 검색 비율")
            age_groups = {
                "1": "0~12세",
                "2": "13~18세",
                "3": "19~24세",
                "4": "25~29세",
                "5": "30~34세",
                "6": "35~39세",
                "7": "40~44세",
                "8": "45~49세",
                "9": "50~54세",
                "10": "55~59세",
                "11": "60세+",
            }

            try:
                age_data: dict[str, float] = {}
                with st.spinner("연령별 데이터 조회 중..."):
                    for age_code, age_label in age_groups.items():
                        try:
                            age_trend = datalab_client.get_search_trend(
                                [main_keyword], ages=[age_code]
                            )
                            if age_trend and age_trend[0].data:
                                avg = sum(d.ratio for d in age_trend[0].data) / len(
                                    age_trend[0].data
                                )
                                age_data[age_label] = avg
                        except Exception:
                            continue

                if age_data:
                    age_total = sum(age_data.values())
                    if age_total > 0:
                        age_pct = {k: v / age_total * 100 for k, v in age_data.items()}
                    else:
                        age_pct = age_data

                    age_df = pd.DataFrame(
                        {"연령대": list(age_pct.keys()), "비율 (%)": list(age_pct.values())}
                    ).set_index("연령대")
                    st.bar_chart(age_df)

                    # 핵심 타겟 연령
                    top_age = max(age_pct, key=age_pct.get)
                    st.info(f"🎯 핵심 타겟 연령층: **{top_age}** ({age_pct[top_age]:.1f}%)")
                else:
                    st.info("연령별 데이터를 가져올 수 없습니다.")
            except Exception as e:
                st.warning(f"연령별 분석 오류: {e}")

    # ─── 글 생성 연동 버튼 ───
    st.divider()
    if metrics:
        if st.button(
            f"📝 '{main_keyword}' 키워드로 블로그 글 생성하러 가기",
            type="primary",
            width="stretch",
        ):
            st.session_state["keyword_for_generation"] = {
                "keyword": main_keyword,
                "related": [m.keyword for m in metrics[1:6]],
            }
            st.success(
                "키워드가 저장되었습니다! **메인 페이지(보보쌤 블로그 글 생성기)**에서 글을 생성해주세요."
            )

elif submitted:
    st.warning("키워드를 입력해주세요!")

# ─── 사이드바 ───
with st.sidebar:
    st.markdown("### ⚙️ 설정")

    with st.expander("API 키 설정 방법"):
        st.markdown("""
**1. 검색광고 API** (검색량/경쟁도)
1. https://searchad.naver.com 가입
2. 도구 > API 사용 관리에서 키 발급
3. `.env`에 추가:
```
NAVER_AD_API_KEY=발급받은키
NAVER_AD_SECRET_KEY=발급받은키
NAVER_AD_CUSTOMER_ID=발급받은ID
```

**2. 개발자 API** (트렌드/인구통계)
1. https://developers.naver.com 가입
2. 애플리케이션 등록 (데이터랩 + 검색 선택)
3. `.env`에 추가:
```
NAVER_CLIENT_ID=발급받은ID
NAVER_CLIENT_SECRET=발급받은키
```
        """)

    st.markdown("")

    if st.button("🗑️ 키워드 캐시 초기화"):
        try:
            count = db.clear_keyword_cache()
            db.clear_expired_cache()
            st.success(f"캐시 {count}개 삭제됨")
        except Exception:
            st.info("캐시가 비어있거나 테이블이 없습니다.")

    if st.button("🗑️ 검색 히스토리 초기화"):
        st.session_state["keyword_history"] = []
        st.success("검색 히스토리가 초기화되었습니다.")

    st.markdown("---")

    # 등급 기준 안내
    with st.expander("키워드 등급 기준"):
        st.markdown("""
| 등급 | 점수 | 의미 |
|------|------|------|
| **S** | 80+ | 최상급 키워드 (높은 검색량, 낮은 경쟁) |
| **A** | 65~79 | 우수 키워드 (좋은 기회) |
| **B** | 50~64 | 괜찮은 키워드 (차별화 필요) |
| **C** | 35~49 | 보통 (롱테일 조합 추천) |
| **D** | ~34 | 비추천 (검색량 부족/경쟁 과다) |

**채점 방식:**
- 검색량 40% + 경쟁도 30% + 포화도 30%
        """)

# ─── 푸터 ───
st.markdown("")
st.markdown("""
<div style="text-align: center; padding: 1rem 0; color: #a1a1aa; font-size: 0.75rem;">
    키워드 분석 · 네이버 검색광고 API + 데이터랩 API<br>
    <span style="color: #34d399;">블랙키위 스타일</span> 키워드 분석 도구
</div>
""", unsafe_allow_html=True)
