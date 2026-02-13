# app/core/rate_limit.py
"""
IP 기반 Rate Limiting.
- rate_limit_middleware: 전역 (모든 요청)
- check_login_rate_limit: 로그인 API 전용 (브루트포스 방지)
"""
import asyncio
import time
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.requests import Request as StarletteRequest

from app.core.config import settings
from app.core.response import raise_http_error

# IP별 요청 시각 목록 (슬라이딩 윈도우). 워커별 메모리. 미사용 IP는 키 삭제로 정리.
_request_times: dict[str, list[float]] = {}
_login_attempt_times: dict[str, list[float]] = {}
_lock = asyncio.Lock()
_login_lock = asyncio.Lock()


def _get_client_ip(request: StarletteRequest) -> str:
    """X-Forwarded-For(프록시 뒤) 또는 request.client.host"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def check_login_rate_limit(request: Request) -> None:
    """로그인 API 전용 rate limit. IP당 분당 시도 횟수 초과 시 429."""
    ip = _get_client_ip(request)
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
            raise_http_error(429, "LOGIN_RATE_LIMIT_EXCEEDED")
        _login_attempt_times[ip] = times
        times.append(now)


async def rate_limit_middleware(request: StarletteRequest, call_next: Callable):
    """IP당 RATE_LIMIT_WINDOW 초 동안 RATE_LIMIT_MAX_REQUESTS 초과 시 429."""
    ip = _get_client_ip(request)
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
            return JSONResponse(
                status_code=429,
                content={"code": "RATE_LIMIT_EXCEEDED", "data": None},
            )
        _request_times[ip] = times
        times.append(now)

    return await call_next(request)
