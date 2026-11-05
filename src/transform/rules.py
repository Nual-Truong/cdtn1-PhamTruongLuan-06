import re
import unicodedata
from datetime import datetime

# 3 định dạng ngày cố tình bị sai trong file orders_2024_2026.csv
DATE_FORMATS = ['%d/%m/%Y', '%d-%m-%y', '%Y.%m.%d']

def chuan_hoa_dien_thoai(raw):
    """
    Xử lý 4 định dạng số điện thoại: 0763247885, 0760.833.592, 076 083 3592, +84760833592.
    Trả về chuỗi 10 số bắt đầu bằng 0. Nếu không hợp lệ trả về None.
    """
    if raw is None or str(raw).strip() == '':
        return None

    # Loại bỏ tất cả các ký tự không phải là số (dấu chấm, khoảng trắng, dấu +)
    digits = re.sub(r'\D', '', str(raw))

    # Đổi tiền tố 84 thành 0
    if digits.startswith('84') and len(digits) == 11:
        digits = '0' + digits[2:]

    # Kiểm tra xem có đúng 10 số và bắt đầu bằng số 0 không
    if len(digits) == 10 and digits.startswith('0'):
        return digits
    return None

def chuan_hoa_ten(raw):
    """
    Bỏ dấu tiếng Việt (kể cả Đ/đ), đưa về chữ thường, gộp khoảng trắng dư thừa.
    Dùng làm KHÓA TỔNG HỢP để hợp nhất khách hàng trùng lặp.
    """
    if raw is None:
        return ''

    # Chuyển Đ/đ thành d trước khi chuẩn hóa Unicode NFD (Sửa BUG-01)
    s = str(raw).replace('đ', 'd').replace('Đ', 'd')
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')

    # Loại bỏ khoảng trắng dư và chuyển chữ thường
    return re.sub(r'\s+', '', s).strip().lower()

def doc_ngay(raw):
    """
    Thử lần lượt 3 khuôn dạng ngày. Dòng nào không khớp sẽ trả về None để đẩy vào bảng Reject.
    """
    if raw is None or str(raw).strip() == '':
        return None
    s = str(raw).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

def khoa_hop_nhat(ho_ten, so_dien_thoai):
    """
    Hàm tạo khóa duy nhất để gom các bản ghi khách hàng bị trùng (Ví dụ: Nguyễn Văn A và Nguyen Van A).
    """
    return (chuan_hoa_dien_thoai(so_dien_thoai) or 'KHONG_SDT', chuan_hoa_ten(ho_ten))
