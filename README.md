# PuppyTalk API

강아지 커뮤니티 서비스를 위한 백엔드 API 서버입니다.  
회원가입, 게시글, 댓글, 좋아요 등 커뮤니티 기능을 제공하며, 웹/앱 프론트엔드에서 이 API를 호출해 사용합니다.

---

## 기능

| 기능 | 설명 |
|------|------|
| **인증 (Auth)** | 회원가입(프로필 이미지 업로드·등록 가능), 로그인, 로그아웃. 로그인 시 쿠키에 세션 저장, 이후 요청에 쿠키 포함. 비밀번호는 bcrypt 암호화 |
| **사용자 (Users)** | 프로필 조회·수정, 비밀번호 변경, 프로필 사진 업로드. `/users/me` 경로 |
| **게시글 (Posts)** | 작성·조회·수정·삭제, 이미지 첨부. 목록은 페이지 단위 조회 |
| **댓글 (Comments)** | 게시글별 댓글 작성·조회·수정·삭제 |
| **좋아요 (Likes)** | 게시글 좋아요 추가·취소 |

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

앱은 루트의 **`.env`** 하나만 읽습니다. **`.env.example`**을 복사해 `.env`로 저장한 뒤 값을 채우면 됩니다. 각 변수 설명은 `.env.example` 주석과 `docs/DEPLOYMENT.md`에 있습니다.

### 4. 서버 실행

```bash
# 로컬/개발 (Uvicorn 단독, --reload 시 코드 변경 반영)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

프로덕션/Docker에서는 Gunicorn + Uvicorn worker 사용. 자세한 내용은 `docs/DEPLOYMENT.md` 참고.

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

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

### 2. 인증·응답

- **인증**: 로그인 시 `session_id`를 Set-Cookie로 전달. 이후 요청 시 브라우저가 자동으로 쿠키 포함.
- **응답**: 성공·실패 모두 `{ "code": "문자열", "data": ... }` 형식으로 통일.

### 3. 요청 처리 예시 (게시글 작성)

- 인증: Cookie의 `session_id`로 사용자 식별
- 검증: Pydantic 스키마로 요청 body 검증
- 처리: Controller → Model → DB 트랜잭션
- 응답: `{ "code": "POST_UPLOADED", "data": { "postId": 5 } }`

---

## 폴더 구조

```
2-kyjness-community-be/
│
├── app/                      # 도메인별: *_route = URL·메서드 라우팅·의존성, *_controller = 비즈니스 로직, *_model = DB·SQL, *_schema = 요청/응답(Pydantic)
│   ├── core/                      # 여러 도메인에서 공통으로 쓰는 코드
│   │   ├── __init__.py
│   │   ├── config.py              # .env에서 읽어오는 설정값 (HOST, PORT, DB_* 등)
│   │   ├── database.py            # MySQL 연결 (get_connection, init_database)
│   │   ├── dependencies.py        # 인증·권한 의존성 (get_current_user, require_post_author 등)
│   │   ├── exception_handlers.py  # 예외 처리 (RequestValidationError, HTTPException → {code, data} 변환)
│   │   ├── file_upload.py         # 프로필/게시글 이미지·비디오 검증·저장·URL 생성
│   │   ├── rate_limit.py          # IP 기반 Rate limiting 미들웨어
│   │   ├── response.py            # success_response, raise_http_error
│   │   └── validators.py          # 비밀번호/닉네임/URL 형식 검증 (DTO에서 사용)
│   │
│   ├── auth/                      # 인증 (회원가입, 로그인, 로그아웃)
│   │   ├── auth_route.py          # POST /auth/upload-signup-profile-image, /signup, /login, /logout, GET /auth/me
│   │   ├── auth_controller.py     # signup, login, logout, get_me
│   │   ├── auth_model.py          # users, sessions 테이블 접근
│   │   └── auth_schema.py         # SignUpRequest, LoginRequest 등
│   │
│   ├── users/                     # 사용자 프로필
│   │   ├── users_route.py         # GET/PATCH/DELETE /users/me, PATCH /users/me/password, POST /users/me/profile-image
│   │   ├── users_controller.py    # get_user, update_user, update_password, upload_profile_image
│   │   ├── users_model.py         # AuthModel 래핑 (닉네임/비밀번호/프로필 수정)
│   │   └── users_schema.py        # UpdateUserRequest, UpdatePasswordRequest, CheckUserExistsQuery
│   │
│   ├── posts/                     # 게시글
│   │   ├── posts_route.py         # GET/POST /posts, GET/PATCH/DELETE /posts/{id}, POST /posts/{id}/image, /posts/{id}/video
│   │   ├── posts_controller.py    # create_post, get_posts, get_post, update_post, delete_post, upload_post_image, upload_post_video
│   │   ├── posts_model.py         # posts, post_files 테이블 접근
│   │   └── posts_schema.py        # PostCreateRequest, PostUpdateRequest
│   │
│   ├── comments/                  # 댓글
│   │   ├── comments_route.py      # GET/POST /posts/{post_id}/comments, PATCH/DELETE /posts/{post_id}/comments/{comment_id}
│   │   ├── comments_controller.py # create_comment, get_comments, update_comment, delete_comment
│   │   ├── comments_model.py      # comments 테이블 접근
│   │   └── comments_schema.py     # CommentCreateRequest, CommentUpdateRequest
│   │
│   └── likes/                     # 좋아요
│       ├── likes_route.py         # POST/DELETE /posts/{post_id}/likes
│       ├── likes_controller.py    # create_like, delete_like
│       ├── likes_model.py         # likes 테이블 접근
│       └── likes_schema.py
│
├── docs/                          # 문서
│   ├── ARCHITECTURE.md            # 아키텍처·요청 흐름
│   ├── DEPLOYMENT.md              # 배포 가이드 (환경 변수, Docker, 플랫폼별)
│   ├── erd.png                    # 데이터베이스 ERD
│   └── puppyytalkdb.sql           # DB 테이블 생성 스크립트
│
├── main.py                        # 앱 진입점, lifespan, 미들웨어(CORS, 보안헤더), 라우터 등록
├── upload/                         # STORAGE_BACKEND=local 시 업로드 파일 저장 (실행 시 생성, git 제외)
│   ├── image/
│   │   ├── profile/                # 프로필 사진
│   │   └── post/                   # 게시글 이미지
│   └── video/
│       └── post/                   # 게시글 비디오
├── pyproject.toml                 # 의존성 패키지 목록
├── .env.example                   # 환경 변수 견본 (저장소에만 존재. 복사해 .env 로 만들어 사용)
└── README.md
```

---

## 설정

환경 변수(`.env`), S3·파일 저장, CORS·프론트 연동 등 상세는 **`.env.example`** 주석과 **`docs/DEPLOYMENT.md`**를 참고하면 됩니다.

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

자세한 배포 절차는 `docs/DEPLOYMENT.md`를 참고하세요.

---

## 확장 전략

- **DB 샤딩**: user_id/post_id 기준으로 테이블 분산
- **읽기 레플리카**: 쓰기 Primary, 조회 Replica 분리
- **캐시 (Redis)**: 자주 조회되는 게시글·댓글 캐싱
- **메시지 큐**: 이미지 업로드·알림 등 비동기 작업 (Celery/RQ + Redis)
- **API 게이트웨이**: Kong, Nginx로 인증·로드밸런싱·레이트리밋 중앙화
