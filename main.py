import logging
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from app.core.config import settings
from app.api.v1 import v1_router
from app.core.codes import ApiCode
from app.core.exception_handlers import register_exception_handlers
from app.core.rate_limit import get_client_ip, rate_limit_middleware
from app.core.response import ApiResponse

_LOG_FMT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _setup_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_LOG_FMT, datefmt=_LOG_DATEFMT))
    root.addHandler(console)
    if settings.LOG_FILE_PATH:
        log_path = Path(settings.LOG_FILE_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(_LOG_FMT, datefmt=_LOG_DATEFMT))
        logging.getLogger().addHandler(file_handler)


_setup_logging()
_access_logger = logging.getLogger("app.access")


async def access_log_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    if settings.DEBUG:
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}"
    if response.status_code >= 400:
        _access_logger.info(
            "%s %s %s %.2fms %s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            get_client_ip(request),
        )
    return response


async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _run_session_cleanup():
    try:
        from app.auth.model import AuthModel
        AuthModel.cleanup_expired_sessions()
    except Exception as e:
        logging.getLogger(__name__).warning("Session cleanup failed: %s", e)


def _session_cleanup_loop():
    interval = max(60, settings.SESSION_CLEANUP_INTERVAL)
    while True:
        time.sleep(interval)
        _run_session_cleanup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import init_database, close_database
    if not init_database():
        logging.getLogger(__name__).critical("DB 연결 실패로 시작 시 검증 실패. 요청 시점에 재시도됨.")

    _run_session_cleanup()
    cleanup_thread = None
    if settings.SESSION_CLEANUP_INTERVAL > 0:
        cleanup_thread = threading.Thread(target=_session_cleanup_loop, daemon=True)
        cleanup_thread.start()

    yield

    close_database()


app = FastAPI(
    title="PuppyTalk API",
    description="소규모 커뮤니티 백엔드 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.middleware("http")(rate_limit_middleware)
app.middleware("http")(access_log_middleware)
app.middleware("http")(add_security_headers)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

upload_dir = Path(__file__).parent / "upload"
upload_dir.mkdir(exist_ok=True)
app.mount("/upload", StaticFiles(directory=str(upload_dir)), name="upload")

app.include_router(v1_router)


@app.get("/", response_model=ApiResponse)
def root():
    return {
        "code": ApiCode.OK.value,
        "data": {
            "message": "PuppyTalk API is running!",
            "version": "1.0.0",
            "docs": "/docs",
        },
    }


@app.get("/health", response_model=ApiResponse)
def health():
    return {"code": ApiCode.OK.value, "data": {"status": "ok"}}

