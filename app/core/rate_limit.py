import asyncio
import time
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.codes import ApiCode
from app.core.response import raise_http_error

_request_times: dict[str, list[float]] = {}
_login_attempt_times: dict[str, list[float]] = {}
_lock = asyncio.Lock()
_login_lock = asyncio.Lock()

_SKIP_PATHS = frozenset({"/health"})


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def _memory_login_check(request: Request) -> bool:
    ip = get_client_ip(request)
    now = time.monotonic()
    window = settings.LOGIN_RATE_LIMIT_WINDOW
    max_attempts = settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS
    async with _login_lock:
        times = _login_attempt_times.get(ip, [])
        cutoff = now - window
        while times and times[0] < cutoff:
            times.pop(0)
        if not times and ip in _login_attempt_times:
            del _login_attempt_times[ip]
        if len(times) >= max_attempts:
            return True
        _login_attempt_times[ip] = times
        times.append(now)
    return False


async def check_login_rate_limit(request: Request) -> None:
    if await _memory_login_check(request):
        raise_http_error(429, ApiCode.LOGIN_RATE_LIMIT_EXCEEDED)


async def _memory_global_check(request: Request) -> bool:
    ip = get_client_ip(request)
    now = time.monotonic()
    window = settings.RATE_LIMIT_WINDOW
    max_requests = settings.RATE_LIMIT_MAX_REQUESTS
    async with _lock:
        times = _request_times.get(ip, [])
        cutoff = now - window
        while times and times[0] < cutoff:
            times.pop(0)
        if not times and ip in _request_times:
            del _request_times[ip]
        if len(times) >= max_requests:
            return True
        _request_times[ip] = times
        times.append(now)
    return False


async def rate_limit_middleware(request: Request, call_next: Callable):
    if request.url.path in _SKIP_PATHS:
        return await call_next(request)
    if await _memory_global_check(request):
        return JSONResponse(
            status_code=429,
            content={"code": ApiCode.RATE_LIMIT_EXCEEDED.value, "data": None},
        )
    return await call_next(request)
