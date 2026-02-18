# app/core/rate_limit.py
"""
IP 기반 Rate Limiting.
- rate_limit_middleware: 전역 (모든 요청). /health 는 제외.
- check_login_rate_limit: 로그인 API 전용 (브루트포스 방지)
REDIS_URL 설정 시 Redis 사용(워커/인스턴스 공통), 미설정 시 인메모리(워커별).
"""
import asyncio
import time
from typing import Callable, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.requests import Request as StarletteRequest

from app.core.config import settings
from app.core.codes import ApiCode
from app.core.response import raise_http_error

# 인메모리 fallback (REDIS_URL 없을 때). 워커별 메모리.
_request_times: dict[str, list[float]] = {}
_login_attempt_times: dict[str, list[float]] = {}
_lock = asyncio.Lock()
_login_lock = asyncio.Lock()

# Health 는 rate limit 카운트 제외
_SKIP_PATHS = frozenset({"/health"})


def _get_client_ip(request: StarletteRequest) -> str:
    """X-Forwarded-For(프록시 뒤) 또는 request.client.host"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


# ----- Redis 클라이언트 (REDIS_URL 있을 때만) -----
_redis: Optional["Redis"] = None


def _get_redis():
    """REDIS_URL 설정 시 Redis 비동기 클라이언트 반환. 지연 초기화."""
    global _redis
    if not settings.REDIS_URL:
        return None
    if _redis is None:
        try:
            from redis.asyncio import Redis
            _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception:
            return None
    return _redis


async def _redis_global_check(ip: str) -> bool:
    """Redis 전역 rate limit. 초과 시 True(거부)."""
    r = _get_redis()
    if not r:
        return False
    try:
        key = f"rl:global:{ip}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, settings.RATE_LIMIT_WINDOW)
        if count > settings.RATE_LIMIT_MAX_REQUESTS:
            return True
        return False
    except Exception:
        return False


async def _redis_login_check(ip: str) -> bool:
    """Redis 로그인 rate limit. 초과 시 True(거부)."""
    r = _get_redis()
    if not r:
        return False
    try:
        key = f"rl:login:{ip}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, settings.LOGIN_RATE_LIMIT_WINDOW)
        if count > settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
            return True
        return False
    except Exception:
        return False


# ----- 인메모리 로직 (REDIS 미사용 시) -----
async def _memory_login_check(request: StarletteRequest) -> bool:
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
            return True
        _login_attempt_times[ip] = times
        times.append(now)
    return False


async def check_login_rate_limit(request: Request) -> None:
    """로그인 API 전용 rate limit. IP당 분당 시도 횟수 초과 시 429."""
    if settings.REDIS_URL:
        rejected = await _redis_login_check(_get_client_ip(request))
    else:
        rejected = await _memory_login_check(request)
    if rejected:
        raise_http_error(429, ApiCode.LOGIN_RATE_LIMIT_EXCEEDED)


async def rate_limit_middleware(request: StarletteRequest, call_next: Callable):
    """IP당 RATE_LIMIT_WINDOW 초 동안 RATE_LIMIT_MAX_REQUESTS 초과 시 429. /health 제외."""
    if request.url.path in _SKIP_PATHS:
        return await call_next(request)

    ip = _get_client_ip(request)

    if settings.REDIS_URL:
        rejected = await _redis_global_check(ip)
        if rejected:
            return JSONResponse(
                status_code=429,
                content={"code": ApiCode.RATE_LIMIT_EXCEEDED.value, "data": None},
            )
        return await call_next(request)
    else:
        # 인메모리 슬라이딩 윈도우
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
                    content={"code": ApiCode.RATE_LIMIT_EXCEEDED.value, "data": None},
                )
            _request_times[ip] = times
            times.append(now)
        return await call_next(request)
