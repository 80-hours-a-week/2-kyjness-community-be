# app/core/rate_limit.py
"""
IP 기반 Rate Limiting 미들웨어.
RATE_LIMIT_WINDOW(초) 동안 RATE_LIMIT_MAX_REQUESTS 초과 시 429 반환.
윈도우 밖 시각 제거 후 리스트가 비면 해당 IP 키 삭제해 메모리 무한 증가 방지.
"""
import asyncio
import time
from typing import Callable

from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.core.config import settings

# IP별 요청 시각 목록 (슬라이딩 윈도우). 워커별 메모리. 미사용 IP는 키 삭제로 정리.
_request_times: dict[str, list[float]] = {}
_lock = asyncio.Lock()


def _get_client_ip(request: Request) -> str:
    """X-Forwarded-For(프록시 뒤) 또는 request.client.host"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def rate_limit_middleware(request: Request, call_next: Callable):
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
