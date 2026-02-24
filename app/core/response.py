from typing import Any, Optional, Union

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict

from app.core.codes import ApiCode


def success_response(code: Union[str, ApiCode], data=None) -> dict:
    code_str = code.value if isinstance(code, ApiCode) else code
    return {"code": code_str, "data": data}


def raise_http_error(status_code: int, error_code: Union[str, ApiCode], message: Optional[str] = None) -> None:
    code_str = error_code.value if isinstance(error_code, ApiCode) else error_code
    detail: dict = {"code": code_str, "data": None}
    if message is not None:
        detail["message"] = message
    raise HTTPException(status_code=status_code, detail=detail)


class ApiResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str
    data: Optional[Any] = None
