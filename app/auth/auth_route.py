# app/auth/auth_route.py
from fastapi import APIRouter, HTTPException, Request, Body, Response, Cookie
from fastapi.responses import JSONResponse
from typing import Optional
from app.auth.auth_scheme import SignUpRequest, LoginRequest
from app.auth.auth_controller import AuthController

router = APIRouter(prefix="/auth", tags=["auth"])

# 회원가입
@router.post("/signup", status_code=201)
async def signup(request: Request, signup_data: Optional[SignUpRequest] = Body(None)):
    """회원가입 API"""
    try:
        # Controller 호출 (모든 비즈니스 로직 및 검증은 Controller에서 처리)
        return AuthController.signup(
            request=request,
            email=signup_data.email if signup_data else None,
            password=signup_data.password if signup_data else None,
            password_confirm=signup_data.passwordConfirm if signup_data else None,
            nickname=signup_data.nickname if signup_data else None,
            profile_image_url=signup_data.profileImageUrl if signup_data else None
        )
    except HTTPException as e:
        # Controller에서 발생한 HTTPException 처리
        if isinstance(e.detail, dict):
            return JSONResponse(status_code=e.status_code, content=e.detail)
        raise
    except Exception as e:
        # 예상치 못한 모든 에러
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_SERVER_ERROR", "data": None}
        )

# 로그인 (쿠키-세션 방식)
@router.post("/login", status_code=200)
async def login(request: Request, response: Response, login_data: Optional[LoginRequest] = Body(None)):
    """로그인 API (쿠키-세션 방식)"""
    try:
        # Controller 호출 (모든 비즈니스 로직 및 검증은 Controller에서 처리)
        result = AuthController.login(
            request=request,
            email=login_data.email if login_data else None,
            password=login_data.password if login_data else None
        )
        
        # 세션 ID를 쿠키에 설정 (HTTP 응답 처리)
        session_id = result["data"]["authToken"]
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,  # XSS 공격 방지
            secure=False,  # HTTPS 사용 시 True로 변경
            samesite="lax",  # CSRF 공격 방지
            max_age=86400  # 24시간 (초 단위)
        )
        
        # 응답 반환
        return result
    except HTTPException as e:
        # Controller에서 발생한 HTTPException 처리
        if isinstance(e.detail, dict):
            return JSONResponse(status_code=e.status_code, content=e.detail)
        raise
    except Exception as e:
        # 예상치 못한 모든 에러
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_SERVER_ERROR", "data": None}
        )

# 로그아웃 (쿠키-세션 방식)
@router.post("/logout", status_code=200)
async def logout(response: Response, session_id: Optional[str] = Cookie(None)):
    """로그아웃 API (쿠키-세션 방식)"""
    try:
        # Controller 호출 (모든 비즈니스 로직 및 검증은 Controller에서 처리)
        result = AuthController.logout(session_id)
        
        # 쿠키 삭제 (HTTP 응답 처리)
        response.delete_cookie(key="session_id")
        
        return result
    except HTTPException as e:
        # Controller에서 발생한 HTTPException 처리
        if isinstance(e.detail, dict):
            return JSONResponse(status_code=e.status_code, content=e.detail)
        raise
    except Exception as e:
        # 예상치 못한 모든 에러
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_SERVER_ERROR", "data": None}
        )

# 로그인 상태 체크 (쿠키-세션 방식)
@router.get("/me", status_code=200)
async def get_me(session_id: Optional[str] = Cookie(None)):
    """로그인 상태 체크 API (쿠키-세션 방식)"""
    try:
        # Controller 호출 (모든 비즈니스 로직 및 검증은 Controller에서 처리)
        return AuthController.get_me(session_id)
    except HTTPException as e:
        # Controller에서 발생한 HTTPException 처리
        if isinstance(e.detail, dict):
            return JSONResponse(status_code=e.status_code, content=e.detail)
        raise
    except Exception as e:
        # 예상치 못한 모든 에러
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_SERVER_ERROR", "data": None}
        )
