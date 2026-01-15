# app/likes/likes_route.py
from fastapi import APIRouter, HTTPException, Cookie, Path
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from typing import Optional
from app.likes.likes_controller import LikesController

router = APIRouter(prefix="/posts/{post_id}/likes", tags=["likes"])

# 좋아요 추가
@router.post("", status_code=201)
async def create_like(
    post_id: int = Path(..., description="게시글 ID"),
    session_id: Optional[str] = Cookie(None)
):
    """좋아요 추가 API"""
    try:
        # Controller 호출
        return LikesController.create_like(
            post_id=post_id,
            session_id=session_id
        )
    except HTTPException as e:
        # status code: Controller에서 발생한 에러 코드 (400, 401, 404 등)
        # HTTPException의 detail이 dict인 경우 그대로 반환
        if isinstance(e.detail, dict):
            return JSONResponse(status_code=e.status_code, content=e.detail)
        raise
    except RequestValidationError as e:
        # status code 400번
        # FastAPI의 RequestValidationError 처리 (잘못된 형식 등)
        return JSONResponse(
            status_code=400,
            content={"code": "INVALID_REQUEST_BODY", "data": None}
        )
    except Exception as e:
        # status code 500번
        # 예상치 못한 모든 에러
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_SERVER_ERROR", "data": None}
        )

# 좋아요 취소
@router.delete("", status_code=204)
async def delete_like(
    post_id: int = Path(..., description="게시글 ID"),
    session_id: Optional[str] = Cookie(None)
):
    """좋아요 취소 API"""
    try:
        # Controller 호출
        LikesController.delete_like(
            post_id=post_id,
            session_id=session_id
        )
        
        # status code 204번(삭제 성공) - 응답 본문 없음
        return Response(status_code=204)
    except HTTPException as e:
        # status code: Controller에서 발생한 에러 코드 (400, 401, 404 등)
        # HTTPException의 detail이 dict인 경우 그대로 반환
        if isinstance(e.detail, dict):
            return JSONResponse(status_code=e.status_code, content=e.detail)
        raise
    except Exception as e:
        # status code 500번
        # 예상치 못한 모든 에러
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_SERVER_ERROR", "data": None}
        )
