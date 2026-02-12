# app/auth/auth_route.py
from fastapi import APIRouter, Response, Cookie, Depends, UploadFile, File
from typing import Optional
from app.auth.auth_schema import SignUpRequest, LoginRequest
from app.auth import auth_controller
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.file_upload import save_profile_image
from app.core.response import success_response

router = APIRouter(prefix="/auth", tags=["auth"])


# 회원가입 전 프로필 이미지 업로드 (인증 불필요, 가입 시 profileImageUrl로 전달)
@router.post("/upload-signup-profile-image", status_code=201)
async def upload_signup_profile_image(
    profileImage: UploadFile = File(description="회원가입용 프로필 이미지"),
):
    """회원가입 화면에서 선택한 프로필 이미지를 업로드하고 URL을 반환. 이후 POST /auth/signup 시 profileImageUrl로 전달."""
    profile_image_url = await save_profile_image(profileImage)
    return success_response("PROFILE_IMAGE_UPLOADED", {"profileImageUrl": profile_image_url})


# 회원가입 (비밀번호는 bcrypt 해시 후 저장)
@router.post("/signup", status_code=201)
async def signup(signup_data: SignUpRequest):
    """회원가입 API — 전달된 비밀번호는 bcrypt로 해시되어 저장됩니다."""
    return auth_controller.signup(
        email=signup_data.email,
        password=signup_data.password,
        nickname=signup_data.nickname,
        profile_image_url=signup_data.profileImageUrl
    )

# 로그인 (쿠키-세션 방식, JWT 아님 — 인증 정보는 Set-Cookie로만 전달)
@router.post("/login", status_code=200)
async def login(login_data: LoginRequest, response: Response):
    """로그인 API — 세션 생성 후 세션 ID만 Set-Cookie로 내려줌. body에는 토큰 없음."""
    result, session_id = auth_controller.login(
        email=login_data.email,
        password=login_data.password
    )
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        path="/",
        samesite="lax",
        max_age=settings.SESSION_EXPIRY_TIME,
    )
    return result

# 로그아웃 (쿠키-세션 방식). 인증 없이 호출 가능 — 만료된 세션이어도 쿠키 제거 가능
@router.post("/logout", status_code=200)
async def logout(response: Response, session_id: Optional[str] = Cookie(None)):
    """로그아웃 API — 세션 삭제 후 쿠키 제거. 세션 없/만료여도 쿠키는 삭제함."""
    result = auth_controller.logout(session_id)
    response.delete_cookie(key="session_id")
    return result

# 로그인 상태 체크 (쿠키-세션 방식)
@router.get("/me", status_code=200)
async def get_me(user_id: int = Depends(get_current_user)):
    """로그인 상태 체크 API (쿠키-세션 방식)"""
    return auth_controller.get_me(user_id)
