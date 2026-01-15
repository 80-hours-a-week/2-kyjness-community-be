# app/comments/comments_route.py
from fastapi import APIRouter, HTTPException, Body, Cookie, Query, Path
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from typing import Optional
from pydantic import ValidationError
from app.comments.comments_scheme import CommentCreateRequest, CommentUpdateRequest
from app.comments.comments_controller import CommentsController

router = APIRouter(prefix="/posts/{post_id}/comments", tags=["comments"])

# 댓글 작성
@router.post("", status_code=201)
async def create_comment(
    post_id: int = Path(..., description="게시글 ID"),
    session_id: Optional[str] = Cookie(None),
    comment_data: Optional[CommentCreateRequest] = Body(None)
):
    """댓글 작성 API"""
    try:
        # status code 400번
        # 빈 body 체크
        if comment_data is None:
            return JSONResponse(
                status_code=400,
                content={"code": "INVALID_REQUEST_BODY", "data": None}
            )
        
        # Controller 호출
        return CommentsController.create_comment(
            post_id=post_id,
            session_id=session_id,
            content=comment_data.content
        )
    except HTTPException as e:
        # status code: Controller에서 발생한 에러 코드 (400, 401, 404 등)
        # HTTPException의 detail이 dict인 경우 그대로 반환
        if isinstance(e.detail, dict):
            return JSONResponse(status_code=e.status_code, content=e.detail)
        raise
    except RequestValidationError as e:
        # status code 400번
        # FastAPI의 RequestValidationError 처리 (빈 body, 잘못된 형식 등)
        return JSONResponse(
            status_code=400,
            content={"code": "INVALID_REQUEST_BODY", "data": None}
        )
    except ValidationError as e:
        # status code 400번
        # Pydantic 검증 오류 처리
        errors = e.errors()
        if errors:
            first_error = errors[0]
            field = first_error.get("loc", [])
            
            if "content" in str(field).lower():
                return JSONResponse(
                    status_code=400,
                    content={"code": "INVALID_CONTENT_FORMAT", "data": None}
                )
        
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

# 댓글 목록 조회
@router.get("", status_code=200)
async def get_comments(
    post_id: int = Path(..., description="게시글 ID"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, description="페이지 크기 (기본값: 20)")
):
    """댓글 목록 조회 API"""
    try:
        # Controller 호출
        return CommentsController.get_comments(post_id=post_id, page=page, size=size)
    except HTTPException as e:
        # status code: Controller에서 발생한 에러 코드 (400, 404 등)
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

# 댓글 수정
@router.patch("/{comment_id}", status_code=200)
async def update_comment(
    post_id: int = Path(..., description="게시글 ID"),
    comment_id: int = Path(..., description="댓글 ID"),
    session_id: Optional[str] = Cookie(None),
    comment_data: Optional[CommentUpdateRequest] = Body(None)
):
    """댓글 수정 API"""
    try:
        # status code 400번
        # 빈 body 체크
        if comment_data is None:
            return JSONResponse(
                status_code=400,
                content={"code": "INVALID_REQUEST_BODY", "data": None}
            )
        
        # Controller 호출
        return CommentsController.update_comment(
            post_id=post_id,
            comment_id=comment_id,
            session_id=session_id,
            content=comment_data.content
        )
    except HTTPException as e:
        # status code: Controller에서 발생한 에러 코드 (400, 401, 403, 404 등)
        # HTTPException의 detail이 dict인 경우 그대로 반환
        if isinstance(e.detail, dict):
            return JSONResponse(status_code=e.status_code, content=e.detail)
        raise
    except RequestValidationError as e:
        # status code 400번
        # FastAPI의 RequestValidationError 처리 (빈 body, 잘못된 형식 등)
        return JSONResponse(
            status_code=400,
            content={"code": "INVALID_REQUEST_BODY", "data": None}
        )
    except ValidationError as e:
        # status code 400번
        # Pydantic 검증 오류 처리
        errors = e.errors()
        if errors:
            first_error = errors[0]
            field = first_error.get("loc", [])
            
            if "content" in str(field).lower():
                return JSONResponse(
                    status_code=400,
                    content={"code": "INVALID_CONTENT_FORMAT", "data": None}
                )
        
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

# 댓글 삭제
@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    post_id: int = Path(..., description="게시글 ID"),
    comment_id: int = Path(..., description="댓글 ID"),
    session_id: Optional[str] = Cookie(None)
):
    """댓글 삭제 API"""
    try:
        # Controller 호출
        CommentsController.delete_comment(
            post_id=post_id,
            comment_id=comment_id,
            session_id=session_id
        )
        
        # status code 204번(삭제 성공) - 응답 본문 없음
        return Response(status_code=204)
    except HTTPException as e:
        # status code: Controller에서 발생한 에러 코드 (400, 401, 403, 404 등)
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
