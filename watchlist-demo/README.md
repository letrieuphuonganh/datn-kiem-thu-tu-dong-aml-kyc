# Watchlist AML Demo (Flask + SQLite)

Web demo quản lý danh sách sàng lọc (Watchlist) trong nghiệp vụ chống rửa tiền, theo mô hình Maker / Checker.
Gồm **Sub-luồng A** (quản lý bản ghi Watchlist, mục 1 đến 8) và **Sub-luồng B** (sàng lọc khách hàng, xử lý Case, hộp thư giả lập, mục 9).
Python Flask + SQLite, HTML thuần (chỉ dùng vài dòng JavaScript thuần cho hộp thoại xác nhận Xóa và ô "Chọn tất cả").

## 1. Cấu trúc thư mục

```
watchlist-demo\
├── app.py                  # Toàn bộ route, CSDL, kiểm tra dữ liệu
├── requirements.txt        # Flask, openpyxl (đọc/ghi .xlsx)
├── README.md
├── TOAN_BO_CODE.md         # Toàn bộ mã nguồn
├── SUB_LUONG_B_CODE.md     # Nội dung đầy đủ các file thay đổi/thêm mới ở Sub-luồng B
├── watchlist.db            # Tự sinh khi chạy lần đầu (không cần tạo tay)
├── samples\                # File mẫu để thử chức năng Import
│   ├── import_hop_le.csv       # 3 dòng hợp lệ
│   ├── import_hop_le.xlsx      # 3 dòng hợp lệ
│   ├── import_co_loi.csv       # 1 dòng hợp lệ + 2 dòng lỗi -> cả file bị từ chối
│   ├── import_sai_cot.csv      # Sai thứ tự cột
│   └── khong_hop_le.txt        # Sai định dạng file
└── templates\
    ├── base.html           # Khung trang, menu, msg-success / msg-error
    ├── login.html          # Đăng nhập
    ├── records.html        # Danh sách bản ghi (màn "Nhập liệu" / "Duyệt bản ghi")
    ├── record_form.html    # Thêm mới / Sửa bản ghi
    ├── record_detail.html  # Chi tiết bản ghi (xem Người duyệt, Ngày duyệt)
    ├── import.html         # Import file .xlsx / .csv
    ├── watchlist.html      # Màn Watchlist
    ├── screening.html          # (B) Sàng lọc khách hàng
    ├── screening_history.html  # (B) Lịch sử sàng lọc
    ├── cases.html              # (B) Danh sách Case
    ├── case_detail.html        # (B) Chi tiết Case, đánh giá Event, phê duyệt
    └── mailbox.html            # (B) Hộp thư giả lập
```

## 2. Cài đặt và chạy trên Windows (Command Prompt)

Yêu cầu: Python 3.9 trở lên (tải tại https://www.python.org/downloads/, khi cài nhớ tick **"Add python.exe to PATH"**).

Mở **Command Prompt** (Win + R, gõ `cmd`, Enter) rồi chạy lần lượt:

```bat
:: 1. Kiểm tra Python
python --version

:: 2. Vào thư mục dự án (sửa đường dẫn cho đúng nơi bạn lưu)
cd /d D:\watchlist-demo

:: 3. Tạo và kích hoạt môi trường ảo
python -m venv venv
venv\Scripts\activate

:: 4. Cài thư viện
pip install -r requirements.txt

:: 5. Chạy ứng dụng
python app.py
```

Khi thấy dòng `Running on http://127.0.0.1:5000`, mở trình duyệt vào: **http://127.0.0.1:5000**

- Lần chạy đầu, `watchlist.db` được tạo tự động và nạp sẵn dữ liệu mẫu.
- Dừng ứng dụng: bấm `Ctrl + C` trong cửa sổ Command Prompt.
- Lần sau chỉ cần: `cd /d D:\watchlist-demo`, `venv\Scripts\activate`, `python app.py`.
- Nếu `python` không chạy được, thử `py` (ví dụ `py -m venv venv`).

Tài khoản: **maker01 / 123456** (Maker), **checker01 / 123456** (Checker).

Reset dữ liệu (xóa toàn bộ, nạp lại dữ liệu mẫu, mã bản ghi đếm lại từ WL-0008): mở **http://127.0.0.1:5000/reset-data**.
Không cần đăng nhập; nếu đang đăng nhập thì vẫn giữ phiên và quay về danh sách bản ghi.

## 3. Dữ liệu mẫu (sau khi chạy lần đầu hoặc /reset-data)

| Mã | Loại | Họ và tên | Số CCCD | Năm sinh | Hoạt động | Trạng thái duyệt | Trong Watchlist |
|---|---|---|---|---|---|---|---|
| WL-0001 | Cá nhân | Nguyen Van A | 001234567890 | 1980 | Active | Authorized | Có |
| WL-0002 | Cá nhân | Tran Thi B | 001987654321 | 1975 | Active | Authorized | Có |
| WL-0003 | Tổ chức | Cong ty ABC | (trống) | (trống) | Active | Authorized | Có |
| WL-0004 | Cá nhân | Tran Thi B | 001555555555 | 1990 | Active | Authorized | Có |
| WL-0005 | Cá nhân | Le Van C | 001111111111 | (trống) | Inactive | Authorized | Không |
| WL-0006 | Cá nhân | Pham Van D | 001222222222 | (trống) | Active | Unauthorized | Không |
| WL-0007 | Cá nhân | Do Van E | 001333333333 | (trống) | Active | Rejected | Không |

Quốc tịch mẫu là "Việt Nam"; Người nhập maker01, Người duyệt checker01 (với bản ghi Authorized/Rejected).

## 4. Quy tắc nghiệp vụ đã cài đặt

| Hành động | Ai | Điều kiện | Kết quả |
|---|---|---|---|
| Thêm mới / Import | Maker | Dữ liệu hợp lệ | Unauthorized |
| Sửa | Maker | Chọn đúng 1 bản ghi Unauthorized hoặc Rejected | Unauthorized (Rejected chuyển về Unauthorized, xóa Người duyệt/Ngày duyệt) |
| Xóa | Maker | Các bản ghi chọn đều Unauthorized hoặc Rejected; bấm OK ở hộp thoại | Xóa ngay khỏi CSDL |
| Authorize | Checker | Các bản ghi chọn đều Unauthorized | Authorized, ghi Người duyệt, Ngày duyệt |
| Reject | Checker | Các bản ghi chọn đều Unauthorized | Rejected, ghi Người duyệt, Ngày duyệt |
| Cập nhật Watchlist | Checker | | Xóa Watchlist cũ, nạp lại toàn bộ bản ghi Authorized + Active |

- Sửa/Xóa bản ghi Authorized bị chặn trong giai đoạn này (sẽ đi qua trạng thái Modified/Deleted sau). Bảng `records` đã có sẵn các giá trị `Modified`, `Deleted` trong ràng buộc CHECK, cột `pending_changes` (lưu dữ liệu sửa chờ duyệt), các cột `updated_by/updated_at`, và bảng `record_actions` ghi lịch sử thao tác.
- Authorize/Reject không tự cập nhật Watchlist; phải bấm "Cập nhật Watchlist".
- Gọi thẳng route không đúng quyền (ví dụ Maker POST `/records/authorize`, Checker mở `/records/new`) bị chặn với thông báo "Bạn không có quyền thực hiện chức năng này".
- Ô nhập không đặt `maxlength` để Selenium có thể nhập quá độ dài và kiểm tra thông báo lỗi phía máy chủ.

### Kiểm tra dữ liệu (form và import dùng chung)

| Trường | Quy tắc | Thông báo lỗi |
|---|---|---|
| Loại đối tượng | Bắt buộc, Cá nhân/Tổ chức | Loại đối tượng là bắt buộc / Loại đối tượng phải là Cá nhân hoặc Tổ chức |
| Họ và tên | Bắt buộc, ≤ 100 ký tự | Họ và tên là bắt buộc / Họ và tên không được vượt quá 100 ký tự |
| Số CCCD | Không bắt buộc; nếu nhập phải đúng 12 chữ số | Số CCCD phải gồm đúng 12 chữ số |
| Năm sinh | Không bắt buộc; nếu nhập phải đúng 4 chữ số | Năm sinh phải gồm 4 chữ số (YYYY) |
| Quốc tịch | ≤ 50 ký tự | Quốc tịch không được vượt quá 50 ký tự |
| Lý do đưa vào danh sách | ≤ 255 ký tự | Lý do đưa vào danh sách không được vượt quá 255 ký tự |
| Trạng thái hoạt động | Active/Inactive, mặc định Active | Trạng thái hoạt động phải là Active hoặc Inactive |

Khi có lỗi, `msg-error` liệt kê tất cả lỗi (mỗi lỗi một dòng), đồng thời mỗi lỗi hiện dưới ô tương ứng (`err-<tên trường>`). Dữ liệu đã nhập được giữ lại.

### Import

- File: `.xlsx` (sheet đầu tiên) hoặc `.csv` (UTF-8 hoặc ANSI tiếng Việt của Excel; dấu phân cách `,` hoặc `;`).
- Dòng 1 là tiêu đề, đúng tên và thứ tự: `Loại đối tượng, Họ và tên, Số CCCD, Năm sinh, Quốc tịch, Lý do đưa vào danh sách, Trạng thái hoạt động`. Ô "Trạng thái hoạt động" để trống thì hiểu là Active. Dòng trống bị bỏ qua.
- Có ít nhất 1 dòng lỗi thì cả file bị từ chối: `msg-error` = "File import có lỗi. Toàn bộ file bị từ chối, không có bản ghi nào được lưu", bảng `tbl-import-errors` liệt kê (Dòng, Nội dung lỗi); số dòng tính theo file (dòng tiêu đề là dòng 1).
- Thành công: "Import thành công N bản ghi".
- Lưu ý Excel: cột Số CCCD trong file .xlsx phải để kiểu **Text**, nếu không Excel bỏ số 0 ở đầu và dòng đó sẽ báo lỗi CCCD. File mẫu tải từ màn Import đã định dạng sẵn.

## 5. Kiểm tra nhanh thủ công

Trước khi bắt đầu (và mỗi khi muốn làm lại từ đầu), mở http://127.0.0.1:5000/reset-data.

**A. Đăng nhập Maker**
1. Mở http://127.0.0.1:5000, nhập `maker01` / `123456`, bấm Đăng nhập.
2. Thấy "Đăng nhập thành công", góc phải hiện `maker01 (Maker)`, menu: Nhập liệu, Watchlist (Thêm mới và Import nằm trên thanh công cụ của danh sách).
3. Danh sách có 7 bản ghi; có nút Thêm mới, Sửa, Xóa, Import; **không** có Authorize/Reject.
4. Nhập sai mật khẩu thì thấy "Tên đăng nhập hoặc mật khẩu không đúng".

**B. Nhập liệu (Maker)**
1. Bấm Thêm mới, bấm Lưu ngay: thấy "Loại đối tượng là bắt buộc" và "Họ và tên là bắt buộc".
2. Chọn Cá nhân, Họ và tên 101 ký tự, CCCD `12345`, Năm sinh `19x0`, bấm Lưu: thấy 3 lỗi độ dài/định dạng.
3. Sửa lại: Họ và tên `Hoang Thi Test`, CCCD `001999999999`, Năm sinh `1985`, Lưu: thấy "Lưu bản ghi thành công", bản ghi WL-0008 trạng thái Unauthorized.
4. Tìm kiếm `tran thi b`: ra WL-0002, WL-0004. Tìm `khong co`: thấy "Không tìm thấy bản ghi phù hợp". Lọc Trạng thái duyệt = Rejected: ra WL-0007.
5. Tick WL-0007 (Rejected), bấm Sửa, đổi Quốc tịch, Lưu: trạng thái về Unauthorized.
6. Bấm Xóa khi chưa tick gì: "Vui lòng chọn ít nhất một bản ghi". Tick WL-0008, bấm Xóa, chọn Cancel: bản ghi còn; bấm lại, chọn OK: "Xóa bản ghi thành công".
7. Tick WL-0001 (Authorized) rồi Sửa hoặc Xóa: bị chặn với thông báo chỉ được sửa/xóa Unauthorized hoặc Rejected.
8. Bấm nút Import (thanh công cụ), rồi bấm Import khi chưa chọn file, chọn `samples\khong_hop_le.txt`, `samples\import_sai_cot.csv`, `samples\import_co_loi.csv` để xem từng lỗi; chọn `samples\import_hop_le.xlsx` để import thành công 3 bản ghi Unauthorized.
9. Bấm Đăng xuất: quay về trang đăng nhập với "Đăng xuất thành công".

**C. Đăng nhập Checker và duyệt**
1. Đăng nhập `checker01` / `123456`: menu chỉ có Duyệt bản ghi, Watchlist; không có Thêm mới/Sửa/Xóa/Import; có Authorize, Reject.
2. Bấm Authorize khi chưa tick: "Vui lòng chọn ít nhất một bản ghi".
3. Tick WL-0006 (Pham Van D), bấm Authorize: "Authorize bản ghi thành công", trạng thái Authorized. Bấm vào mã WL-0006 để xem Người duyệt = checker01 và Ngày duyệt.
4. Tick một bản ghi Unauthorized khác (ví dụ bản ghi vừa import), bấm Reject: "Reject bản ghi thành công".

**D. Cập nhật Watchlist**
1. Vào menu Watchlist: đang có 4 bản ghi WL-0001..WL-0004.
2. (Checker) bấm "Cập nhật Watchlist": thấy "Cập nhật Watchlist thành công"; danh sách gồm WL-0001..WL-0004 và WL-0006. WL-0005 (Inactive), WL-0007 (Unauthorized/Rejected) và bản ghi bị Reject không có mặt.
3. Đăng nhập Maker vào Watchlist: xem được nhưng không có nút "Cập nhật Watchlist".

## 6. Bảng id theo từng màn hình

Quy ước: id của ô nhập = `name` của ô = tên cột SQLite = tên biến Python (`subject_type`, `fullname`, `id_number`, `birth_year`, `nationality`, `reason`, `active_status`). Phần tử thông báo luôn có mặt trên trang (ẩn bằng `display:none` khi rỗng) nên id không đổi trước và sau khi báo lỗi. `<code>` là mã bản ghi, ví dụ `chk-WL-0001`.

### Dùng chung mọi màn hình (base.html)

| id | Loại | Ý nghĩa |
|---|---|---|
| app-title | div | Tên ứng dụng |
| main-menu | nav | Menu (chỉ khi đã đăng nhập) |
| nav-records | a | Menu "Nhập liệu" (Maker) / "Duyệt bản ghi" (Checker) |
| nav-watchlist | a | Menu "Watchlist" |
| current-user | b | Tên đăng nhập hiện tại |
| current-role | span | Vai trò (Maker/Checker) |
| frm-logout | form | Form đăng xuất |
| btn-logout | button | Nút Đăng xuất |
| msg-success | div | Thông báo thành công |
| msg-error | div | Thông báo lỗi (nhiều lỗi thì mỗi lỗi một dòng) |
| saved-record-code | span (ẩn) | Mã bản ghi vừa lưu (sau Thêm mới/Sửa thành công) |
| page-title | h1 | Tiêu đề màn hình |

### Màn Đăng nhập (`/login`)

| id | Loại | Ý nghĩa |
|---|---|---|
| frm-login | form | Form đăng nhập |
| username | input text | Tên đăng nhập |
| password | input password | Mật khẩu |
| btn-login | button | Nút Đăng nhập |
| login-hint | p | Gợi ý tài khoản demo |

### Màn Danh sách bản ghi: "Nhập liệu" / "Duyệt bản ghi" (`/records`)

| id | Loại | Ý nghĩa | Vai trò |
|---|---|---|---|
| frm-search | form | Form tìm kiếm (GET) | Cả hai |
| search_fullname | input text | Tìm theo Họ và tên | Cả hai |
| search_id_number | input text | Tìm theo Số CCCD | Cả hai |
| filter_auth_status | select | Lọc Trạng thái duyệt (rỗng, Unauthorized, Authorized, Rejected) | Cả hai |
| btn-search | button | Tìm kiếm | Cả hai |
| btn-clear-search | a | Xóa điều kiện tìm kiếm | Cả hai |
| frm-records | form | Form chứa checkbox và nút thao tác | Cả hai |
| btn-add | a | Thêm mới | Maker |
| btn-edit | button | Sửa bản ghi đã tick (đúng 1) | Maker |
| btn-delete | button | Xóa các bản ghi đã tick (hộp thoại OK/Cancel) | Maker |
| btn-import | a | Mở màn Import | Maker |
| btn-authorize | button | Authorize các bản ghi đã tick | Checker |
| btn-reject | button | Reject các bản ghi đã tick | Checker |
| record-count | span | Tổng số bản ghi đang hiển thị | Cả hai |
| tbl-records | table | Bảng bản ghi | Cả hai |
| tbl-records-body | tbody | Thân bảng | Cả hai |
| chk-all | checkbox | Chọn/bỏ chọn tất cả | Cả hai |
| row-`<code>` | tr | Dòng của bản ghi | Cả hai |
| chk-`<code>` | checkbox | Chọn bản ghi (name=`selected_codes`) | Cả hai |
| lnk-view-`<code>` | a | Mở chi tiết bản ghi | Cả hai |
| msg-no-result | div | "Không tìm thấy bản ghi phù hợp" | Cả hai |

Thứ tự cột của `tbl-records`: (checkbox), Mã bản ghi, Loại đối tượng, Họ và tên, Số CCCD, Năm sinh, Quốc tịch, Trạng thái hoạt động, Trạng thái duyệt, Người nhập, Ngày nhập, Người duyệt, Ngày duyệt.

Người duyệt / Ngày duyệt chỉ có giá trị với bản ghi Authorized hoặc Rejected; để trống với bản ghi Unauthorized (kể cả bản ghi Rejected vừa được Maker sửa lại).

### Màn Thêm mới / Sửa bản ghi (`/records/new`, `/records/<code>/edit`, chỉ Maker)

| id | Loại | Ý nghĩa |
|---|---|---|
| frm-record | form | Form bản ghi |
| record_code | input (readonly) | Mã bản ghi (rỗng khi thêm mới, tự sinh khi lưu) |
| subject_type | select | Loại đối tượng* (rỗng, Cá nhân, Tổ chức) |
| fullname | input text | Họ và tên* |
| id_number | input text | Số CCCD |
| birth_year | input text | Năm sinh |
| nationality | input text | Quốc tịch |
| reason | textarea | Lý do đưa vào danh sách |
| active_status | select | Trạng thái hoạt động (Active, Inactive) |
| auth_status | input (readonly) | Trạng thái duyệt |
| created_by | input (readonly) | Người nhập |
| created_at | input (readonly) | Ngày nhập |
| err-subject_type | span | Lỗi Loại đối tượng |
| err-fullname | span | Lỗi Họ và tên |
| err-id_number | span | Lỗi Số CCCD |
| err-birth_year | span | Lỗi Năm sinh |
| err-nationality | span | Lỗi Quốc tịch |
| err-reason | span | Lỗi Lý do |
| err-active_status | span | Lỗi Trạng thái hoạt động |
| btn-save | button | Lưu |
| btn-cancel | a | Hủy, quay lại danh sách |

### Màn Chi tiết bản ghi (`/records/<code>`)

| id | Loại | Ý nghĩa |
|---|---|---|
| tbl-record-detail | table | Bảng chi tiết |
| view-record_code | td | Mã bản ghi |
| view-subject_type | td | Loại đối tượng |
| view-fullname | td | Họ và tên |
| view-id_number | td | Số CCCD |
| view-birth_year | td | Năm sinh |
| view-nationality | td | Quốc tịch |
| view-reason | td | Lý do đưa vào danh sách |
| view-active_status | td | Trạng thái hoạt động |
| view-auth_status | td | Trạng thái duyệt |
| view-created_by | td | Người nhập |
| view-created_at | td | Ngày nhập |
| view-updated_by | td | Người sửa |
| view-updated_at | td | Ngày sửa |
| view-authorized_by | td | Người duyệt |
| view-authorized_at | td | Ngày duyệt |
| view-in_watchlist | td | Đang có trong Watchlist (Có/Không) |
| btn-back | a | Quay lại danh sách |

### Màn Import (`/records/import`, chỉ Maker)

| id | Loại | Ý nghĩa |
|---|---|---|
| tbl-import-columns | table | Mẫu tiêu đề cột |
| lnk-template-xlsx | a | Tải file mẫu .xlsx |
| lnk-template-csv | a | Tải file mẫu .csv |
| frm-import | form | Form import |
| import_file | input file | Chọn file |
| btn-import-submit | button | Thực hiện Import |
| btn-cancel | a | Hủy, quay lại danh sách |
| tbl-import-errors | table | Danh sách lỗi theo dòng (Dòng, Nội dung lỗi) |
| tbl-import-errors-body | tbody | Thân bảng lỗi |
| import-error-`<n>` | tr | Dòng lỗi thứ n trong bảng lỗi |

### Màn Watchlist (`/watchlist`)

| id | Loại | Ý nghĩa | Vai trò |
|---|---|---|---|
| frm-update-watchlist | form | Form cập nhật | Checker |
| btn-update-watchlist | button | Cập nhật Watchlist | Checker |
| watchlist-count | span | Tổng số bản ghi trong Watchlist | Cả hai |
| tbl-watchlist | table | Bảng Watchlist | Cả hai |
| tbl-watchlist-body | tbody | Thân bảng | Cả hai |
| wl-row-`<code>` | tr | Dòng của bản ghi trong Watchlist | Cả hai |
| msg-watchlist-empty | div | "Watchlist chưa có bản ghi nào" | Cả hai |

Thứ tự cột của `tbl-watchlist`: Mã bản ghi, Loại đối tượng, Họ và tên, Số CCCD, Năm sinh, Quốc tịch, Lý do đưa vào danh sách, Người cập nhật, Ngày cập nhật.

## 7. Route

| Route | Method | Quyền | Chức năng |
|---|---|---|---|
| / | GET | | Chuyển tới /records hoặc /login |
| /login | GET, POST | | Đăng nhập |
| /logout | GET, POST | | Đăng xuất |
| /reset-data | GET, POST | | Xóa dữ liệu, nạp lại dữ liệu mẫu |
| /records | GET | Đăng nhập | Danh sách, tìm kiếm, lọc |
| /records/`<code>` | GET | Đăng nhập | Chi tiết bản ghi |
| /records/new | GET, POST | Maker | Thêm mới |
| /records/edit-selected | POST | Maker | Kiểm tra checkbox rồi chuyển tới màn Sửa |
| /records/`<code>`/edit | GET, POST | Maker | Sửa |
| /records/delete | POST | Maker | Xóa |
| /records/import | GET, POST | Maker | Import |
| /records/import/template.csv | GET | Đăng nhập | Tải mẫu CSV |
| /records/import/template.xlsx | GET | Đăng nhập | Tải mẫu XLSX |
| /records/authorize | POST | Checker | Authorize |
| /records/reject | POST | Checker | Reject |
| /watchlist | GET | Đăng nhập | Xem Watchlist |
| /watchlist/update | POST | Checker | Cập nhật Watchlist |

## 8. Gợi ý Selenium

- Hộp thoại xác nhận Xóa là `confirm()` của trình duyệt: `driver.switch_to.alert.accept()` (OK) hoặc `.dismiss()` (Cancel). Nếu chưa tick bản ghi nào thì không hiện hộp thoại, máy chủ trả "Vui lòng chọn ít nhất một bản ghi".
- Chọn giá trị: `Select(driver.find_element(By.ID, "subject_type")).select_by_visible_text("Cá nhân")`.
- Thông báo rỗng vẫn tồn tại nhưng bị ẩn, nên dùng `visibility_of_element_located((By.ID, "msg-success"))` hoặc so sánh `.text`.
- Import: `driver.find_element(By.ID, "import_file").send_keys(r"D:\watchlist-demo\samples\import_hop_le.xlsx")`.

## 9. Sub-luồng B: Sàng lọc khách hàng và xử lý Case

### 9.1. File thay đổi / thêm mới và cách cập nhật

| File | Thay đổi |
|---|---|
| `app.py` | **Sửa**: thêm bảng DB mới, hàm so khớp `find_watchlist_matches()`, `normalize_name()`, `cif_decision()` và các route của B; `/reset-data` xóa và nạp lại cả dữ liệu B; khởi động tự bổ sung bảng mới vào database cũ. Code của A giữ nguyên. |
| `templates/base.html` | **Sửa**: thêm 4 mục menu mới. Các id cũ giữ nguyên. |
| `templates/screening.html` | **Mới** |
| `templates/screening_history.html` | **Mới** |
| `templates/cases.html` | **Mới** |
| `templates/case_detail.html` | **Mới** |
| `templates/mailbox.html` | **Mới** |
| `README.md`, `TOAN_BO_CODE.md`, `SUB_LUONG_B_CODE.md` | Tài liệu |

Các file khác của A (`records.html`, `record_form.html`, `record_detail.html`, `import.html`, `login.html`, `watchlist.html`, `requirements.txt`, `samples\`) **không đổi**.

- Nếu tự chép tay: chép đè `app.py` và `templates\base.html`, chép thêm 5 file template mới vào `templates\`.
- **Không cần xóa `watchlist.db`.** Khi chạy `python app.py`, app thấy database cũ của A sẽ giữ nguyên dữ liệu A và chỉ tạo thêm các bảng của B. Không cần cài thêm thư viện.
- Muốn bắt đầu sạch (mã đếm lại từ SC-0001, CASE-0001): mở http://127.0.0.1:5000/reset-data.
- Nhớ dừng app (`Ctrl + C`) rồi chạy lại `python app.py` sau khi thay `app.py`.

### 9.2. Quy tắc đã cài đặt

**Sàng lọc** (chỉ Maker thực hiện; Checker xem màn hình nhưng ô nhập và nút "Sàng lọc" bị vô hiệu hóa, server cũng chặn):
- Kiểm tra: Loại khách hàng bắt buộc; Họ và tên bắt buộc, ≤ 100 ký tự; Số CCCD nếu nhập phải đúng 12 chữ số. Với Tổ chức, Số CCCD được bỏ qua (không lưu, không so khớp).
- Hàm `find_watchlist_matches()` trong `app.py`: chỉ so với bản ghi đang ở bảng `watchlist` (do Checker "Cập nhật Watchlist") mà bản ghi gốc vẫn Authorized + Active, và cùng Loại đối tượng. HIT khi **Số CCCD trùng** (chỉ khi cả hai bên có CCCD) **hoặc Họ và tên trùng sau chuẩn hóa** (`normalize_name()`: bỏ dấu tiếng Việt kể cả đ, chữ thường, bỏ khoảng trắng thừa).
- Mỗi bản ghi trùng = 1 Event; mỗi lần HIT tạo đúng 1 Case "Chờ Maker". Mã tự tăng SC-0001, CASE-0001.
- Sau khi bấm Sàng lọc, trang chuyển sang `/screening?sc=SC-xxxx` để hiện kết quả, nên bấm F5 không tạo thêm lần sàng lọc/Case.
- Thông báo: NO-HIT → `msg-success` = "Không phát hiện trùng khớp với Watchlist"; HIT → `msg-success` = "Phát hiện N bản ghi trùng khớp với Watchlist. Đã tạo CASE-xxxx".
- Bản ghi mới Authorize ở A chỉ được so khớp sau khi Checker bấm "Cập nhật Watchlist".

**Case**

| Trạng thái | Maker | Checker |
|---|---|---|
| Chờ Maker | Đánh giá Event, Đề xuất | Chỉ xem |
| Cần bổ sung | Gửi bổ sung | Chỉ xem |
| Chờ Checker | Chỉ xem | Yêu cầu bổ sung, Đóng - Hit sai, Đóng - Chấm dứt quan hệ, Đóng - Duy trì có kiểm soát |
| Đã đóng - ... | Chỉ xem | Chỉ xem |

- Nút không được phép thì **không hiển thị**; select Đánh giá và ô Lý do của Event bị **vô hiệu hóa** (vẫn giữ id) khi không được sửa. Gọi thẳng route `/cases/<mã>/action` sai quyền/trạng thái bị chặn với "Bạn không có quyền thực hiện hành động này ở trạng thái hiện tại của case".
- Đề xuất: mọi Event phải khác "Chưa đánh giá" và có Lý do; lỗi có thể hiện cùng lúc. Khi lỗi, giá trị đã chọn/nhập được giữ lại trên màn hình (chưa lưu vào DB).
- Ở "Cần bổ sung", đánh giá Event không sửa lại được, Maker chỉ gửi nội dung bổ sung (đúng theo đề).
- Mọi hành động đều bắt buộc nhập lý do: Đề xuất (Lý do của từng Event), Gửi bổ sung (Nội dung bổ sung), Yêu cầu bổ sung và 3 hành động Đóng (Lý do quyết định, thiếu thì báo "Vui lòng nhập lý do quyết định").
- Khi đóng Case, kiểm tra điều kiện Event trước, rồi Lý do quyết định; nếu sai cả hai thì `msg-error` hiện cả hai lỗi.
- Mọi hành động (kể cả "Tạo case") ghi vào Lịch sử xử lý, kèm ghi chú (đánh giá từng Event, nội dung bổ sung, lý do quyết định).

**Quyết định mở CIF** luôn tính lại từ trạng thái Case hiện tại (hàm `cif_decision()`), nên màn Sàng lọc và Lịch sử sàng lọc tự cập nhật khi Case đổi trạng thái.

| Tình huống | Quyết định mở CIF |
|---|---|
| NO-HIT | Đủ điều kiện mở CIF |
| Chờ Maker / Chờ Checker / Cần bổ sung | Chờ xử lý case |
| Đã đóng - Hit sai | Đủ điều kiện mở CIF |
| Đã đóng - Chấm dứt quan hệ | Không đủ điều kiện mở CIF |
| Đã đóng - Duy trì có kiểm soát | Đủ điều kiện mở CIF - có theo dõi |

**Hộp thư giả lập** (chỉ ghi bảng `emails`, mỗi user chỉ thấy email gửi cho mình, mới nhất ở trên):

| Sự kiện | Người nhận | Tiêu đề | Nội dung (mỗi ý một dòng) |
|---|---|---|---|
| Maker Đề xuất | checker01 | [Demo AML] Case CASE-xxxx chờ phê duyệt | Mã case; Họ và tên khách hàng; "Case đã được Maker (maker01) đề xuất và đang chờ Checker phê duyệt."; Thời gian gửi |
| Checker Yêu cầu bổ sung | maker01 | [Demo AML] Case CASE-xxxx cần bổ sung thông tin | Mã case; Họ và tên khách hàng; Ghi chú của Checker; "Đề nghị Maker bổ sung thông tin cho case và gửi lại để Checker phê duyệt."; Thời gian gửi |
| Đóng - Chấm dứt quan hệ | maker01 | [Demo AML] Case CASE-xxxx - Hit đúng, chấm dứt quan hệ | Mã case; Họ và tên khách hàng; "Kết luận: Hit đúng. Chấm dứt quan hệ với khách hàng."; Lý do quyết định của Checker; Thời gian gửi |
| Đóng - Duy trì có kiểm soát | maker01 | [Demo AML] Case CASE-xxxx - Hit đúng, duy trì có kiểm soát | Mã case; Họ và tên khách hàng; "Kết luận: Hit đúng. Duy trì quan hệ với khách hàng, kèm theo dõi (có kiểm soát)."; Lý do quyết định của Checker; Thời gian gửi |

Lưu ý: email Đề xuất gửi cho **checker01**, nên phải đăng nhập checker01 mới thấy trong Hộp thư giả lập.

Không gửi email khi: sàng lọc, Đóng - Hit sai, Gửi bổ sung.

**Dữ liệu mẫu của B**: `/reset-data` xóa sạch lần sàng lọc, Case, Event, lịch sử, email và nạp lại Watchlist mẫu của A. B không có Case mẫu để mã luôn bắt đầu từ SC-0001, CASE-0001 khi chạy test.

### 9.3. Route mới

| Route | Method | Quyền | Chức năng |
|---|---|---|---|
| /screening | GET | Đăng nhập | Màn Sàng lọc (`?sc=SC-xxxx` để xem kết quả một lần sàng lọc) |
| /screening | POST | Maker | Thực hiện sàng lọc |
| /screening-history | GET | Đăng nhập | Lịch sử sàng lọc, tìm theo Họ và tên |
| /cases | GET | Đăng nhập | Danh sách Case, lọc theo Trạng thái |
| /cases/`<mã case>` | GET | Đăng nhập | Chi tiết Case |
| /cases/`<mã case>`/action | POST | Theo bảng phân quyền | `action` = propose, send_supplement, request_supplement, close_false_hit, close_terminate, close_maintain |
| /mailbox | GET | Đăng nhập | Hộp thư giả lập |

### 9.4. Bảng id mới theo từng màn hình

`<n>` là số thứ tự Event trong Case (1, 2, ...); `<SC>` là mã sàng lọc; `<CASE>` là mã case. Các id dùng chung (`msg-success`, `msg-error`, `page-title`, `btn-logout`...) giữ như mục 6.

#### Menu (base.html)

| id | Loại | Ý nghĩa |
|---|---|---|
| nav-screening | a | Menu "Sàng lọc khách hàng" |
| nav-cases | a | Menu "Danh sách Case" |
| nav-screening-history | a | Menu "Lịch sử sàng lọc" |
| nav-mailbox | a | Menu "Hộp thư giả lập" |

#### Màn Sàng lọc khách hàng (`/screening`)

| id | Loại | Ý nghĩa |
|---|---|---|
| frm-screening | form | Form sàng lọc |
| customer_type | select | Loại khách hàng* (rỗng, Cá nhân, Tổ chức) |
| fullname | input text | Họ và tên / Tên tổ chức* |
| id_number | input text | Số CCCD |
| err-customer_type | span | Lỗi Loại khách hàng |
| err-fullname | span | Lỗi Họ và tên |
| err-id_number | span | Lỗi Số CCCD |
| btn-screen | button | Nút "Sàng lọc" (vô hiệu hóa với Checker) |
| screening-readonly-note | p | Ghi chú "Chỉ Maker được thực hiện sàng lọc" (hiện với Checker) |
| screening-result | div | Khung kết quả (ẩn khi chưa sàng lọc) |
| tbl-screening-result | table | Bảng thông tin kết quả |
| result-screening-code | td | Mã sàng lọc |
| result-fullname | td | Họ và tên khách hàng |
| result-customer-type | td | Loại khách hàng |
| result-id-number | td | Số CCCD |
| result-status | td | Kết quả: HIT / NO-HIT |
| result-message | td | "Không phát hiện trùng khớp với Watchlist" hoặc "Phát hiện N bản ghi trùng khớp với Watchlist" |
| result-case-code | td | Mã case vừa tạo (rỗng khi NO-HIT) |
| lnk-result-case | a | Link mở chi tiết case (chỉ khi HIT) |
| result-cif-decision | td | Quyết định mở CIF |
| tbl-screening-matches | table | Bảng bản ghi trùng khớp: Mã bản ghi, Họ và tên, Số CCCD, Căn cứ trùng khớp |
| tbl-screening-matches-body | tbody | Thân bảng |
| match-row-`<mã bản ghi>` | tr | Dòng trùng, ví dụ `match-row-WL-0002` |

#### Màn Lịch sử sàng lọc (`/screening-history`)

| id | Loại | Ý nghĩa |
|---|---|---|
| frm-search | form | Form tìm kiếm |
| search_fullname | input text | Tìm theo Họ và tên |
| btn-search | button | Tìm kiếm |
| btn-clear-search | a | Xóa điều kiện |
| screening-count | span | Tổng số lần sàng lọc đang hiển thị |
| tbl-screenings | table | Bảng lịch sử |
| tbl-screenings-body | tbody | Thân bảng |
| sc-row-`<SC>` | tr | Dòng của lần sàng lọc |
| lnk-sc-`<SC>` | a | Mở lại kết quả sàng lọc |
| lnk-sc-case-`<SC>` | a | Mở case của lần sàng lọc (chỉ khi HIT) |
| msg-no-result | div | "Không tìm thấy lần sàng lọc phù hợp" |

Thứ tự cột `tbl-screenings`: Mã sàng lọc, Họ và tên, Loại khách hàng, Kết quả, Mã case, Quyết định mở CIF, Ngày sàng lọc, Người thực hiện.

#### Màn Danh sách Case (`/cases`)

| id | Loại | Ý nghĩa |
|---|---|---|
| frm-case-filter | form | Form lọc |
| filter_case_status | select | Lọc theo Trạng thái (rỗng = tất cả, 6 trạng thái) |
| btn-filter | button | Lọc |
| btn-clear-filter | a | Xóa điều kiện |
| case-count | span | Tổng số case đang hiển thị |
| tbl-cases | table | Bảng case |
| tbl-cases-body | tbody | Thân bảng |
| case-row-`<CASE>` | tr | Dòng của case |
| lnk-case-`<CASE>` | a | Mở chi tiết case |
| msg-no-result | div | "Không tìm thấy case phù hợp" |

Thứ tự cột `tbl-cases`: Mã case, Họ và tên khách hàng, Loại khách hàng, Số Event, Trạng thái, Ngày tạo.

#### Màn Chi tiết Case (`/cases/<CASE>`)

| id | Loại | Ý nghĩa | Hiện khi |
|---|---|---|---|
| tbl-case-info | table | Thông tin khách hàng sàng lọc | Luôn |
| case-code | td | Mã case | Luôn |
| case-status | td | Trạng thái | Luôn |
| case-cif-decision | td | Quyết định mở CIF | Luôn |
| case-screening-code | td | Mã sàng lọc | Luôn |
| case-customer-type | td | Loại khách hàng | Luôn |
| case-fullname | td | Họ và tên khách hàng | Luôn |
| case-id-number | td | Số CCCD | Luôn |
| case-created-by | td | Người tạo | Luôn |
| case-created-at | td | Ngày tạo | Luôn |
| frm-case-action | form | Form xử lý case | Luôn |
| tbl-events | table | Bảng Event | Luôn |
| tbl-events-body | tbody | Thân bảng Event | Luôn |
| event-row-`<n>` | tr | Dòng Event thứ n | Luôn |
| event-code-`<n>` | td | Mã bản ghi Watchlist | Luôn |
| event-name-`<n>` | td | Họ và tên | Luôn |
| event-idnum-`<n>` | td | Số CCCD | Luôn |
| event-match-`<n>` | td | Căn cứ trùng khớp | Luôn |
| eval-`<n>` | select | Đánh giá (Chưa đánh giá, Hit đúng, Hit sai) | Luôn; chỉ bật khi Maker + Chờ Maker |
| reason-`<n>` | input text | Lý do của Event | Luôn; chỉ bật khi Maker + Chờ Maker |
| btn-propose | button | Đề xuất | Maker + Chờ Maker |
| supplement_note | textarea | Nội dung bổ sung | Maker + Cần bổ sung |
| btn-send-supplement | button | Gửi bổ sung | Maker + Cần bổ sung |
| decision_reason | textarea | Lý do quyết định (bắt buộc cho cả 4 hành động của Checker) | Checker + Chờ Checker |
| btn-request-supplement | button | Yêu cầu bổ sung | Checker + Chờ Checker |
| btn-close-false-hit | button | Đóng - Hit sai | Checker + Chờ Checker |
| btn-close-terminate | button | Đóng - Chấm dứt quan hệ | Checker + Chờ Checker |
| btn-close-maintain | button | Đóng - Duy trì có kiểm soát | Checker + Chờ Checker |
| case-readonly-note | p | "Bạn chỉ được xem case này ở trạng thái hiện tại." | Khi không có hành động nào |
| tbl-case-history | table | Lịch sử xử lý: Thời gian, Người thực hiện, Hành động, Ghi chú | Luôn |
| tbl-case-history-body | tbody | Thân bảng | Luôn |
| history-row-`<n>` | tr | Dòng lịch sử thứ n (theo thời gian) | Luôn |
| btn-back-cases | a | Quay lại Danh sách Case | Luôn |

#### Màn Hộp thư giả lập (`/mailbox`)

| id | Loại | Ý nghĩa |
|---|---|---|
| mailbox-note | p | Ghi chú hộp thư giả lập |
| email-count | span | Tổng số email |
| tbl-emails | table | Bảng email: Thời gian, Người nhận, Tiêu đề, Nội dung |
| tbl-emails-body | tbody | Thân bảng |
| email-row-`<id>` | tr | Dòng email (id trong bảng `emails`) |
| msg-mailbox-empty | div | "Hộp thư chưa có email nào" |

#### Thông báo mới (luôn hiện ở `msg-success` / `msg-error`)

| Phần tử | Nội dung |
|---|---|
| msg-error | Loại khách hàng là bắt buộc; Họ và tên là bắt buộc; Họ và tên không được vượt quá 100 ký tự; Số CCCD phải gồm đúng 12 chữ số; Vui lòng đánh giá tất cả Event; Vui lòng nhập lý do cho từng Event; Vui lòng nhập nội dung bổ sung; Vui lòng nhập lý do quyết định; Chỉ được chọn hành động này khi tất cả Event là Hit sai; Chỉ được chọn hành động này khi có ít nhất 1 Event là Hit đúng; Bạn không có quyền thực hiện hành động này ở trạng thái hiện tại của case |
| msg-success | Không phát hiện trùng khớp với Watchlist; Phát hiện N bản ghi trùng khớp với Watchlist. Đã tạo CASE-xxxx; Đề xuất thành công; Gửi bổ sung thành công; Yêu cầu bổ sung thành công; Đóng case thành công: <trạng thái mới> |

### 9.5. Bảng database mới

| Bảng | Nội dung | Cột chính |
|---|---|---|
| `screenings` | Mỗi lần sàng lọc | screening_code (SC-0001), customer_type, fullname, id_number, result (HIT/NO-HIT), case_id (NULL khi NO-HIT), screened_by, screened_at |
| `cases` | Mỗi Case tạo ra khi HIT | case_code (CASE-0001), screening_id, customer_type, fullname, id_number, status, created_by, created_at, updated_by, updated_at |
| `case_events` | Mỗi bản ghi Watchlist trùng = 1 Event | case_id, event_no (1, 2...), record_id, record_code, subject_type, fullname, id_number, match_reason, evaluation, reason |
| `case_history` | Lịch sử xử lý Case | case_id, acted_at, actor, action, note |
| `emails` | Hộp thư giả lập | case_id, recipient, subject, body, sent_at |

Bảng `sequences` (của A) có thêm 2 dòng `screening` và `case` để sinh mã SC-xxxx, CASE-xxxx. Quyết định mở CIF **không lưu** trong DB mà tính lại từ `screenings.result` và `cases.status`.

### 9.6. Thử nhanh 3 kịch bản

Trước tiên mở http://127.0.0.1:5000/reset-data.

**Kịch bản 1: NO-HIT**
1. Đăng nhập `maker01`, vào **Sàng lọc khách hàng**.
2. Chọn Cá nhân, Họ và tên `Hoang Van Z`, Số CCCD `009999999999`, bấm **Sàng lọc**.
3. Thấy "Không phát hiện trùng khớp với Watchlist", Kết quả NO-HIT, Mã sàng lọc SC-0001, không có Mã case, Quyết định mở CIF "Đủ điều kiện mở CIF".
4. Thử thêm Tổ chức `Cong ty XYZ`: cũng NO-HIT. Vào **Lịch sử sàng lọc** thấy 2 dòng.

**Kịch bản 2: HIT → Hit sai → Checker đóng Hit sai**
1. (maker01) Sàng lọc Cá nhân, Họ và tên `Tran Thi B`, không nhập CCCD. Thấy HIT, bảng trùng khớp có WL-0002 và WL-0004, Mã case CASE-0001 (NO-HIT không tạo case), Quyết định mở CIF "Chờ xử lý case".
2. Bấm link mã case. Bấm **Đề xuất** ngay để thấy 2 lỗi. Chọn `eval-1`, `eval-2` = Hit sai, nhập Lý do cho cả 2 Event, bấm **Đề xuất**: "Đề xuất thành công", trạng thái "Chờ Checker".
3. Đăng xuất, đăng nhập `checker01`. Vào **Hộp thư giả lập**: có email "[Demo AML] Case CASE-0001 chờ phê duyệt".
4. Vào **Danh sách Case**, mở CASE-0001. Bấm **Đóng - Chấm dứt quan hệ** để thấy lỗi "Chỉ được chọn hành động này khi có ít nhất 1 Event là Hit đúng". Nhập Lý do quyết định, bấm **Đóng - Hit sai**: trạng thái "Đã đóng - Hit sai", Quyết định mở CIF "Đủ điều kiện mở CIF".
5. Lịch sử xử lý có: Tạo case, Đề xuất, Đóng - Hit sai. Hộp thư của maker01 không có email mới.

**Kịch bản 3: HIT → Hit đúng → Checker chọn Chấm dứt quan hệ → xem Hộp thư**
1. (maker01) Sàng lọc Cá nhân, Họ và tên `NGUYỄN  VĂN A` (viết hoa, có dấu, 2 khoảng trắng). Thấy HIT WL-0001 và một Mã case mới.
2. Mở case, chọn `eval-1` = Hit đúng, nhập Lý do, bấm **Đề xuất**.
3. Đăng nhập `checker01`, mở case đó. Bấm **Đóng - Hit sai** để thấy lỗi "Chỉ được chọn hành động này khi tất cả Event là Hit sai". Nhập Lý do quyết định, bấm **Đóng - Chấm dứt quan hệ**: trạng thái "Đã đóng - Chấm dứt quan hệ", Quyết định mở CIF "Không đủ điều kiện mở CIF".
4. Vào **Lịch sử sàng lọc**: dòng `NGUYỄN  VĂN A` có Quyết định mở CIF "Không đủ điều kiện mở CIF".
5. Đăng nhập `maker01`, vào **Hộp thư giả lập**: có email "[Demo AML] Case CASE-xxxx - Hit đúng, chấm dứt quan hệ".

(Tùy chọn) Thử "Yêu cầu bổ sung": ở bước 3 kịch bản 3, Checker nhập Lý do quyết định rồi bấm **Yêu cầu bổ sung** → Maker nhận email "cần bổ sung thông tin", mở case, nhập Nội dung bổ sung, bấm **Gửi bổ sung** → case về "Chờ Checker" (không có email).

---

## 9. Mở rộng: kiểm soát sàng lọc lặp lại (K1, K2) và đồng hồ giả lập

Bổ sung theo góp ý của giảng viên hướng dẫn về kịch bản theo ngày (cùng một khách hàng đến sàng lọc nhiều lần).
Mô phỏng đơn giản hóa, không phải quy trình của một ngân hàng cụ thể.

**Định danh** của khách hàng dùng cho K1, K2: Số CCCD nếu có (Cá nhân), nếu không thì họ tên đã chuẩn hóa
(cùng Loại khách hàng).

| Quy tắc | Nội dung |
|---|---|
| K1 | Cùng một định danh bị sàng lọc ra HIT tối đa `MAX_HIT_PER_DAY` = 3 lần trong ngày. Lần thứ 4 bị chặn, báo "Vượt giới hạn ... Chuyển Compliance xử lý", **không** ghi vào Lịch sử sàng lọc. Sang ngày mới thì bộ đếm về 0. Kết quả NO-HIT không bị giới hạn. |
| K2 | Nếu định danh đang có Case chưa đóng (Chờ Maker, Chờ Checker, Cần bổ sung), lần sàng lọc HIT lặp lại được gắn vào Case đó, **không** tạo Case mới (báo "Khách hàng đã có CASE-xxxx đang xử lý. Không tạo Case mới", Lịch sử Case ghi "Sàng lọc lặp"). Case đã đóng thì sàng lọc lại sẽ mở Case mới. |

**Đồng hồ giả lập (chỉ dùng cho kiểm thử):**
- `/set-date?offset=N` (N từ 0 đến 999): hệ thống coi như đã qua N ngày kể từ ngày thật. Mọi thời điểm ghi mới (sàng lọc, Case...) dùng ngày giả lập.
- `/set-date` không kèm tham số: xem ngày giả lập hiện tại.
- `/reset-data` đặt lại đồng hồ về ngày thật.

Các quy tắc cũ (so khớp Watchlist, Maker-Checker, quyết định mở CIF) không thay đổi.

