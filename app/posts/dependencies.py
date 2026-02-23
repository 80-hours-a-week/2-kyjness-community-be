# app/posts/dependencies.py
"""posts 라우트에서 Depends()로 사용하는 의존성."""

from fastapi import Query

from app.posts.schema import PostListQuery


def get_post_list_query(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기 (기본 10, 최대 100)"),
) -> PostListQuery:
    return PostListQuery(page=page, size=size)
