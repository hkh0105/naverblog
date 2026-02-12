# 보보쌤 블로그 글 생성기 (naverblog)

## 프로젝트 개요

보보쌤의 네이버 블로그 글을 자동 생성하는 Streamlit 웹 앱.
주제 입력 → 최신 정보 검색 → 보보쌤 문체로 글 생성 → HTML 복사 → 네이버에 붙여넣기.

**보보쌤**: 서울대 졸업 → 직장 생활 → 77일 만에 의대 합격한 20대 중후반 여성 입시 전문가. 입시 전략, 공부법, 생기부, 면접 등 교육 콘텐츠 블로그 운영.

**사용자**: 비개발자 (웹 UI 필수)
**범위**: 글 생성 + 미리보기 + HTML 복사까지. 네이버 업로드 자동화 없음.

## 배포

- **GitHub**: https://github.com/hkh0105/naverblog.git
- **배포**: Streamlit Cloud (무료) — `streamlit run app.py`
- **로컬 실행**: `cd ~/naverblog && streamlit run app.py`

## 기술 스택

| 역할 | 기술 |
|------|------|
| 웹 UI | Streamlit |
| Multi-LLM | LiteLLM (Claude/GPT/Gemini) |
| 검색 | Tavily API |
| 데이터 모델 | Pydantic v2 |
| 프롬프트 | Jinja2 템플릿 |
| DB | SQLite (~/.naverblog/naverblog.db) |
| MD→HTML | markdown 라이브러리 |
| 이미지 생성 | Google Imagen 3 (google-genai) |
| Python | ≥ 3.11 |

## 프로젝트 구조

```
naverblog/
├── app.py                           # Streamlit 메인 앱 (진입점)
├── pages/
│   ├── 1_스타일_편집.py              # 카테고리별 스타일 가이드 편집
│   └── 2_레퍼런스_글_관리.py         # 크롤링된 블로그 글 관리
├── src/naverblog/
│   ├── config.py                    # 설정 (APP_DIR, 기본 API 키)
│   ├── models.py                    # Pydantic 모델 (PostType, Persona, Generation)
│   ├── database.py                  # SQLite CRUD (personas, generations, blog_posts)
│   ├── llm.py                       # LiteLLM 래퍼, MODEL_REGISTRY
│   ├── pipeline.py                  # 핵심 파이프라인: 스킬→프롬프트→LLM→포맷→저장
│   ├── formatter.py                 # Markdown → 네이버 호환 HTML
│   ├── crawler.py                   # 보보쌤 블로그 50개 글 자동 크롤링
│   ├── image_gen.py                 # Imagen 3 이미지 생성
│   ├── prompts/
│   │   ├── builder.py               # Jinja2 프롬프트 조립
│   │   └── templates/
│   │       ├── system.j2            # 시스템 프롬프트 (페르소나 + 블로그 규칙)
│   │       ├── blog_general.j2      # 일반 정보 포스트
│   │       ├── blog_review.j2       # 리뷰 포스트
│   │       └── blog_listicle.j2     # 리스트형 포스트
│   └── skills/
│       ├── __init__.py              # SkillRegistry (자동 발견)
│       ├── base.py                  # SkillBase ABC
│       ├── search.py                # Tavily 웹 검색
│       ├── blog_style.py            # 카테고리별 문체/구조 스타일 가이드
│       └── reference_posts.py       # 기존 블로그 글 레퍼런스
├── data/presets/
│   └── personas.json                # 내장 페르소나 프리셋 (학부모/고등학생/재수생/일반)
├── scripts/
│   └── crawl_blog.py                # 블로그 크롤링 스크립트
├── .env                             # API 키 (gitignore됨)
├── .env.example                     # API 키 템플릿
├── .streamlit/config.toml           # Streamlit 테마/서버 설정
├── pyproject.toml                   # 프로젝트 메타데이터 + 의존성
└── requirements.txt                 # pip 의존성
```

## 핵심 아키텍처

### 파이프라인 흐름 (`pipeline.py`)

```
사용자 입력 (주제, 페르소나, 모델, 글 유형, 카테고리)
    ↓
스킬 실행 (search → blog_style → reference_posts)
    ↓  SkillResult
프롬프트 빌더 (system.j2 + 페르소나 + blog_{type}.j2 + 스킬 결과)
    ↓  system_prompt + user_prompt
LLM 호출 (litellm.completion)
    ↓  markdown
포맷터 (markdown → 네이버 HTML)
    ↓
DB 저장 + UI 출력
```

### 스킬 시스템 (플러그인 구조)

`skills/` 폴더에 `.py` 파일 추가하면 자동 등록. `SkillBase` 상속, `execute()` 구현.

| 스킬 | 설명 |
|------|------|
| `search` | Tavily 웹 검색으로 최신 정보 수집 |
| `blog_style` | 카테고리별 문체/구조 스타일 가이드 주입 |
| `reference_posts` | 보보쌤 기존 블로그 글을 레퍼런스로 제공 |

### LLM 모델 레지스트리 (`llm.py`)

```python
MODEL_REGISTRY = {
    "Claude Sonnet":  "claude-sonnet-4-20250514",
    "Claude Haiku":   "claude-haiku-4-20250414",
    "GPT-4o":         "gpt-4o",
    "GPT-4o Mini":    "gpt-4o-mini",
    "Gemini Pro":     "gemini/gemini-2.5-pro",
    "Gemini Flash":   "gemini/gemini-2.5-flash",
}
```

### 카테고리별 스킬 프리셋 (`app.py`)

10개 카테고리: 과목별 공부 로직, 입시 파이널(면접/자소서), 생기부, 77일만에 의대 가기, 입시 설계 전략, 시기별 로드맵, 학원/과외, 블로그 후기, 입시 정보 모음. 각 카테고리가 스킬 ON/OFF 자동 설정.

### 페르소나 (대상 독자)

모든 페르소나의 system_prompt에 보보쌤 정체성 포함. 대상 독자별 문체 차별화:
- **학부모**: 자녀 입시 지도 관점, 전문적+따뜻한 톤
- **고등학생**: 친근한 존댓말, 동기부여, 구체적 공부법
- **재수생/반수생**: 77일 합격 경험 기반, 효율적 전략, 현실적 조언
- **일반**: 친근하고 읽기 쉬운 입시 정보

### DB 구조 (`database.py`)

SQLite, `~/.naverblog/naverblog.db`:
- `personas`: 페르소나 프리셋 + 커스텀
- `generations`: 생성 기록 (주제, 모델, 프롬프트, 결과 markdown/html)
- `blog_posts`: 크롤링된 보보쌤 블로그 원문 (레퍼런스용)
- `skill_configs`: 스킬 활성화/설정
- `app_settings`: 앱 설정
- `blog_styles`: 카테고리별 스타일 가이드

### 자동 크롤링

첫 실행 시 DB가 비어있으면 `crawler.py`로 보보쌤 블로그 글 50개 자동 수집. `reference_posts` 스킬과 `blog_style` 스킬이 이 데이터 활용.

## API 키 설정

**`.env` 파일** (로컬):
```
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
OPENAI_API_KEY=sk-...      # 선택
TAVILY_API_KEY=tvly-...    # 검색 스킬용
```

**`config.py`에 기본 키 내장**: Anthropic, Gemini 키가 `_DEFAULT_KEYS`로 하드코딩되어 있음. `.env` 없어도 동작.

**Streamlit Cloud**: `st.secrets` 또는 환경변수로 설정.

## 개발 워크플로우

```bash
# 로컬 실행
cd ~/naverblog
streamlit run app.py

# 의존성 설치
pip install -e .
# 또는
pip install -r requirements.txt

# Git 배포
git add . && git commit -m "..." && git push
# Streamlit Cloud가 자동 재배포
```

## 주요 기능

1. **글 생성**: 주제 + 페르소나 + 모델 + 글 유형 선택 → 블로그 글 자동 생성
2. **웹 검색**: Tavily API로 최신 정보 수집하여 글에 반영
3. **보보쌤 스타일**: 크롤링된 실제 블로그 글 기반 문체 재현
4. **레퍼런스 글**: 기존 글 N개를 LLM에 컨텍스트로 제공 (1~50개 조절 가능)
5. **카테고리별 프리셋**: 10개 블로그 카테고리별 스킬 자동 설정
6. **다중 LLM**: Claude/GPT/Gemini 자유 전환
7. **HTML 복사**: 네이버 에디터 HTML 모드에 바로 붙여넣기 가능
8. **AI 이미지 생성**: Imagen 3로 블로그용 이미지 생성
9. **이미지 업로드**: 사용자 이미지 업로드 + 배치 지시
10. **생성 기록**: 이전 생성 결과 조회
11. **스타일 편집**: 카테고리별 문체/구조 스타일 가이드 커스터마이징
12. **레퍼런스 관리**: 크롤링된 블로그 글 조회/삭제/재크롤링

## 주의사항

- Streamlit Cloud는 재배포 시 파일 시스템 초기화됨 (SQLite 데이터 유실 가능)
- `config.py`에 API 키가 하드코딩되어 있음 — 공개 저장소 주의
- 첫 실행 시 크롤링에 ~30초 소요
- 레퍼런스 글 많이 넣으면 토큰 비용 증가 (글당 평균 1000~3000자)
