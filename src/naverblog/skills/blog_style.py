"""Hospital blog style skill.

Style data is stored in the app DB and can be edited in the UI.
When the DB has no custom values, the defaults below are seeded.
"""

from __future__ import annotations

from naverblog.skills.base import SkillBase, SkillContext, SkillResult


DEFAULT_COMMON_STYLE = """\
## 메디블로그 AI 병원 콘텐츠 공통 스타일 가이드

### 블로그 정체성
- 블로그명: 메디블로그 AI 병원 콘텐츠
- 필자 관점: 개원의 또는 병원 내부 의료진이 직접 검토한 건강정보
- 타겟: 지역 환자, 보호자, 병원 방문을 고민하는 일반 독자
- 핵심 가치: 신뢰, 쉬운 설명, 과장 없는 안내, 병원 방문 판단에 도움

### 문체 규칙
- 기본 어미: ~합니다/~해요를 자연스럽게 혼용
- 전문 용어는 먼저 쉬운 말로 풀어 쓰고, 괄호 안에 의학 용어를 보조적으로 제시
- 독자를 불안하게 몰아가지 않고, 필요한 경우 진료 상담을 권유
- 특정 치료 효과를 단정하지 않고 개인 상태에 따라 달라질 수 있음을 안내
- 병원명, 지역명, 진료과, 증상 키워드를 제목과 소제목에 자연스럽게 포함

### 글 구조
1. 제목: 지역/진료과/증상 키워드를 포함하되 과장하지 않음
2. 도입: 환자가 실제로 검색할 만한 고민에서 시작
3. 쉬운 설명: 증상, 원인, 검사, 치료 흐름을 환자 눈높이로 정리
4. 방문 기준: 병원에 가야 하는 상황과 지켜볼 수 있는 상황을 구분
5. 의료진 코멘트: 원장이 직접 설명하는 듯한 신뢰도 높은 문장
6. FAQ 또는 체크리스트: 독자가 저장하고 싶은 형태로 마무리
7. 주의 문구: 온라인 글은 일반 정보이며 정확한 판단은 진료가 필요함

### 반드시 피할 표현
- 완치 보장, 100% 효과, 부작용 없음, 무조건 좋아짐
- 최고, 유일, 압도적 1위처럼 객관적 근거 없는 최상급 표현
- 환자 후기처럼 보이는 과장된 체험담
- 불필요한 공포 조장이나 특정 시술 유도
- 의료광고 심의상 문제가 될 수 있는 전후사진/가격 중심 표현

### 콘텐츠 전략
- 의사가 직접 쓰거나 검토했다는 신뢰감을 문장 구조로 보여줌
- 단순 마케팅 문구보다 환자의 검색 의도 해결을 먼저 배치
- 대행사식 광고 문구보다 진료실에서 설명하듯 자연스럽게 작성
- 글 하단에는 예약 유도보다 상담/진료 필요성 안내를 부드럽게 배치
- 체크리스트, 표, FAQ를 활용해 저장 가치가 있는 글로 구성"""


DEFAULT_CATEGORY_STYLES: dict[str, str] = {
    "지역 진료 키워드": """\
### 카테고리: 지역 진료 키워드
- **톤**: 지역 주민에게 차분히 안내하는 병원 공식 블로그
- **구조**: 지역 환자 고민 → 진료과 설명 → 방문 기준 → 병원 선택 체크포인트
- **핵심 메시지**: "가까운 병원에서도 충분히 확인해야 할 증상이 있습니다"
- **포함 요소**: 지역명, 진료과, 대표 증상, 내원 전 준비사항""",
    "증상 설명 콘텐츠": """\
### 카테고리: 증상 설명 콘텐츠
- **톤**: 불안을 낮추는 의료진 설명형
- **구조**: 흔한 증상 → 가능한 원인 → 위험 신호 → 진료 시 확인 항목
- **핵심 메시지**: "증상만으로 단정하지 말고 지속 기간과 동반 증상을 함께 봐야 합니다"
- **포함 요소**: 자가 확인 체크리스트, 응급/비응급 구분, FAQ""",
    "검사·시술 안내": """\
### 카테고리: 검사·시술 안내
- **톤**: 객관적이고 안전 중심
- **구조**: 검사 목적 → 준비 과정 → 진행 흐름 → 결과 상담 → 주의사항
- **핵심 메시지**: "검사와 시술은 개인 상태에 맞게 결정되어야 합니다"
- **주의**: 효과 보장, 가격 강조, 과장된 전후 비교 금지""",
    "건강검진·예방접종": """\
### 카테고리: 건강검진·예방접종
- **톤**: 실용적이고 일정 관리에 도움 되는 안내
- **구조**: 대상자 → 권장 시기 → 준비물 → 검사/접종 후 주의사항
- **핵심 메시지**: "증상이 없을 때 확인하는 것이 예방의 시작입니다"
- **포함 요소**: 연령/상황별 체크리스트, 예약 전 확인사항""",
    "병원 이용 안내": """\
### 카테고리: 병원 이용 안내
- **톤**: 친절한 안내 데스크와 의료진이 함께 설명하는 느낌
- **구조**: 방문 전 궁금증 → 접수/진료 흐름 → 소요 시간 → 준비물 → FAQ
- **핵심 메시지**: "처음 방문하는 환자도 편하게 이해할 수 있어야 합니다"
- **포함 요소**: 운영시간, 위치 설명, 진료 전 준비사항""",
    "FAQ 콘텐츠": """\
### 카테고리: FAQ 콘텐츠
- **톤**: 짧고 명확한 질의응답
- **구조**: 질문 5~7개 → 답변 → 의료진 한 줄 코멘트 → 내원 기준
- **핵심 메시지**: "환자가 검색창에 묻는 질문에 먼저 답합니다"
- **포함 요소**: 오해 바로잡기, 병원 방문 기준, 주의사항""",
    "의료광고 표현 점검": """\
### 카테고리: 의료광고 표현 점검
- **톤**: 내부 검수자처럼 차분하고 정확한 문체
- **구조**: 원문 표현 → 위험 이유 → 대체 표현 → 최종 문장
- **핵심 메시지**: "신뢰도 높은 글은 과장 표현을 줄일수록 강해집니다"
- **포함 요소**: 금지/주의 표현, 환자 안전 중심 대체 문장""",
}


def seed_default_styles(db) -> None:
    """Seed default styles when the database has no style rows."""
    if db.get_blog_style("common") is None:
        db.save_blog_style("common", DEFAULT_COMMON_STYLE)
    for cat_name, cat_style in DEFAULT_CATEGORY_STYLES.items():
        if db.get_blog_style(cat_name) is None:
            db.save_blog_style(cat_name, cat_style)


def get_available_categories(db) -> list[str]:
    """Return stored category names except the shared common style."""
    styles = db.list_blog_styles()
    return [key for key in styles if key != "common"]


AVAILABLE_CATEGORIES = list(DEFAULT_CATEGORY_STYLES.keys())


class BlogStyleSkill(SkillBase):
    """Inject hospital blog writing style into LLM prompts."""

    @property
    def name(self) -> str:
        return "blog_style"

    @property
    def description(self) -> str:
        return "병원 블로그 스타일 가이드 (카테고리별 문체/구조 적용)"

    def execute(self, context: SkillContext) -> SkillResult:
        category = getattr(context, "category", None) or ""
        db = getattr(context, "db", None)

        common = db.get_blog_style("common") if db else None
        style_parts = [common or DEFAULT_COMMON_STYLE]

        if category:
            cat_style = db.get_blog_style(category) if db else DEFAULT_CATEGORY_STYLES.get(category)
            if cat_style:
                style_parts.append(cat_style)
            elif db:
                for cat_name, style_text in db.list_blog_styles().items():
                    if cat_name != "common" and (category in cat_name or cat_name in category):
                        style_parts.append(style_text)
                        break

        available = get_available_categories(db) if db else AVAILABLE_CATEGORIES

        return SkillResult(
            skill_name=self.name,
            data={
                "blog_name": "메디블로그 AI 병원 콘텐츠",
                "blog_id": "clinic-blog",
                "category": category,
                "available_categories": available,
            },
            summary="\n".join(style_parts),
        )
