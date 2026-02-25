import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# ENV=development → .env.development, ENV=production → .env.production (없으면 .env)
_env = os.getenv("ENV", "development")
_root = Path(__file__).resolve().parent.parent.parent
_env_file = _root / f".env.{_env}"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    load_dotenv(_root / ".env")


class Settings:
    # 서버 설정
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    # CORS 설정
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:5500",
        ).split(",")
        if origin.strip()
    ]
    # 세션 설정
    SESSION_EXPIRY_TIME: int = int(os.getenv("SESSION_EXPIRY_TIME", "86400"))
    SESSION_CLEANUP_INTERVAL: int = int(os.getenv("SESSION_CLEANUP_INTERVAL", "3600"))
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    # Rate limit
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100"))
    LOGIN_RATE_LIMIT_WINDOW: int = int(os.getenv("LOGIN_RATE_LIMIT_WINDOW", "60"))
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = int(os.getenv("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "5"))
    # 파일 업로드 설정
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    ALLOWED_IMAGE_TYPES: List[str] = [
        img_type.strip()
        for img_type in os.getenv("ALLOWED_IMAGE_TYPES", "image/jpeg,image/jpg,image/png").split(",")
        if img_type.strip()
    ]
    # API 기본 URL
    BE_API_URL: str = os.getenv("BE_API_URL", "http://127.0.0.1:8000")
    # 파일 저장소 (local | S3)
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-2")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    S3_PUBLIC_BASE_URL: str = os.getenv("S3_PUBLIC_BASE_URL", "")
    # 로깅
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "").strip()
    # MySQL 설정
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "puppytalk")


# 전역 설정 인스턴스
settings = Settings()
