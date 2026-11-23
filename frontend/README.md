# HƯỚNG DẪN DỰ ÁN FRONTEND - AI INTERVIEW PLATFORM (TEAM 12)

Thư mục này chứa toàn bộ thiết kế, prototype và tài liệu đặc tả giao diện người dùng (UI/UX) cho nền tảng **AI Interview**.

---

## 1. Cấu Trúc Thư Mục `frontend/`

```
frontend/
├── index.html                 # Trang web giao diện AI Interview hoàn chỉnh 10 màn hình
├── app.js                     # Toàn bộ logic tương tác, WebRTC Cam/Mic, Speech-to-Text, Code Runner & Chart.js
├── style.css                  # Hiệu ứng Glassmorphism, animations sóng âm AI và Dark Theme
├── serve.py                   # Script khởi chạy nhanh Local Server (cổng 3000)
├── tokens.json                # Bộ Design Tokens cho Figma Tokens Studio
├── FIGMA_SPECIFICATION.md     # Tài liệu đặc tả kỹ thuật chi tiết 10 Frames trong Figma
└── README.md                  # Hướng dẫn phát triển và kết nối Backend
```

---

## 2. Cách Chạy Và Trải Nghiệm Giao Diện

Bạn có 2 cách cực kỳ nhanh để mở và trải nghiệm:

### Cách 1: Khởi chạy Local Server (Khuyên dùng)
Mở terminal và chạy lệnh:
```powershell
python frontend/serve.py
```
Trình duyệt sẽ tự động mở tại: `http://localhost:3000`.

### Cách 2: Nhấp đúp chuột trực tiếp
Nhấp đúp chuột trực tiếp vào file `frontend/index.html` để mở ngay trên Chrome/Edge.
- Thanh menu phía trên (Top Header) cho phép bạn chuyển đổi qua lại giữa tất cả **10 màn hình**:
  1. **Dashboard**: Thống kê KPI, tiến độ dự án, nhật ký Audit Trail.
  2. **Dự Án & Tasks**: Bảng Kanban kéo thả trạng thái `TODO` &rarr; `IN_PROGRESS` &rarr; `DONE`.
  3. **Thiết Lập AI (Setup Wizard)**: Cấu hình vị trí ứng tuyển, cấp độ, upload CV, nhập JD.
  4. **Test Thiết Bị (Device Check)**: Kiểm tra camera nhận diện khuôn mặt, thanh đo âm lượng mic thời gian thực.
  5. **Phòng Phỏng Vấn Live**: AI Avatar phát sáng, sóng âm giọng nói, nhận diện Speech-to-Text, **Trình soạn thảo Live Code Editor**.
  6. **Báo Cáo AI**: Điểm tổng kết /100, **Biểu đồ Radar Chart 6 kỹ năng**, phân tích Điểm mạnh / Yếu.
  7. **Lịch Sử**: Danh sách các buổi phỏng vấn đã thực hiện và tiến trình điểm số.
  8. **Quản Lý Users**: Phân quyền RBAC cho Admin (`ADMIN`, `MANAGER`, `USER`).
  9. **Tài Khoản**: Cập nhật hồ sơ cá nhân và đổi mật khẩu.
  10. **Login / Register**: Đăng nhập form/JSON OAuth2, đăng ký, quên mật khẩu.

---

## 3. Cách Nhập Vào Figma Thành Vector & Auto-Layout (1 Phút)

1. Mở phần mềm **Figma** &rarr; Tạo file thiết kế mới.
2. Mở tab **Plugins** &rarr; Tìm plugin **`html.to.design`**.
3. Chọn tab **HTML / Code** trong plugin.
4. Mở file `index.html`, copy toàn bộ mã nguồn (`Ctrl + A` &rarr; `Ctrl + C`) và dán vào plugin.
5. Bấm **Import**: Figma sẽ tự động dựng toàn bộ 10 Frame với Auto-Layout, Components và Icons vector chuẩn 100%.

---

## 4. Hướng Dẫn Khởi Tạo Dự Án Code Frontend (React / Next.js)

Khi nhóm bắt đầu triển khai code Frontend chính thức:

### Khuyên dùng: React + Vite + Tailwind CSS hoặc Next.js
```bash
# 1. Tạo project React Vite
npm create vite@latest . -- --template react-ts

# 2. Cài đặt các thư viện cần thiết
npm install lucide-react axios @tanstack/react-query chart.js react-chartjs-2 tailwindcss postcss autoprefixer

# 3. Khởi tạo cấu hình Tailwind CSS
npx tailwindcss init -p
```

### Cấu hình kết nối API Backend FastAPI
Cấu hình base URL kết nối với `backend/` đang chạy tại port `8000`:

```typescript
// src/api/axiosClient.ts
import axios from 'axios';

const axiosClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Tự động đính kèm JWT Bearer Token
axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default axiosClient;
```
