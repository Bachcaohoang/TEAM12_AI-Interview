# HỆ THỐNG AI INTERVIEW & QUẢN LÝ DỰ ÁN (TEAM 12)

### Thành viên dự án:
1. **Cao Hoàng Bách** - Trưởng nhóm (Team Leader / Admin)
2. **Trần Quốc Việt** - Nhà tuyển dụng & Đánh giá phỏng vấn (Recruiter / Lead Interviewer)
3. **Nguyễn Trọng Nhân** - Kỹ sư hệ thống & Phát triển (Software Engineer / Member)

---

Dự án được phân chia cấu trúc rõ ràng thành 2 phân hệ độc lập: **Backend API** và **Frontend UI / Figma Design**.

```
TEAM12_AI-Interview/
├── backend/                  # Toàn bộ mã nguồn Backend FastAPI của nhóm 12
│   ├── app/                  # FastAPI Application (Routers, Models, Schemas, Services, Core)
│   ├── alembic/              # Database Migrations
│   ├── tests/                # Test suite tự động (11/11 tasks passed)
│   ├── requirements.txt      # Thư viện Python
│   ├── alembic.ini           # Cấu hình migration
│   ├── Dockerfile            # Container build cho Backend
│   ├── seed.py               # Khởi tạo dữ liệu mẫu
│   └── README.md             # Hướng dẫn chi tiết chạy Backend API
│
├── frontend/                 # Bộ Giao Diện & Thiết Kế Figma Master Kit
│   ├── index.html            # Prototype tương tác 10 màn hình chuẩn SaaS Dark Mode
│   ├── tokens.json           # Design Tokens (Colors, Typography, Spacing, Radius)
│   ├── FIGMA_SPECIFICATION.md# Đặc tả chi tiết từng Artboard/Frame trong Figma
│   └── README.md             # Hướng dẫn phát triển và kết nối Frontend
│
├── docker-compose.yml        # Điều phối khởi chạy toàn bộ dịch vụ (MySQL + Backend)
└── README.md                 # Tài liệu tổng quan dự án
```

---

## 1. PHÂN HỆ BACKEND (`backend/`)

Toàn bộ 11/11 nhiệm vụ backend đã được nhóm hoàn thiện với **FastAPI**, **SQLAlchemy 2.0**, **Pydantic v2** và **JWT OAuth2**:

- **Authentication & Security**: Đăng nhập (JSON & OAuth2 Form), Đăng ký, Refresh Token, Quên & Đổi mật khẩu, Role Guard RBAC (`ADMIN`, `MANAGER`, `USER`).
- **Project Management**: CRUD dự án, soft-delete, thành viên dự án, dashboard thống kê tiến độ.
- **Task Management**: Tìm kiếm theo title, lọc đa tiêu chí (`status`, `priority`, `assignee`), phân trang offset/limit, sắp xếp linh hoạt, quy trình trạng thái (Workflow Transitions).
- **Collaboration & Notifications**: Nhật ký hoạt động (Activity Logs), bình luận công việc (Comments), tệp đính kèm CV/tài liệu (Attachments), hệ thống thông báo đẩy (Notifications).

### Khởi động nhanh Backend:
```powershell
cd backend
# Cài đặt thư viện nếu chưa có
pip install -r requirements.txt

# Chạy server FastAPI
uvicorn app.main:app --reload --port 8000
```
- Swagger Docs: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## 2. PHÂN HỆ FRONTEND (`frontend/`)

Bộ thiết kế giao diện hoàn chỉnh bám sát 100% nghiệp vụ **AI Interview**:

- **10 Màn hình chuẩn Figma**:
  1. *Dashboard*: Thống kê tổng quan KPI, biểu đồ tiến độ và nhật ký thao tác.
  2. *Quản Lý Dự Án & Tasks*: Bảng Kanban kéo thả trạng thái `TODO` &rarr; `IN_PROGRESS` &rarr; `DONE`.
  3. *Thiết Lập Phỏng Vấn (Setup Wizard)*: Chọn vị trí ứng tuyển, cấp độ, upload CV và dán JD.
  4. *Kiểm Tra Thiết Bị (Device Check)*: Khung preview camera nhận diện khuôn mặt, thanh đo âm lượng mic thời gian thực.
  5. *Phòng Phỏng Vấn AI Live*: AI Avatar 3D phát sáng + sóng âm giọng nói, nhận diện giọng nói Speech-to-Text, **Trình soạn thảo Live Code Editor chạy Test Cases**.
  6. *Báo Cáo Đánh Giá AI*: Điểm tổng kết /100, **Biểu đồ Radar Chart 6 kỹ năng**, phân tích Strengths / Weaknesses.
  7. *Lịch Sử Phỏng Vấn*: Lưu trữ các buổi phỏng vấn đã thực hiện và tiến trình điểm số.
  8. *Quản Lý Users*: Bảng phân quyền tài khoản cho Admin.
  9. *Hồ Sơ & Mật Khẩu*: Cập nhật thông tin cá nhân và đổi mật khẩu.
  10. *Cổng Xác Thực*: Đăng nhập, đăng ký, quên mật khẩu.

### Cách xem và đưa vào Figma:
- **Xem giao diện ngay**: Nhấp đúp chuột mở file `frontend/index.html` trên trình duyệt.
- **Import vào Figma trong 1 phút**: Mở Figma &rarr; Cài plugin **`html.to.design`** &rarr; Copy toàn bộ mã nguồn `frontend/index.html` dán vào plugin và bấm **Import**.
