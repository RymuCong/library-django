# Hệ Thống Quản Lý Thư Viện (Library Management System)

## Thông tin dự án
- **Công nghệ:** Django 6.0.1 + SQLite
- **Thời gian phát triển:** < 2 giờ
- **Ngôn ngữ:** Tiếng Việt

## Tính năng chính

### 1. Quản lý Thể loại sách
- Phân loại sách theo thể loại (Văn học, KHTN, Thiếu nhi...)

### 2. Quản lý Sách
- Mã sách duy nhất
- Thông tin chi tiết: tên, tác giả, NXB, giá
- Quản lý số lượng (tổng số và số lượng khả dụng)
- Soft delete: sách bị hủy không hiển thị nhưng giữ lịch sử
- Thống kê số lần được mượn (có thể sắp xếp)

### 3. Quản lý Bạn đọc
- Mã thẻ bạn đọc duy nhất
- Thông tin: họ tên, SĐT, ngày cấp thẻ
- Xem lịch sử mượn trả inline

### 4. Quản lý Mượn/Trả sách
- Tự động tính hạn trả (14 ngày từ ngày mượn)
- Kiểm tra số lượng sách khả dụng trước khi cho mượn
- Tự động cập nhật số lượng sách khi mượn/trả
- Tính phạt quá hạn: 1,000 VNĐ/ngày
- Hiển thị tiền phạt màu đỏ nếu trễ hạn

### 5. Báo cáo & Thống kê
- Lọc phiếu mượn theo trạng thái, ngày mượn, hạn trả
- Sắp xếp sách theo số lần được mượn
- Tìm kiếm nhanh theo mã thẻ, tên độc giả, mã sách

## Cài đặt và Chạy

### 1. Cài đặt dependencies (đã cài)
```bash
pip install django
```

### 2. Chạy migrations (đã chạy)
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Tạo superuser (đã tạo)
- Username: `admin`
- Password: `admin`

### 4. Chạy server
```bash
python manage.py runserver
```

### 5. Truy cập Admin
Mở trình duyệt: http://127.0.0.1:8000/admin/

## Dữ liệu Test (đã tạo sẵn)

### Thể loại (3):
- Văn học
- Khoa học tự nhiên
- Thiếu nhi

### Sách (5 active + 1 inactive):
1. VH001 - Dế Mèn Phiêu Lưu Ký (5 quyển, available: 4)
2. VH002 - Số Đỏ (3 quyển, available: 3)
3. KH001 - Vật Lý Đại Cương (4 quyển, available: 3)
4. VH003 - Chí Phèo (2 quyển, available: 2)
5. TN001 - Doraemon Tập 1 (10 quyển, available: 10) - Được mượn 2 lần

### Bạn đọc (3):
- BD001 - Nguyễn Văn A
- BD002 - Trần Thị B
- BD003 - Lê Văn C

### Phiếu mượn (5):
- Nguyễn Văn A đang mượn Dế Mèn (active)
- Trần Thị B trả Số Đỏ muộn 3 ngày → Phạt 3,000 VNĐ (hiển thị màu đỏ)
- Lê Văn C đang mượn Vật Lý Đại Cương (active)
- 2 phiếu đã trả cho Doraemon (để test thống kê)

## Kiểm tra Acceptance Criteria

### ✅ Test 1: Mượn sách (Giảm số lượng)
- Vào **Sách** → Kiểm tra "Dế Mèn" có **Available = 4** (giảm từ 5)

### ✅ Test 2: Trả sách quá hạn (Tính phạt)
- Vào **Phiếu mượn** → Tìm phiếu của "Trần Thị B"
- Kiểm tra cột **Tiền phạt** hiển thị **3,000 VNĐ màu đỏ**

### ✅ Test 3: Mượn sách hết hàng (Validation)
- Thử tạo phiếu mượn với sách có available = 0
- Hệ thống sẽ báo lỗi: "Sách đã hết. Không thể mượn."

### ✅ Test 4: Thống kê số lần mượn
- Vào **Sách** → Nhấn vào cột **Số lần mượn** để sắp xếp
- "Doraemon Tập 1" sẽ hiển thị **2 lần mượn**

### ✅ Test 5: Lịch sử mượn của độc giả
- Vào **Bạn đọc** → Chọn "Nguyễn Văn A"
- Phần dưới hiển thị inline danh sách phiếu mượn

### ✅ Test 6: Soft delete sách
- Sách bị đánh dấu `is_active=False` không hiển thị trong dropdown khi tạo phiếu mượn
- Nhưng vẫn xem được trong danh sách Sách (admin)

## Cấu trúc Code

### Models ([core/models.py](core/models.py))
- `Category`: Thể loại sách
- `Book`: Sách với ActiveBookManager (soft delete)
- `Reader`: Bạn đọc
- `Loan`: Phiếu mượn với logic tự động:
  - Auto-set `due_date` = `borrow_date + 14 days`
  - Validate `book.available > 0` trước khi mượn
  - Tự động tăng/giảm `book.available`
  - Property `fine()` tính tiền phạt

### Admin ([core/admin.py](core/admin.py))
- `CategoryAdmin`: Quản lý thể loại
- `BookAdmin`: Hiển thị cột "Số lần mượn" với annotation
- `ReaderAdmin`: Inline hiển thị lịch sử mượn
- `LoanAdmin`: 
  - `select_related()` optimize queries
  - Custom display cho tiền phạt (màu đỏ)
  - Filters và search fields

### Settings ([library_system/settings.py](library_system/settings.py))
- `LANGUAGE_CODE = 'vi'`
- `TIME_ZONE = 'Asia/Ho_Chi_Minh'`
- SQLite database

## Thao tác nhanh

### Xem tất cả sách (kể cả inactive)
```python
from core.models import Book
Book.all_objects.all()
```

### Xem chỉ sách active
```python
Book.objects.all()  # Chỉ is_active=True
```

### Tạo phiếu mượn mới (tự động tính hạn trả)
```python
from core.models import Loan, Reader, Book
from datetime import date

loan = Loan.objects.create(
    reader=Reader.objects.get(card_id='BD001'),
    book=Book.objects.get(code='VH001'),
    borrow_date=date.today()
    # due_date sẽ tự động = borrow_date + 14 ngày
)
```

### Trả sách
```python
from datetime import date

loan = Loan.objects.get(id=1)
loan.return_date = date.today()
loan.status = 'returned'
loan.save()  # Tự động tăng book.available
```

## Tối ưu hóa

1. **Queries**: Sử dụng `select_related()` trong admin để giảm số queries
2. **Soft Delete**: Custom manager tự động lọc sách inactive
3. **Validation**: Kiểm tra số lượng trước khi mượn
4. **Annotation**: Tính số lần mượn bằng `Count()` thay vì query riêng

## Ghi chú

- Dự án được thiết kế để code xong trong **< 2 giờ**
- Tập trung vào **logic nghiệp vụ chính xác** theo tài liệu SRS
- Sử dụng **Django Admin** thay vì tự build frontend
- Code ngắn gọn, dễ đọc, dễ bảo trì
