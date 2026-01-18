# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.auth.auth_route import router as auth_router
from app.users.users_route import router as users_router
from app.posts.posts_route import router as posts_router
from app.comments.comments_route import router as comments_router
from app.likes.likes_route import router as likes_router
from config import settings

app = FastAPI(
    title="PuppyTalk API",
    description="커뮤니티 백엔드 API",
    version="1.0.0"
)

# CORS 설정 (프론트엔드와 연결할 때 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 예외 핸들러
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 검증 오류 처리"""
    return JSONResponse(
        status_code=400,
        content={"code": "INVALID_REQUEST_BODY", "data": None}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리"""
    # HTTP 상태 코드는 그대로 유지하면서, 응답 포맷만 통일
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    # detail이 문자열인 경우 (일반적인 HTTPException)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": str(exc.detail) if exc.detail else "HTTP_ERROR", "data": None}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_SERVER_ERROR", "data": None}
    )

# 라우터 등록
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(likes_router)

# 루트 엔드포인트 (서버 작동 확인용)
@app.get("/")
def root():
    return {
        "message": "PuppyTalk API is running!",
        "version": "1.0.0",
        "docs": "/docs"
    }

# 헬스체크 엔드포인트 (서버 상태 확인용)
@app.get("/health")
def health_check():
    return {"status": "healthy"}

