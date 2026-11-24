"""Cơ chế giới hạn tần suất gọi API (Rate Limiting) và chống Brute-Force ở mức demo (in-memory)."""

import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Lớp quản lý Rate Limit (Sliding Window) và Anti-Brute-Force (Temporary Lockout)."""

    def __init__(self) -> None:
        # key -> list các timestamp float của các request trong window
        self._requests: Dict[str, List[float]] = defaultdict(list)
        # key -> [failed_count: int, locked_until: float]
        self._login_failures: Dict[str, List[float]] = defaultdict(lambda: [0, 0.0])

    def check_rate_limit(
        self, key: str, max_requests: int, window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Kiểm tra tần suất gọi request theo key (IP hoặc IP + endpoint).
        Trả về: (is_allowed: bool, retry_after: int)
        """
        now = time.time()
        timestamps = self._requests[key]

        # Loại bỏ các timestamp đã quá hạn cửa sổ window_seconds
        cutoff = now - window_seconds
        valid_timestamps = [t for t in timestamps if t > cutoff]
        self._requests[key] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            earliest = valid_timestamps[0]
            retry_after = max(1, int(earliest + window_seconds - now))
            return False, retry_after

        self._requests[key].append(now)
        return True, 0

    def check_brute_force(self, key: str) -> Tuple[bool, int]:
        """
        Kiểm tra xem key có đang bị tạm khóa do nhập sai mật khẩu nhiều lần không.
        Trả về: (is_locked: bool, retry_after: int)
        """
        now = time.time()
        record = self._login_failures.get(key)
        if not record:
            return False, 0

        failed_count, locked_until = record
        if locked_until > now:
            retry_after = max(1, int(locked_until - now))
            return True, retry_after

        # Nếu đã hết thời gian khóa thì reset
        if locked_until > 0 and locked_until <= now:
            self._login_failures[key] = [0, 0.0]

        return False, 0

    def record_login_failure(
        self, key: str, max_failures: int = 5, lockout_seconds: int = 60
    ) -> Tuple[int, bool, int]:
        """
        Ghi nhận một lần đăng nhập thất bại.
        Trả về: (failed_count: int, is_now_locked: bool, retry_after: int)
        """
        now = time.time()
        record = self._login_failures[key]
        failed_count, locked_until = record

        # Nếu đã hết hạn khóa trước đó thì reset đếm
        if locked_until > 0 and locked_until <= now:
            failed_count = 0
            locked_until = 0.0

        failed_count += 1
        is_locked = False
        retry_after = 0

        if failed_count >= max_failures:
            is_locked = True
            locked_until = now + lockout_seconds
            retry_after = lockout_seconds

        self._login_failures[key] = [failed_count, locked_until]
        return failed_count, is_locked, retry_after

    def record_login_success(self, key: str) -> None:
        """Đăng nhập thành công -> xóa bỏ toàn bộ lịch sử thất bại."""
        if key in self._login_failures:
            del self._login_failures[key]

    def reset(self) -> None:
        """Clear toàn bộ state trong memory (dùng cho test suite)."""
        self._requests.clear()
        self._login_failures.clear()


# Khởi tạo instance dùng chung
limiter = InMemoryRateLimiter()


def get_client_ip(request: Request) -> str:
    """Lấy địa chỉ IP của client từ Request (ưu tiên X-Forwarded-For nếu qua proxy)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def check_rate_limit(
    request: Request,
    prefix: str,
    max_requests: int = 5,
    window_seconds: int = 60,
) -> None:
    """Hàm kiểm tra rate limit cho endpoint. Ném HTTPException(429) nếu vi phạm."""
    client_ip = get_client_ip(request)
    key = f"{prefix}:{client_ip}"
    allowed, retry_after = limiter.check_rate_limit(
        key=key, max_requests=max_requests, window_seconds=window_seconds
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quá nhiều yêu cầu. Vui lòng thử lại sau {retry_after} giây.",
            headers={"Retry-After": str(retry_after)},
        )


def check_login_security(
    request: Request,
    email: Optional[str] = None,
    max_requests: int = 10,
    window_seconds: int = 60,
) -> None:
    """
    Kiểm tra bảo mật trước khi xử lý đăng nhập:
    1. Kiểm tra xem tài khoản/IP có đang bị khóa do brute-force hay không (ưu tiên).
    2. Kiểm tra rate limit theo IP chung nếu chưa bị khóa.
    """
    client_ip = get_client_ip(request)

    # 1. Kiểm tra brute force theo email/IP trước
    if email:
        email_clean = email.strip().lower()
        brute_key = f"{client_ip}:{email_clean}"
        is_locked, retry_after = limiter.check_brute_force(brute_key)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Tài khoản tạm thời bị khóa do đăng nhập sai quá nhiều lần. Vui lòng thử lại sau {retry_after} giây.",
                headers={"Retry-After": str(retry_after)},
            )

    # 2. Kiểm tra rate limit IP chung
    rate_key = f"login:{client_ip}"
    allowed, retry_after = limiter.check_rate_limit(
        key=rate_key, max_requests=max_requests, window_seconds=window_seconds
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quá nhiều yêu cầu đăng nhập từ thiết bị của bạn. Vui lòng thử lại sau {retry_after} giây.",
            headers={"Retry-After": str(retry_after)},
        )


def handle_login_failure(
    request: Request,
    email: str,
    max_failures: int = 5,
    lockout_seconds: int = 60,
) -> None:
    """Ghi nhận đăng nhập thất bại. Nếu chạm ngưỡng khóa, thông báo lỗi rõ ràng."""
    client_ip = get_client_ip(request)
    email_clean = email.strip().lower()
    brute_key = f"{client_ip}:{email_clean}"

    failed_count, is_now_locked, retry_after = limiter.record_login_failure(
        key=brute_key, max_failures=max_failures, lockout_seconds=lockout_seconds
    )

    if is_now_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Tài khoản tạm thời bị khóa do đăng nhập sai quá {max_failures} lần. Vui lòng thử lại sau {retry_after} giây.",
            headers={"Retry-After": str(retry_after)},
        )


def handle_login_success(request: Request, email: str) -> None:
    """Ghi nhận đăng nhập thành công, xóa bộ đếm brute force."""
    client_ip = get_client_ip(request)
    email_clean = email.strip().lower()
    brute_key = f"{client_ip}:{email_clean}"
    limiter.record_login_success(brute_key)
