# 인증 비즈니스 로직. 회원가입·로그인·로그아웃·세션 생성.
import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.auth.model import AuthModel
from app.auth.schema import SignUpRequest, LoginRequest, LoginResponse, SessionUserResponse
from app.common import ApiCode
from app.core.dependencies import CurrentUser
from app.core.security import hash_password, verify_password
from app.common import raise_http_error, success_response
from app.media.model import MediaModel
from app.users.model import UsersModel


def signup_user(data: SignUpRequest, db: Session) -> dict:
    if UsersModel.email_exists(data.email, db=db):
        raise_http_error(409, ApiCode.EMAIL_ALREADY_EXISTS)
    if UsersModel.nickname_exists(data.nickname, db=db):
        raise_http_error(409, ApiCode.NICKNAME_ALREADY_EXISTS)
    has_image = data.profile_image_id is not None
    has_token = bool(data.signup_token)
    if has_image != has_token:
        raise_http_error(400, ApiCode.MISSING_REQUIRED_FIELD)
    profile_image_id = None
    if has_image and has_token:
        if MediaModel.verify_signup_token(data.profile_image_id, data.signup_token, db=db) is None:
            raise_http_error(400, ApiCode.SIGNUP_IMAGE_TOKEN_INVALID)
        profile_image_id = data.profile_image_id
    hashed = hash_password(data.password)
    created = UsersModel.create_user(
        data.email,
        hashed,
        data.nickname,
        profile_image_id=profile_image_id,
        db=db,
    )
    if profile_image_id is not None:
        MediaModel.attach_signup_image(profile_image_id, created.id, db=db),
    return success_response(ApiCode.SIGNUP_SUCCESS)


def login_user(data: LoginRequest, db: Session) -> tuple[dict, str]:
    user = UsersModel.get_user_by_email(data.email, db=db)
    if not user:
        raise_http_error(401, ApiCode.INVALID_CREDENTIALS, "이메일 또는 비밀번호가 일치하지 않습니다")
    if not verify_password(data.password, user.password):
        raise_http_error(401, ApiCode.INVALID_CREDENTIALS, "이메일 또는 비밀번호가 일치하지 않습니다")
    session_id = AuthModel.create_session(user.id, db=db)
    payload = LoginResponse.model_validate(user).model_dump(by_alias=True)
    return success_response(ApiCode.LOGIN_SUCCESS, payload), session_id


def logout_user(session_id: Optional[str], db: Session) -> dict:
    AuthModel.revoke_session(session_id, db=db)
    return success_response(ApiCode.LOGOUT_SUCCESS)


def get_session_user(user: CurrentUser) -> dict:
    data = SessionUserResponse.model_validate(user).model_dump(by_alias=True)
    return success_response(ApiCode.AUTH_SUCCESS, data)
