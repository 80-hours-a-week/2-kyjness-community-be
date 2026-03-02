# PuppyTalk Backend

**PuppyTalk**는 반려견을 키우는 사람들을 위한 커뮤니티 서비스의 백엔드로, **FastAPI** 기반의 **RESTful API**로 설계·구현된 서버입니다.
커뮤니티 운영에 필요한 아래 핵심 기능들을 제공합니다.

- **인증** — 회원가입·로그인·로그아웃 (쿠키 세션)
- **사용자** — 프로필 조회·수정, 비밀번호 변경
- **게시글** — CRUD, 무한 스크롤 피드, 조회수·좋아요
- **댓글** — 페이지네이션, 작성자 검증
- **미디어** — 이미지 업로드 (로컬/S3), 회원가입 전 프로필 첨부

- **프론트엔드**: 별도 프로젝트에서 이 API를 사용합니다. → [**PuppyTalk Frontend**](https://github.com/kyjness/2-kyjness-community-fe)
- **인프라·배포**: Docker Compose, EC2, Kubernetes 등 배포 정의는 [**PuppyTalk Infra**](https://github.com/kyjness/2-kyjness-community-infra) 레포에서 관리합니다.

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| **언어** | Python 3.8+ |
| **패키지 관리** | Poetry 2.x |
| **서버** | Uvicorn (개발), Gunicorn + Uvicorn worker (프로덕션) |
| **DB** | MySQL (pymysql) |
| **ORM** | SQLAlchemy 2.x |
| **마이그레이션** | Alembic |
| **스토리지** | 로컬 파일 / S3 (boto3) |
| **검증** | Pydantic v2 |
| **암호화** | bcrypt (비밀번호) |

---

## 폴더 구조

- **루트** — 실행·배포 설정, 테스트·문서를 두며, 애플리케이션 코드는 **app/** 패키지에 둡니다.
- **app/** — 공통·인프라와 기능 단위 **domain**으로 구분합니다.
- **도메인** — **router**(엔드포인트) → **controller**(비즈니스 로직) → **model**(DB 접근) → **schema**(요청·응답 DTO) 흐름으로 처리합니다.

```
2-kyjness-community-be/
├── app/
│   ├── api/
│   │   └── v1.py            # /v1 경로에 라우터 묶어서 등록
│   ├── common/
│   │   ├── codes.py         # API 응답 코드 상수
│   │   ├── response.py      # 공통 응답 포맷·에러 처리
│   │   ├── validators.py    # 닉네임·비밀번호 형식 검증
│   │   └── logging_config.py # 로깅 설정
│   ├── core/
│   │   ├── config.py        # 환경 변수 설정
│   │   ├── dependencies/   # 로그인 유저·작성자 검증 등 의존성
│   │   ├── middleware/     # 요청 ID·접근 로그·속도 제한·보안 헤더
│   │   ├── security.py     # 비밀번호 해시·세션 ID 생성
│   │   ├── storage.py      # 로컬/S3 파일 업로드
│   │   ├── exception_handlers.py  # 전역 예외 → 공통 응답 형식
│   │   └── cleanup.py      # 만료 세션·미사용 이미지 정리
│   ├── db/                  # 엔진·세션·연결·Base
│   └── domain/
│       ├── auth/            # 로그인·로그아웃·회원가입
│       ├── users/           # 프로필 조회·수정
│       ├── media/           # 이미지 업로드
│       ├── posts/           # 게시글 CRUD·피드·좋아요
│       └── comments/        # 댓글 CRUD
│   └── main.py              # 앱 진입점·미들웨어·라우터 등록
├── alembic/                 # DB 스키마 마이그레이션 스크립트
├── docs/                    # 상세 문서·참고용 SQL
├── test/                    # pytest
├── alembic.ini              # Alembic 설정 (DB URL 등)
├── pyproject.toml           # Poetry 의존성·스크립트 정의
├── poetry.lock              # 의존성 잠금 (poetry install 시 참조)
├── Dockerfile               # 프로덕션 이미지 빌드
└── .env.example             # 환경 변수 예시 (복사 후 .env.development,.env.production 으로 사용)
```

---

## API 문서

서버를 실행한 뒤, 브라우저에서 **아래 주소**로 접속하시면 API 명세를 보실 수 있습니다.  
(Swagger UI는 요청 테스트용, ReDoc은 읽기용 정리 문서입니다.)

| 문서 | 주소 |
|------|------|
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |

---

## 설계 배경

| 선택 | 이유 |
|------|------|
| **무한 스크롤 vs 페이지네이션** | 게시글은 피드처럼 스크롤로 이어 보는 흐름이 중요해서 무한 스크롤(hasMore). 댓글은 "몇 페이지·총 몇 개" 파악이 중요해서 페이지 번호(totalCount, totalPages)로 두었습니다. |
| **세션 저장소: MySQL** | Redis 없이 단일 DB로 운영 부담을 줄이려고 합니다. 규모가 커지면 Redis로 바꿀 수 있습니다. |
| **쿠키-세션 방식** | JWT는 클라이언트에 두면 XSS·CSRF 위험이 커서, 세션 ID만 쿠키(HttpOnly, SameSite)로 주고 서버에서만 검증하려고 합니다. |
| **로그인 전용 rate limit** | 전역 제한만으로는 로그인 브루트포스에 부족해서, 로그인 API에 IP당 분당 5회로 따로 두었습니다. |
| **조회수 전용 엔드포인트** | GET 상세는 멱등하게 두고, 조회수 증가는 부수효과라 POST /view로 분리했습니다. |
| **이미지 미리 업로드** | 본문 제출 전에 먼저 올려두면 실패 시 재시도만 하면 되고, 본문·파일 동시 전송 부담을 줄이려고 합니다. |
| **스토리지: 로컬/S3** | 개발·소규모는 로컬, 확장 시 S3로 바꿀 수 있게 환경 변수로 전환 가능하게 하려고 합니다. |

---

## 실행 방법

**이 프로젝트 폴더(`2-kyjness-community-be`)를 연 터미널에서** 진행합니다.  
Docker로 실행할 경우 [**인프라 레포(2-kyjness-community-infra)**](https://github.com/kyjness/2-kyjness-community-infra)에서 실행하세요.

---

### 로컬 실행 (Python + MySQL 직접 설치)

1. **사전 준비** — Python 3.8 이상, MySQL 설치·실행 중이어야 합니다.
2. **DB·테이블** — MySQL에서 `puppytalk` DB 생성 후, 테이블은 아래 중 하나로 만듭니다.
   - **Alembic (권장)**: 3단계 후 `alembic revision --autogenerate -m "initial"` → `alembic upgrade head`
   - **수동**: `mysql -u root -p puppytalk < docs/puppytalkdb.sql`
3. **패키지** — 프로젝트 루트에서 `poetry install`
4. **환경 변수** — `.env.example`을 복사해 `.env.development`로 저장한 뒤 DB 주소·비밀번호 등 입력. `ENV` 미설정 시 development 로드
5. **서버** — `poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

- **테스트**: `poetry run pytest test/ -v` (MySQL·환경 변수 필요)

**Alembic** (스키마 변경 시): `alembic revision --autogenerate -m "메시지"` → `alembic upgrade head`. 이미 `docs/puppytalkdb.sql`로 테이블을 만든 경우 `alembic stamp head` 한 번 후 위 흐름으로 변경분만 적용.

---

- Docker 단독 이미지: [인프라 레포 docs/docker.md](https://github.com/kyjness/2-kyjness-community-infra) 참고.

---

## 확장 전략

### 기능

- **검색/필터**: 견종·지역·태그로 게시글 검색
- **신고/차단**: 게시글 신고, 사용자 차단 (차단한 사람 글 숨김)
- **알림**: 내 글에 댓글 달리면 알림 리스트
- **관리자**: 신고 누적 글 숨김, 유저 제재 (ROLE 기반)

### 인프라 (규모 확대 시)

- **세션 저장소**: 현재 MySQL. 확장 시 Redis 등으로 이전 가능.
- 기타: 로드밸런서·캐시·메시지 큐 등 필요 시 도입.

---

## 상세 문서 (docs/)

| 문서 | 설명 |
|------|------|
| [architecture.md](docs/architecture.md) | 폴더 역할·요청 흐름·인증 흐름 등 구조 설명 |
| [api-codes.md](docs/api-codes.md) | API 응답 코드(성공·에러)와 HTTP 상태 코드 매핑 |
| [puppytalkdb.sql](docs/puppytalkdb.sql) | 참고용 DDL (수동 테이블 생성 시 사용. 스키마 기준은 Alembic 마이그레이션) |
