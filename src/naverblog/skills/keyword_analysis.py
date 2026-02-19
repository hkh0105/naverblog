"""키워드 분석 스킬 - 네이버 검색광고 API 기반 키워드 데이터를 프롬프트에 주입."""

from __future__ import annotations

import os

from naverblog.skills.base import SkillBase, SkillContext, SkillResult


class KeywordAnalysisSkill(SkillBase):
    """키워드 검색량/경쟁도 분석 스킬.

    네이버 검색광고 API를 사용하여 키워드 검색량, 경쟁도,
    연관 키워드를 조회하고 프롬프트에 SEO 데이터를 주입합니다.
    """

    @property
    def name(self) -> str:
        return "keyword_analysis"

    @property
    def description(self) -> str:
        return "네이버 키워드 분석 (검색량, 경쟁도, 연관 키워드)"

    def execute(self, context: SkillContext) -> SkillResult:
        ad_key = os.environ.get("NAVER_AD_API_KEY", "")
        if not ad_key:
            return SkillResult(
                skill_name=self.name,
                data={},
                summary="[키워드 분석 스킵: NAVER_AD_API_KEY가 설정되지 않았습니다]",
            )

        try:
            from naverblog.naver_api import NaverSearchAdClient
        except ImportError as e:
            return SkillResult(
                skill_name=self.name,
                data={},
                summary=f"[키워드 분석 스킵: {e}]",
            )

        # 캐시 확인
        db = getattr(context, "db", None)
        cache_key = context.topic.strip()

        if db:
            try:
                cached = db.get_keyword_cache(cache_key, "search_volume")
                if cached:
                    return SkillResult(
                        skill_name=self.name,
                        data=cached.get("data", {}),
                        summary=cached.get("summary", ""),
                        raw=cached,
                    )
            except Exception:
                pass  # 캐시 테이블 없어도 무시

        # API 호출
        try:
            ad_client = NaverSearchAdClient()
            metrics = ad_client.get_keyword_metrics([cache_key])
        except Exception as e:
            return SkillResult(
                skill_name=self.name,
                data={},
                summary=f"[키워드 분석 오류: {e}]",
            )

        if not metrics:
            return SkillResult(
                skill_name=self.name,
                data={},
                summary="[키워드 분석: 결과 없음]",
            )

        # 메인 키워드와 연관 키워드 분리
        input_kw = metrics[0]
        related = metrics[1:11]  # Top 10

        # 프롬프트 주입용 요약 생성
        comp_labels = {"low": "낮음", "medium": "보통", "high": "높음"}
        summary_parts = ["## 키워드 분석 결과 (SEO 데이터)\n"]

        comp_label = comp_labels.get(input_kw.comp_idx, input_kw.comp_idx)
        summary_parts.append(
            f"### 메인 키워드: {input_kw.keyword}\n"
            f"- 월간 검색량: PC {input_kw.monthly_pc_qc:,}건 / "
            f"모바일 {input_kw.monthly_mobile_qc:,}건 / "
            f"합계 {input_kw.total_monthly_qc:,}건\n"
            f"- 경쟁도: {comp_label}\n"
        )

        if related:
            summary_parts.append("### 연관 키워드 (검색량 순)\n")
            for kw in sorted(
                related, key=lambda x: x.total_monthly_qc, reverse=True
            ):
                summary_parts.append(
                    f"- {kw.keyword}: "
                    f"월 {kw.total_monthly_qc:,}건 "
                    f"(PC {kw.monthly_pc_qc:,} / 모바일 {kw.monthly_mobile_qc:,})"
                )

        summary_parts.append(
            "\n### SEO 가이드\n"
            "위 키워드들을 글 제목과 본문에 자연스럽게 포함하여 "
            "네이버 검색 상위 노출을 노려주세요. "
            "특히 검색량이 높은 키워드를 소제목(##)에 배치하면 효과적입니다."
        )

        summary = "\n".join(summary_parts)

        data = {
            "main_keyword": input_kw.model_dump(),
            "related_keywords": [kw.model_dump() for kw in related],
            "total_results": len(metrics),
        }

        # 캐시 저장
        if db:
            try:
                cache_data = {"data": data, "summary": summary}
                db.save_keyword_cache(cache_key, "search_volume", cache_data, ttl_hours=24)
            except Exception:
                pass  # 캐시 테이블 없어도 무시

        return SkillResult(
            skill_name=self.name,
            data=data,
            summary=summary,
            raw={"metrics": [m.model_dump() for m in metrics]},
        )
