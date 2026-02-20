# app/core/exception_handlers.py
"""전역 예외 핸들러. 모든 오류 응답을 { code, data } 형식으로 통일."""

import logging

import pymysql
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.codes import ApiCode

logger = logging.getLogger(__name__)


# 라우트 없음(404), 메서드 불일치(405) 등 공통 code 매핑
HTTP_STATUS_TO_CODE = {
    400: ApiCode.INVALID_REQUEST,
    401: ApiCode.UNAUTHORIZED,
    403: ApiCode.FORBIDDEN,
    404: ApiCode.NOT_FOUND,
    405: ApiCode.METHOD_NOT_ALLOWED,
    409: ApiCode.CONFLICT,
    422: ApiCode.UNPROCESSABLE_ENTITY,
    429: ApiCode.RATE_LIMIT_EXCEEDED,
    500: ApiCode.INTERNAL_SERVER_ERROR,
}


def register_exception_handlers(app: FastAPI) -> None:
    """전역 예외 핸들러 등록. 어떤 예외든 { code, data } 형식으로 응답."""

    _KNOWN_CODES = frozenset({
        "INVALID_EMAIL_FORMAT", "INVALID_PASSWORD_FORMAT", "INVALID_NICKNAME_FORMAT",
        "INVALID_PROFILEIMAGEURL", "INVALID_FILE_URL", "INVALID_REQUEST",
        "MISSING_REQUIRED_FIELD", "POST_FILE_LIMIT_EXCEEDED",
    })

    def _pick_validation_code(request: Request, errors: list) -> str:
        """에러 목록에서 클라이언트에 반환할 code 하나 선택. 로그인 경로는 이메일 오류 우선."""
        is_login = "/auth/login" in request.url.path or request.url.path.endswith("/login")
        email_code = None
        other_code = None
        for err in errors:
            loc = err.get("loc", ())
            msg = err.get("msg", "") if isinstance(err.get("msg"), str) else ""
            if "email" in loc or ("email" in msg.lower() and "valid" in msg.lower()):
                email_code = "INVALID_EMAIL_FORMAT"
            for known in _KNOWN_CODES:
                if known in msg or msg == known:
                    if "email" in loc or known == "INVALID_EMAIL_FORMAT":
                        email_code = known
                    else:
                        other_code = known
                    break
        if is_login and email_code:
            return email_code
        if other_code:
            return other_code
        if email_code:
            return email_code
        for err in errors:
            msg = err.get("msg", "") if isinstance(err.get("msg"), str) else ""
            for known in _KNOWN_CODES:
                if known in msg or msg == known:
                    return known
        return ApiCode.INVALID_REQUEST_BODY.value

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        code = _pick_validation_code(request, exc.errors())
        return JSONResponse(status_code=400, content={"code": code, "data": None})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # 응답 포맷 통일: 우리 포맷(dict with code)이면 그대로, 아니면 code 매핑
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        code = HTTP_STATUS_TO_CODE.get(exc.status_code)
        if not code and isinstance(exc.detail, dict):
            code = exc.detail.get("code", ApiCode.HTTP_ERROR.value)
        if code is None:
            code = str(exc.detail) if exc.detail else ApiCode.HTTP_ERROR.value
        code_str = code.value if isinstance(code, ApiCode) else code
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": code_str, "data": None},
        )

    # DB 예외: 중복키/무결성/연결실패 등 { code, data } 통일
    @app.exception_handler(pymysql.err.IntegrityError)
    async def integrity_error_handler(request: Request, exc: pymysql.err.IntegrityError):
        err_msg = exc.args[1] if len(exc.args) > 1 else str(exc)
        errno = getattr(exc, "args", (0, ""))[0] if exc.args else 0
        # 1062=Duplicate entry (UNIQUE 위반)
        if errno == 1062:
            # 회원가입 시 이메일/닉네임 중복 → 구체적 코드 반환
            msg_lower = err_msg.lower() if isinstance(err_msg, str) else ""
            if "email" in msg_lower or "key 'email'" in msg_lower:
                return JSONResponse(status_code=409, content={"code": ApiCode.EMAIL_ALREADY_EXISTS.value, "data": None})
            if "nickname" in msg_lower or "key 'nickname'" in msg_lower:
                return JSONResponse(status_code=409, content={"code": ApiCode.NICKNAME_ALREADY_EXISTS.value, "data": None})
            return JSONResponse(status_code=409, content={"code": ApiCode.CONFLICT.value, "data": None})
        if errno in (1451, 1452):  # FK 제약 위반
            return JSONResponse(status_code=409, content={"code": ApiCode.CONSTRAINT_ERROR.value, "data": None})
        return JSONResponse(status_code=400, content={"code": ApiCode.INVALID_REQUEST.value, "data": None})

    @app.exception_handler(pymysql.err.OperationalError)
    async def operational_error_handler(request: Request, exc: pymysql.err.OperationalError):
        logger.error(
            "DB OperationalError: Path=%s, Errno=%s",
            request.url.path,
            getattr(exc, "args", ())[:1],
        )
        return JSONResponse(status_code=500, content={"code": ApiCode.DB_ERROR.value, "data": None})

    @app.exception_handler(pymysql.err.Error)
    async def pymysql_error_handler(request: Request, exc: pymysql.err.Error):
        logger.error(
            "DB Error: Path=%s, Exception=%s",
            request.url.path,
            type(exc).__name__,
        )
        return JSONResponse(status_code=500, content={"code": ApiCode.DB_ERROR.value, "data": None})

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception: Path=%s, Exception=%s: %s",
            request.url.path,
            type(exc).__name__,
            str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"code": ApiCode.INTERNAL_SERVER_ERROR.value, "data": None},
        )

