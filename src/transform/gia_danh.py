import hashlib
import hmac
import os

from dotenv import load_dotenv

load_dotenv()

KHOA_BI_MAT = os.environ.get("PSEUDO_KEY")

if not KHOA_BI_MAT:
    raise SystemExit("Thiếu PSEUDO_KEY. Vui lòng cấu hình trong file .env")

KHOA = KHOA_BI_MAT.encode("utf-8")

if len(KHOA) < 32:
    raise SystemExit("PSEUDO_KEY phải có ít nhất 32 byte")


def gia_danh(gia_tri: str | None) -> str | None:
    """Giả danh hóa số điện thoại/định danh bằng HMAC-SHA256 ổn định."""
    if gia_tri is None or str(gia_tri).strip() == "":
        return None

    return hmac.new(
        KHOA,
        str(gia_tri).strip().encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def tao_khoa_khach_hang(ho_ten, so_dien_thoai):
    """Tạo khóa khách hàng bằng HMAC-SHA256 từ SĐT và họ tên đã chuẩn hóa."""
    from src.transform.rules import chuan_hoa_dien_thoai, chuan_hoa_ten

    sdt = chuan_hoa_dien_thoai(so_dien_thoai) or "KHONG_SDT"
    ten = chuan_hoa_ten(ho_ten)

    return gia_danh(f"{sdt}_{ten}")
