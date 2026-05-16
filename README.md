# 메디블로그 AI 마케팅 툴

개원의를 위한 병원 블로그 글 생성 및 의료광고 표현 점검 도구입니다. 환자가 실제로 검색하는 지역, 진료과, 증상 키워드를 바탕으로 의사가 직접 설명하는 듯한 신뢰도 높은 블로그 글 초안을 만들고, 과장 광고로 보일 수 있는 표현을 줄이는 것을 목표로 합니다.

## 핵심 기능

- 병원 블로그 글 초안 생성
- 환자 눈높이 설명 구조 추천
- 카테고리별 병원 콘텐츠 스타일 적용
- 의료광고 위험 표현 점검형 프롬프트
- 레퍼런스 글 직접 등록 및 문체 참고
- 키워드 분석, 썸네일 제작, 워터마크 제작

## 과제 산출물

- 최종 보고서 구조 초안: `docs/PROJECT_REPORT_OUTLINE.md`
- Python 프로토타입: `scripts/medical_blog_prototype.py`
- Streamlit 구현 앱: `app.py`

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Python 프로토타입 실행

```bash
python scripts/medical_blog_prototype.py
```

## 배포

Streamlit Community Cloud에서 이 저장소를 연결하고 `app.py`를 엔트리포인트로 지정하면 배포할 수 있습니다. LLM/API 키는 저장소에 올리지 말고 Streamlit Secrets에 등록해야 합니다.
