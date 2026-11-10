"""Nơi đặt nghiệp vụ người dùng; ví dụ hàm chuẩn hóa dữ liệu hồ sơ."""


def normalize_full_name(full_name: str) -> str:
    return " ".join(full_name.split())
