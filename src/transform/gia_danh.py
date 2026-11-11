import hashlib
import hmac
import os
from dotenv import load_dotenv

load_dotenv()

KHOA_MAC_DINH = "mekong-mobile-hmac-secret-key-2026-min-32-bytes"
KHOA = os.environ.get("PSEUDO_KEY", KHOA_MAC_DINH).encode("utf-8")

if len(KHOA) < 32:
    raise SystemExit("PSEUDO_KEY phải có ít nhất 32 ký tự")

def gia_danh(gia_tri: str | None) -> str | None:
    """Giả danh hóa số điện thoại/định danh bằng HMAC-SHA256 ổn định."""
    if not gia_tri or str(gia_tri).strip() == "":
        return None
    return hmac.new(KHOA, str(gia_tri).strip().encode("utf-8"), hashlib.sha256).hexdigest()
