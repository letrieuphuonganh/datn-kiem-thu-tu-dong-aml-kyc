# -*- coding: utf-8 -*-
"""
Web demo quản lý danh sách sàng lọc (Watchlist) - nghiệp vụ chống rửa tiền.
Sub-luồng A: quản lý bản ghi Watchlist (Maker/Checker).
Sub-luồng B: sàng lọc khách hàng, xử lý Case, hộp thư giả lập.
Flask + SQLite, HTML thuần (không dùng framework JavaScript).

Chạy:  python app.py   rồi mở http://127.0.0.1:5000
"""
import csv
import io
import os
import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, flash, g, redirect, render_template, request,
                   send_file, session, url_for)
from openpyxl import Workbook, load_workbook

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "watchlist.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = "aml-watchlist-demo-secret-key"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

# ---------------------------------------------------------------------------
# Hằng số nghiệp vụ
# ---------------------------------------------------------------------------
USERS = {
    "maker01": {"password": "123456", "role": "maker"},
    "checker01": {"password": "123456", "role": "checker"},
}
ROLE_LABELS = {"maker": "Maker", "checker": "Checker"}

SUBJECT_TYPES = ["Cá nhân", "Tổ chức"]
ACTIVE_STATUSES = ["Active", "Inactive"]
# Giai đoạn này chỉ dùng 3 trạng thái duyệt. Modified/Deleted đã được khai báo
# sẵn trong ràng buộc CHECK của bảng records để bổ sung sau.
AUTH_STATUSES = ["Unauthorized", "Authorized", "Rejected"]
ALL_AUTH_STATUSES = ["Unauthorized", "Authorized", "Rejected", "Modified", "Deleted"]
EDITABLE_STATUSES = ["Unauthorized", "Rejected"]

# Tên trường dùng thống nhất cho: cột SQLite = biến Python = name/id trong HTML
RECORD_FIELDS = ["subject_type", "fullname", "id_number", "birth_year",
                 "nationality", "reason", "active_status"]

# Mẫu file import: đúng tên và đúng thứ tự cột
IMPORT_COLUMNS = ["Loại đối tượng", "Họ và tên / Tên tổ chức", "Số CCCD / Số ĐKKD (MST)", "Năm sinh",
                  "Quốc tịch", "Lý do đưa vào danh sách", "Trạng thái hoạt động"]

MSG = {
    "login_required": "Vui lòng đăng nhập",
    "login_empty": "Vui lòng nhập tên đăng nhập và mật khẩu",
    "login_failed": "Tên đăng nhập hoặc mật khẩu không đúng",
    "login_success": "Đăng nhập thành công",
    "logout_success": "Đăng xuất thành công",
    "no_permission": "Bạn không có quyền thực hiện chức năng này",
    "subject_type_required": "Loại đối tượng là bắt buộc",
    "subject_type_invalid": "Loại đối tượng phải là Cá nhân hoặc Tổ chức",
    "fullname_required": "Họ và tên là bắt buộc",
    "fullname_too_long": "Họ và tên không được vượt quá 100 ký tự",
    "id_number_invalid": "Số CCCD phải gồm đúng 12 chữ số",
    "org_name_required": "Tên tổ chức là bắt buộc",
    "org_name_too_long": "Tên tổ chức không được vượt quá 100 ký tự",
    "org_tax_invalid": "Số ĐKKD/MST phải gồm 10 chữ số hoặc 13 ký tự dạng 10 chữ số-3 chữ số",
    "birth_year_invalid": "Năm sinh phải gồm 4 chữ số (YYYY)",
    "nationality_too_long": "Quốc tịch không được vượt quá 50 ký tự",
    "reason_too_long": "Lý do đưa vào danh sách không được vượt quá 255 ký tự",
    "active_status_invalid": "Trạng thái hoạt động phải là Active hoặc Inactive",
    "save_success": "Lưu bản ghi thành công",
    "select_required": "Vui lòng chọn ít nhất một bản ghi",
    "select_one_to_edit": "Vui lòng chọn duy nhất một bản ghi để sửa",
    "record_not_found": "Không tìm thấy bản ghi",
    "edit_not_allowed": "Chỉ được sửa bản ghi ở trạng thái Unauthorized hoặc Rejected",
    "delete_not_allowed": "Chỉ được xóa bản ghi ở trạng thái Unauthorized hoặc Rejected",
    "delete_success": "Xóa bản ghi thành công",
    "authorize_not_allowed": "Chỉ được Authorize/Reject bản ghi ở trạng thái Unauthorized",
    "authorize_success": "Authorize bản ghi thành công",
    "reject_success": "Reject bản ghi thành công",
    "no_result": "Không tìm thấy bản ghi phù hợp",
    "import_file_required": "Vui lòng chọn file import",
    "import_file_type": "Chỉ chấp nhận file .xlsx hoặc .csv",
    "import_header_invalid": "Tên hoặc thứ tự cột không đúng mẫu",
    "import_unreadable": "Không đọc được nội dung file import",
    "import_empty": "File import không có dòng dữ liệu nào",
    "import_too_many_columns": "Dòng có nhiều cột hơn mẫu",
    "import_rejected": "File import có lỗi. Toàn bộ file bị từ chối, không có bản ghi nào được lưu",
    "import_success": "Import thành công {count} bản ghi",
    "watchlist_success": "Cập nhật Watchlist thành công",
    "watchlist_empty": "Watchlist chưa có bản ghi nào",
    "reset_success": "Đã xóa toàn bộ dữ liệu và nạp lại dữ liệu mẫu",
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS records (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    record_code      TEXT NOT NULL UNIQUE,
    subject_type     TEXT NOT NULL CHECK (subject_type IN ('Cá nhân', 'Tổ chức')),
    fullname         TEXT NOT NULL,
    id_number        TEXT,
    birth_year       TEXT,
    nationality      TEXT,
    reason           TEXT,
    active_status    TEXT NOT NULL DEFAULT 'Active'
                     CHECK (active_status IN ('Active', 'Inactive')),
    auth_status      TEXT NOT NULL DEFAULT 'Unauthorized'
                     CHECK (auth_status IN ('Unauthorized', 'Authorized', 'Rejected', 'Modified', 'Deleted')),
    pending_changes  TEXT,  -- JSON dữ liệu sửa chờ duyệt (dành cho trạng thái Modified sau này)
    created_by       TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    updated_by       TEXT,
    updated_at       TEXT,
    authorized_by    TEXT,
    authorized_at    TEXT
);

CREATE TABLE IF NOT EXISTS watchlist (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id     INTEGER NOT NULL,
    record_code   TEXT NOT NULL,
    subject_type  TEXT NOT NULL,
    fullname      TEXT NOT NULL,
    id_number     TEXT,
    birth_year    TEXT,
    nationality   TEXT,
    reason        TEXT,
    loaded_by     TEXT NOT NULL,
    loaded_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS record_actions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    record_code  TEXT NOT NULL,
    action       TEXT NOT NULL,  -- CREATE, IMPORT, UPDATE, DELETE, AUTHORIZE, REJECT
    actor        TEXT NOT NULL,
    acted_at     TEXT NOT NULL,
    note         TEXT
);

CREATE TABLE IF NOT EXISTS sequences (
    name   TEXT PRIMARY KEY,
    value  INTEGER NOT NULL
);
"""

# ---------------------------------------------------------------------------
# Sub-luồng B: sàng lọc khách hàng, Case, hộp thư giả lập
# ---------------------------------------------------------------------------
SCHEMA_B_SQL = """
CREATE TABLE IF NOT EXISTS screenings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    screening_code  TEXT NOT NULL UNIQUE,          -- SC-0001
    customer_type   TEXT NOT NULL CHECK (customer_type IN ('Cá nhân', 'Tổ chức')),
    fullname        TEXT NOT NULL,
    id_number       TEXT,
    result          TEXT NOT NULL CHECK (result IN ('HIT', 'NO-HIT')),
    case_id         INTEGER,                        -- NULL khi NO-HIT
    screened_by     TEXT NOT NULL,
    screened_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_code       TEXT NOT NULL UNIQUE,          -- CASE-0001
    screening_id    INTEGER NOT NULL,
    customer_type   TEXT NOT NULL,
    fullname        TEXT NOT NULL,
    id_number       TEXT,
    status          TEXT NOT NULL CHECK (status IN ('Chờ Maker', 'Chờ Checker', 'Cần bổ sung',
                    'Đã đóng - Hit sai', 'Đã đóng - Chấm dứt quan hệ', 'Đã đóng - Duy trì có kiểm soát')),
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_by      TEXT,
    updated_at      TEXT
);

CREATE TABLE IF NOT EXISTS case_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER NOT NULL,
    event_no        INTEGER NOT NULL,               -- số thứ tự 1, 2, 3 trong từng Case (dùng cho id eval-1, reason-1)
    record_id       INTEGER NOT NULL,
    record_code     TEXT NOT NULL,                  -- Mã bản ghi Watchlist bị trùng
    subject_type    TEXT NOT NULL,
    fullname        TEXT NOT NULL,
    id_number       TEXT,
    match_reason    TEXT NOT NULL,                  -- Trùng Số CCCD|Số ĐKKD/MST / Trùng Họ và tên|Tên tổ chức
    evaluation      TEXT NOT NULL DEFAULT 'Chưa đánh giá'
                    CHECK (evaluation IN ('Chưa đánh giá', 'Hit đúng', 'Hit sai')),
    reason          TEXT,
    UNIQUE (case_id, event_no)
);

CREATE TABLE IF NOT EXISTS case_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER NOT NULL,
    acted_at        TEXT NOT NULL,
    actor           TEXT NOT NULL,
    action          TEXT NOT NULL,
    note            TEXT
);

CREATE TABLE IF NOT EXISTS emails (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER,
    recipient       TEXT NOT NULL,
    subject         TEXT NOT NULL,
    body            TEXT NOT NULL,
    sent_at         TEXT NOT NULL
);
"""

CUSTOMER_TYPES = SUBJECT_TYPES
EVALUATIONS = ["Chưa đánh giá", "Hit đúng", "Hit sai"]
CASE_WAIT_MAKER = "Chờ Maker"
CASE_WAIT_CHECKER = "Chờ Checker"
CASE_NEED_SUPPLEMENT = "Cần bổ sung"
CASE_CLOSED_FALSE_HIT = "Đã đóng - Hit sai"
CASE_CLOSED_TERMINATE = "Đã đóng - Chấm dứt quan hệ"
CASE_CLOSED_MAINTAIN = "Đã đóng - Duy trì có kiểm soát"
CASE_STATUSES = [CASE_WAIT_MAKER, CASE_WAIT_CHECKER, CASE_NEED_SUPPLEMENT,
                 CASE_CLOSED_FALSE_HIT, CASE_CLOSED_TERMINATE, CASE_CLOSED_MAINTAIN]

# K1: tối đa số lần sàng lọc ra HIT của cùng một định danh trong 1 ngày (tương tự giới hạn số lần
# thử thất bại trong ngày). Vượt quá thì khóa sàng lọc đến hết ngày và chuyển Compliance xử lý.
MAX_HIT_PER_DAY = 3

CIF_ELIGIBLE = "Đủ điều kiện mở CIF"
CIF_PENDING = "Chờ xử lý case"
CIF_NOT_ELIGIBLE = "Không đủ điều kiện mở CIF"
CIF_ELIGIBLE_MONITOR = "Đủ điều kiện mở CIF - có theo dõi"

MSG_B = {
    "customer_type_required": "Loại khách hàng là bắt buộc",
    "customer_type_invalid": "Loại khách hàng phải là Cá nhân hoặc Tổ chức",
    "no_hit": "Không phát hiện trùng khớp với Watchlist",
    "hit": "Phát hiện {count} bản ghi trùng khớp với Watchlist. Đã tạo {case_code}",
    "screening_not_found": "Không tìm thấy lần sàng lọc",
    "case_not_found": "Không tìm thấy case",
    "action_not_allowed": "Bạn không có quyền thực hiện hành động này ở trạng thái hiện tại của case",
    "eval_required": "Vui lòng đánh giá tất cả Event",
    "event_reason_required": "Vui lòng nhập lý do cho từng Event",
    "propose_success": "Đề xuất thành công",
    "supplement_required": "Vui lòng nhập nội dung bổ sung",
    "supplement_success": "Gửi bổ sung thành công",
    "request_supplement_success": "Yêu cầu bổ sung thành công",
    "decision_reason_required": "Vui lòng nhập lý do quyết định",
    "only_all_false_hit": "Chỉ được chọn hành động này khi tất cả Event là Hit sai",
    "need_true_hit": "Chỉ được chọn hành động này khi có ít nhất 1 Event là Hit đúng",
    "close_success": "Đóng case thành công: {status}",
    "no_case": "Không tìm thấy case phù hợp",
    "no_screening": "Không tìm thấy lần sàng lọc phù hợp",
    "mailbox_empty": "Hộp thư chưa có email nào",
    "hit_existing_case": "Khách hàng đã có {case_code} đang xử lý. Không tạo Case mới",
    "limit_exceeded": ("Vượt giới hạn: khách hàng này đã bị HIT {limit} lần trong ngày {date}. "
                       "Chuyển Compliance xử lý, không sàng lọc thêm trong ngày"),
}

# Dữ liệu mẫu: (subject_type, fullname, id_number, birth_year, nationality,
#               reason, active_status, auth_status, in_watchlist)
SEED_RECORDS = [
    ("Cá nhân", "Nguyen Van A", "001234567890", "1980", "Việt Nam",
     "Nghi vấn liên quan rửa tiền", "Active", "Authorized", True),
    ("Cá nhân", "Tran Thi B", "001987654321", "1975", "Việt Nam",
     "Nằm trong danh sách cấm vận", "Active", "Authorized", True),
    ("Tổ chức", "Cong ty ABC", "0101234567", "", "Việt Nam",
     "Tổ chức có giao dịch đáng ngờ", "Active", "Authorized", True),
    ("Cá nhân", "Tran Thi B", "001555555555", "1990", "Việt Nam",
     "Trùng tên đối tượng cần theo dõi", "Active", "Authorized", True),
    ("Cá nhân", "Le Van C", "001111111111", "", "Việt Nam",
     "Đã ngừng theo dõi", "Inactive", "Authorized", False),
    ("Cá nhân", "Pham Van D", "001222222222", "", "Việt Nam",
     "Chờ duyệt", "Active", "Unauthorized", False),
    ("Cá nhân", "Do Van E", "001333333333", "", "Việt Nam",
     "Thông tin chưa đủ căn cứ", "Active", "Rejected", False),
]


# ---------------------------------------------------------------------------
# Cơ sở dữ liệu
# ---------------------------------------------------------------------------
# Đồng hồ giả lập: chỉ dùng để kiểm thử các kịch bản theo ngày mà không phải chờ qua ngày thật.
# 0 = ngày thật. /set-date?offset=1 -> hệ thống coi như đã sang ngày hôm sau. /reset-data đặt lại về 0.
SIM_DAY_OFFSET = 0


def now_dt():
    return datetime.now() + timedelta(days=SIM_DAY_OFFSET)


def now_str():
    return now_dt().strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return now_dt().strftime("%Y-%m-%d")


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if "db" not in g:
        g.db = connect_db()
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def next_record_code(conn):
    """Sinh mã tăng dần WL-0001, WL-0002, WL-0003; không tái sử dụng mã đã xóa."""
    conn.execute("UPDATE sequences SET value = value + 1 WHERE name = 'record'")
    value = conn.execute("SELECT value FROM sequences WHERE name = 'record'").fetchone()[0]
    return "WL-%04d" % value


def log_action(conn, record_code, action, actor, note=None):
    conn.execute(
        "INSERT INTO record_actions (record_code, action, actor, acted_at, note) "
        "VALUES (?, ?, ?, ?, ?)",
        (record_code, action, actor, now_str(), note))


def insert_record(conn, data, created_by, auth_status="Unauthorized",
                  authorized_by=None, authorized_at=None, action="CREATE"):
    record_code = next_record_code(conn)
    created_at = now_str()
    conn.execute(
        "INSERT INTO records (record_code, subject_type, fullname, id_number, birth_year, "
        "nationality, reason, active_status, auth_status, created_by, created_at, "
        "authorized_by, authorized_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (record_code, data["subject_type"], data["fullname"], data["id_number"],
         data["birth_year"], data["nationality"], data["reason"], data["active_status"],
         auth_status, created_by, created_at, authorized_by, authorized_at))
    log_action(conn, record_code, action, created_by)
    return record_code


def create_schema(conn):
    conn.executescript(SCHEMA_SQL)
    conn.executescript(SCHEMA_B_SQL)
    for name in ("record", "screening", "case"):
        conn.execute("INSERT OR IGNORE INTO sequences (name, value) VALUES (?, 0)", (name,))


def seed_data(conn):
    ts = now_str()
    for (subject_type, fullname, id_number, birth_year, nationality, reason,
         active_status, auth_status, in_watchlist) in SEED_RECORDS:
        data = {
            "subject_type": subject_type, "fullname": fullname, "id_number": id_number,
            "birth_year": birth_year, "nationality": nationality, "reason": reason,
            "active_status": active_status,
        }
        decided = auth_status in ("Authorized", "Rejected")
        code = insert_record(conn, data, "maker01", auth_status,
                             "checker01" if decided else None, ts if decided else None)
        if in_watchlist:
            row = conn.execute("SELECT * FROM records WHERE record_code = ?", (code,)).fetchone()
            conn.execute(
                "INSERT INTO watchlist (record_id, record_code, subject_type, fullname, id_number, "
                "birth_year, nationality, reason, loaded_by, loaded_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["id"], row["record_code"], row["subject_type"], row["fullname"],
                 row["id_number"], row["birth_year"], row["nationality"], row["reason"],
                 "checker01", ts))


def reset_database():
    conn = connect_db()
    try:
        conn.executescript(
            "DROP TABLE IF EXISTS records; DROP TABLE IF EXISTS watchlist; "
            "DROP TABLE IF EXISTS record_actions; DROP TABLE IF EXISTS sequences; "
            "DROP TABLE IF EXISTS screenings; DROP TABLE IF EXISTS cases; "
            "DROP TABLE IF EXISTS case_events; DROP TABLE IF EXISTS case_history; "
            "DROP TABLE IF EXISTS emails;")
        create_schema(conn)
        seed_data(conn)
        conn.commit()
    finally:
        conn.close()


def init_db_if_needed():
    """Tự tạo CSDL và nạp dữ liệu mẫu khi chạy lần đầu.
    Nếu file watchlist.db cũ của Sub-luồng A đã có thì giữ nguyên dữ liệu A,
    chỉ tạo thêm các bảng mới của Sub-luồng B (không cần xóa file database)."""
    conn = connect_db()
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'records'").fetchone()
        if exists:
            create_schema(conn)
            conn.commit()
    finally:
        conn.close()
    if not exists:
        reset_database()


# ---------------------------------------------------------------------------
# Đăng nhập / phân quyền
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            flash(MSG["login_required"], "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "username" not in session:
                flash(MSG["login_required"], "error")
                return redirect(url_for("login"))
            if session.get("role") != role:
                flash(MSG["no_permission"], "error")
                return redirect(url_for("records"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.context_processor
def inject_user():
    role = session.get("role")
    return {
        "current_user": session.get("username"),
        "current_role": role,
        "current_role_label": ROLE_LABELS.get(role, ""),
    }


# ---------------------------------------------------------------------------
# Kiểm tra dữ liệu bản ghi (dùng chung cho form và import)
# ---------------------------------------------------------------------------
def normalize_text(value):
    if value is None:
        return ""
    return unicodedata.normalize("NFC", str(value)).strip()


def read_record_form(form):
    data = {field: normalize_text(form.get(field, "")) for field in RECORD_FIELDS}
    if data["active_status"] == "":
        data["active_status"] = "Active"
    return data


MST_PATTERN = r"[0-9]{10}(-[0-9]{3})?"   # MST 10 số, hoặc 13 ký tự (10 số + "-" + 3 số) cho đơn vị phụ thuộc


def validate_name_and_id(subject_type, fullname, id_number):
    """Kiểm tra Họ và tên/Tên tổ chức và Số CCCD/Số ĐKKD(MST) theo Loại đối tượng.
    Trả về dict lỗi theo khóa fullname, id_number (dùng chung cho Nhập liệu, Import, Sàng lọc)."""
    errors = {}
    org = subject_type == "Tổ chức"
    if fullname == "":
        errors["fullname"] = MSG["org_name_required" if org else "fullname_required"]
    elif len(fullname) > 100:
        errors["fullname"] = MSG["org_name_too_long" if org else "fullname_too_long"]
    if id_number != "":
        pattern = MST_PATTERN if org else r"[0-9]{12}"
        if not re.fullmatch(pattern, id_number):
            errors["id_number"] = MSG["org_tax_invalid" if org else "id_number_invalid"]
    return errors


def validate_record(data):
    """Trả về dict {tên trường: thông báo lỗi}, theo thứ tự các trường trên form."""
    errors = {}
    if data["subject_type"] == "":
        errors["subject_type"] = MSG["subject_type_required"]
    elif data["subject_type"] not in SUBJECT_TYPES:
        errors["subject_type"] = MSG["subject_type_invalid"]

    errors.update(validate_name_and_id(data["subject_type"], data["fullname"], data["id_number"]))

    if data["birth_year"] != "" and not re.fullmatch(r"[0-9]{4}", data["birth_year"]):
        errors["birth_year"] = MSG["birth_year_invalid"]

    if len(data["nationality"]) > 50:
        errors["nationality"] = MSG["nationality_too_long"]

    if len(data["reason"]) > 255:
        errors["reason"] = MSG["reason_too_long"]

    if data["active_status"] not in ACTIVE_STATUSES:
        errors["active_status"] = MSG["active_status_invalid"]
    return errors


def get_record(code):
    return get_db().execute("SELECT * FROM records WHERE record_code = ?", (code,)).fetchone()


def get_selected_records(codes):
    db = get_db()
    rows = []
    for code in codes:
        row = db.execute("SELECT * FROM records WHERE record_code = ?", (code,)).fetchone()
        if row is not None:
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Routes: đăng nhập, đăng xuất, reset dữ liệu
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("records"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" and "username" in session:
        return redirect(url_for("records"))
    username = ""
    page_errors = []
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == "" or password == "":
            page_errors.append(MSG["login_empty"])
        else:
            user = USERS.get(username)
            if user is None or user["password"] != password:
                page_errors.append(MSG["login_failed"])
            else:
                session.clear()
                session["username"] = username
                session["role"] = user["role"]
                flash(MSG["login_success"], "success")
                return redirect(url_for("records"))
    return render_template("login.html", username=username, page_errors=page_errors)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash(MSG["logout_success"], "success")
    return redirect(url_for("login"))


@app.route("/reset-data", methods=["GET", "POST"])
def reset_data():
    global SIM_DAY_OFFSET
    SIM_DAY_OFFSET = 0  # đặt lại đồng hồ giả lập về ngày thật
    reset_database()
    flash(MSG["reset_success"], "success")
    if "username" in session:
        return redirect(url_for("records"))
    return redirect(url_for("login"))


@app.route("/set-date", methods=["GET", "POST"])
def set_date():
    """Chỉ dùng cho kiểm thử: /set-date?offset=N giả lập đã qua N ngày kể từ ngày thật (0 = ngày thật)."""
    global SIM_DAY_OFFSET
    raw = (request.values.get("offset") or "").strip()
    if raw != "":
        if re.fullmatch(r"[0-9]{1,3}", raw):
            SIM_DAY_OFFSET = int(raw)
            flash("Ngày giả lập hiện tại: %s (cộng %d ngày)" % (today_str(), SIM_DAY_OFFSET), "success")
        else:
            flash("Giá trị offset không hợp lệ (số nguyên từ 0 đến 999)", "error")
    else:
        flash("Ngày giả lập hiện tại: %s (cộng %d ngày)" % (today_str(), SIM_DAY_OFFSET), "success")
    if "username" in session:
        return redirect(url_for("records"))
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Routes: danh sách bản ghi (màn "Nhập liệu")
# ---------------------------------------------------------------------------
@app.route("/records")
@login_required
def records():
    search_fullname = normalize_text(request.args.get("search_fullname", ""))
    search_id_number = normalize_text(request.args.get("search_id_number", ""))
    filter_auth_status = normalize_text(request.args.get("filter_auth_status", ""))
    if filter_auth_status not in AUTH_STATUSES:
        filter_auth_status = ""

    rows = get_db().execute("SELECT * FROM records ORDER BY id").fetchall()
    if search_fullname:
        key = search_fullname.casefold()
        rows = [r for r in rows if key in normalize_text(r["fullname"]).casefold()]
    if search_id_number:
        rows = [r for r in rows if search_id_number in (r["id_number"] or "")]
    if filter_auth_status:
        rows = [r for r in rows if r["auth_status"] == filter_auth_status]

    return render_template(
        "records.html", rows=rows, auth_statuses=AUTH_STATUSES,
        search_fullname=search_fullname, search_id_number=search_id_number,
        filter_auth_status=filter_auth_status, no_result_message=MSG["no_result"])


@app.route("/records/<code>")
@login_required
def record_detail(code):
    row = get_record(code)
    if row is None:
        flash(MSG["record_not_found"], "error")
        return redirect(url_for("records"))
    in_watchlist = get_db().execute(
        "SELECT COUNT(*) FROM watchlist WHERE record_code = ?", (code,)).fetchone()[0] > 0
    return render_template("record_detail.html", row=row, in_watchlist=in_watchlist)


# ---------------------------------------------------------------------------
# Routes: Maker - thêm, sửa, xóa
# ---------------------------------------------------------------------------
def empty_form_data():
    data = {field: "" for field in RECORD_FIELDS}
    data["active_status"] = "Active"
    return data


@app.route("/records/new", methods=["GET", "POST"])
@role_required("maker")
def record_new():
    data = empty_form_data()
    errors = {}
    if request.method == "POST":
        data = read_record_form(request.form)
        errors = validate_record(data)
        if not errors:
            db = get_db()
            code = insert_record(db, data, session["username"])
            db.commit()
            flash(MSG["save_success"], "success")
            flash(code, "saved_code")
            return redirect(url_for("records"))
    info = {"record_code": "", "auth_status": "Unauthorized",
            "created_by": session["username"], "created_at": ""}
    return render_template("record_form.html", mode="new", data=data, info=info,
                           errors=errors, page_errors=list(errors.values()),
                           subject_types=SUBJECT_TYPES, active_statuses=ACTIVE_STATUSES)


@app.route("/records/edit-selected", methods=["POST"])
@role_required("maker")
def record_edit_selected():
    codes = request.form.getlist("selected_codes")
    if len(codes) == 0:
        flash(MSG["select_required"], "error")
        return redirect(url_for("records"))
    if len(codes) > 1:
        flash(MSG["select_one_to_edit"], "error")
        return redirect(url_for("records"))
    return redirect(url_for("record_edit", code=codes[0]))


@app.route("/records/<code>/edit", methods=["GET", "POST"])
@role_required("maker")
def record_edit(code):
    row = get_record(code)
    if row is None:
        flash(MSG["record_not_found"], "error")
        return redirect(url_for("records"))
    if row["auth_status"] not in EDITABLE_STATUSES:
        flash(MSG["edit_not_allowed"] + ": " + code, "error")
        return redirect(url_for("records"))

    data = {field: (row[field] or "") for field in RECORD_FIELDS}
    errors = {}
    if request.method == "POST":
        data = read_record_form(request.form)
        errors = validate_record(data)
        if not errors:
            db = get_db()
            # Sửa bản ghi Unauthorized -> vẫn Unauthorized; Rejected -> về Unauthorized
            db.execute(
                "UPDATE records SET subject_type = ?, fullname = ?, id_number = ?, birth_year = ?, "
                "nationality = ?, reason = ?, active_status = ?, auth_status = 'Unauthorized', "
                "authorized_by = NULL, authorized_at = NULL, updated_by = ?, updated_at = ? "
                "WHERE record_code = ?",
                (data["subject_type"], data["fullname"], data["id_number"], data["birth_year"],
                 data["nationality"], data["reason"], data["active_status"],
                 session["username"], now_str(), code))
            log_action(db, code, "UPDATE", session["username"],
                       "Trạng thái trước khi sửa: " + row["auth_status"])
            db.commit()
            flash(MSG["save_success"], "success")
            flash(code, "saved_code")
            return redirect(url_for("records"))
    info = {"record_code": row["record_code"], "auth_status": row["auth_status"],
            "created_by": row["created_by"], "created_at": row["created_at"]}
    return render_template("record_form.html", mode="edit", data=data, info=info,
                           errors=errors, page_errors=list(errors.values()),
                           subject_types=SUBJECT_TYPES, active_statuses=ACTIVE_STATUSES)


@app.route("/records/delete", methods=["POST"])
@role_required("maker")
def record_delete():
    codes = request.form.getlist("selected_codes")
    if len(codes) == 0:
        flash(MSG["select_required"], "error")
        return redirect(url_for("records"))
    rows = get_selected_records(codes)
    if len(rows) != len(codes):
        flash(MSG["record_not_found"], "error")
        return redirect(url_for("records"))
    not_allowed = [r["record_code"] for r in rows if r["auth_status"] not in EDITABLE_STATUSES]
    if not_allowed:
        flash(MSG["delete_not_allowed"] + ": " + ", ".join(not_allowed), "error")
        return redirect(url_for("records"))
    db = get_db()
    for r in rows:
        # Unauthorized / Rejected -> xóa ngay (chưa làm trạng thái Deleted)
        db.execute("DELETE FROM records WHERE record_code = ?", (r["record_code"],))
        log_action(db, r["record_code"], "DELETE", session["username"],
                   "Trạng thái trước khi xóa: " + r["auth_status"])
    db.commit()
    flash(MSG["delete_success"], "success")
    return redirect(url_for("records"))


# ---------------------------------------------------------------------------
# Routes: Maker - import file .xlsx / .csv
# ---------------------------------------------------------------------------
def cell_to_text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return normalize_text(value)


def read_csv_rows(content):
    text = None
    for encoding in ("utf-8-sig", "cp1258"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("encoding")
    text = unicodedata.normalize("NFC", text)
    lines = text.splitlines()
    first_line = lines[0] if lines else ""
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    return [[normalize_text(cell) for cell in row] for row in reader]


def read_xlsx_rows(content):
    workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        sheet = workbook.worksheets[0]
        return [[cell_to_text(v) for v in row] for row in sheet.iter_rows(values_only=True)]
    finally:
        workbook.close()


def strip_trailing_empty(row):
    row = list(row)
    while row and row[-1] == "":
        row.pop()
    return row


@app.route("/records/import", methods=["GET", "POST"])
@role_required("maker")
def record_import():
    page_errors = []
    import_errors = []  # danh sách (số dòng, thông báo lỗi)
    if request.method == "POST":
        uploaded = request.files.get("import_file")
        filename = uploaded.filename if uploaded else ""
        if not filename:
            page_errors.append(MSG["import_file_required"])
        else:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in (".xlsx", ".csv"):
                page_errors.append(MSG["import_file_type"])
            else:
                content = uploaded.read()
                try:
                    rows = read_xlsx_rows(content) if ext == ".xlsx" else read_csv_rows(content)
                except Exception:
                    rows = None
                if rows is None:
                    page_errors.append(MSG["import_unreadable"])
                else:
                    page_errors, import_errors, valid_rows = check_import_rows(rows)
                    if not page_errors and not import_errors:
                        db = get_db()
                        for data in valid_rows:
                            insert_record(db, data, session["username"], action="IMPORT")
                        db.commit()
                        flash(MSG["import_success"].format(count=len(valid_rows)), "success")
                        return redirect(url_for("records"))
    return render_template("import.html", page_errors=page_errors,
                           import_errors=import_errors, import_columns=IMPORT_COLUMNS)


def check_import_rows(rows):
    """Kiểm tra toàn bộ file. Trả về (lỗi chung, lỗi theo dòng, các dòng hợp lệ)."""
    if not rows or strip_trailing_empty(rows[0]) != IMPORT_COLUMNS:
        return [MSG["import_header_invalid"]], [], []
    import_errors = []
    valid_rows = []
    for line_no, row in enumerate(rows[1:], start=2):
        row = strip_trailing_empty(row)
        if not row:
            continue  # bỏ qua dòng trống
        if len(row) > len(IMPORT_COLUMNS):
            import_errors.append((line_no, MSG["import_too_many_columns"]))
            continue
        row = row + [""] * (len(IMPORT_COLUMNS) - len(row))
        data = dict(zip(RECORD_FIELDS, row))
        if data["active_status"] == "":
            data["active_status"] = "Active"
        errors = validate_record(data)
        for message in errors.values():
            import_errors.append((line_no, message))
        if not errors:
            valid_rows.append(data)
    if not import_errors and not valid_rows:
        return [MSG["import_empty"]], [], []
    if import_errors:
        return [MSG["import_rejected"]], import_errors, []
    return [], [], valid_rows


@app.route("/records/import/template.csv")
@login_required
def import_template_csv():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(IMPORT_COLUMNS)
    data = buffer.getvalue().encode("utf-8-sig")  # có BOM để Excel hiển thị đúng tiếng Việt
    return send_file(io.BytesIO(data), mimetype="text/csv", as_attachment=True,
                     download_name="mau_import_watchlist.csv")


@app.route("/records/import/template.xlsx")
@login_required
def import_template_xlsx():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Import"
    sheet.append(IMPORT_COLUMNS)
    for col in ("C", "D"):  # Số CCCD, Năm sinh để dạng Text để giữ số 0 ở đầu
        for row in range(1, 1001):
            sheet[f"{col}{row}"].number_format = "@"
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="mau_import_watchlist.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ---------------------------------------------------------------------------
# Routes: Checker - Authorize / Reject
# ---------------------------------------------------------------------------
def change_auth_status(new_status, success_message, action):
    codes = request.form.getlist("selected_codes")
    if len(codes) == 0:
        flash(MSG["select_required"], "error")
        return redirect(url_for("records"))
    rows = get_selected_records(codes)
    if len(rows) != len(codes):
        flash(MSG["record_not_found"], "error")
        return redirect(url_for("records"))
    not_allowed = [r["record_code"] for r in rows if r["auth_status"] != "Unauthorized"]
    if not_allowed:
        flash(MSG["authorize_not_allowed"] + ": " + ", ".join(not_allowed), "error")
        return redirect(url_for("records"))
    db = get_db()
    ts = now_str()
    for r in rows:
        db.execute(
            "UPDATE records SET auth_status = ?, authorized_by = ?, authorized_at = ? "
            "WHERE record_code = ?",
            (new_status, session["username"], ts, r["record_code"]))
        log_action(db, r["record_code"], action, session["username"])
    db.commit()
    flash(success_message, "success")
    return redirect(url_for("records"))


@app.route("/records/authorize", methods=["POST"])
@role_required("checker")
def record_authorize():
    return change_auth_status("Authorized", MSG["authorize_success"], "AUTHORIZE")


@app.route("/records/reject", methods=["POST"])
@role_required("checker")
def record_reject():
    return change_auth_status("Rejected", MSG["reject_success"], "REJECT")


# ---------------------------------------------------------------------------
# Routes: Watchlist
# ---------------------------------------------------------------------------
@app.route("/watchlist")
@login_required
def watchlist():
    rows = get_db().execute("SELECT * FROM watchlist ORDER BY record_id").fetchall()
    return render_template("watchlist.html", rows=rows, empty_message=MSG["watchlist_empty"])


@app.route("/watchlist/update", methods=["POST"])
@role_required("checker")
def watchlist_update():
    db = get_db()
    ts = now_str()
    db.execute("DELETE FROM watchlist")
    # Chỉ nạp bản ghi Authorized + Active (không nạp Unauthorized, Rejected, Inactive)
    db.execute(
        "INSERT INTO watchlist (record_id, record_code, subject_type, fullname, id_number, "
        "birth_year, nationality, reason, loaded_by, loaded_at) "
        "SELECT id, record_code, subject_type, fullname, id_number, birth_year, nationality, "
        "reason, ?, ? FROM records WHERE auth_status = 'Authorized' AND active_status = 'Active' "
        "ORDER BY id",
        (session["username"], ts))
    db.commit()
    flash(MSG["watchlist_success"], "success")
    return redirect(url_for("watchlist"))


# ===========================================================================
# SUB-LUỒNG B: SÀNG LỌC KHÁCH HÀNG, XỬ LÝ CASE, HỘP THƯ GIẢ LẬP
# ===========================================================================
def normalize_name(value):
    """Chuẩn hóa họ tên để so khớp:
    - bỏ dấu tiếng Việt (kể cả chữ đ/Đ -> d),
    - chuyển chữ thường,
    - bỏ khoảng trắng thừa ở đầu, cuối và giữa các từ.
    Ví dụ: "  NGUYỄN  VĂN   A " -> "nguyen van a"."""
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")  # bỏ dấu
    text = text.replace("đ", "d").replace("Đ", "D")
    return " ".join(text.lower().split())


def find_watchlist_matches(conn, customer_type, fullname, id_number):
    """Quy tắc so khớp khách hàng với Watchlist (Sub-luồng B).

    - Chỉ so với bản ghi đang nằm trong bảng watchlist (do Checker "Cập nhật Watchlist"
      ở Sub-luồng A) mà bản ghi gốc vẫn Authorized + Active, và cùng Loại đối tượng
      với Loại khách hàng.
    - HIT khi thỏa 1 trong 2 điều kiện:
        (1) Số CCCD (Cá nhân) / Số ĐKKD-MST (Tổ chức) trùng, chỉ xét khi cả hai bên đều có, HOẶC
        (2) Họ và tên / Tên tổ chức trùng sau khi chuẩn hóa bằng normalize_name().
    - Mỗi bản ghi Watchlist trùng là 1 phần tử trong kết quả (= 1 Event).

    Trả về danh sách dict: record_id, record_code, subject_type, fullname, id_number, match_reason.
    """
    rows = conn.execute(
        "SELECT w.record_id, w.record_code, w.subject_type, w.fullname, w.id_number "
        "FROM watchlist w JOIN records r ON r.id = w.record_id "
        "WHERE r.auth_status = 'Authorized' AND r.active_status = 'Active' "
        "AND w.subject_type = ? ORDER BY w.record_id",
        (customer_type,)).fetchall()
    key_name = normalize_name(fullname)
    key_id = (id_number or "").strip()
    id_label = "Số ĐKKD/MST" if customer_type == "Tổ chức" else "Số CCCD"
    name_label = "Tên tổ chức" if customer_type == "Tổ chức" else "Họ và tên"
    matches = []
    for row in rows:
        reasons = []
        if key_id and (row["id_number"] or "") == key_id:
            reasons.append("Trùng " + id_label)
        if key_name and normalize_name(row["fullname"]) == key_name:
            reasons.append("Trùng " + name_label)
        if reasons:
            matches.append({
                "record_id": row["record_id"], "record_code": row["record_code"],
                "subject_type": row["subject_type"], "fullname": row["fullname"],
                "id_number": row["id_number"] or "", "match_reason": ", ".join(reasons),
            })
    return matches


def cif_decision(result, case_status):
    """Quyết định mở CIF tính theo kết quả sàng lọc và trạng thái Case hiện tại."""
    if result == "NO-HIT":
        return CIF_ELIGIBLE
    if case_status == CASE_CLOSED_FALSE_HIT:
        return CIF_ELIGIBLE
    if case_status == CASE_CLOSED_TERMINATE:
        return CIF_NOT_ELIGIBLE
    if case_status == CASE_CLOSED_MAINTAIN:
        return CIF_ELIGIBLE_MONITOR
    return CIF_PENDING  # Chờ Maker, Chờ Checker, Cần bổ sung


def next_code(conn, name, prefix):
    conn.execute("UPDATE sequences SET value = value + 1 WHERE name = ?", (name,))
    value = conn.execute("SELECT value FROM sequences WHERE name = ?", (name,)).fetchone()[0]
    return "%s-%04d" % (prefix, value)


def add_case_history(conn, case_id, actor, action, note=None):
    conn.execute(
        "INSERT INTO case_history (case_id, acted_at, actor, action, note) VALUES (?, ?, ?, ?, ?)",
        (case_id, now_str(), actor, action, note))


def send_mock_email(conn, case_id, recipient, subject, body_lines):
    """Hộp thư giả lập: chỉ ghi vào bảng emails, không gửi email thật.
    body_lines là danh sách các dòng nội dung; dòng "Thời gian gửi" được thêm tự động."""
    sent_at = now_str()
    body = "\n".join(list(body_lines) + ["Thời gian gửi: " + sent_at])
    conn.execute(
        "INSERT INTO emails (case_id, recipient, subject, body, sent_at) VALUES (?, ?, ?, ?, ?)",
        (case_id, recipient, subject, body, sent_at))


def identity_key(customer_type, fullname, id_number):
    """Định danh dùng cho K1/K2: Số CCCD/Số ĐKKD nếu có, nếu không thì tên đã chuẩn hóa."""
    id_number = (id_number or "").strip()
    if id_number:   # Cá nhân: Số CCCD; Tổ chức: Số ĐKKD/MST (loại KH đã tách riêng khi tra K1/K2)
        return ("id", id_number)
    return ("name", normalize_name(fullname))


def count_hits_today(conn, customer_type, key):
    """K1: số lần sàng lọc ra HIT của cùng định danh trong ngày hiện tại (theo đồng hồ giả lập)."""
    rows = conn.execute(
        "SELECT fullname, id_number FROM screenings "
        "WHERE customer_type = ? AND result = 'HIT' AND substr(screened_at, 1, 10) = ?",
        (customer_type, today_str())).fetchall()
    return sum(1 for r in rows
               if identity_key(customer_type, r["fullname"], r["id_number"]) == key)


def find_open_case(conn, customer_type, key):
    """K2: Case chưa đóng của cùng định danh (nếu có), để không tạo Case thứ hai."""
    rows = conn.execute(
        "SELECT * FROM cases WHERE customer_type = ? AND status IN (?, ?, ?) ORDER BY id",
        (customer_type, CASE_WAIT_MAKER, CASE_WAIT_CHECKER, CASE_NEED_SUPPLEMENT)).fetchall()
    for r in rows:
        if identity_key(customer_type, r["fullname"], r["id_number"]) == key:
            return r
    return None


def read_screening_form(form):
    data = {
        "customer_type": normalize_text(form.get("customer_type", "")),
        "fullname": normalize_text(form.get("fullname", "")),
        "id_number": normalize_text(form.get("id_number", "")),
    }
    return data


def validate_screening(data):
    errors = {}
    if data["customer_type"] == "":
        errors["customer_type"] = MSG_B["customer_type_required"]
    elif data["customer_type"] not in CUSTOMER_TYPES:
        errors["customer_type"] = MSG_B["customer_type_invalid"]
    errors.update(validate_name_and_id(data["customer_type"], data["fullname"], data["id_number"]))
    return errors


def load_screening_result(code):
    db = get_db()
    sc = db.execute(
        "SELECT s.*, c.case_code, c.status AS case_status FROM screenings s "
        "LEFT JOIN cases c ON c.id = s.case_id WHERE s.screening_code = ?", (code,)).fetchone()
    if sc is None:
        return None
    events = []
    if sc["case_id"]:
        events = db.execute("SELECT * FROM case_events WHERE case_id = ? ORDER BY event_no",
                            (sc["case_id"],)).fetchall()
    return {"sc": sc, "events": events, "cif": cif_decision(sc["result"], sc["case_status"])}


@app.route("/screening", methods=["GET", "POST"])
@login_required
def screening():
    data = {"customer_type": "", "fullname": "", "id_number": ""}
    errors = {}
    if request.method == "POST":
        if session.get("role") != "maker":
            flash(MSG["no_permission"], "error")
            return redirect(url_for("screening"))
        data = read_screening_form(request.form)
        errors = validate_screening(data)
        db = get_db()
        matches = []
        key = None
        if not errors:
            matches = find_watchlist_matches(db, data["customer_type"], data["fullname"],
                                             data["id_number"])
            key = identity_key(data["customer_type"], data["fullname"], data["id_number"])
            # K1: chặn khi cùng định danh đã bị HIT đủ số lần cho phép trong ngày
            if matches and count_hits_today(db, data["customer_type"], key) >= MAX_HIT_PER_DAY:
                errors = {"_": MSG_B["limit_exceeded"].format(limit=MAX_HIT_PER_DAY,
                                                              date=today_str())}
        if not errors:
            user = session["username"]
            ts = now_str()
            screening_code = next_code(db, "screening", "SC")
            result = "HIT" if matches else "NO-HIT"
            cur = db.execute(
                "INSERT INTO screenings (screening_code, customer_type, fullname, id_number, result, "
                "case_id, screened_by, screened_at) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)",
                (screening_code, data["customer_type"], data["fullname"], data["id_number"],
                 result, user, ts))
            screening_id = cur.lastrowid
            open_case = find_open_case(db, data["customer_type"], key) if matches else None
            if open_case is not None:
                # K2: đã có Case chưa đóng của cùng định danh -> gắn lần sàng lọc vào Case đó
                db.execute("UPDATE screenings SET case_id = ? WHERE id = ?",
                           (open_case["id"], screening_id))
                add_case_history(db, open_case["id"], user, "Sàng lọc lặp",
                                 "Sàng lọc %s HIT lặp lại, không tạo Case mới" % screening_code)
                flash(MSG_B["hit_existing_case"].format(case_code=open_case["case_code"]), "success")
            elif matches:
                # Mỗi lần sàng lọc HIT tạo đúng 1 Case; mỗi bản ghi trùng = 1 Event
                case_code = next_code(db, "case", "CASE")
                cur = db.execute(
                    "INSERT INTO cases (case_code, screening_id, customer_type, fullname, id_number, "
                    "status, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (case_code, screening_id, data["customer_type"], data["fullname"],
                     data["id_number"], CASE_WAIT_MAKER, user, ts))
                case_id = cur.lastrowid
                for no, m in enumerate(matches, start=1):
                    db.execute(
                        "INSERT INTO case_events (case_id, event_no, record_id, record_code, "
                        "subject_type, fullname, id_number, match_reason) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (case_id, no, m["record_id"], m["record_code"], m["subject_type"],
                         m["fullname"], m["id_number"], m["match_reason"]))
                db.execute("UPDATE screenings SET case_id = ? WHERE id = ?", (case_id, screening_id))
                add_case_history(db, case_id, user, "Tạo case",
                                 "Sàng lọc %s HIT %d bản ghi Watchlist: %s" % (
                                     screening_code, len(matches),
                                     ", ".join(m["record_code"] for m in matches)))
                flash(MSG_B["hit"].format(count=len(matches), case_code=case_code), "success")
            else:
                flash(MSG_B["no_hit"], "success")
            db.commit()
            return redirect(url_for("screening", sc=screening_code))

    result = None
    sc_code = request.args.get("sc", "").strip()
    if sc_code:
        result = load_screening_result(sc_code)
        if result is None:
            errors = {"_": MSG_B["screening_not_found"]}
    return render_template("screening.html", data=data, errors=errors,
                           page_errors=list(errors.values()), result=result,
                           customer_types=CUSTOMER_TYPES)


@app.route("/screening-history")
@login_required
def screening_history():
    search_fullname = normalize_text(request.args.get("search_fullname", ""))
    rows = get_db().execute(
        "SELECT s.*, c.case_code, c.status AS case_status FROM screenings s "
        "LEFT JOIN cases c ON c.id = s.case_id ORDER BY s.id").fetchall()
    if search_fullname:
        key = search_fullname.casefold()
        rows = [r for r in rows if key in normalize_text(r["fullname"]).casefold()]
    items = [{"row": r, "cif": cif_decision(r["result"], r["case_status"])} for r in rows]
    return render_template("screening_history.html", items=items, search_fullname=search_fullname,
                           no_result_message=MSG_B["no_screening"])


@app.route("/cases")
@login_required
def cases():
    filter_case_status = normalize_text(request.args.get("filter_case_status", ""))
    if filter_case_status not in CASE_STATUSES:
        filter_case_status = ""
    sql = ("SELECT c.*, (SELECT COUNT(*) FROM case_events e WHERE e.case_id = c.id) AS event_count "
           "FROM cases c")
    params = ()
    if filter_case_status:
        sql += " WHERE c.status = ?"
        params = (filter_case_status,)
    rows = get_db().execute(sql + " ORDER BY c.id", params).fetchall()
    return render_template("cases.html", rows=rows, case_statuses=CASE_STATUSES,
                           filter_case_status=filter_case_status,
                           no_result_message=MSG_B["no_case"])


def case_permissions(status, role):
    """Hành động được phép theo vai trò và trạng thái Case."""
    return {
        "maker_evaluate": role == "maker" and status == CASE_WAIT_MAKER,
        "maker_supplement": role == "maker" and status == CASE_NEED_SUPPLEMENT,
        "checker_decide": role == "checker" and status == CASE_WAIT_CHECKER,
    }


def load_case(code):
    db = get_db()
    case = db.execute(
        "SELECT c.*, s.screening_code FROM cases c JOIN screenings s ON s.id = c.screening_id "
        "WHERE c.case_code = ?", (code,)).fetchone()
    if case is None:
        return None, [], []
    events = db.execute("SELECT * FROM case_events WHERE case_id = ? ORDER BY event_no",
                        (case["id"],)).fetchall()
    history = db.execute("SELECT * FROM case_history WHERE case_id = ? ORDER BY id",
                         (case["id"],)).fetchall()
    return case, events, history


def render_case(code, page_errors=None, form_events=None, supplement_note="", decision_reason=""):
    case, events, history = load_case(code)
    if case is None:
        flash(MSG_B["case_not_found"], "error")
        return redirect(url_for("cases"))
    # form_events: giá trị Maker vừa nhập (giữ lại khi có lỗi)
    event_items = []
    for e in events:
        value = (form_events or {}).get(e["event_no"])
        event_items.append({
            "e": e,
            "evaluation": value["evaluation"] if value else e["evaluation"],
            "reason": value["reason"] if value else (e["reason"] or ""),
        })
    return render_template(
        "case_detail.html", case=case, event_items=event_items, history=history,
        perms=case_permissions(case["status"], session.get("role")),
        evaluations=EVALUATIONS, page_errors=page_errors or [],
        supplement_note=supplement_note, decision_reason=decision_reason,
        cif=cif_decision("HIT", case["status"]))


@app.route("/cases/<code>")
@login_required
def case_detail(code):
    return render_case(code)


CHECKER_CLOSE_ACTIONS = {
    # action: (trạng thái mới, cần tất cả Hit sai?, tiêu đề email hoặc None, kết luận trong email)
    "close_false_hit": (CASE_CLOSED_FALSE_HIT, True, None, None),
    "close_terminate": (CASE_CLOSED_TERMINATE, False,
                        "[Demo AML] Case {code} - Hit đúng, chấm dứt quan hệ",
                        "Hit đúng. Chấm dứt quan hệ với khách hàng."),
    "close_maintain": (CASE_CLOSED_MAINTAIN, False,
                       "[Demo AML] Case {code} - Hit đúng, duy trì có kiểm soát",
                       "Hit đúng. Duy trì quan hệ với khách hàng, kèm theo dõi (có kiểm soát)."),
}
ACTION_LABELS = {
    "propose": "Đề xuất",
    "send_supplement": "Gửi bổ sung",
    "request_supplement": "Yêu cầu bổ sung",
    "close_false_hit": "Đóng - Hit sai",
    "close_terminate": "Đóng - Chấm dứt quan hệ",
    "close_maintain": "Đóng - Duy trì có kiểm soát",
}


@app.route("/cases/<code>/action", methods=["POST"])
@login_required
def case_action(code):
    case, events, _ = load_case(code)
    if case is None:
        flash(MSG_B["case_not_found"], "error")
        return redirect(url_for("cases"))
    action = request.form.get("action", "")
    user = session["username"]
    perms = case_permissions(case["status"], session.get("role"))
    allowed = {
        "propose": perms["maker_evaluate"],
        "send_supplement": perms["maker_supplement"],
        "request_supplement": perms["checker_decide"],
        "close_false_hit": perms["checker_decide"],
        "close_terminate": perms["checker_decide"],
        "close_maintain": perms["checker_decide"],
    }
    if not allowed.get(action, False):
        # Server chặn cả khi gọi trực tiếp route mà không qua nút trên giao diện
        flash(MSG_B["action_not_allowed"], "error")
        return redirect(url_for("case_detail", code=code))

    db = get_db()
    ts = now_str()

    if action == "propose":
        form_events = {}
        for e in events:
            n = e["event_no"]
            evaluation = normalize_text(request.form.get("eval-%d" % n, ""))
            if evaluation not in EVALUATIONS:
                evaluation = "Chưa đánh giá"
            form_events[n] = {"evaluation": evaluation,
                              "reason": normalize_text(request.form.get("reason-%d" % n, ""))}
        errors = []
        if any(v["evaluation"] == "Chưa đánh giá" for v in form_events.values()):
            errors.append(MSG_B["eval_required"])
        if any(v["reason"] == "" for v in form_events.values()):
            errors.append(MSG_B["event_reason_required"])
        if errors:
            return render_case(code, page_errors=errors, form_events=form_events)
        notes = []
        for n, v in form_events.items():
            db.execute("UPDATE case_events SET evaluation = ?, reason = ? "
                       "WHERE case_id = ? AND event_no = ?",
                       (v["evaluation"], v["reason"], case["id"], n))
            record_code = next(e["record_code"] for e in events if e["event_no"] == n)
            notes.append("Event %d (%s): %s - %s" % (n, record_code, v["evaluation"], v["reason"]))
        db.execute("UPDATE cases SET status = ?, updated_by = ?, updated_at = ? WHERE id = ?",
                   (CASE_WAIT_CHECKER, user, ts, case["id"]))
        add_case_history(db, case["id"], user, ACTION_LABELS[action], "; ".join(notes))
        send_mock_email(
            db, case["id"], "checker01", "[Demo AML] Case %s chờ phê duyệt" % code,
            ["Mã case: %s" % code,
             "Khách hàng: %s" % case["fullname"],
             "Case đã được Maker (%s) đề xuất và đang chờ Checker phê duyệt." % user])
        db.commit()
        flash(MSG_B["propose_success"], "success")
        return redirect(url_for("case_detail", code=code))

    if action == "send_supplement":
        note = normalize_text(request.form.get("supplement_note", ""))
        if note == "":
            return render_case(code, page_errors=[MSG_B["supplement_required"]])
        db.execute("UPDATE cases SET status = ?, updated_by = ?, updated_at = ? WHERE id = ?",
                   (CASE_WAIT_CHECKER, user, ts, case["id"]))
        add_case_history(db, case["id"], user, ACTION_LABELS[action], note)  # không gửi email
        db.commit()
        flash(MSG_B["supplement_success"], "success")
        return redirect(url_for("case_detail", code=code))

    decision_reason = normalize_text(request.form.get("decision_reason", ""))

    if action == "request_supplement":
        if decision_reason == "":
            return render_case(code, page_errors=[MSG_B["decision_reason_required"]])
        db.execute("UPDATE cases SET status = ?, updated_by = ?, updated_at = ? WHERE id = ?",
                   (CASE_NEED_SUPPLEMENT, user, ts, case["id"]))
        add_case_history(db, case["id"], user, ACTION_LABELS[action], decision_reason)
        send_mock_email(
            db, case["id"], "maker01", "[Demo AML] Case %s cần bổ sung thông tin" % code,
            ["Mã case: %s" % code,
             "Khách hàng: %s" % case["fullname"],
             "Ghi chú của Checker: %s" % decision_reason,
             "Đề nghị Maker bổ sung thông tin cho case và gửi lại để Checker phê duyệt."])
        db.commit()
        flash(MSG_B["request_supplement_success"], "success")
        return redirect(url_for("case_detail", code=code))

    # Các hành động đóng Case
    new_status, need_all_false, email_subject, email_conclusion = CHECKER_CLOSE_ACTIONS[action]
    evaluations = [e["evaluation"] for e in events]
    errors = []
    if need_all_false and not all(v == "Hit sai" for v in evaluations):
        errors.append(MSG_B["only_all_false_hit"])
    if not need_all_false and "Hit đúng" not in evaluations:
        errors.append(MSG_B["need_true_hit"])
    if decision_reason == "":
        errors.append(MSG_B["decision_reason_required"])
    if errors:
        return render_case(code, page_errors=errors, decision_reason=decision_reason)
    db.execute("UPDATE cases SET status = ?, updated_by = ?, updated_at = ? WHERE id = ?",
               (new_status, user, ts, case["id"]))
    add_case_history(db, case["id"], user, ACTION_LABELS[action], decision_reason)
    if email_subject:
        send_mock_email(
            db, case["id"], "maker01", email_subject.format(code=code),
            ["Mã case: %s" % code,
             "Khách hàng: %s" % case["fullname"],
             "Kết luận: %s" % email_conclusion,
             "Lý do quyết định của Checker: %s" % decision_reason])
    db.commit()
    flash(MSG_B["close_success"].format(status=new_status), "success")
    return redirect(url_for("case_detail", code=code))


@app.route("/mailbox")
@login_required
def mailbox():
    # Mỗi user chỉ thấy email gửi cho mình
    rows = get_db().execute("SELECT * FROM emails WHERE recipient = ? ORDER BY id DESC",
                            (session["username"],)).fetchall()
    return render_template("mailbox.html", rows=rows, empty_message=MSG_B["mailbox_empty"])


# Tạo CSDL ngay khi nạp module (kể cả khi chạy bằng "flask run")
init_db_if_needed()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
