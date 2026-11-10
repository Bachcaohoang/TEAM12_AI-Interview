# Hệ thống quản lý dự án & công việc

Bộ khung backend dùng **FastAPI, SQLAlchemy và MySQL**. Các endpoint mẫu không cần kết nối database, nên có thể chạy Swagger trước khi cài MySQL.

## 1. Yêu cầu

- Windows và VS Code
- Python 3.10 trở lên (`py --version`)
- Git; tài khoản GitHub nếu cần đẩy mã nguồn

Mở terminal PowerShell tại thư mục dự án. Trong VS Code có thể chọn **Terminal → New Terminal**.

## 2. Tạo môi trường ảo và cài thư viện

```powershell
py -m venv .venv
```

Kích hoạt môi trường ảo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn script, chạy lệnh sau một lần cho tài khoản hiện tại rồi kích hoạt lại:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Cài các thư viện đã khai báo:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Các thư viện chính: `fastapi` tạo API; `uvicorn[standard]` chạy ứng dụng; `sqlalchemy` ORM; `pymysql` kết nối MySQL; `pydantic-settings` và `python-dotenv` đọc cấu hình; `python-jose[cryptography]` xử lý JWT; `passlib[bcrypt]` băm mật khẩu; `alembic` quản lý migration.

Để chụp lại chính xác phiên bản đã cài trong môi trường hiện tại:

```powershell
pip freeze > requirements.txt
```

Lệnh trên thay nội dung `requirements.txt` bằng toàn bộ phiên bản đã phân giải; nếu muốn giữ danh sách thư viện trực tiếp, không cần chạy lại lệnh này.

## 3. Cấu trúc module

```text
app/
├── __init__.py
├── main.py
├── routers/        # endpoint theo nhóm auth, users, projects, tasks
├── models/         # model SQLAlchemy ánh xạ bảng
├── schemas/        # schema Pydantic kiểm tra request/response
├── services/       # nghiệp vụ, tách khỏi giao tiếp HTTP
├── dependencies/   # database session, user hiện tại, role guard
├── core/           # cấu hình, bảo mật, ngoại lệ
└── db/             # Base, engine, session
requirements.txt
README.md
.gitignore
```

Mỗi thư mục Python có `__init__.py` để được nhận diện là package. Khi thêm module mới, router chỉ nên nhận request và gọi service; service thực hiện nghiệp vụ; model/schema lần lượt đại diện dữ liệu lưu trữ và dữ liệu trao đổi API. Nhờ vậy code dễ kiểm thử, bảo trì và mở rộng hơn.

## 4. Cấu hình database (khi bắt đầu dùng MySQL)

Tạo file `.env` tại thư mục gốc (file này đã bị Git bỏ qua), điền thông tin MySQL của bạn:

```dotenv
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/project_management
SECRET_KEY=replace-with-a-long-random-secret
```

Tạo database `project_management` trong MySQL trước khi dùng model. Không đưa `.env` hoặc secret thật lên GitHub. Hiện tại starter chưa tự tạo bảng khi khởi động; nên dùng Alembic để tạo và áp dụng migration khi thêm model.

## 5. Chạy ứng dụng

Từ thư mục gốc, khi môi trường ảo đang kích hoạt:

```powershell
uvicorn app.main:app --reload
```

Mở `http://127.0.0.1:8000/docs` để xem Swagger. Có thể thử `GET /`, `GET /auth/health`, `GET /users/sample`, `GET /projects/sample` và `GET /tasks/sample`. Dừng server bằng `Ctrl+C`.

## 6. Khởi tạo Git và đẩy lên GitHub

Nếu đây là thư mục chưa có Git, chạy:

```powershell
git init
git add .
git commit -m "Create FastAPI project scaffold"
git branch -M main
```

Tạo một repository mới trên GitHub (không khởi tạo README/license ở GitHub để tránh hai lịch sử ban đầu), rồi thay URL bên dưới bằng URL repo của bạn:

```powershell
git remote add origin https://github.com/<username>/<repository>.git
git push -u origin main
```

Nếu thư mục đã có remote `origin`, kiểm tra trước bằng `git remote -v`; không thêm lại remote. Khi remote trỏ tới repo cần nộp, commit các thay đổi và đẩy nhánh hiện tại:

```powershell
git add .
git commit -m "Add FastAPI backend scaffold"
git push -u origin HEAD
```

Link nộp là `https://github.com/<username>/<repository>`. Nếu repository đặt **Private**, thêm giảng viên làm collaborator hoặc đổi sang **Public** theo yêu cầu môn học.
