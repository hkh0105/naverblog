"""키워드 분석 가이드 - 지표 해석 방법과 활용 전략."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="키워드 분석 가이드",
    page_icon="📖",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .block-container { max-width: 900px; padding-top: 1.5rem; }

    .guide-hero {
        background: linear-gradient(135deg, #6366f1 0%, #818cf8 50%, #a5b4fc 100%);
        padding: 2rem 2.5rem 1.5rem;
        border-radius: 1.25rem;
        color: white;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .guide-hero::before {
        content: '';
        position: absolute; top: -50%; right: -20%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .guide-hero h1 {
        color: white !important;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
    }
    .guide-hero .subtitle {
        color: rgba(255,255,255,0.88);
        font-size: 0.88rem;
        font-weight: 300;
    }

    /* 카드 스타일 */
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-card h4 {
        margin: 0 0 0.5rem 0;
        font-size: 1.1rem;
    }
    .metric-card p {
        color: #4b5563;
        font-size: 0.9rem;
        line-height: 1.7;
        margin: 0;
    }

    /* 등급 뱃지 */
    .g-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 40px; height: 40px;
        border-radius: 50%;
        font-size: 1.1rem; font-weight: 800;
        color: white;
    }
    .g-S { background: linear-gradient(135deg, #f59e0b, #f97316); }
    .g-A { background: linear-gradient(135deg, #10b981, #059669); }
    .g-B { background: linear-gradient(135deg, #3b82f6, #2563eb); }
    .g-C { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
    .g-D { background: linear-gradient(135deg, #ef4444, #dc2626); }

    /* 레벨 태그 */
    .lv-tag {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 0.35rem;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .lv-low { background: #d1fae5; color: #065f46; }
    .lv-mid { background: #fef3c7; color: #92400e; }
    .lv-high { background: #fee2e2; color: #991b1b; }

    /* 팁 박스 */
    .tip-box {
        background: #f0fdf4;
        border-left: 4px solid #10b981;
        border-radius: 0 0.5rem 0.5rem 0;
        padding: 1rem 1.2rem;
        margin: 1rem 0;
        font-size: 0.88rem;
        color: #166534;
    }
    .warn-box {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        border-radius: 0 0.5rem 0.5rem 0;
        padding: 1rem 1.2rem;
        margin: 1rem 0;
        font-size: 0.88rem;
        color: #92400e;
    }

    /* 구분선 */
    .section-divider {
        border: none;
        border-top: 2px solid #f3f4f6;
        margin: 2rem 0;
    }

    /* TOC */
    .toc-item {
        display: block;
        padding: 0.4rem 0;
        color: #4b5563;
        font-size: 0.88rem;
        text-decoration: none;
        border-bottom: 1px solid #f3f4f6;
    }
    .toc-item:hover { color: #6366f1; }
</style>
""", unsafe_allow_html=True)

# ─── 헤더 ───
st.markdown("""
<div class="guide-hero">
    <h1>📖 키워드 분석 가이드</h1>
    <p class="subtitle">각 지표의 의미, 해석 기준, 그리고 블로그 전략에 활용하는 방법을 알아보세요</p>
</div>
""", unsafe_allow_html=True)

# ─── 목차 ───
with st.sidebar:
    st.markdown("### 📑 목차")
    st.markdown("""
1. [키워드 등급](#키워드-등급-s-a-b-c-d)
2. [월간 검색량](#월간-검색량)
3. [경쟁도](#경쟁도)
4. [콘텐츠 포화지수](#콘텐츠-포화지수)
5. [콘텐츠 발행수](#콘텐츠-발행수)
6. [연관 키워드](#연관-키워드)
7. [검색 트렌드](#검색-트렌드)
8. [인구통계](#인구통계)
9. [스마트블록](#스마트블록)
10. [실전 활용 전략](#실전-활용-전략)
    """)

# ═══════════════════════════════════════════════════════
# 1. 키워드 등급
# ═══════════════════════════════════════════════════════
st.markdown("## 키워드 등급 (S / A / B / C / D)")
st.markdown("""
키워드의 **블로그 진입 가치**를 종합적으로 평가한 등급입니다.
3가지 요소를 점수화하여 100점 만점으로 산출합니다.
""")

st.markdown("#### 채점 기준")

gc1, gc2, gc3 = st.columns(3)
with gc1:
    st.markdown("""
    <div class="metric-card">
        <h4>🔍 검색량 (40%)</h4>
        <p>
        월간 검색량이 높을수록 높은 점수.<br>
        검색량이 많다 = 사람들의 관심이 높다.<br><br>
        50,000건+ → 100점<br>
        10,000건+ → 80점<br>
        3,000건+ → 60점<br>
        1,000건+ → 40점<br>
        100건+ → 20점<br>
        100건 미만 → 5점
        </p>
    </div>
    """, unsafe_allow_html=True)
with gc2:
    st.markdown("""
    <div class="metric-card">
        <h4>⚔️ 경쟁도 (30%)</h4>
        <p>
        경쟁이 낮을수록 높은 점수.<br>
        경쟁 낮음 = 상위 노출이 쉽다.<br><br>
        🟢 낮음 → 100점<br>
        🟡 보통 → 50점<br>
        🔴 높음 → 10점<br><br>
        <em>네이버 검색광고 API의<br>
        광고 경쟁 지수 기반</em>
        </p>
    </div>
    """, unsafe_allow_html=True)
with gc3:
    st.markdown("""
    <div class="metric-card">
        <h4>📊 포화도 (30%)</h4>
        <p>
        포화도가 낮을수록 높은 점수.<br>
        포화도 낮음 = 콘텐츠가 부족하다.<br><br>
        ≤ 0.1 → 100점<br>
        ≤ 0.3 → 80점<br>
        ≤ 0.5 → 60점<br>
        ≤ 1.0 → 30점<br>
        > 1.0 → 10점
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
st.markdown("#### 등급 기준표")

st.markdown("""
| 등급 | 점수 | 의미 | 전략 |
|:---:|:---:|------|------|
| <span class="g-badge g-S">S</span> | **80점+** | 최상급 키워드. 검색량 높고 경쟁 낮음 | 즉시 진입! 시리즈 글로 선점하세요 |
| <span class="g-badge g-A">A</span> | **65~79** | 우수 키워드. 좋은 기회 | 양질의 콘텐츠로 상위 노출 가능 |
| <span class="g-badge g-B">B</span> | **50~64** | 괜찮은 키워드 | 차별화된 콘텐츠와 꾸준한 발행 필요 |
| <span class="g-badge g-C">C</span> | **35~49** | 보통 수준 | 롱테일 키워드 조합 추천 |
| <span class="g-badge g-D">D</span> | **~34** | 비추천 키워드 | 검색량 부족 또는 경쟁 과다. 키워드 변경 추천 |
""", unsafe_allow_html=True)

st.markdown("""
<div class="tip-box">
    💡 <strong>팁:</strong> S·A등급 키워드를 메인 키워드로, B·C등급 키워드를 보조 키워드로 활용하면 효과적입니다.
    D등급이라도 연관 키워드 중에 높은 등급이 있을 수 있으니 꼭 확인하세요.
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 2. 월간 검색량
# ═══════════════════════════════════════════════════════
st.markdown("## 월간 검색량")
st.markdown("""
지난 한 달간 해당 키워드가 네이버에서 **검색된 횟수**입니다.
PC와 모바일을 분리하여 보여주며, 합계도 함께 제공됩니다.
""")

st.markdown("#### 검색량 규모별 해석")

st.markdown("""
| 검색량 (월) | 규모 | 해석 |
|:---:|:---:|------|
| **50,000건+** | 🔥 대형 | 대중적 키워드. 경쟁 치열하지만 트래픽 확보 가능 |
| **10,000~49,999** | 📈 중대형 | 적당한 수요. 꾸준한 유입 기대 |
| **3,000~9,999** | 📊 중형 | 니치 시장. 상위 노출 시 안정적 유입 |
| **1,000~2,999** | 📉 소형 | 롱테일 영역. 타겟 정확하면 전환율 높음 |
| **100~999** | 🔍 마이크로 | 매우 세분화된 키워드. 블루오션 가능성 |
| **~99** | ⚪ 극소 | 검색량 부족. 단독 키워드로는 부적합 |
""")

st.markdown("""
<div class="tip-box">
    💡 <strong>PC vs 모바일:</strong> 모바일 검색 비율이 높은 키워드는 모바일 친화적 글 구조가 중요합니다.
    짧은 문단, 핵심 먼저 배치, 이미지 활용이 효과적입니다.
</div>
""", unsafe_allow_html=True)

st.markdown("")
st.markdown("#### 이번 달 예상 검색량")
st.markdown("""
최근 검색 트렌드를 기반으로 **이번 달 검색량을 추정**한 값입니다.
전월 대비 증감률(%)도 함께 표시됩니다.

- **상승 중 (+)**: 관심이 높아지고 있는 키워드 → 빠른 진입 추천
- **하락 중 (-)**: 관심이 떨어지고 있는 키워드 → 트렌드 변화 확인 필요
- **안정적 (±5% 이내)**: 꾸준한 수요 키워드 → 장기적 콘텐츠 전략에 적합
""")

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 3. 경쟁도
# ═══════════════════════════════════════════════════════
st.markdown("## 경쟁도")
st.markdown("""
네이버 검색광고 시스템에서 제공하는 **광고 경쟁 지수**입니다.
해당 키워드에 얼마나 많은 광고주가 경쟁하고 있는지를 나타냅니다.
""")

cc1, cc2, cc3 = st.columns(3)
with cc1:
    st.markdown("""
    <div class="metric-card" style="border-left: 4px solid #10b981;">
        <h4>🟢 낮음</h4>
        <p>
        광고 경쟁이 적음.<br>
        상위 노출 진입 장벽이 낮고,<br>
        양질의 콘텐츠만으로 상위 가능.<br><br>
        <strong>추천 전략:</strong><br>
        적극적으로 글 작성!
        </p>
    </div>
    """, unsafe_allow_html=True)
with cc2:
    st.markdown("""
    <div class="metric-card" style="border-left: 4px solid #f59e0b;">
        <h4>🟡 보통</h4>
        <p>
        적당한 경쟁 수준.<br>
        차별화된 콘텐츠가 필요하며,<br>
        꾸준한 발행이 효과적.<br><br>
        <strong>추천 전략:</strong><br>
        양질 + 정기 발행
        </p>
    </div>
    """, unsafe_allow_html=True)
with cc3:
    st.markdown("""
    <div class="metric-card" style="border-left: 4px solid #ef4444;">
        <h4>🔴 높음</h4>
        <p>
        치열한 경쟁 상태.<br>
        상위 노출이 어렵고,<br>
        롱테일 키워드 전환 고려.<br><br>
        <strong>추천 전략:</strong><br>
        세부 키워드 공략
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
st.markdown("#### 함께 보는 지표")

st.markdown("""
| 지표 | 설명 |
|------|------|
| **PC 평균 CTR** | PC 검색 결과에서 광고를 클릭하는 비율. 높을수록 사용자 관심도 높음 |
| **모바일 평균 CTR** | 모바일 검색 결과 클릭률. 보통 PC보다 높음 |
| **노출 광고수** | 해당 키워드 검색 시 노출되는 평균 광고 개수. 많을수록 상업적 가치 높음 |
""")

st.markdown("""
<div class="warn-box">
    ⚠️ <strong>주의:</strong> 경쟁도는 '광고' 경쟁 기준입니다. 블로그 콘텐츠 경쟁과 정확히 일치하지는 않지만,
    상업적 가치가 높은 키워드일수록 블로그 경쟁도 함께 높아지는 경향이 있습니다.
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 4. 콘텐츠 포화지수
# ═══════════════════════════════════════════════════════
st.markdown("## 콘텐츠 포화지수")
st.markdown("""
**포화지수 = 콘텐츠 발행수 ÷ 월간 검색량**

검색 수요 대비 얼마나 많은 콘텐츠가 발행되었는지를 나타내는 지표입니다.
블로그, 카페, 전체를 분리하여 각각의 포화 상태를 확인할 수 있습니다.
""")

st.markdown("#### 포화지수 해석 기준")

st.markdown("""
| 포화지수 | 수준 | 의미 | 전략 |
|:---:|:---:|------|------|
| **≤ 0.3** | <span class="lv-tag lv-low">낮음</span> | 콘텐츠 부족. 수요 > 공급 | 🎯 블루오션! 적극 진입 추천 |
| **0.3 ~ 0.7** | <span class="lv-tag lv-mid">보통</span> | 적절한 경쟁. 수요 ≈ 공급 | 양질의 콘텐츠로 차별화 |
| **> 0.7** | <span class="lv-tag lv-high">높음</span> | 콘텐츠 과잉. 수요 < 공급 | 롱테일 키워드로 전환 추천 |
""", unsafe_allow_html=True)

st.markdown("")
st.markdown("#### 블로그 vs 카페 포화지수 활용법")

st.markdown("""
<div class="metric-card">
    <h4>📝 블로그 포화지수</h4>
    <p>
    네이버블로그에 발행된 글 수 기준.<br>
    <strong>블로그 포화 높음 + 카페 포화 낮음</strong> → 카페 콘텐츠로 우회 진입 가능<br>
    <strong>블로그 포화 낮음</strong> → 블로그 집중 공략!<br>
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="metric-card">
    <h4>☕ 카페 포화지수</h4>
    <p>
    네이버 카페에 발행된 글 수 기준.<br>
    카페 포화가 높으면 카페 마케팅 경쟁이 치열하다는 의미.<br>
    블로그와 카페 포화를 비교하여 <strong>어느 채널에 집중할지</strong> 결정하세요.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="metric-card">
    <h4>📊 전체 포화지수</h4>
    <p>
    블로그 + 카페 합산 기준.<br>
    <strong>전체 포화가 낮으면 해당 키워드는 아직 미개척 영역</strong>입니다.<br>
    어떤 채널이든 진입하면 상위 노출 가능성이 높습니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="tip-box">
    💡 <strong>실전 예시:</strong><br>
    "감기 증상 병원 방문 기준" → 포화지수 100+ (극도로 포화)<br>
    "강남 내과 감기 몸살 진료" → 포화지수 0.2 (블루오션!)<br><br>
    포화지수가 높은 키워드는 더 구체적인 롱테일 키워드로 쪼개면 기회를 찾을 수 있습니다.
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 5. 콘텐츠 발행수
# ═══════════════════════════════════════════════════════
st.markdown("## 콘텐츠 발행수")
st.markdown("""
해당 키워드로 네이버에 발행된 **블로그 글**과 **카페 글**의 총 개수입니다.
검색 API를 통해 실시간으로 조회합니다.
""")

st.markdown("""
| 항목 | 데이터 소스 | 설명 |
|------|-----------|------|
| **블로그 발행수** | 네이버블로그 검색 API | 해당 키워드가 포함된 블로그 글 총 수 |
| **카페 발행수** | 네이버 카페 검색 API | 해당 키워드가 포함된 카페 글 총 수 |
| **전체 발행수** | 블로그 + 카페 합산 | 전체 콘텐츠 경쟁 규모 |
""")

st.markdown("""
<div class="warn-box">
    ⚠️ <strong>참고:</strong> 발행수는 '누적' 총 수입니다 (최근 1개월이 아님).
    포화지수는 이 누적 발행수를 월간 검색량으로 나눈 것이므로,
    오래된 키워드일수록 포화지수가 높게 나올 수 있습니다.
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 6. 연관 키워드
# ═══════════════════════════════════════════════════════
st.markdown("## 연관 키워드")
st.markdown("""
메인 키워드와 함께 검색되거나 관련된 키워드 목록입니다.
네이버 검색광고 API의 키워드 도구에서 제공하는 데이터입니다.
""")

st.markdown("#### 연관 키워드 테이블 읽는 법")

st.markdown("""
| 컬럼 | 의미 | 활용법 |
|------|------|--------|
| **월간 검색량** | PC + 모바일 합산 검색량 | 높을수록 트래픽 잠재력 높음 |
| **PC / 모바일** | 기기별 검색량 분리 | 모바일 비율 높으면 모바일 최적화 글 작성 |
| **경쟁도** | 광고 경쟁 수준 | 낮음 → 진입 쉬움 |
| **PC CTR** | PC 검색 클릭률 | 높을수록 클릭 가능성 높음 |
| **블로그 발행수** | 해당 키워드 블로그 글 수 | 적을수록 블루오션 |
| **철자 유사도** | 메인 키워드와의 유사도 | 높을수록 동일 의도의 검색어 |
""")

st.markdown("")
st.markdown("#### 주제 클러스터")
st.markdown("""
연관 키워드를 **공통 주제별로 묶어** 보여줍니다.
같은 클러스터의 키워드는 하나의 글에서 함께 다루면 SEO에 효과적입니다.

예시: "강남 내과" 키워드 클러스터
- 🏷️ **내과** 클러스터: 강남 내과, 강남 내과 진료, 강남역 내과, 주말 내과 진료
- 🏷️ **피부과** 클러스터: 피부과 여드름 치료, 피부과 흉터 상담, 피부과 색소 치료
- 🏷️ **검진** 클러스터: 건강검진 비용, 건강검진 전 준비, 예방접종 주의사항
""")

st.markdown("")
st.markdown("#### 해시태그 & 워드 클라우드")
st.markdown("""
- **해시태그**: 검색량 상위 키워드를 `#태그` 형태로 추출. 블로그 하단에 복사하여 사용
- **워드 클라우드**: 검색량에 비례하여 키워드 크기를 시각화. 한눈에 핵심 키워드 파악
""")

st.markdown("""
<div class="tip-box">
    💡 <strong>활용 팁:</strong><br>
    1. 검색량 높은 연관 키워드를 소제목(H2, H3)에 배치<br>
    2. 같은 클러스터의 키워드를 한 섹션에서 자연스럽게 언급<br>
    3. 해시태그를 블로그 글 하단에 추가<br>
    4. 철자 유사도가 높은 키워드는 같은 검색 의도 → 하나의 글로 커버 가능
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 7. 검색 트렌드
# ═══════════════════════════════════════════════════════
st.markdown("## 검색 트렌드")
st.markdown("""
네이버 데이터랩 기반 검색어 **인기도 추이**입니다.
절대 검색량이 아닌 **상대적 비율(0~100)**로 표시됩니다.
가장 검색이 많았던 시점이 100, 나머지는 그에 비례한 값입니다.
""")

st.markdown("#### 필터 옵션")

st.markdown("""
| 필터 | 설명 | 활용 |
|------|------|------|
| **기간 단위** | 월별 / 주별 / 일별 | 월별로 전체 흐름 파악, 일별로 최근 변화 확인 |
| **기기** | 전체 / PC / 모바일 | 기기별 트렌드 차이 확인 |
| **성별** | 전체 / 남성 / 여성 | 타겟 성별의 관심도 변화 추적 |
| **연령대** | 전체 / 세분화 (0세~60세+) | 타겟 연령의 관심도 확인 |
| **비교 키워드** | 최대 4개 추가 | 여러 키워드의 트렌드를 한눈에 비교 |
""")

st.markdown("")
st.markdown("#### 트렌드 읽는 법")

st.markdown("""
<div class="metric-card">
    <h4>📈 상승 트렌드</h4>
    <p>
    최근 몇 달간 지수가 꾸준히 상승 중이라면, 관심이 커지고 있는 키워드입니다.<br>
    <strong>빠른 진입이 유리</strong>합니다. 트렌드가 피크에 도달하기 전에 콘텐츠를 발행하면
    상위 노출 확보에 유리합니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="metric-card">
    <h4>📉 하락 트렌드</h4>
    <p>
    지수가 하락하고 있다면 관심이 줄어들고 있습니다.<br>
    <strong>장기적 가치</strong>를 판단해야 합니다. 일시적 하락인지 영구적 감소인지 확인하세요.
    계절성 키워드라면 다음 시즌에 다시 상승할 수 있습니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="metric-card">
    <h4>🔄 주기적 패턴 (계절성)</h4>
    <p>
    매년 특정 시기에 반복적으로 오르내리는 패턴입니다.<br>
    예: "건강검진" (11월 급등), "여름 다이어트" (5~7월 상승)<br>
    <strong>상승 시기 1~2개월 전에 글을 발행</strong>하면 트래픽을 극대화할 수 있습니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="tip-box">
    💡 <strong>키워드 비교 활용:</strong><br>
    유사한 키워드를 비교하여 더 인기 있는 표현을 제목에 사용하세요.<br>
    예: "감기 증상 병원 방문 기준" vs "건강검진 준비 방법" → 트렌드가 더 높은 쪽을 메인 키워드로!
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 8. 인구통계
# ═══════════════════════════════════════════════════════
st.markdown("## 인구통계")
st.markdown("""
해당 키워드를 검색하는 사용자의 **성별 및 연령대 분포**입니다.
네이버 데이터랩 기반 상대적 비율로 제공됩니다.
""")

st.markdown("#### 성별 분석")
st.markdown("""
- 남성 / 여성 비율을 시각적 바와 트렌드 차트로 표시
- **주요 독자층의 성별**을 파악하여 글의 톤과 예시를 맞출 수 있음
- 예: 여성 비율 높은 키워드 → 감성적 표현, 공감 요소 강화
""")

st.markdown("#### 연령대 분석")
st.markdown("""
- 11개 연령대 (0~12세 ~ 60세+)의 검색 비율
- **핵심 타겟 연령**을 자동으로 표시
- 글의 난이도, 예시, 톤을 타겟 연령에 맞춤

| 연령대 | 글쓰기 팁 |
|--------|-----------|
| **20~39세** (초진 환자) | 쉬운 설명, 방문 기준, 예약 전 준비사항 |
| **40~54세** (보호자) | 전문적 + 따뜻한 톤, 가족 건강관리 관점 |
| **55세 이상** (만성질환 환자) | 차분한 톤, 검사 주기, 생활관리 강조 |
| **전체** (일반 환자) | 과장 없는 정보, FAQ, 의료진 코멘트 |
""")

st.markdown("""
<div class="tip-box">
    💡 <strong>페르소나 매칭:</strong><br>
    인구통계 결과와 병원 블로그 생성기의 <strong>페르소나(대상 독자)</strong>를 매칭하세요.<br>
    보호자 비율 높음 → "보호자" 페르소나 / 학생 비율 높음 → "일반 환자" 페르소나
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 9. 스마트블록
# ═══════════════════════════════════════════════════════
st.markdown("## 스마트블록")

st.markdown("""
네이버 스마트블록은 검색 의도에 따라 **검색결과 페이지를 여러 블록으로 자동 구성**하는 시스템입니다.
키워드마다 블록 구성이 다르며, 블로그 블록의 위치가 노출도에 직접적인 영향을 미칩니다.
""")

st.markdown("#### 주요 블록 유형")
st.markdown("""
<div class="metric-card">

| 블록 유형 | 설명 | 노출 영향 |
|-----------|------|-----------|
| 🧱 **블로그/리뷰** | 블로그·카페 게시글 (VIEW 탭) | 블로거에게 가장 중요한 블록 |
| 📰 **뉴스** | 최신 뉴스 기사 | 시의성 있는 키워드에 등장 |
| ❓ **지식iN** | Q&A 콘텐츠 | 질문형 키워드에 등장 |
| 🖼️ **이미지** | 관련 이미지 모음 | 시각적 키워드에 등장 |
| 🎬 **동영상** | 유튜브·네이버TV 영상 | 영상 콘텐츠 키워드에 등장 |
| 🛍️ **쇼핑** | 쇼핑 상품 | 상업적 키워드에 등장 |
| 📍 **플레이스** | 지도·장소 정보 | 지역 키워드에 등장 |
| 💰 **광고** | 검색광고 (파워링크) | 유기 검색을 한 단계 밀어냄 |
| 👤 **인플루언서** | 네이버 인플루언서 | 인플루언서 주제에 등장 |

</div>
""", unsafe_allow_html=True)

st.markdown("#### 블로그 노출 위치별 의미")
st.markdown("""
<div class="metric-card">

| 위치 | 의미 | CTR 영향 |
|------|------|----------|
| **1~2번째** | 🟢 스크롤 없이 바로 노출 | 매우 높음 (상위 노출 유리) |
| **3~4번째** | 🟡 한 번 스크롤 후 노출 | 보통 (콘텐츠 품질로 승부) |
| **5번째 이후** | 🔴 많은 스크롤 필요 | 낮음 (롱테일 전환 추천) |
| **블록 없음** | ⚠️ 블로그 전용 블록 미등장 | VIEW탭 확인 필요 |

</div>
""", unsafe_allow_html=True)

st.markdown("#### 스마트블록 활용 전략")
st.markdown("""
<div class="tip-box">
    💡 <strong>스마트블록 기반 SEO 전략:</strong><br><br>
    <strong>블로그가 상단일 때:</strong> 제목·썸네일 최적화 집중, 상위 노출 경쟁이 치열하므로 차별화된 콘텐츠 필수<br>
    <strong>광고 블록이 있을 때:</strong> 유기 검색 노출이 밀리므로, 더 강력한 제목과 메타 정보 필요<br>
    <strong>뉴스 블록이 있을 때:</strong> 시의성 있는 콘텐츠가 유리, 최신 이슈 반영<br>
    <strong>지식iN 블록이 있을 때:</strong> Q&A 형식의 콘텐츠 구성이 검색 의도에 부합<br>
    <strong>동영상 블록이 있을 때:</strong> 텍스트와 영상 콘텐츠 병행이 노출에 유리<br>
    <strong>쇼핑 블록이 있을 때:</strong> 상업적 의도 키워드 → 제품 리뷰 형태가 효과적<br>
    <strong>블로그 블록이 없을 때:</strong> 다른 콘텐츠 유형이 우선 → 롱테일 키워드로 전환 고려
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="warn-box">
    ⚠️ <strong>주의:</strong> 스마트블록 구성은 네이버 알고리즘에 의해 수시로 변경됩니다.
    분석 시점과 실제 검색 시 블록 순서가 다를 수 있으며, 기기(PC/모바일)와 로그인 상태에 따라서도 달라집니다.
    정기적으로 재분석하여 변화를 추적하는 것이 좋습니다.
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 10. 실전 활용 전략
# ═══════════════════════════════════════════════════════
st.markdown("## 실전 활용 전략")

st.markdown("### 1단계: 키워드 발굴")
st.markdown("""
<div class="metric-card">
    <p>
    1. 떠오르는 주제 키워드를 입력하여 분석<br>
    2. <strong>등급 S~B</strong>인 키워드를 메인 후보로 선정<br>
    3. 연관 키워드 중 <strong>검색량 1,000건+ & 포화 낮음</strong>인 키워드 발굴<br>
    4. 트렌드 상승 중인 키워드 우선 선택
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 2단계: 키워드 조합 전략")
st.markdown("""
<div class="metric-card">
    <p>
    <strong>제목 공식:</strong> [메인 키워드] + [연관 키워드] + [차별화 요소]<br><br>
    예시:<br>
    • 메인: "강남 내과" → "2026 강남 내과 감기 총정리 (의료진 검토)"<br>
    • 메인: "건강검진 준비사항" → "건강검진 준비사항 작성법 5가지 (의료진 검토 체크리스트)"<br><br>
    <strong>본문 키워드 배치:</strong><br>
    • H2 소제목에 검색량 높은 연관 키워드 배치<br>
    • 자연스럽게 3~5개 연관 키워드를 본문에 포함<br>
    • 해시태그를 글 하단에 추가
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 3단계: 타이밍 전략")
st.markdown("""
<div class="metric-card">
    <p>
    <strong>계절성 키워드:</strong> 트렌드 상승 시점 1~2개월 전에 발행<br>
    <strong>상승 트렌드:</strong> 즉시 발행 → 트렌드 피크에서 트래픽 극대화<br>
    <strong>안정 키워드:</strong> 꾸준한 정기 발행으로 누적 트래픽 확보<br><br>
    <strong>발행 주기 추천:</strong><br>
    • 포화 낮음 키워드: 주 1~2회 → 빠르게 상위 선점<br>
    • 포화 보통 키워드: 주 2~3회 → 꾸준한 양으로 승부<br>
    • 포화 높음 키워드: 월 1~2회 고퀄리티 글 → 차별화
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 4단계: 분석 → 글 생성 연동")
st.markdown("""
<div class="metric-card">
    <p>
    1. 키워드 분석 페이지에서 키워드 분석 실행<br>
    2. 연관 키워드 탭에서 사용할 키워드 선택<br>
    3. <strong>"글 생성 페이지로 이동"</strong> 버튼 클릭<br>
    4. 메인 페이지에서 <strong>키워드 분석 스킬 ON</strong> 확인<br>
    5. 글 생성 → SEO 데이터가 자동으로 프롬프트에 주입됨<br><br>
    ✅ AI가 검색량 높은 키워드를 제목과 소제목에 자동 배치합니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("")
st.markdown("""
<div class="tip-box">
    💡 <strong>핵심 요약:</strong><br>
    좋은 블로그 키워드 = <strong>검색량 높음</strong> + <strong>경쟁 낮음</strong> + <strong>포화 낮음</strong> + <strong>트렌드 상승</strong><br>
    이 4가지를 모두 만족하는 키워드가 S등급입니다. 완벽한 키워드를 찾기 어렵다면,
    2~3가지를 만족하는 A·B등급 키워드로 꾸준히 발행하는 것이 가장 효과적입니다.
</div>
""", unsafe_allow_html=True)

# ─── 푸터 ───
st.markdown("")
st.markdown("""
<div style="text-align: center; padding: 1.5rem 0; color: #a1a1aa; font-size: 0.75rem;">
    키워드 분석 가이드 · 메디블로그 AI 마케팅 툴<br>
    <span style="color: #818cf8;">데이터 기반 블로그 SEO 전략</span>
</div>
""", unsafe_allow_html=True)
