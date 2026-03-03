# 아키텍처

이 문서는 PuppyTalk 백엔드의 **도메인 레이어 역할**, **폴더 구조**, **요청·인증 흐름**을 정리합니다.

---

## 도메인 레이어 역할

`app/domain` 아래 각 기능 폴더(auth, users, posts, comments, media)는 같은 패턴을 따릅니다.  
요청이 들어오면 **router → controller → model** 순으로 처리되고, 요청·응답은 **schema(Pydantic)** 로 검증·직렬화합니다.

| 파일 | 역할 |
|------|------|
| **router** | HTTP 엔드포인트 정의. `Depends(get_db, get_current_user)` 등으로 DB 세션·로그인 유저 주입. controller 호출 후 schema로 응답 매핑. |
| **controller** | 비즈니스 로직(유효성 검사·권한 확인·트랜잭션 흐름). DB 접근은 model에 위임. |
| **model** | DB 접근(CRUD·쿼리). `Depends(get_db)` 로 받은 Session만 사용. commit/rollback은 세션을 제공하는 `get_db` 스코프에서 처리. |
| **schema** | 요청/응답 DTO. Pydantic v2로 검증·alias. 400 에러 시 공통 형식으로 반환. |

- **의존성 방향**: router는 controller를 호출하고, controller는 model을 호출. model은 `app.db`의 Session만 사용. 도메인끼리는 직접 import하지 않고, 공통·인프라(common, core, db)만 공유.

---

## 폴더 구조

`app` 하위는 **공통/인프라**(api, common, core, db)와 **도메인**(domain)으로 구분됩니다.  
(마이그레이션 스크립트는 프로젝트 루트 `alembic/`에 두는 것이 관례입니다.)

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
│   │   ├── config.py        # 환경 변수 설정 (ENV에 따라 .env.development / .env.production)
│   │   ├── cleanup.py       # 만료 세션·회원가입용 이미지 TTL 정리
│   │   ├── exception_handlers.py  # 전역 예외 → { code, data } 통일
│   │   ├── security.py      # 비밀번호 해시·세션 ID 생성
│   │   ├── storage.py       # 로컬/S3 파일 업로드
│   │   ├── dependencies/
│   │   │   ├── availability.py    # 쿼리 파싱 (가용성 등)
│   │   │   ├── comment_author.py  # 댓글 작성자 검증
│   │   │   ├── current_user.py   # 쿠키 세션 → CurrentUser
│   │   │   └── post_author.py    # 게시글 작성자 검증
│   │   └── middleware/
│   │       ├── access_log.py     # 4xx/5xx 접근 로그
│   │       ├── rate_limit.py     # IP당 요청 제한
│   │       ├── request_id.py     # X-Request-ID 생성·전달
│   │       └── security_headers.py # 보안 헤더
│   ├── db/
│   │   ├── base.py          # SQLAlchemy DeclarativeBase
│   │   ├── connection.py    # init_database, check_database, close_database
│   │   ├── engine.py        # DB 엔진·SessionLocal
│   │   └── session.py       # get_db, get_connection
│   └── domain/
│       ├── auth/            # 로그인·로그아웃·회원가입
│       │   ├── controller.py     # 인증 비즈니스 로직 (회원가입·로그인·로그아웃)
│       │   ├── model.py          # 세션 CRUD, AuthSession 모델
│       │   ├── router.py         # 인증 엔드포인트 (login, logout, signup, /me)
│       │   └── schema.py         # 인증 요청/응답 DTO
│       ├── users/            # 프로필 조회·수정
│       │   ├── controller.py     # 사용자 비즈니스 로직 (프로필·비밀번호)
│       │   ├── model.py          # 사용자 CRUD, User 모델
│       │   ├── router.py         # 사용자 엔드포인트 (/users/me)
│       │   └── schema.py         # 사용자 요청/응답 DTO
│       ├── media/            # 이미지 업로드
│       │   ├── controller.py     # 이미지 업로드 비즈니스 로직
│       │   ├── image_policy.py   # 회원가입용/일반 업로드 정책·signup token 검증
│       │   ├── model.py          # 이미지 CRUD, Image 모델
│       │   └── router.py         # 이미지 업로드 (POST /media/images, ?purpose=profile|post / POST /media/images/signup)
│       ├── posts/            # 게시글 CRUD·피드·좋아요
│       │   ├── controller.py     # 게시글 비즈니스 로직 (생성·수정·삭제·피드·좋아요·조회수)
│       │   ├── mapper.py          # 모델 → PostResponse 변환
│       │   ├── model.py          # 게시글·좋아요·post_images CRUD
│       │   ├── router.py         # 게시글 엔드포인트 (CRUD, 피드, 상세, 댓글 목록)
│       │   └── schema.py         # 게시글 요청/응답 DTO
│       └── comments/         # 댓글 CRUD
│           ├── controller.py     # 댓글 비즈니스 로직 (생성·수정·삭제·목록)
│           ├── model.py          # 댓글 CRUD, Comment 모델
│           ├── router.py         # 댓글 엔드포인트 (CRUD, 목록 페이지네이션)
│           └── schema.py         # 댓글 요청/응답 DTO
│   └── main.py               # 앱 진입점·미들웨어·라우터 등록
├── alembic/                 # DB 스키마 마이그레이션
│   ├── env.py               # 마이그레이션 환경 (DB URL·모델 로드)
│   ├── README               # Alembic 사용법 요약
│   ├── script.py.mako       # 리비전 스크립트 템플릿
│   └── versions/            # 마이그레이션 리비전 파일
├── docs/                    # 상세 문서·참고용 SQL
│   ├── api-codes.md         # API 응답 code · HTTP 상태 매핑
│   ├── architecture.md     # 이 문서 (아키텍처·폴더 구조·요청·인증 흐름)
│   ├── clear_db.sql         # 데이터만 비우기
│   └── puppytalkdb.sql      # 참고용 DDL
├── test/                    # pytest
│   ├── auth.py              # 인증 API 테스트
│   ├── comments.py          # 댓글 API 테스트
│   ├── conftest.py          # pytest 픽스처·공통 설정
│   ├── health.py            # /health 엔드포인트 테스트
│   ├── media.py             # 미디어(이미지 업로드) API 테스트
│   ├── posts.py             # 게시글 API 테스트
│   └── users.py             # 사용자 API 테스트
├── alembic.ini              # Alembic 설정
├── pyproject.toml           # Poetry 의존성·스크립트
├── poetry.lock              # 의존성 잠금
├── Dockerfile               # 프로덕션 이미지 빌드
├── docker-compose.yml       # 로컬·배포용 Compose
├── docker-compose.ec2.yml   # EC2 배포용 Compose
└── .env.example             # 환경 변수 예시
```

---

## 미들웨어 순서 (바깥 → 안)

`app/main.py`에 등록된 순서대로, **요청**은 아래에서 위로, **응답**은 위에서 아래로 통과합니다.

| 순서 | 이름 | 설명 |
|------|------|------|
| 1 | **CORS** | 허용 Origin 검사. `allow_credentials=True`로 쿠키 전송 허용. |
| 2 | **security_headers** | X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy. HSTS는 설정으로 켜기. |
| 3 | **rate_limit** | IP당 요청 수 제한. 초과 시 429. 로그인 API는 별도 제한(IP당 분당 5회). |
| 4 | **access_log** | 4xx/5xx 응답 시 request_id, Method, Path, Status, 소요 시간 로깅. DEBUG 시 X-Process-Time 헤더. |
| 5 | **request_id** | X-Request-ID 생성·전달. 응답 헤더·로그에 포함해 요청 추적. |

---

## 요청 흐름

```
[클라이언트]  HTTP 요청 (JSON body, Cookie)
    │
    ▼
① Lifespan (앱 시작 1회)
   → init_database() 로 DB 연결 확인
   → cleanup run_once + run_loop (만료 세션·회원가입용 이미지 TTL 정리). 종료 시 stop_event 후 close_database()

② GET /health
   → DB ping. 성공 200, 실패 503 (로드밸런서·배포 검사용)

③ 미들웨어 (요청마다, 위 순서)
   CORS → security_headers → rate_limit → access_log → request_id

④ 라우터 매칭 (v1_router prefix=/v1)
   auth, users, media, posts, comments 순으로 include. 예: /v1/auth/login, /v1/users/me, /v1/posts, /v1/posts/{id}/comments

⑤ 의존성 (Depends)
   → get_db: 요청마다 Session 주입. 성공 시 commit, 예외 시 rollback (session.py)
   → get_current_user: Cookie session_id → 세션 조회 → CurrentUser 반환
   → require_post_author / require_comment_author: 게시글·댓글 수정/삭제 시 작성자 본인 여부

⑥ Pydantic (Schema)
   요청 body·쿼리 검증. 실패 시 400 + code

⑦ Route 핸들러 → Controller → Model
   Model은 Session만 사용. commit/rollback은 get_db 스코프

⑧ 예외 핸들러 (전역)
   RequestValidationError, HTTPException, DB 예외 → { code, data } 통일
    │
    ▼
HTTP 응답  { "code": "...", "data": { ... } }
```

---

## 인증 흐름

| 단계 | 설명 |
|------|------|
| **로그인** | POST /v1/auth/login → 세션 생성 후 `session_id` 쿠키 설정 (HttpOnly, SameSite) |
| **이후 요청** | Cookie로 `session_id` 전송 → `get_current_user`에서 세션 조회 → CurrentUser 주입 |
| **로그아웃** | POST /v1/auth/logout → 해당 세션 삭제 |

세션 저장소는 MySQL(`sessions` 테이블).

---

## 이미지 (업로드·회원가입·생명주기)

이미지는 **미리 업로드**, **회원가입 시 소유 묶기(signupToken)**, **참조 카운팅(ref_count)** 세 가지 흐름으로 설계되어 있습니다. 관련 코드는 `app/domain/media/`(router, controller, model, image_policy), 게시글/사용자 도메인에서 `MediaModel.increment_ref_count` / `decrement_ref_count` 호출로 생명주기에 관여합니다.

### 1. 미리 업로드 (파일 먼저, 본문/가입 나중)

- **목적**: DB 트랜잭션 점유를 줄이고, 본문 작성·회원가입 실패 시에도 업로드된 파일만 재사용할 수 있게 합니다.
- **흐름**:
  - **회원가입용**: 비로그인 상태에서 `POST /v1/media/images/signup`으로 업로드 → 스토리지 저장 + `images` 테이블에 `uploader_id=NULL`, `signup_token_hash`, `signup_expires_at` 저장. 응답에 `imageId`, `signupToken` 반환.
  - **로그인 후**: `POST /v1/media/images?purpose=profile|post`로 업로드 → 스토리지 저장 + `images`에 `uploader_id=현재 사용자`, `ref_count`는 이후 프로필/게시글 첨부 시 증가.
- **정책**: `image_policy.save_image_for_media`에서 purpose 검증, 매직 바이트로 JPEG/PNG/WebP 판별, 크기 제한(`MAX_FILE_SIZE`), `storage_save`(로컬 또는 S3) 호출. 회원가입용 업로드는 rate limit 별도 적용(`check_signup_upload_rate_limit`).

### 2. 회원가입·signupToken (가입 전 이미지 소유 증명)

- **상황**: 가입 전에는 계정이 없어 프로필 이미지는 `uploader_id=NULL`로만 저장됩니다. 가입 폼에서 "이미 업로드한 imageId"를 넘기면, 제3자가 그 imageId만 알아서 남의 이미지를 자기 프로필로 가져가는 것을 막아야 합니다.
- **방식**: 업로드 시에만 발급되는 **signupToken**(일회성, TTL 있음)으로 소유를 증명합니다.
  - 업로드 응답: `imageId` + **signupToken**(평문, 클라이언트가 보관).
  - 가입 요청: `profile_image_id` + **signupToken**을 함께 보냄.
  - 서버: `MediaModel.verify_signup_token(image_id, token)`으로 동일 이미지·토큰 해시 일치·미만료·아직 미첨부(`uploader_id IS NULL`)인지 검증. 통과 시 `attach_signup_image`로 해당 이미지에 `uploader_id=신규 사용자`, `ref_count+=1`, `signup_token_hash`/`signup_expires_at` NULL 처리해 회원가입용 상태를 해제합니다.
- **만료 미첨부 이미지**: 주기적으로 `cleanup_expired_signup_images`가 `uploader_id IS NULL`이고 `signup_token_hash`/`signup_expires_at`가 있으며 만료된 로우를 찾아 스토리지 삭제 후 DB에서 삭제합니다(`app/core/cleanup.py` 연동).

### 3. 생명주기 (Reference Counting, ref_count)

- **의미**: 한 이미지가 "프로필 사진" 또는 "게시글 첨부"로 몇 번 참조되는지 `images.ref_count`로 관리합니다. 참조가 0이 되면 해당 로우와 스토리지 파일을 삭제하는 **즉시 처리** 방식을 쓰며, 향후 비동기 배치(Batch GC)로 바꿀 수 있도록 한 곳(`decrement_ref_count`)에서만 삭제 판단을 합니다.
- **증가(ref_count += 1)**:
  - 회원가입 시 프로필 이미지로 묶을 때: `attach_signup_image` 내부에서 `ref_count+1`.
  - 게시글 생성/수정 시 첨부 이미지로 추가할 때: `PostsModel`에서 `MediaModel.increment_ref_count(image_id)`.
  - 프로필 이미지 변경 시 새 이미지 선택: `UsersModel` 업데이트 후 `MediaModel.increment_ref_count(새 profile_image_id)`.
- **감소(ref_count -= 1)**:
  - 게시글 수정 시 특정 이미지를 첨부에서 뺄 때, 게시글 삭제 시 해당 글의 모든 첨부 이미지: `MediaModel.decrement_ref_count(image_id)`.
  - 프로필 이미지 변경/삭제 시 이전 이미지: `decrement_ref_count(이전 profile_image_id)`.
  - 회원 탈퇴 시 프로필 이미지: `decrement_ref_count(profile_image_id)`.
- **삭제 판단**: `decrement_ref_count` 안에서 `ref_count`를 1 줄인 뒤 `ref_count <= 0`이면 스토리지 파일 삭제(`storage_delete`) 후 해당 `images` 로우 `DELETE`. 동시성은 `with_for_update()`로 해당 로우 락 후 감소·판단합니다.
- **FK 정책**: `post_images`는 `posts`에 대해 `ON DELETE RESTRICT`로 두어, 게시글 삭제 시 앱에서 먼저 `post_images` 정리 및 각 `image_id`에 대해 `decrement_ref_count`를 호출한 뒤 게시글을 삭제하도록 합니다.

### 4. API·코드 위치 요약

| 구분 | 엔드포인트/동작 | 코드 위치 |
|------|-----------------|-----------|
| 회원가입용 업로드 | POST /v1/media/images/signup | media/router.py, controller.upload_image_for_signup, MediaModel.create_signup_image |
| 로그인 후 업로드 | POST /v1/media/images?purpose=profile\|post | media/router, controller.upload_image, MediaModel.create_image |
| 가입 시 이미지 소유 묶기 | signup 시 profile_image_id + signupToken | auth/controller.signup_user → MediaModel.verify_signup_token, attach_signup_image |
| ref_count 증가 | 게시글 첨부, 프로필 설정/변경 | posts/model(create_post, update_post), users/controller(update_me), auth(attach_signup_image) |
| ref_count 감소·삭제 | 게시글 첨부 해제/삭제, 프로필 변경/탈퇴 | posts/model(update_post, delete_post), users/controller(update_me, delete_me), MediaModel.decrement_ref_count |
| 만료 회원가입용 이미지 정리 | 주기 작업 | core/cleanup.py → MediaModel.cleanup_expired_signup_images |

