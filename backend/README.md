# Hệ thống Quản lý Dự án & Phỏng vấn AI (Backend API)

Bộ backend hoàn chỉnh được xây dựng bằng **FastAPI**, **SQLAlchemy 2.0**, **Pydantic v2** và **JWT Authentication (OAuth2)**.

---

## Danh Sách Nhiệm Vụ Đã Hoàn Thành (11/11 Tasks)

| STT | Nhiệm vụ | Điểm | Loại | Endpoint chính / Thành phần |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Project – Danh sách dự án** | 3 | Chính | `GET /projects`, `POST /projects`, `GET /projects/{id}`, `PUT /projects/{id}`, `DELETE /projects/{id}` |
| **2** | **User – Quên/Reset mật khẩu** | 5 | Bonus | `POST /auth/forgot-password`, `POST /auth/reset-password` |
| **3** | **User – Đổi mật khẩu** | 3 | Bonus | `POST /auth/change-password` |
| **4** | **User – Profile** | 2 | Chính | `GET /users/profile`, `PUT /users/profile`, `GET /users/{id}` |
| **5** | **Authentication – Password** | 2 | Chính | `app/core/security.py` (Băm mật khẩu bcrypt, kiểm tra chính sách độ mạnh tối thiểu 6 ký tự) |
| **6** | **Authentication – Login** | 3 | Chính | `POST /auth/login` (chuẩn OAuth2 form) & `POST /auth/login-json` (JSON body) |
| **7** | **Authorization – Role guard** | 3 | Chính | `app/dependencies/auth.py` (`require_role("admin", "manager")` bảo vệ các endpoint nhạy cảm) |
| **8** | **User – Danh sách user** | 3 | Chính | `GET /users` (phân trang `skip`, `limit`, tìm kiếm `search`, lọc theo `role`) |
| **9** | **Authentication – Register** | 3 | Chính | `POST /auth/register` (đăng ký tài khoản, mã hóa mật khẩu, kiểm tra trùng lặp) |
| **10** | **Refresh token** | 2 | Bonus | `POST /auth/refresh` (cấp cặp Access Token và Refresh Token mới) |
| **11** | **Authentication – Current user** | 3 | Chính | `GET /auth/me` (lấy thông tin người dùng đang đăng nhập từ JWT Bearer token) |

---

## 1. Cài đặt và kích hoạt môi trường

Mở terminal PowerShell tại thư mục dự án:

```powershell
# Tạo môi trường ảo nếu chưa có
py -m venv .venv

# Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# Cài đặt các thư viện
pip install -r requirements.txt
```

---

## 2. Cấu hình cơ sở dữ liệu

Dự án mặc định sử dụng SQLite (`sqlite:///./project_management.db`) để có thể chạy và kiểm thử ngay lập tức mà không cần cài đặt thêm server.

Nếu muốn kết nối **MySQL**, tạo file `.env` tại thư mục gốc:

```dotenv
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/project_management
SECRET_KEY=your-super-long-random-secret-key-at-least-32-chars
```

Khi khởi động ứng dụng, bảng dữ liệu và tài khoản quản trị viên mặc định sẽ tự động được tạo:
- **Tài khoản mẫu**: `admin@example.com`
- **Mật khẩu**: `Admin@123456`

---

## 3. Chạy ứng dụng

Từ thư mục gốc khi môi trường ảo đang được kích hoạt:

```powershell
uvicorn app.main:app --reload
```

Truy cập tài liệu API tương tác tại:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

Bạn có thể ấn nút **Authorize** ở góc phải Swagger UI và đăng nhập với tài khoản `admin@example.com` / `Admin@123456` để gọi trực tiếp các API yêu cầu xác thực.

---

## 4. Chạy kiểm thử tự động (Unit / Integration Tests)

Dự án đi kèm bộ test kiểm thử đầy đủ toàn bộ 11 nhiệm vụ:

```powershell
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe -m pytest -v tests/test_all_tasks.py
```


# Hướng Dẫn Setup & Triển Khai Dự Án TEAM12_AI-Interview (FastAPI + MySQL)

## 1. Yêu cầu hệ thống
- **Cách 1 (Khuyên dùng - Docker):** Docker Desktop / Docker Engine + Docker Compose v2+
- **Cách 2 (Chạy trực tiếp trên máy):** Python 3.11+, MySQL Server 8.0+

---

## 2. Cấu hình biến môi trường (`.env`)
Tạo file `.env` tại thư mục gốc dự án (tham khảo từ `.env.example` nếu có):

```env
APP_NAME="TEAM12 AI Interview API"
ENVIRONMENT=development
DEBUG=True

# Cấu hình MySQL
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=team12_ai_interview
MYSQL_USER=team12_user
MYSQL_PASSWORD=team12_pass
DATABASE_URL=mysql+pymysql://team12_user:team12_pass@localhost:3306/team12_ai_interview

# Bảo mật JWT
SECRET_KEY=change_this_to_a_secure_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7