# BỘ ĐẶC TẢ THIẾT KẾ FIGMA TOÀN DIỆN CHO NỀN TẢNG AI INTERVIEW (TEAM 12)

> **Dự án**: AI Interview & Project Management Platform (FastAPI + SQLAlchemy 2.0 + SQLite/MySQL)  
> **Trạng thái**: Đã hoàn thiện 100% các màn hình chuẩn quy trình End-to-End từ Khách &rarr; Ứng viên &rarr; Phỏng vấn viên &rarr; Quản trị viên (Admin).

---

## 1. BẢNG ĐỐI CHIẾU: ĐÃ ĐẦY ĐỦ CHO MỘT WEB AI INTERVIEW HOÀN CHỈNH CHƯA?

Để một website **AI Interview** hoạt động trơn tru trong thực tế và bảo vệ đồ án/dự án doanh nghiệp đạt điểm tối đa, hệ thống cần đáp ứng đầy đủ **4 Trụ Cột Nghiệp Vụ**:

| Trụ Cột Nghiệp Vụ | Yêu Cầu Thiết Kế UI / UX | Tình Trạng Thiết Kế Trong Bộ Kit | Ánh Xạ Backend API (TEAM 12) |
| :--- | :--- | :---: | :--- |
| **I. Quản Lý & Xác Thực** | Đăng ký, Đăng nhập, Quên mật khẩu, Đổi mật khẩu, Phân quyền RBAC. | ✅ **Đã hoàn thiện** | `POST /auth/login-json`, `POST /auth/register`, `POST /auth/change-password`, `POST /auth/forgot-password` |
| **II. Quản Trị Tuyển Dụng & Dự Án** | Dashboard thống kê, Bảng Kanban chuyển trạng thái task, Quản lý thành viên, Tải lên CV. | ✅ **Đã hoàn thiện** | `GET /projects`, `GET /projects/{id}/dashboard`, `GET /projects/{id}/tasks`, `POST /attachments` |
| **III. Quy Trình Phỏng Vấn AI Trực Tuyến** | Cấu hình đề bài (Job Role/JD), Kiểm tra Cam/Mic, Phòng phỏng vấn live, Live Code Editor, Nhận diện giọng nói. | ✅ **Đã hoàn thiện** | Tích hợp Stream Microphone, AI Agent Prompts, Live Transcript, Monaco Code Runner |
| **IV. Đánh Giá & Hậu Phỏng Vấn** | Báo cáo Radar Chart 6 kỹ năng, Điểm số /100, Đánh giá Strengths/Weaknesses, Lịch sử phỏng vấn. | ✅ **Đã hoàn thiện** | AI Analytics Matrix, Export PDF Report, Lịch sử lưu trữ Database |

---

## 2. CHI TIẾT 10 MÀN HÌNH (FRAMES) TRONG FIGMA MASTER KIT

### Frame 01: Cổng Xác Thực (Authentication Module)
- **Mục tiêu**: Đăng nhập, Đăng ký, Cấp cặp Access Token & Refresh Token, Quên và Đặt lại mật khẩu.
- **Kích thước**: `1440 x 1024 px` (Modal form: `460 x 580 px`).
- **Thành phần**: Form email/password, validate mật khẩu >= 6 ký tự, checkbox ghi nhớ đăng nhập (Refresh token flow).

### Frame 02: Executive Dashboard (Tổng Quan Dự Án & Phỏng Vấn)
- **Mục tiêu**: Bảng điều khiển trung tâm cho Quản lý / Ứng viên.
- **Thành phần**:
  - 4 Thẻ KPI: Dự án đang chạy, Tỷ lệ hoàn thành (`completion_rate`), Số lượt phỏng vấn AI, Nhiệm vụ quá hạn.
  - Bảng dự án gần đây kèm thanh tiến độ hoàn thành task.
  - Audit Trail: Dòng thời gian ghi nhận hành động thực từ API `GET /activities`.

### Frame 03: Quản Lý Dự Án & Bảng Kanban Tasks
- **Mục tiêu**: Quản lý vòng đời tuyển dụng và ứng viên theo phương pháp Agile/Kanban.
- **Thành phần**: 3 Cột trạng thái (`TODO`, `IN_PROGRESS`, `DONE`), thẻ card công việc có nhãn Priority (`HIGH`, `MEDIUM`, `LOW`), avatar assignee, thời hạn deadline.

### Frame 04: Drawer Chi Tiết Task & Hồ Sơ Ứng Viên (Modal)
- **Mục tiêu**: Xem chi tiết công việc, tải CV/tài liệu đính kèm và thảo luận nội bộ.
- **Thành phần**: Tab Bình luận (`GET/POST /comments`), Tab Tệp đính kèm (`GET/POST /attachments`), nút đổi trạng thái task.

### Frame 05: Thiết Lập Buổi Phỏng Vấn AI (Mock Setup Wizard)
- **Mục tiêu**: Bước chuẩn bị đề thi và ngữ cảnh phỏng vấn.
- **Thành phần**:
  - Chọn vị trí công việc: Backend Python, AI/ML, Fullstack, Frontend, DevOps.
  - Chọn cấp độ: Junior, Middle, Senior, Lead.
  - Chọn hình thức: Phỏng vấn Kỹ thuật, Live Coding, Câu hỏi hành vi (Behavioral).
  - Vùng tải lên CV ứng viên (PDF/DOCX) và ô nhập JD (Job Description) để AI phân tích.

### Frame 06: Kiểm Tra Thiết Bị & Camera/Mic (Device Check Pre-room)
- **Mục tiêu**: Đảm bảo điều kiện kỹ thuật trước khi bước vào phòng thi chính thức.
- **Thành phần**:
  - Khung hình xem trước Webcam 1080p có nhận diện khuôn mặt (Face Recognition indicator).
  - Thước đo âm lượng Microphone thời gian thực (Live animated audio bars).
  - Nút phát thử âm thanh AI và Hộp cảnh báo quy chế phỏng vấn.

### Frame 07: Phòng Phỏng Vấn Kỹ Thuật AI Live (AI Interview Room)
- **Mục tiêu**: Trải nghiệm phỏng vấn tương tác thông minh nhất giữa Người và AI.
- **Thành phần**:
  - **Khung AI Interviewer Avatar**: Robot/Chuyên gia AI với hiệu ứng phát sáng (Pulse glow) và sóng âm giọng nói (Voice wave synthesizer) khi AI nói.
  - **Khung Webcam ứng viên**: Tích hợp các nút tắt/bật Camera và Micro.
  - **Khung Câu hỏi hiện hành**: Hiển thị rõ ràng câu hỏi kỹ thuật số 03/08.
  - **Trình Soạn Thảo Live Code Editor (Python/JS)**: Hỗ trợ syntax highlight và nút "Chạy Test Cases".
  - **Live Speech-to-Text Transcript**: Trích xuất giọng nói của ứng viên thành văn bản theo thời gian thực.
  - **Cột Real-time AI Signals**: Đánh giá độ tự tin (88%), độ chính xác thuật ngữ (92%), tốc độ phản xạ (1.2s).

### Frame 08: Báo Cáo Đánh Giá Năng Lực AI (Assessment Report)
- **Mục tiêu**: Kết quả đầu ra toàn diện của buổi phỏng vấn.
- **Thành phần**:
  - Điểm tổng thể lớn `88 / 100` font mono phát sáng kèm nhãn `PASSED`.
  - **Biểu đồ Radar Chart 6 trục kỹ năng**: Kiến thức Python, FastAPI/Async, ORM Database, Thuật toán, Giao tiếp, Giải quyết vấn đề.
  - Hộp phân tích Điểm mạnh (Strengths) và Điểm cần cải thiện (Opportunities).
  - Nhận xét và nút phê duyệt Offer tuyển dụng.

### Frame 09: Lịch Sử Phỏng Vấn & Tiến Trình Năng Lực (Interview History)
- **Mục tiêu**: Ứng viên hoặc Nhà tuyển dụng xem lại toàn bộ các buổi phỏng vấn trong quá khứ.
- **Thành phần**: Bảng danh sách ngày phỏng vấn, vị trí, thời lượng, điểm số và nút xem lại báo cáo chi tiết.

### Frame 10: Hồ Sơ Cá Nhân & Quản Trị RBAC (Profile & User Management)
- **Mục tiêu**: Quản lý thông tin tài khoản và phân quyền người dùng.
- **Thành phần**:
  - Màn hình thông tin User, form đổi mật khẩu an toàn.
  - Màn hình dành cho Admin: Quản lý danh sách người dùng (`GET /users`), khóa/mở tài khoản và phân vai trò (`ADMIN`, `MANAGER`, `USER`).

---

## 3. CÁCH XUẤT THÀNH BẢN VẼ VECTOR TRONG FIGMA

Toàn bộ 10 màn hình trên đã được tích hợp trong file:
**[frontend_design/index.html](file:///d:/H%E1%BB%8Dc%20k%E1%BB%B3%202%20rikei/ThucTap/TEAM12_AI-Interview/frontend_design/index.html)**

Chỉ cần:
1. Mở Figma &rarr; Mở plugin **`html.to.design`**.
2. Chọn tab **HTML / Code**.
3. Dán toàn bộ mã nguồn file `frontend_design/index.html` vào và bấm **Import**.
4. Toàn bộ 10 màn hình sẽ hiển thị dưới dạng **Figma Frames với Auto-Layout, Components, Layers vector độc lập**, sẵn sàng để bạn bàn giao cho lập trình viên Frontend làm việc ngay lập tức!
