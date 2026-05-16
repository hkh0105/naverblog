"""Educational Python prototype for the clinic blog marketing project.

This script is intentionally standard-library only so it can be submitted as a
clear implementation artifact for the problem-solving process report.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class BlogRequest:
    region: str
    department: str
    symptom: str
    doctor_comment: str


@dataclass
class RiskFinding:
    expression: str
    reason: str
    suggestion: str


RISK_PATTERNS: list[RiskFinding] = [
    RiskFinding("완치", "치료 결과를 보장하는 표현으로 보일 수 있습니다.", "증상 호전에 도움을 줄 수 있습니다"),
    RiskFinding("100%", "모든 환자에게 동일한 결과를 보장할 수 없습니다.", "개인 상태에 따라 결과가 달라질 수 있습니다"),
    RiskFinding("부작용 없음", "의료 행위는 개인 상태에 따라 부작용 가능성이 있습니다.", "부작용 가능성을 진료 시 확인합니다"),
    RiskFinding("최고", "객관적 근거 없는 최상급 표현으로 보일 수 있습니다.", "경험과 원칙을 바탕으로 진료합니다"),
    RiskFinding("유일", "배타적 우위 표현은 근거 제시가 필요합니다.", "차별화된 진료 경험을 제공합니다"),
    RiskFinding("무조건", "환자별 차이를 무시한 단정 표현입니다.", "상태에 따라 다르게 판단합니다"),
]


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def build_request(region: str, department: str, symptom: str, doctor_comment: str) -> BlogRequest:
    return BlogRequest(
        region=normalize_text(region),
        department=normalize_text(department),
        symptom=normalize_text(symptom),
        doctor_comment=normalize_text(doctor_comment),
    )


def recommend_title(request: BlogRequest) -> str:
    return f"{request.region} {request.department} {request.symptom}, 병원 방문이 필요한 경우"


def generate_outline(request: BlogRequest) -> list[str]:
    comment = request.doctor_comment or "증상은 지속 기간과 동반 증상을 함께 확인하는 것이 중요합니다."
    return [
        f"1. {request.symptom} 때문에 검색한 환자의 흔한 고민",
        f"2. {request.department}에서 확인하는 주요 원인과 검사 흐름",
        "3. 집에서 지켜볼 수 있는 경우와 바로 진료가 필요한 경우",
        f"4. 의료진 코멘트: {comment}",
        "5. 자주 묻는 질문과 진료 전 준비사항",
        "6. 온라인 정보는 일반 안내이며 정확한 판단은 진료가 필요하다는 문구",
    ]


def check_ad_risk_expression(text: str) -> list[RiskFinding]:
    findings: list[RiskFinding] = []
    for pattern in RISK_PATTERNS:
        if pattern.expression in text:
            findings.append(pattern)
    return findings


def print_risk_report(findings: list[RiskFinding]) -> None:
    print("\n[의료광고 표현 점검]")
    if not findings:
        print("- 위험 표현이 발견되지 않았습니다.")
        return

    for item in findings:
        print(f"- 표현: {item.expression}")
        print(f"  이유: {item.reason}")
        print(f"  대체 방향: {item.suggestion}")


def print_final_preview(request: BlogRequest, draft_text: str = "") -> None:
    print("\n[블로그 글 기획안]")
    print(f"추천 제목: {recommend_title(request)}")
    print("\n글 구조:")
    for line in generate_outline(request):
        print(f"- {line}")

    if draft_text:
        print_risk_report(check_ad_risk_expression(draft_text))


def run_demo() -> None:
    print("메디블로그 AI 마케팅 툴 - Python 프로토타입")
    region = input("지역 키워드: ")
    department = input("진료과: ")
    symptom = input("증상/검사 키워드: ")
    doctor_comment = input("의사 코멘트: ")
    draft_text = input("점검할 홍보 문장(선택): ")

    request = build_request(region, department, symptom, doctor_comment)
    print_final_preview(request, draft_text)


if __name__ == "__main__":
    run_demo()
