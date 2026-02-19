"""네이버 API 클라이언트 - 키워드 분석 (검색광고, DataLab, 블로그 검색, 스마트블록)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote_plus

import requests
from pydantic import BaseModel, Field


# ── Pydantic 응답 모델 ──


class KeywordMetrics(BaseModel):
    """검색광고 API 키워드 결과."""

    keyword: str
    monthly_pc_qc: int = 0
    monthly_mobile_qc: int = 0
    monthly_pc_click: float = 0.0
    monthly_mobile_click: float = 0.0
    monthly_pc_ctr: float = 0.0
    monthly_mobile_ctr: float = 0.0
    comp_idx: str = ""  # low / medium / high
    pl_avg_depth: int = 0

    @property
    def total_monthly_qc(self) -> int:
        return self.monthly_pc_qc + self.monthly_mobile_qc


class TrendDataPoint(BaseModel):
    """DataLab 트렌드 데이터 포인트."""

    period: str
    ratio: float


class TrendResult(BaseModel):
    """DataLab 트렌드 결과."""

    title: str
    keywords: list[str] = Field(default_factory=list)
    data: list[TrendDataPoint] = Field(default_factory=list)


class SaturationResult(BaseModel):
    """포화지수 결과."""

    keyword: str
    blog_post_count: int = 0
    monthly_search_volume: int = 0
    saturation_index: float = 0.0
    classification: str = ""  # 포화 / 경쟁 / 기회 / 블루오션


class DetailedSaturation(BaseModel):
    """블로그/카페/전체 분리 포화지수."""

    keyword: str
    blog_count: int = 0
    cafe_count: int = 0
    monthly_search_volume: int = 0
    blog_saturation: float = 0.0
    cafe_saturation: float = 0.0
    total_saturation: float = 0.0
    blog_level: str = ""  # 낮음 / 보통 / 높음
    cafe_level: str = ""
    total_level: str = ""


class KeywordGrade(BaseModel):
    """키워드 종합 등급."""

    keyword: str
    grade: str = ""  # S / A / B / C / D
    score: float = 0.0
    search_volume_score: float = 0.0
    competition_score: float = 0.0
    saturation_score: float = 0.0
    summary: str = ""


# ── API 클라이언트 ──


class NaverSearchAdClient:
    """네이버 검색광고 API (키워드 도구).

    HMAC-SHA256 서명 인증.
    필요 환경변수: NAVER_AD_API_KEY, NAVER_AD_SECRET_KEY, NAVER_AD_CUSTOMER_ID
    """

    BASE_URL = "https://api.searchad.naver.com"

    def __init__(self) -> None:
        self.api_key = os.environ.get("NAVER_AD_API_KEY", "")
        self.secret_key = os.environ.get("NAVER_AD_SECRET_KEY", "")
        self.customer_id = os.environ.get("NAVER_AD_CUSTOMER_ID", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.secret_key and self.customer_id)

    def _generate_signature(self, timestamp: str, method: str, path: str) -> str:
        message = f"{timestamp}.{method}.{path}"
        raw = hmac.new(
            self.secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(raw).decode("utf-8")

    def _get_headers(self, method: str, path: str) -> dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        return {
            "X-API-KEY": self.api_key,
            "X-CUSTOMER": self.customer_id,
            "X-Timestamp": timestamp,
            "X-Signature": self._generate_signature(timestamp, method, path),
            "Content-Type": "application/json",
        }

    @staticmethod
    def _safe_int(value: Any) -> int:
        """'< 10' 같은 문자열 값 안전하게 처리."""
        if isinstance(value, str):
            return 0
        try:
            return int(value or 0)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _safe_float(value: Any) -> float:
        if isinstance(value, str):
            return 0.0
        try:
            return float(value or 0.0)
        except (ValueError, TypeError):
            return 0.0

    def get_keyword_metrics(self, keywords: list[str]) -> list[KeywordMetrics]:
        """키워드 검색량 및 경쟁도 조회."""
        if not self.is_configured:
            return []

        # 네이버 검색광고 API는 공백이 포함된 키워드를 허용하지 않음
        cleaned = [kw.replace(" ", "") for kw in keywords if kw.strip()]
        if not cleaned:
            return []

        path = "/keywordstool"
        headers = self._get_headers("GET", path)
        params = {
            "hintKeywords": ",".join(cleaned),
            "showDetail": "1",
        }

        response = requests.get(
            f"{self.BASE_URL}{path}",
            headers=headers,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        results: list[KeywordMetrics] = []
        for item in data.get("keywordList", []):
            results.append(
                KeywordMetrics(
                    keyword=item.get("relKeyword", ""),
                    monthly_pc_qc=self._safe_int(item.get("monthlyPcQcCnt")),
                    monthly_mobile_qc=self._safe_int(item.get("monthlyMobileQcCnt")),
                    monthly_pc_click=self._safe_float(item.get("monthlyAvePcClkCnt")),
                    monthly_mobile_click=self._safe_float(
                        item.get("monthlyAveMobileClkCnt")
                    ),
                    monthly_pc_ctr=self._safe_float(item.get("monthlyAvePcCtr")),
                    monthly_mobile_ctr=self._safe_float(
                        item.get("monthlyAveMobileCtr")
                    ),
                    comp_idx=str(item.get("compIdx", "")),
                    pl_avg_depth=self._safe_int(item.get("plAvgDepth")),
                )
            )

        return results


class NaverDataLabClient:
    """네이버 DataLab API (검색어 트렌드, 인구통계).

    필요 환경변수: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
    """

    BASE_URL = "https://openapi.naver.com"

    def __init__(self) -> None:
        self.client_id = os.environ.get("NAVER_CLIENT_ID", "")
        self.client_secret = os.environ.get("NAVER_CLIENT_SECRET", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _get_headers(self) -> dict[str, str]:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Content-Type": "application/json",
        }

    def get_search_trend(
        self,
        keywords: list[str],
        start_date: str = "",
        end_date: str = "",
        time_unit: str = "month",
        device: str = "",
        ages: list[str] | None = None,
        gender: str = "",
    ) -> list[TrendResult]:
        """검색어 트렌드 조회."""
        if not self.is_configured:
            return []

        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # 키워드 그룹 구성 (최대 5개)
        keyword_groups = [
            {"groupName": kw, "keywords": [kw]} for kw in keywords[:5]
        ]

        body: dict[str, Any] = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": keyword_groups,
        }
        if device:
            body["device"] = device
        if ages:
            body["ages"] = ages
        if gender:
            body["gender"] = gender

        response = requests.post(
            f"{self.BASE_URL}/v1/datalab/search",
            headers=self._get_headers(),
            json=body,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        results: list[TrendResult] = []
        for result in data.get("results", []):
            results.append(
                TrendResult(
                    title=result.get("title", ""),
                    keywords=result.get("keywords", []),
                    data=[
                        TrendDataPoint(period=d["period"], ratio=d["ratio"])
                        for d in result.get("data", [])
                    ],
                )
            )

        return results

    def get_blog_count(self, keyword: str) -> int:
        """블로그 검색 결과 수 조회 (포화지수용)."""
        if not self.is_configured:
            return 0

        response = requests.get(
            f"{self.BASE_URL}/v1/search/blog.json",
            headers=self._get_headers(),
            params={"query": keyword, "display": 1},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("total", 0)

    def get_cafe_count(self, keyword: str) -> int:
        """카페 검색 결과 수 조회 (포화지수용)."""
        if not self.is_configured:
            return 0

        response = requests.get(
            f"{self.BASE_URL}/v1/search/cafearticle.json",
            headers=self._get_headers(),
            params={"query": keyword, "display": 1},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("total", 0)


def calculate_saturation(
    keyword: str,
    blog_count: int,
    monthly_search_volume: int,
) -> SaturationResult:
    """포화지수 계산.

    포화지수 = 블로그 발행수 / 월간 검색량
    - > 1.0: 포화 (콘텐츠가 수요보다 많음)
    - > 0.5: 경쟁 (경쟁 치열)
    - > 0.1: 기회 (진입 여지 있음)
    - ≤ 0.1: 블루오션
    """
    if monthly_search_volume == 0:
        return SaturationResult(
            keyword=keyword,
            blog_post_count=blog_count,
            monthly_search_volume=0,
            saturation_index=999.0,
            classification="검색량 없음",
        )

    idx = blog_count / monthly_search_volume

    if idx > 1.0:
        classification = "포화"
    elif idx > 0.5:
        classification = "경쟁"
    elif idx > 0.1:
        classification = "기회"
    else:
        classification = "블루오션"

    return SaturationResult(
        keyword=keyword,
        blog_post_count=blog_count,
        monthly_search_volume=monthly_search_volume,
        saturation_index=round(idx, 3),
        classification=classification,
    )


def _saturation_level(index: float) -> str:
    """포화지수 → 낮음/보통/높음 레벨."""
    if index <= 0.3:
        return "낮음"
    elif index <= 0.7:
        return "보통"
    else:
        return "높음"


def calculate_detailed_saturation(
    keyword: str,
    blog_count: int,
    cafe_count: int,
    monthly_search_volume: int,
) -> DetailedSaturation:
    """블로그/카페/전체 분리 포화지수 계산."""
    if monthly_search_volume == 0:
        return DetailedSaturation(
            keyword=keyword,
            blog_count=blog_count,
            cafe_count=cafe_count,
            monthly_search_volume=0,
            blog_saturation=999.0,
            cafe_saturation=999.0,
            total_saturation=999.0,
            blog_level="측정불가",
            cafe_level="측정불가",
            total_level="측정불가",
        )

    blog_sat = blog_count / monthly_search_volume
    cafe_sat = cafe_count / monthly_search_volume
    total_sat = (blog_count + cafe_count) / monthly_search_volume

    return DetailedSaturation(
        keyword=keyword,
        blog_count=blog_count,
        cafe_count=cafe_count,
        monthly_search_volume=monthly_search_volume,
        blog_saturation=round(blog_sat, 3),
        cafe_saturation=round(cafe_sat, 3),
        total_saturation=round(total_sat, 3),
        blog_level=_saturation_level(blog_sat),
        cafe_level=_saturation_level(cafe_sat),
        total_level=_saturation_level(total_sat),
    )


def calculate_keyword_grade(
    keyword: str,
    monthly_search_volume: int,
    comp_idx: str,
    blog_saturation: float,
) -> KeywordGrade:
    """키워드 종합 등급 계산.

    3가지 요소를 점수화하여 종합 등급 산출:
    - 검색량 점수 (40%): 검색량이 높을수록 좋음
    - 경쟁도 점수 (30%): 경쟁이 낮을수록 좋음
    - 포화도 점수 (30%): 포화도가 낮을수록 좋음
    """
    # 검색량 점수 (0~100)
    if monthly_search_volume >= 50000:
        vol_score = 100
    elif monthly_search_volume >= 10000:
        vol_score = 80
    elif monthly_search_volume >= 3000:
        vol_score = 60
    elif monthly_search_volume >= 1000:
        vol_score = 40
    elif monthly_search_volume >= 100:
        vol_score = 20
    else:
        vol_score = 5

    # 경쟁도 점수 (0~100, 낮을수록 좋음)
    comp_score_map = {"low": 100, "medium": 50, "high": 10}
    comp_score = comp_score_map.get(comp_idx, 50)

    # 포화도 점수 (0~100, 낮을수록 좋음)
    if blog_saturation <= 0.1:
        sat_score = 100
    elif blog_saturation <= 0.3:
        sat_score = 80
    elif blog_saturation <= 0.5:
        sat_score = 60
    elif blog_saturation <= 1.0:
        sat_score = 30
    else:
        sat_score = 10

    total = vol_score * 0.4 + comp_score * 0.3 + sat_score * 0.3

    if total >= 80:
        grade = "S"
        summary = "최상급 키워드! 검색량 높고 경쟁 낮아 진입 적기입니다."
    elif total >= 65:
        grade = "A"
        summary = "우수한 키워드. 양질의 콘텐츠로 상위 노출을 노릴 수 있습니다."
    elif total >= 50:
        grade = "B"
        summary = "괜찮은 키워드. 차별화된 콘텐츠가 필요합니다."
    elif total >= 35:
        grade = "C"
        summary = "보통 수준. 롱테일 키워드 조합을 고려해보세요."
    else:
        grade = "D"
        summary = "비추천 키워드. 검색량이 부족하거나 경쟁이 너무 치열합니다."

    return KeywordGrade(
        keyword=keyword,
        grade=grade,
        score=round(total, 1),
        search_volume_score=round(vol_score, 1),
        competition_score=round(comp_score, 1),
        saturation_score=round(sat_score, 1),
        summary=summary,
    )


# ── 스마트블록 모델 & 스크래퍼 ──


class SmartBlockItem(BaseModel):
    """스마트블록 내 개별 콘텐츠 아이템."""

    title: str = ""
    url: str = ""
    source: str = ""  # blog.naver.com, cafe.naver.com, kin.naver.com 등
    content_type: str = ""  # blog, cafe, web, kin, news, image, video 등


class SmartBlock(BaseModel):
    """네이버 검색결과 스마트블록."""

    position: int = 0  # 페이지 내 순서 (1부터)
    block_id: str = ""  # data-meta-area 값
    block_type: str = ""  # 블록 유형 (블로그, 뉴스, 지식iN 등)
    content_type: str = ""  # data-meta-ssuid 기반 (review, web, kin, news 등)
    item_count: int = 0  # 블록 내 아이템 수
    items: list[SmartBlockItem] = Field(default_factory=list)


class SmartBlockResult(BaseModel):
    """스마트블록 분석 전체 결과."""

    keyword: str
    total_blocks: int = 0
    blocks: list[SmartBlock] = Field(default_factory=list)
    blog_position: int = 0  # 블로그 블록의 위치 (0이면 없음)
    blog_count: int = 0  # 블로그 탭 내 아이템 수
    has_ad_block: bool = False  # 광고 블록 존재 여부
    block_type_summary: dict[str, int] = Field(default_factory=dict)  # 유형별 블록 수


# 블록 유형 매핑
_BLOCK_TYPE_MAP: dict[str, str] = {
    "review": "블로그/리뷰",
    "web": "웹사이트",
    "kin": "지식iN",
    "image": "이미지",
    "video": "동영상",
    "news": "뉴스",
    "qra": "연관주제",
    "faq": "FAQ",
    "view": "VIEW(통합)",
    "blog": "블로그",
    "cafe": "카페",
    "shop": "쇼핑",
    "place": "플레이스",
    "map": "지도",
    "music": "뮤직",
    "book": "도서",
    "movie": "영화",
    "dict": "사전",
    "academic": "학술정보",
    "encyclopedia": "백과사전",
}

# 블록 ID → 블록 유형 추정 매핑
_BLOCK_ID_MAP: dict[str, str] = {
    "ugB_pkR": "광고/브랜드",
    "ugB_adR": "광고/브랜드",
    "ugB_ipR": "인플루언서",
    "urB_coR": "통합검색",
    "urB_imM": "이미지",
    "urB_boR": "블로그/콘텐츠",
    "kwX_ndT": "연관주제",
    "nws_all": "뉴스",
    "kwL_ssT": "연관검색어",
    "pll_alR": "플레이스",
    "vdo_alR": "동영상",
    "klg_alR": "지식iN",
    "shp_alR": "쇼핑",
    "web_nrg": "웹사이트",
    "dct_alR": "사전",
}


def _detect_block_type(block_id: str, content_type: str) -> str:
    """블록 ID와 content_type으로 블록 유형 추정."""
    # 블록 ID로 매칭
    if block_id in _BLOCK_ID_MAP:
        return _BLOCK_ID_MAP[block_id]
    # content_type으로 매칭
    if content_type in _BLOCK_TYPE_MAP:
        return _BLOCK_TYPE_MAP[content_type]
    # 블록 ID 패턴 매칭
    if "nws" in block_id:
        return "뉴스"
    if "shp" in block_id:
        return "쇼핑"
    if "vdo" in block_id:
        return "동영상"
    if "klg" in block_id or "kin" in block_id:
        return "지식iN"
    if "pll" in block_id or "plc" in block_id:
        return "플레이스"
    if "img" in block_id or "imM" in block_id:
        return "이미지"
    if "web" in block_id:
        return "웹사이트"
    if "dct" in block_id:
        return "사전"
    if "bk_" in block_id or "book" in block_id:
        return "도서"
    return block_id  # fallback: 원본 ID 반환


def _detect_item_source(url: str) -> str:
    """URL에서 콘텐츠 소스 타입 추출."""
    if "blog.naver.com" in url:
        return "blog"
    if "cafe.naver.com" in url:
        return "cafe"
    if "kin.naver.com" in url:
        return "kin"
    if "news.naver.com" in url:
        return "news"
    if "shopping.naver.com" in url or "smartstore" in url:
        return "shop"
    if "tv.naver.com" in url or "youtube.com" in url:
        return "video"
    if "map.naver.com" in url or "place.naver.com" in url:
        return "place"
    return "web"


def scrape_smart_blocks(keyword: str) -> SmartBlockResult:
    """네이버 검색결과 페이지에서 스마트블록 구조를 스크래핑.

    requests + BeautifulSoup로 search.naver.com/search.naver 파싱.
    API 키 불필요 (공개 페이지 스크래핑).
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return SmartBlockResult(keyword=keyword)

    url = f"https://search.naver.com/search.naver?query={quote_plus(keyword)}&where=nexearch"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception:
        return SmartBlockResult(keyword=keyword)

    soup = BeautifulSoup(resp.text, "html.parser")

    # 스마트블록 탐색: div.sc_new[data-meta-area]
    block_divs = soup.select("div.sc_new[data-meta-area]")
    if not block_divs:
        # 대체 선택자
        block_divs = soup.select("section[data-meta-area]")

    blocks: list[SmartBlock] = []
    blog_position = 0
    blog_count = 0
    has_ad = False
    block_type_summary: dict[str, int] = {}

    for idx, div in enumerate(block_divs, start=1):
        block_id = div.get("data-meta-area", "")
        content_type_raw = div.get("data-meta-ssuid", "")

        # content_type 추출 (여러 값일 수 있음, 첫 번째 사용)
        content_type = content_type_raw.split(",")[0].strip() if content_type_raw else ""

        block_type = _detect_block_type(block_id, content_type)

        # 아이템 추출: 블록 내 링크들
        items: list[SmartBlockItem] = []
        seen_urls: set[str] = set()

        # 무시할 텍스트 패턴 (UI 버튼 등)
        _skip_texts = {
            "Keep에 저장", "Keep에 바로가기", "저장", "관련도순", "최신순",
            "팬하기", "더보기", "전체보기", "접기", "펼치기",
            "모바일 메인 언론사", "검색결과 더보기", "뉴스 더보기",
        }

        # 콘텐츠 도메인 패턴 (우선 추출)
        _content_domains = (
            "blog.naver.com", "cafe.naver.com", "kin.naver.com",
            "news.naver.com", "tv.naver.com", "youtube.com",
            "in.naver.com", "post.naver.com",
        )

        for a_tag in div.select("a[href]"):
            href = a_tag.get("href", "")
            title = a_tag.get_text(strip=True)

            if not href or not title or href in seen_urls:
                continue
            if not href.startswith("http"):
                continue
            if title in _skip_texts or len(title) < 3:
                continue
            # 네이버 서비스 홈 링크 스킵 (예: "네이버 지식iN")
            if title.startswith("네이버 ") and len(title) < 15:
                continue

            seen_urls.add(href)
            source = _detect_item_source(href)
            items.append(SmartBlockItem(
                title=title[:100],
                url=href,
                source=source,
                content_type=content_type or source,
            ))
            if len(items) >= 10:
                break

        # 콘텐츠 도메인 아이템을 앞으로 정렬
        items.sort(
            key=lambda x: (
                0 if any(d in x.url for d in _content_domains) else 1,
                -len(x.title),
            )
        )

        block = SmartBlock(
            position=idx,
            block_id=block_id,
            block_type=block_type,
            content_type=content_type,
            item_count=len(items),
            items=items,
        )
        blocks.append(block)

        # 블로그 블록 위치 감지
        is_blog_block = (
            content_type in ("review", "view", "blog")
            or "블로그" in block_type
            or "VIEW" in block_type
            or "리뷰" in block_type
            or block_id in ("urB_boR",)
        )
        if is_blog_block and blog_position == 0:
            blog_position = idx
            blog_count = len(items)

        # 광고 블록 감지
        if "광고" in block_type or "브랜드" in block_type or block_id == "ugB_pkR":
            has_ad = True

        # 유형별 집계
        block_type_summary[block_type] = block_type_summary.get(block_type, 0) + 1

    return SmartBlockResult(
        keyword=keyword,
        total_blocks=len(blocks),
        blocks=blocks,
        blog_position=blog_position,
        blog_count=blog_count,
        has_ad_block=has_ad,
        block_type_summary=block_type_summary,
    )
