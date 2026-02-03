# app/core/database.py
"""DB 연결 관리 (MySQL puppytalk). per-call 연결, 요청 후 close 보장."""

from contextlib import contextmanager
from datetime import datetime

import pymysql
from pymysql.cursors import DictCursor

from app.core.config import settings


@contextmanager
def get_connection():
    """MySQL 연결 context manager. DictCursor로 dict 형태 행 반환. 사용 후 자동 close."""
    conn = None
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )
        yield conn
    finally:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass


def init_database() -> bool:
    """서버 시작 시 DB 연결 체크. SELECT 1 실행 후 로그 1회 출력."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] MySQL 연결 성공 ({settings.DB_NAME})", flush=True)
        return True
    except Exception as e:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] MySQL 연결 실패: {e}", flush=True)
        return False


def close_database() -> None:
    """연결 종료. per-call 연결 사용 시 no-op."""
    pass
