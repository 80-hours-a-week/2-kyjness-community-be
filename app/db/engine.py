# DB 엔진·SessionLocal 생성. config 기반 DATABASE_URL, pool 설정.
# 연결 시 세션 타임존을 UTC로 고정해 저장/조회 시각을 일치시킴.
from urllib.parse import quote_plus

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{quote_plus(settings.DB_PASSWORD)}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    "?charset=utf8mb4"
)

engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"connect_timeout": settings.DB_PING_TIMEOUT},
)


@event.listens_for(engine, "connect")
def _set_mysql_utc(dbapi_conn, connection_record):
    """매 연결마다 MySQL 세션 타임존을 UTC로 설정. 저장/조회 시각 일치."""
    cursor = dbapi_conn.cursor()
    cursor.execute("SET SESSION time_zone = '+00:00'")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
