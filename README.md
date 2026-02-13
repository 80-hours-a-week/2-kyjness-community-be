# PuppyTalk API

강아지 커뮤니티 서비스를 위한 백엔드 API 서버입니다.  
회원가입, 게시글, 댓글, 좋아요 등 커뮤니티 기능을 제공하며, 웹/앱 프론트엔드에서 이 API를 호출해 사용합니다.

---

## 기능

| 기능 | 설명 |
|------|------|
| **인증 (Auth)** | 회원가입(프로필 이미지 업로드·등록 가능), 로그인, 로그아웃. 로그인 시 쿠키에 세션 저장, 이후 요청에 쿠키 포함. 비밀번호는 bcrypt 암호화. 로그인 API 전용 rate limit(IP당 분당 5회) |
| **사용자 (Users)** | 프로필 조회·수정, 비밀번호 변경, 프로필 사진 업로드. `/users/me` 경로 |
| **게시글 (Posts)** | 작성·조회·수정·삭제, 이미지 최대 5장 첨부, 좋아요 추가·취소. 목록은 무한 스크롤 조회 (응답에 `hasMore`) |
| **댓글 (Comments)** | 게시글별 댓글 작성·조회·수정·삭제. 목록은 20개 단위 페이징 (응답에 `totalCount`, `totalPages`, `currentPage`) |

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| **언어** | Python 3.8+ |
| **프레임워크** | FastAPI |
| **DB** | MySQL |
| **검증** | Pydantic |
| **암호화** | bcrypt (비밀번호) |

---

## 폴더 구조

```
2-kyjness-community-be/
│
├── app/
│   ├── core/                      # 공통 유틸·설정
│   │   ├── config.py              # 환경 변수 (포트, DB, CORS, 파일 업로드 등)
│   │   ├── database.py            # MySQL 연결 관리
│   │   ├── dependencies.py        # 로그인 검증, 게시글/댓글 작성자 검증
│   │   ├── exception_handlers.py  # 에러 응답 포맷 통일 ({code, data})
│   │   ├── file_upload.py         # 이미지 검증·저장·URL 반환 (로컬/S3)
│   │   ├── rate_limit.py          # 요청 제한 (전역 + 로그인 전용)
│   │   ├── response.py            # 성공/실패 응답 포맷
│   │   └── validators.py          # 비밀번호·닉네임·URL 형식 검증
│   │
│   ├── auth/                      # 인증
│   │   ├── auth_route.py          # 회원가입·로그인·로그아웃·프로필 업로드 API
│   │   ├── auth_controller.py     # 인증 비즈니스 로직
│   │   ├── auth_model.py          # users·sessions DB 접근
│   │   └── auth_schema.py         # 요청/응답 형식 정의
│   │
│   ├── users/                     # 사용자
│   │   ├── users_route.py         # 프로필 조회·수정·비밀번호 변경·프로필 사진 API
│   │   ├── users_controller.py    # 사용자 비즈니스 로직
│   │   ├── users_model.py         # 사용자 정보 DB 접근
│   │   └── users_schema.py        # 요청 형식 정의
│   │
│   ├── posts/                     # 게시글
│   │   ├── posts_route.py         # 게시글 CRUD·이미지 업로드(최대 5장)·좋아요 API
│   │   ├── posts_controller.py    # 게시글 비즈니스 로직
│   │   ├── posts_model.py         # 게시글·이미지·좋아요 DB 접근
│   │   └── posts_schema.py        # 요청 형식 정의
│   │
│   ├── comments/                  # 댓글
│   │   ├── comments_route.py      # 댓글 CRUD API (20개 단위 페이징)
│   │   ├── comments_controller.py # 댓글 비즈니스 로직
│   │   ├── comments_model.py      # 댓글 DB 접근
│   │   └── comments_schema.py     # 요청 형식 정의
│   │
├── docs/                          # 문서
│   ├── erd.png                    # DB ERD
│   └── puppyytalkdb.sql           # 테이블 생성 스크립트
│
├── main.py                        # 앱 진입점
├── upload/                        # 업로드 파일 저장 (로컬 시)
│   ├── profile/                   # 프로필 사진
│   └── post/                      # 게시글 이미지
├── pyproject.toml                 # 의존성
├── .env.example                   # 환경 변수 견본
└── README.md
```

---

## 실행 방법

### 1. 사전 준비

- **Python 3.8 이상** 설치
- **MySQL** 설치·실행 후 `puppytalk` DB 생성 및 테이블 생성

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS puppytalk;"
mysql -u root -p puppytalk < docs/puppyytalkdb.sql
```

테이블 관계는 `docs/erd.png`를, DDL은 `docs/puppyytalkdb.sql`을 참고합니다.

### 2. 가상환경 및 패키지

```bash
cd 2-kyjness-community-be
python -m venv venv

# 활성화
# Windows CMD:        venv\Scripts\activate
# Windows PowerShell: .\venv\Scripts\Activate.ps1
# Git Bash:           source venv/Scripts/activate

pip install .
```

테스트까지 포함: `pip install ".[dev]"`

### 3. 환경 변수

앱은 루트의 **`.env`** 하나만 읽습니다. **`.env.example`**을 복사해 `.env`로 저장한 뒤 값을 채우면 됩니다. 각 변수 설명은 `.env.example` 주석을 참고하면 됩니다.

### 4. 서버 실행

```bash
# 로컬/개발 (Uvicorn 단독, --reload 시 코드 변경 반영)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

프로덕션/Docker에서는 Gunicorn + Uvicorn worker 사용을 권장합니다.

로컬에서 서버를 실행한 뒤 브라우저에서 다음 주소로 API 문서를 확인할 수 있습니다.

| 문서 | 주소 (로컬 실행 시) |
|------|---------------------|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

> GitHub에서 README를 볼 때는 위 링크에 접속할 수 없습니다. 프로젝트를 클론한 뒤 서버를 실행해야 접근 가능합니다.

---

## 아키텍처

### 1. 전체 흐름

```
[프론트엔드 / 클라이언트]  HTTP 요청 (JSON body, Cookie)
    │
    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  백엔드 (FastAPI)                                                     │
│                                                                      │
│  ① Lifespan (앱 시작 시 1회)                                          │
│     → init_database()로 DB 연결 확인. 종료 시 close_database()        │
│                                                                      │
│  ② 미들웨어 (요청마다, 등록 역순으로 실행)                             │
│     → rate_limit: IP당 요청 수 제한, 초과 시 429 RATE_LIMIT_EXCEEDED  │
│     → 로그인 API: check_login_rate_limit (IP당 분당 5회, 브루트포스 방지)│
│     → access_log: Method, Path, Status, 소요 시간 로깅                │
│     → CORS: Origin 검사, allow_credentials=True (쿠키 전송 허용)     │
│     → add_security_headers: X-Frame-Options, X-Content-Type-Options   │
│                                                                      │
│  ③ 라우터 매칭                                                        │
│     → URL·HTTP 메서드별 분기. /auth/*, /users/me, /posts, /comments 등│
│                                                                      │
│  ④ 의존성 (Depends)                                                   │
│     → get_current_user: Cookie의 session_id → 세션 조회 → user_id 반환│
│     → require_post_author: 게시글 수정/삭제 시 작성자 본인인지 확인    │
│                                                                      │
│  ⑤ Pydantic (Schema)                                                  │
│     → 요청 body를 DTO(PostCreateRequest 등)로 검증. 실패 시 400 + code │
│                                                                      │
│  ⑥ Route 핸들러                                                       │
│     → auth_controller.signup(), posts_controller.create_post() 등 호출│
│                                                                      │
│  ⑦ Controller                                                        │
│     → 비즈니스 로직 처리, Model 호출, success_response / raise_http   │
│                                                                      │
│  ⑧ Model                                                              │
│     → get_connection()으로 DB 연결, SQL 실행, 명시적 commit (autocommit=False)│
│                                                                      │
│  ⑨ 예외 핸들러 (전역)                                                 │
│     → RequestValidationError, HTTPException, DB 예외 → { code, data } 통일│
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
    │
    ▼
HTTP 응답  { "code": "POST_UPLOADED", "data": { "postId": 1 } }
```

### 2. 세션 저장소

- **저장소**: MySQL `sessions` 테이블 (Redis 아님). `docs/puppyytalkdb.sql` 참고.
- **로그인 시**: 세션 ID 생성 → DB에 저장 → 쿠키로 브라우저에 전달
- **이후 요청 시**: 브라우저가 쿠키 자동 전송 → 서버가 세션 ID로 사용자 식별
- **로그아웃·만료 시**: 세션 삭제

### 3. 설계 배경

| 선택 | 이유 |
|------|------|
| **무한 스크롤 vs 페이지네이션** | 게시글 목록은 피드 형태로 스크롤하며 읽는 UX가 자연스럽고, "다음 페이지" 클릭 없이 계속 로드 가능. 커뮤니티 피드는 새 글 보는 흐름이 중요해 무한 스크롤(hasMore) 선택. 댓글은 "몇 페이지인지", "총 몇 개인지"가 중요해 페이지 번호(totalCount, totalPages) 선택. 특정 댓글 찾기·목록 전체 파악이 용이함. |
| **세션 저장소: MySQL** | Redis 없이도 단일 DB로 세션·유저·게시글 일괄 관리 가능. 소규모 서비스에서 운영 부담을 줄이기 위해 MySQL `sessions` 테이블 사용. 규모 확장 시 Redis로 이전 가능. |
| **쿠키-세션 방식** | JWT는 클라이언트 저장·전송 시 XSS·CSRF 관리 부담. 쿠키(HttpOnly, SameSite)로 세션 ID만 전달하면 브라우저가 자동 전송하고, 서버에서 세션 검증으로 보안 부담을 줄임. |
| **로그인 전용 rate limit** | 전역 rate limit만으로는 로그인 브루트포스에 충분하지 않음. 로그인 API에 IP당 분당 5회 제한을 별도 적용해 시도 횟수를 제한. |


---

## 설정

환경 변수(`.env`), S3·파일 저장, CORS·프론트 연동 등 상세는 **`.env.example`** 주석을 참고하면 됩니다.

---

## 체크리스트

### 로컬 실행 시

- [ ] Python 3.8+, MySQL 설치·실행
- [ ] `puppytalk` DB 생성 및 `docs/puppyytalkdb.sql` 적용
- [ ] `.env.example`을 복사해 `.env` 생성 후 DB·CORS 등 값 채우기
- [ ] `pip install .` 후 `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

### 배포 전

- [ ] `DEBUG=False`
- [ ] `CORS_ORIGINS`에 실제 프론트 URL만 명시
- [ ] `COOKIE_SECURE=true` (HTTPS 환경)
- [ ] `BE_API_URL`에 실제 API 주소
- [ ] DB 비밀번호·S3 키 등 .env에만 두고 저장소에 미포함
- [ ] (선택) `LOG_FILE_PATH` 설정 시 디스크 용량·로테이션 확인


---

## 확장 전략

### 기능

- **검색/필터**: 견종·지역·태그로 게시글 검색
- **신고/차단**: 게시글 신고, 사용자 차단 (차단한 사람 글 숨김)
- **알림**: 내 글에 댓글 달리면 알림 리스트
- **관리자**: 신고 누적 글 숨김, 유저 제재 (ROLE 기반)

### 인프라 (규모 확대 시)

- **캐시 (Redis)**: 인기 게시글·댓글 캐싱
- **메시지 큐**: 알림·이미지 처리 등 비동기 작업
