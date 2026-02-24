from typing import Optional

from sqlalchemy.orm import Session

from app.auth.model import AuthModel
from app.auth.schema import SignUpRequest, LoginRequest, LoginResponse, SessionUserResponse
from app.core.dependencies import CurrentUser
from app.core.codes import ApiCode
from app.core.security import hash_password, verify_password
from app.core.response import success_response, raise_http_error
from app.media.model import MediaModel
from app.users.model import UsersModel


def signup_user(data: SignUpRequest, db: Session) -> dict:
    if UsersModel.email_exists(data.email, db=db):
        raise_http_error(409, ApiCode.EMAIL_ALREADY_EXISTS)
    if UsersModel.nickname_exists(data.nickname, db=db):
        raise_http_error(409, ApiCode.NICKNAME_ALREADY_EXISTS)
    profile_image_url = None
    if data.profile_image_id:
        profile_image_url = MediaModel.get_url_by_id(data.profile_image_id, db=db)
    hashed = hash_password(data.password)
    UsersModel.create_user(data.email, hashed, data.nickname, profile_image_url, db=db)
    return success_response(ApiCode.SIGNUP_SUCCESS)


def login_user(data: LoginRequest, db: Session) -> tuple[dict, str]:
    row = UsersModel.find_user_by_email(data.email, db=db)
    if not row:
        raise_http_error(401, ApiCode.EMAIL_NOT_FOUND, "존재하지 않는 이메일입니다")
    if not verify_password(data.password, row["password"]):
        raise_http_error(401, ApiCode.INVALID_CREDENTIALS)
    session_id = AuthModel.create_session(row["id"], db=db)
    payload = LoginResponse.model_validate(row).model_dump(by_alias=True)
    return success_response(ApiCode.LOGIN_SUCCESS, payload), session_id


def logout_user(session_id: Optional[str], db: Session) -> dict:
    AuthModel.revoke_session(session_id, db=db)
    return success_response(ApiCode.LOGOUT_SUCCESS)


def get_session_user(user: CurrentUser) -> dict:
    data = SessionUserResponse.model_validate(user).model_dump(by_alias=True)
    return success_response(ApiCode.AUTH_SUCCESS, data)
