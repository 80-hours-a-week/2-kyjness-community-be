# app/core/response.py
"""공통 응답 포맷: 모든 성공/실패는 { "code": "SOME_CODE", "data": ... } 통일. 실패 시 data는 null."""

from typing import Any, Optional, Union

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict

from app.core.codes import ApiCode


def _to_code_string(value: Union[str, ApiCode]) -> str:
    """ApiCode 또는 str을 응답용 code 문자열로 변환."""
    return value.value if isinstance(value, ApiCode) else value


def success_response(code: Union[str, ApiCode], data=None) -> dict:
    """성공 응답 dict. Route에서 그대로 반환."""
    return {"code": _to_code_string(code), "data": data}


def raise_http_error(
    status_code: int, error_code: Union[str, ApiCode], message: Optional[str] = None
) -> None:
    """HTTPException 발생 (detail 포맷 통일). message가 있으면 응답에 포함됨."""
    detail: dict = {"code": _to_code_string(error_code), "data": None}
    if message is not None:
        detail["message"] = message
    raise HTTPException(status_code=status_code, detail=detail)


class ApiResponse(BaseModel):
    """OpenAPI용 공통 응답 스키마. response_model 지정 시 /docs 에 표시됨."""

    model_config = ConfigDict(extra="allow")

    code: str
    data: Optional[Any] = None
