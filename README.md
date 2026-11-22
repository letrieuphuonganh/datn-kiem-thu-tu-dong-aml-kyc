# Kiểm thử tự động cho quy trình sàng lọc và quản lý hồ sơ khách hàng (mô phỏng AML/KYC)

Đồ án tốt nghiệp, Lê Triệu Phương Anh (MSSV 0000768), GVHD: ThS. Nguyễn Hồng Hạnh.

## Cấu trúc

- `watchlist-demo/`: hệ thống demo (Python Flask + SQLite)
- `kyc-autotest/`: bộ kiểm thử Selenium WebDriver 4.49.0 + TestNG 7.10.2 (Page Object, data-driven)
- `testcases/`: 83 test case thủ công (hai file Excel: luồng A 46, luồng B 37) và 8 test case mở rộng theo ngày (sheet `TC_MoRong_Ngay`)

## Yêu cầu

- Python 3 (đã thử với 3.12)
- JDK 17 trở lên
- Google Chrome
- Maven (nếu chạy bằng dòng lệnh) hoặc IntelliJ IDEA

## Chạy hệ thống demo

```
cd watchlist-demo
pip install -r requirements.txt
python app.py
```

Mở http://127.0.0.1:5000 (cổng cố định trong `app.py`).
Tài khoản demo: `maker01` / `123456` (Maker), `checker01` / `123456` (Checker).
Đặt lại dữ liệu mẫu: http://127.0.0.1:5000/reset-data

## Chạy bộ kiểm thử

Bật demo trước, rồi chạy theo một trong hai cách:

- Dòng lệnh, trong thư mục `kyc-autotest`:
  ```
  mvn test
  ```
  Lần chạy đầu cần kết nối mạng để Maven tải thư viện.
- IntelliJ IDEA: mở thư mục `kyc-autotest`, Maven → Reload project, chuột phải `testng.xml` → Run.

Tùy chọn:

- Demo chạy ở địa chỉ khác: `mvn test -DbaseUrl=http://<địa chỉ>`
- Chạy ẩn trình duyệt: `mvn test -Dheadless=true`

Bộ kiểm thử tự gọi `/reset-data` nên không cần đặt lại dữ liệu trước khi chạy.

## Kết quả

37 lượt chạy (29 cơ sở + 8 mở rộng), đạt 37/37 ở 10 lần chạy liên tiếp.

| Lớp kiểm thử | Số lượt |
|---|---|
| WatchlistFlowTest | 1 |
| RecordValidationTest | 11 |
| ScreeningTest | 12 |
| CaseWorkflowTest | 5 |
| RepeatControlTest (mở rộng) | 8 |
| **Tổng** | **37** |
