# app/posts/posts_model.py
"""게시글 모델 (MySQL posts, post_files 테이블)"""

from typing import Optional, List

from app.core.database import get_connection


class PostsModel:
    """게시글 모델 (MySQL)"""

    MAX_POST_FILES = 5

    @classmethod
    def _row_to_post(cls, row: dict, file_rows: Optional[List[dict]] = None) -> dict:
        """DB 행을 API 형식 post dict로 변환. file_rows는 최대 5개까지."""
        if not row:
            return None
        post = {
            "postId": row["id"],
            "title": row["title"],
            "content": row["content"],
            "hits": row["view_count"],
            "likeCount": row["like_count"],
            "commentCount": row["comment_count"],
            "authorId": row["user_id"],
            "files": [],
            "createdAt": row["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            if row.get("created_at")
            else "",
        }
        if file_rows:
            for fr in file_rows[: cls.MAX_POST_FILES]:
                if fr and fr.get("file_url"):
                    post["files"].append({"fileId": fr["id"], "fileUrl": fr["file_url"]})
        return post

    @classmethod
    def create_post(
        cls, user_id: int, title: str, content: str, file_url: str = ""
    ) -> dict:
        """게시글 생성"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO posts (user_id, title, content)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, title, content),
                )
                post_id = cur.lastrowid

                file_id = None
                if file_url:
                    cur.execute(
                        """
                        INSERT INTO post_files (post_id, file_url)
                        VALUES (%s, %s)
                        """,
                        (post_id, file_url),
                    )
                    file_id = cur.lastrowid

            conn.commit()

        files = []
        if file_url and file_id:
            files = [{"fileId": file_id, "fileUrl": file_url}]
        return {
            "postId": post_id,
            "title": title,
            "content": content,
            "hits": 0,
            "likeCount": 0,
            "commentCount": 0,
            "authorId": user_id,
            "files": files,
            "createdAt": "",
        }

    @classmethod
    def find_post_by_id(cls, post_id: int) -> Optional[dict]:
        """게시글 조회"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, title, content, view_count, like_count, comment_count, created_at
                    FROM posts WHERE id = %s AND deleted_at IS NULL
                    """,
                    (post_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None

                cur.execute(
                    "SELECT id, file_url FROM post_files WHERE post_id = %s AND deleted_at IS NULL ORDER BY id",
                    (post_id,),
                )
                file_rows = cur.fetchall()

        return cls._row_to_post(row, file_rows or None)

    @classmethod
    def get_all_posts(cls, page: int = 1, size: int = 20) -> tuple[List[dict], bool]:
        """무한 스크롤용 목록 조회. (posts, has_more) 반환."""
        offset = (page - 1) * size
        fetch_limit = size + 1
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, title, content, view_count, like_count, comment_count, created_at
                    FROM posts WHERE deleted_at IS NULL
                    ORDER BY id DESC LIMIT %s OFFSET %s
                    """,
                    (fetch_limit, offset),
                )
                rows = cur.fetchall()

                has_more = len(rows) > size
                result = []
                for row in rows[:size]:
                    cur.execute(
                        "SELECT id, file_url FROM post_files WHERE post_id = %s AND deleted_at IS NULL ORDER BY id",
                        (row["id"],),
                    )
                    file_rows = cur.fetchall()
                    result.append(cls._row_to_post(row, file_rows or None))

        return result, has_more

    @classmethod
    def update_post(
        cls,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        file_url: Optional[str] = None,
    ) -> bool:
        """게시글 수정"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                if title is not None:
                    cur.execute(
                        "UPDATE posts SET title = %s WHERE id = %s AND deleted_at IS NULL",
                        (title, post_id),
                    )
                if content is not None:
                    cur.execute(
                        "UPDATE posts SET content = %s WHERE id = %s AND deleted_at IS NULL",
                        (content, post_id),
                    )

                if file_url is not None:
                    cur.execute(
                        "SELECT id FROM post_files WHERE post_id = %s AND deleted_at IS NULL",
                        (post_id,),
                    )
                    existing = cur.fetchall()
                    if file_url:
                        if len(existing) < cls.MAX_POST_FILES:
                            cur.execute(
                                "INSERT INTO post_files (post_id, file_url) VALUES (%s, %s)",
                                (post_id, file_url),
                            )
                    else:
                        for row in existing:
                            cur.execute(
                                "UPDATE post_files SET deleted_at = NOW() WHERE id = %s",
                                (row["id"],),
                            )

            conn.commit()
        return True

    @classmethod
    def delete_post(cls, post_id: int) -> bool:
        """게시글 삭제 (soft delete)"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE posts SET deleted_at = NOW() WHERE id = %s",
                    (post_id,),
                )
                affected = cur.rowcount
            conn.commit()
        return affected > 0

    @classmethod
    def increment_hits(cls, post_id: int) -> bool:
        """조회수 증가"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE posts SET view_count = view_count + 1 WHERE id = %s AND deleted_at IS NULL",
                    (post_id,),
                )
            conn.commit()
        return True

    @classmethod
    def increment_like_count(cls, post_id: int) -> bool:
        """좋아요 수 증가"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE posts SET like_count = like_count + 1 WHERE id = %s",
                    (post_id,),
                )
            conn.commit()
        return True

    @classmethod
    def decrement_like_count(cls, post_id: int) -> bool:
        """좋아요 수 감소"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE posts SET like_count = GREATEST(0, like_count - 1) WHERE id = %s",
                    (post_id,),
                )
            conn.commit()
        return True

    @classmethod
    def increment_comment_count(cls, post_id: int) -> bool:
        """댓글 수 증가"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE posts SET comment_count = comment_count + 1 WHERE id = %s",
                    (post_id,),
                )
            conn.commit()
        return True

    @classmethod
    def decrement_comment_count(cls, post_id: int) -> bool:
        """댓글 수 감소"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE posts SET comment_count = GREATEST(0, comment_count - 1) WHERE id = %s",
                    (post_id,),
                )
            conn.commit()
        return True

    @classmethod
    def count_post_files(cls, post_id: int) -> int:
        """게시글의 이미지 파일 개수 (삭제 제외)"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) as cnt FROM post_files WHERE post_id = %s AND deleted_at IS NULL",
                    (post_id,),
                )
                row = cur.fetchone()
        return row["cnt"] if row else 0

    @classmethod
    def get_post_author_id(cls, post_id: int) -> Optional[int]:
        """게시글 작성자 ID 조회"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id FROM posts WHERE id = %s AND deleted_at IS NULL",
                    (post_id,),
                )
                row = cur.fetchone()
        return row["user_id"] if row else None


class PostLikesModel:
    """게시글 좋아요 모델 (MySQL likes 테이블)"""

    @classmethod
    def create_like(cls, post_id: int, user_id: int) -> Optional[dict]:
        """좋아요 생성 (중복 시 None)"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO likes (post_id, user_id) VALUES (%s, %s)",
                        (post_id, user_id),
                    )
                conn.commit()
            return {"postId": post_id, "userId": user_id, "createdAt": ""}
        except Exception:
            return None

    @classmethod
    def has_liked(cls, post_id: int, user_id: int) -> bool:
        """좋아요 존재 여부"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM likes WHERE post_id = %s AND user_id = %s LIMIT 1",
                    (post_id, user_id),
                )
                return cur.fetchone() is not None

    @classmethod
    def delete_like(cls, post_id: int, user_id: int) -> bool:
        """좋아요 삭제"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM likes WHERE post_id = %s AND user_id = %s",
                    (post_id, user_id),
                )
                affected = cur.rowcount
            conn.commit()
        return affected > 0
