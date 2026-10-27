import json
import logging
import os
import sys


class DinhDangJson(logging.Formatter):
    """Mỗi dòng log là một đối tượng JSON: thời điểm, mức, nguồn, thông điệp, ngữ cảnh."""
    TRUONG_NGU_CANH = ('ma_lo', 'request_id', 'so_dong', 'ma_quy_tac')

    def format(self, r: logging.LogRecord) -> str:
        d = {
            'thoi_diem': self.formatTime(r, '%Y-%m-%dT%H:%M:%S%z'),
            'muc': r.levelname,
            'nguon': r.name,
            'thong_diep': r.getMessage(),
        }
        for k in self.TRUONG_NGU_CANH:
            if hasattr(r, k):
                d[k] = getattr(r, k)
        if r.exc_info:
            d['loi'] = self.formatException(r.exc_info)
        return json.dumps(d, ensure_ascii=False)


def cau_hinh_log() -> None:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(DinhDangJson())
    logging.basicConfig(
        level=os.getenv('LOG_LEVEL', 'INFO').upper(),
        handlers=[h],
        force=True
    )