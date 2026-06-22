# 보보쌤 블로그 글 생성기

보보쌤의 네이버 블로그 문체를 참고해 입시, 공부법, 생기부, 면접, 학원/과외 관련 글 초안을 생성하는 Streamlit 앱입니다.

## 핵심 기능

- 보보쌤 스타일 네이버 블로그 글 생성
- 학부모, 고등학생, 재수생/반수생, 일반 독자 페르소나
- 카테고리별 보보쌤 문체/구조 스타일 적용
- 보보쌤 기존 블로그 글 RSS 수집 및 레퍼런스 반영
- Claude Opus 4.8, GPT-5.5, GPT-4o, Gemini 기반 글 생성
- Tavily 웹 검색, 네이버 키워드 분석, 썸네일 제작, 워터마크 제작
- Markdown → 네이버 HTML 변환

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 배포

Streamlit Community Cloud에서 이 저장소를 연결하고 `app.py`를 엔트리포인트로 지정하면 배포할 수 있습니다. LLM/API 키는 저장소에 올리지 말고 Streamlit Secrets에 등록해야 합니다.

GPT-5.5를 사용하려면 `OPENAI_API_KEY`를 Streamlit Secrets에 등록하세요.
실제 호출 검증까지 끝난 뒤 `NAVERBLOG_GPT55_VERIFIED=1`을 설정하면 GPT-5.5가 기본 모델이 됩니다. 검증 전 기본 모델은 Claude Opus 4.8입니다.
