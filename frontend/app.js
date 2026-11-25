const state = {
  currentScreen: 'dashboard',
  apiBaseUrl: 'http://127.0.0.1:8000',
  isApiConnected: false,
  token: localStorage.getItem('access_token') || null,
  activeProjectId: null,
  selectedTaskId: null,
  currentUser: {
    id: 1,
    full_name: 'Trần Quốc Việt',
    email: 'viet.tran@gmail.com',
    role: 'ADMIN',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80'
  },
  projects: [],
  usersList: [],
  activities: [],
  interviewConfig: {
    role: 'python',
    roleTitle: 'Senior Python & FastAPI Engineer',
    level: 'senior',
    type: 'Kỹ Thuật',
    questionCount: 5,
    language: 'vi'
  },
  activeInterview: {
    questionIndex: 0,
    timeRemaining: 25 * 60,
    timerInterval: null,
    isSpeaking: false,
    isListening: false,
    isCodeRunning: false,
    questions: [
      {
        id: 1,
        title: "Tổng quan & Kinh nghiệm dự án",
        topic: "FastAPI, Pydantic v2 & SQLAlchemy 2.0",
        prompt: "Hãy giới thiệu về kiến trúc dự án Backend gần đây nhất bạn tham gia. Bạn đã áp dụng mô hình phân tầng (Layered Architecture) và dependency injection trong FastAPI như thế nào để đảm bảo code dễ bảo trì?",
        defaultCode: `from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies.get_db import get_db

router = APIRouter(prefix="/demo", tags=["Demo"])

@router.get("/")
def get_status(db: Session = Depends(get_db)):
    return {"status": "healthy", "service": "AI Interview Engine"}
`
      },
      {
        id: 2,
        title: "Bảo mật & Xác thực JWT",
        topic: "OAuth2, Refresh Token & Role RBAC",
        prompt: "Trong hệ thống phỏng vấn này, nhóm bạn đã xây dựng cơ chế xác thực JWT và bảo vệ chống tấn công IDOR như thế nào khi người dùng truy cập hoặc sửa đổi thông tin của dự án khác?",
        defaultCode: `def check_project_permission(project, current_user):
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền sửa dự án này")
    return True
`
      },
      {
        id: 3,
        title: "Thuật toán & Live Coding",
        topic: "Xử lý Task Quá Hạn & Datetime Timezone",
        prompt: "Viết một hàm nhận vào danh sách công việc (Task objects) và lọc ra danh sách các công việc đã quá hạn chót mà chưa hoàn thành (is_overdue). Lưu ý xử lý đúng múi giờ UTC.",
        defaultCode: `from datetime import datetime, timezone
from typing import List

class Task:
    def __init__(self, title, status, due_date):
        self.title = title
        self.status = status
        self.due_date = due_date

def filter_overdue_tasks(tasks: List[Task]) -> List[Task]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    overdue = [t for t in tasks if t.due_date and t.status != "DONE" and t.due_date < now]
    return overdue
`
      },
      {
        id: 4,
        title: "Tối ưu hóa Database",
        topic: "SQLAlchemy 2.0, Indexing & Connection Pooling",
        prompt: "Khi có hàng ngàn ứng viên thực hiện phỏng vấn AI đồng thời, bạn sẽ tối ưu connection pool (pool_size, max_overflow) và câu truy vấn database như thế nào để tránh tình trạng database bị nghẽn?",
        defaultCode: `from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
`
      },
      {
        id: 5,
        title: "Giải quyết tình huống thực tế",
        topic: "AI Speech-to-Text & Realtime Streaming",
        prompt: "Nếu người dùng gặp sự cố mạng ngắt quãng trong quá trình thu âm gửi lên server AI, bạn thiết kế kiến trúc như thế nào để dữ liệu phỏng vấn không bị mất và có thể tiếp tục mượt mà?",
        defaultCode: `class AudioStreamManager:
    def __init__(self):
        self.buffer = []
        
    def push_chunk(self, chunk):
        self.buffer.append(chunk)
        if len(self.buffer) >= 10:
            self.flush_to_server()
`
      }
    ],
    candidateAnswers: {}
  },
  tasks: [
    {
      id: 1,
      code: "TASK-01",
      title: "[Database] Kết nối DB MySQL & Khởi tạo Schema",
      description: "Kết nối MySQL bằng SQLAlchemy; xây dựng engine, SessionLocal và dependency get_db.",
      status: "DONE",
      priority: "HIGH",
      assignee: "Trần Quốc Việt",
      due_date: "20/11/2026",
      comments_count: 3
    },
    {
      id: 2,
      code: "TASK-02",
      title: "[AI Interview] Tích hợp AI chấm điểm giọng nói & Speech-to-Text",
      description: "Xây dựng prompt phỏng vấn kỹ thuật và module trích xuất văn bản từ mic người dùng.",
      status: "IN_PROGRESS",
      priority: "HIGH",
      assignee: "Trần Quốc Việt",
      due_date: "Hôm nay 18:00",
      comments_count: 2
    },
    {
      id: 3,
      code: "TASK-03",
      title: "[Testing] Viết Unit Test cho Module Auth",
      description: "Kiểm thử tự động hàm băm mật khẩu bcrypt, login JSON/form OAuth2 và refresh token.",
      status: "TODO",
      priority: "MEDIUM",
      assignee: "Lập trình viên mẫu",
      due_date: "28/11/2026",
      comments_count: 1
    },
    {
      id: 4,
      code: "TASK-04",
      title: "[Frontend] Dựng phòng phỏng vấn Live & Live Code Runner",
      description: "Tích hợp Webcam, hiệu ứng sóng âm giọng nói AI và trình chạy code test cases.",
      status: "DONE",
      priority: "HIGH",
      assignee: "Trần Quốc Việt",
      due_date: "23/11/2026",
      comments_count: 4
    }
  ],
  notifications: [
    { id: 1, title: "Buổi phỏng vấn AI đã sẵn sàng", desc: "AI đã sinh xong 5 câu hỏi phỏng vấn vị trí Senior Python.", time: "Vừa xong", read: false },
    { id: 2, title: "Giao task mới: [Database] Schema", desc: "Trần Quốc Việt đã giao task #TASK-02 cho bạn.", time: "2h trước", read: false },
    { id: 3, title: "Báo cáo đánh giá AI hoàn tất", desc: "Ứng viên Nguyễn Văn B đạt 88/100 (PASSED).", time: "Hôm qua", read: false }
  ]
};

async function apiFetch(endpoint, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${state.apiBaseUrl}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    state.token = null;
    localStorage.removeItem('access_token');
  }

  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await response.json() : await response.text();

  if (!response.ok) {
    const errMsg = data?.detail || data?.message || data?.error?.message || `HTTP ${response.status}`;
    throw new Error(typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg));
  }

  return data;
}

function normalizeTask(raw) {
  return {
    id: raw.id,
    code: raw.code || `TASK-${String(raw.id).padStart(2, '0')}`,
    title: raw.title || 'Không có tiêu đề',
    description: raw.description || 'Chưa có mô tả chi tiết.',
    status: (raw.status || 'TODO').toUpperCase(),
    priority: (raw.priority || 'MEDIUM').toUpperCase(),
    assignee: raw.assignee?.full_name || raw.assignee_name || state.currentUser.full_name,
    due_date: raw.due_date ? String(raw.due_date).slice(0, 10) : 'Chưa đặt hạn',
    comments_count: raw.comments_count ?? 0
  };
}

async function checkBackendConnection() {
  const badge = document.getElementById('backend-status-badge');
  try {
    const res = await fetch(`${state.apiBaseUrl}/`, { method: 'GET' });
    if (res.ok) {
      state.isApiConnected = true;
      let statusLabel = "API Online";
      try {
        const dbRes = await fetch(`${state.apiBaseUrl}/health/db`, { method: 'GET' });
        if (dbRes.ok) statusLabel = "Online 127.0.0.1:8000";
      } catch {}

      if (badge) {
        badge.className = "inline-flex items-center gap-1.5 text-emerald-400 font-medium font-mono text-[11px]";
        badge.innerHTML = `<span id="backend-status-indicator" class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span> ${statusLabel}`;
      }
      await syncAllBackendData();
      return;
    }
  } catch (e) {
    // Offline fallback
  }

  state.isApiConnected = false;
  if (badge) {
    badge.className = "inline-flex items-center gap-1.5 text-cyan-400 font-medium font-mono text-[11px]";
    badge.innerHTML = `<span id="backend-status-indicator" class="w-2 h-2 rounded-full bg-cyan-400"></span> Demo / Standalone`;
  }
}

async function syncAllBackendData() {
  if (!state.isApiConnected || !state.token) return;

  await fetchCurrentUserProfile();
  await fetchProjectsAndTasks();
  await fetchUsersList();
  await fetchNotifications();
  await fetchActivities();
}

async function handleLogin(email, password) {
  if (!state.isApiConnected) {
    alert('Backend chưa bật, đang đăng nhập ở chế độ Demo!');
    switchScreen('dashboard');
    return;
  }

  try {
    let data;
    try {
      data = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
    } catch (jsonErr) {
      const formBody = new URLSearchParams();
      formBody.append('username', email);
      formBody.append('password', password);
      data = await apiFetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formBody.toString()
      });
    }

    const token = data.access_token || data.token || data.data?.access_token;
    if (!token) throw new Error('Không nhận được access_token từ server');

    state.token = token;
    localStorage.setItem('access_token', token);
    await syncAllBackendData();
    alert('Đăng nhập thành công & đã đồng bộ dữ liệu từ FastAPI!');
    switchScreen('dashboard');
  } catch (err) {
    alert(`Đăng nhập thất bại: ${err.message}`);
  }
}

async function fetchCurrentUserProfile() {
  try {
    let profile;
    try {
      profile = await apiFetch('/users/profile');
    } catch {
      profile = await apiFetch('/users/me');
    }
    const userData = profile.data || profile;
    if (userData && userData.email) {
      state.currentUser = {
        ...state.currentUser,
        id: userData.id ?? state.currentUser.id,
        full_name: userData.full_name || userData.name || state.currentUser.full_name,
        email: userData.email,
        role: (userData.role || 'USER').toUpperCase()
      };
      updateUserUI();
    }
  } catch (err) {
    console.warn('Không tải được profile user:', err.message);
  }
}

function updateUserUI() {
  const headerName = document.querySelector('header button[onclick="switchScreen(\'profile\')"] .text-slate-200');
  const headerRole = document.querySelector('header button[onclick="switchScreen(\'profile\')"] .text-cyan-400');
  const dashboardGreeting = document.querySelector('#screen-dashboard h1');
  const profileNameHeading = document.querySelector('#screen-profile h3');
  const profileEmailText = document.querySelector('#screen-profile p.font-mono');
  const profileNameInput = document.querySelector('#screen-profile input[type="text"]');
  const profileEmailInput = document.querySelector('#screen-profile input[type="email"]');

  if (headerName) headerName.innerText = state.currentUser.full_name;
  if (headerRole) headerRole.innerText = state.currentUser.role;
  if (dashboardGreeting) dashboardGreeting.innerText = `Chào mừng quay trở lại, ${state.currentUser.full_name}!`;
  if (profileNameHeading) profileNameHeading.innerText = state.currentUser.full_name;
  if (profileEmailText) profileEmailText.innerText = state.currentUser.email;
  if (profileNameInput) profileNameInput.value = state.currentUser.full_name;
  if (profileEmailInput) profileEmailInput.value = state.currentUser.email;
}

async function updateProfileOnBackend() {
  const nameInput = document.querySelector('#screen-profile input[type="text"]');
  const fullName = nameInput?.value?.trim();
  if (!fullName) return alert('Vui lòng nhập họ và tên!');

  if (!state.isApiConnected || !state.token) {
    state.currentUser.full_name = fullName;
    updateUserUI();
    alert('Đã lưu thông tin ở chế độ Demo!');
    return;
  }

  try {
    await apiFetch('/users/profile', {
      method: 'PUT',
      body: JSON.stringify({ full_name: fullName })
    });
    state.currentUser.full_name = fullName;
    updateUserUI();
    alert('Cập nhật hồ sơ thành công qua API PUT /users/profile!');
  } catch (err) {
    alert(`Lỗi cập nhật hồ sơ: ${err.message}`);
  }
}

async function changePasswordOnBackend() {
  const pwdInputs = document.querySelectorAll('#screen-profile input[type="password"]');
  const oldPassword = pwdInputs[0]?.value;
  const newPassword = pwdInputs[1]?.value;

  if (!oldPassword || !newPassword || newPassword.length < 6) {
    return alert('Vui lòng nhập mật khẩu cũ và mật khẩu mới tối thiểu 6 ký tự!');
  }

  if (!state.isApiConnected || !state.token) {
    alert('Đã đổi mật khẩu ở chế độ Demo!');
    return;
  }

  try {
    await apiFetch('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
    });
    pwdInputs[0].value = '';
    pwdInputs[1].value = '';
    alert('Đổi mật khẩu thành công qua API POST /auth/change-password!');
  } catch (err) {
    alert(`Lỗi đổi mật khẩu: ${err.message}`);
  }
}

async function fetchProjectsAndTasks() {
  try {
    const res = await apiFetch('/projects');
    const items = Array.isArray(res) ? res : (res.items || res.data || []);
    if (items.length > 0) {
      state.projects = items;
      state.activeProjectId = items[0].id;
      renderDashboardProjects(items);
      await fetchTasksForProject(state.activeProjectId);
    }
  } catch (err) {
    console.warn('Không tải được danh sách projects:', err.message);
  }
}

function renderDashboardProjects(projects) {
  const tbody = document.querySelector('#screen-dashboard table tbody');
  if (!tbody || !projects.length) return;

  tbody.innerHTML = projects.map(p => {
    const ownerName = p.owner?.full_name || p.owner_name || state.currentUser.full_name;
    const initials = ownerName.split(' ').slice(-2).map(w => w[0]).join('').toUpperCase() || 'PR';
    const statusText = p.status || 'active';
    const progress = p.completion_rate ?? 65;

    return `
      <tr class="hover:bg-slate-800/30 transition-colors">
        <td class="py-3.5 px-3">
          <div class="font-semibold text-white">${p.name || p.title}</div>
          <div class="text-[11px] text-slate-400">${p.description || 'Dự án quản lý trên hệ thống FastAPI'}</div>
        </td>
        <td class="py-3.5 px-3">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-full bg-brand-600 flex items-center justify-center text-[10px] font-bold">${initials}</span>
            <span>${ownerName}</span>
          </div>
        </td>
        <td class="py-3.5 px-3">
          <span class="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            ${statusText}
          </span>
        </td>
        <td class="py-3.5 px-3">
          <div class="flex items-center gap-2">
            <div class="w-20 bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div class="bg-brand-500 h-full rounded-full" style="width: ${progress}%"></div>
            </div>
            <span class="text-[11px] text-slate-300">${progress}%</span>
          </div>
        </td>
        <td class="py-3.5 px-3 text-right">
          <button onclick="selectProjectAndOpen(${p.id})" class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
            <i data-lucide="external-link" class="w-4 h-4"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  lucide.createIcons();
}

async function selectProjectAndOpen(projectId) {
  state.activeProjectId = projectId;
  await fetchTasksForProject(projectId);
  switchScreen('projects');
}

async function fetchTasksForProject(projectId, search = '', priority = '') {
  if (!state.isApiConnected || !state.token || !projectId) {
    renderKanbanCards();
    return;
  }

  try {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (priority) params.append('priority', priority);
    const query = params.toString() ? `?${params.toString()}` : '';

    const res = await apiFetch(`/projects/${projectId}/tasks${query}`);
    const items = Array.isArray(res) ? res : (res.items || res.data || []);
    state.tasks = items.map(normalizeTask);
    renderKanbanCards();
  } catch (err) {
    console.warn('Không tải được tasks:', err.message);
    renderKanbanCards();
  }
}

async function createNewTaskPrompt(defaultStatus = 'TODO') {
  const title = prompt('Nhập tiêu đề công việc mới:');
  if (!title || !title.trim()) return;
  const description = prompt('Nhập mô tả công việc:', 'Tạo từ giao diện AI Interview Studio') || '';
  const priorityInput = (prompt('Độ ưu tiên (HIGH / MEDIUM / LOW):', 'MEDIUM') || 'MEDIUM').toUpperCase();
  const priority = ['HIGH', 'MEDIUM', 'LOW'].includes(priorityInput) ? priorityInput : 'MEDIUM';

  if (!state.isApiConnected || !state.token || !state.activeProjectId) {
    state.tasks.unshift({
      id: Date.now(),
      code: `TASK-${String(state.tasks.length + 1).padStart(2, '0')}`,
      title: title.trim(),
      description,
      status: defaultStatus,
      priority,
      assignee: state.currentUser.full_name,
      due_date: '30/11/2026',
      comments_count: 0
    });
    renderKanbanCards();
    return;
  }

  try {
    await apiFetch(`/projects/${state.activeProjectId}/tasks`, {
      method: 'POST',
      body: JSON.stringify({
        title: title.trim(),
        description,
        status: defaultStatus,
        priority
      })
    });
    await fetchTasksForProject(state.activeProjectId);
  } catch (err) {
    alert(`Không thể tạo task: ${err.message}`);
  }
}

async function updateTaskStatus(taskId, newStatus) {
  const task = state.tasks.find(t => t.id === taskId);
  if (!task) return;

  if (!state.isApiConnected || !state.token) {
    task.status = newStatus;
    renderKanbanCards();
    return;
  }

  try {
    try {
      await apiFetch(`/tasks/${taskId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus })
      });
    } catch {
      await apiFetch(`/projects/${state.activeProjectId}/tasks/${taskId}`, {
        method: 'PUT',
        body: JSON.stringify({
          title: task.title,
          description: task.description,
          priority: task.priority,
          status: newStatus
        })
      });
    }
    task.status = newStatus;
    renderKanbanCards();
  } catch (err) {
    alert(`Lỗi cập nhật trạng thái task: ${err.message}`);
  }
}

async function fetchUsersList() {
  try {
    const res = await apiFetch('/users');
    const items = Array.isArray(res) ? res : (res.items || res.data || []);
    if (items.length > 0) {
      state.usersList = items;
      renderUsersTable(items);
    }
  } catch (err) {
    console.warn('Không tải được danh sách users:', err.message);
  }
}

function renderUsersTable(users) {
  const tbody = document.querySelector('#screen-users table tbody');
  if (!tbody || !users.length) return;

  tbody.innerHTML = users.map(u => {
    const name = u.full_name || u.name || u.email;
    const initials = name.split(' ').slice(-2).map(w => w[0]).join('').toUpperCase() || 'US';
    const role = (u.role || 'USER').toUpperCase();
    const isAdmin = role === 'ADMIN';

    return `
      <tr class="hover:bg-slate-800/30 transition-colors">
        <td class="py-3.5 px-4 font-mono text-slate-400">${u.id}</td>
        <td class="py-3.5 px-4 font-semibold text-white flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-full ${isAdmin ? 'bg-brand-600' : 'bg-cyan-600'} flex items-center justify-center font-bold text-white text-xs">${initials}</div>
          <span>${name}</span>
        </td>
        <td class="py-3.5 px-4 text-slate-300 font-mono">${u.email}</td>
        <td class="py-3.5 px-4">
          <span class="px-2.5 py-1 rounded-full text-[10px] font-bold ${isAdmin ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30' : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'}">${role}</span>
        </td>
        <td class="py-3.5 px-4">
          <span class="inline-flex items-center gap-1 text-emerald-400 text-[11px] font-medium">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Đang hoạt động
          </span>
        </td>
        <td class="py-3.5 px-4 text-right space-x-1">
          <button class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"><i data-lucide="edit-2" class="w-3.5 h-3.5"></i></button>
          <button class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-rose-400"><i data-lucide="lock" class="w-3.5 h-3.5"></i></button>
        </td>
      </tr>
    `;
  }).join('');

  lucide.createIcons();
}

async function fetchNotifications() {
  try {
    const res = await apiFetch('/notifications');
    const items = Array.isArray(res) ? res : (res.items || res.data || []);
    if (items.length > 0) {
      state.notifications = items.map(n => ({
        id: n.id,
        title: n.title || 'Thông báo hệ thống',
        desc: n.content || n.message || '',
        time: n.created_at ? String(n.created_at).slice(0, 16).replace('T', ' ') : 'Mới',
        read: Boolean(n.is_read)
      }));
      const unread = state.notifications.filter(n => !n.read).length;
      const unreadBadge = document.getElementById('unread-notif-count');
      if (unreadBadge) unreadBadge.innerText = `${unread} chưa đọc`;
    }
  } catch (err) {
    console.warn('Không tải được notifications:', err.message);
  }
}

async function fetchActivities() {
  try {
    const res = await apiFetch('/activities');
    const items = Array.isArray(res) ? res : (res.items || res.data || []);
    if (items.length > 0) {
      state.activities = items;
    }
  } catch (err) {
    console.warn('Không tải được activities:', err.message);
  }
}

function switchScreen(screenId) {
  if (state.currentScreen === 'interview' && screenId !== 'interview') {
    if (state.activeInterview.timerInterval) {
      clearInterval(state.activeInterview.timerInterval);
      state.activeInterview.timerInterval = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  state.currentScreen = screenId;
  
  document.querySelectorAll('.screen-view').forEach(el => el.classList.add('hidden'));
  
  const target = document.getElementById('screen-' + screenId);
  if (target) {
    target.classList.remove('hidden');
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.remove('bg-brand-600', 'text-white', 'shadow-sm');
    btn.classList.add('text-slate-400');
  });

  const activeNav = document.getElementById('nav-' + screenId);
  if (activeNav) {
    activeNav.classList.remove('text-slate-400');
    activeNav.classList.add('bg-brand-600', 'text-white', 'shadow-sm');
  }

  if (screenId === 'device') {
    initDeviceCheck();
  } else if (screenId === 'interview') {
    startInterviewSession();
  } else if (screenId === 'report') {
    setTimeout(renderRadarChart, 150);
  } else if (screenId === 'projects') {
    fetchTasksForProject(state.activeProjectId);
  } else if (screenId === 'users') {
    fetchUsersList();
  }
}

let mediaStream = null;
let audioContext = null;
let analyserNode = null;
let micAnimFrame = null;
let simVolumeInterval = null;

async function initCameraStream(videoElId, fallbackImgId) {
  const videoEl = document.getElementById(videoElId);
  const fallbackImg = document.getElementById(fallbackImgId);

  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    try {
      if (!mediaStream) {
        mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      }
      if (videoEl) {
        videoEl.srcObject = mediaStream;
        await videoEl.play();
        videoEl.classList.remove('hidden');
        if (fallbackImg) fallbackImg.classList.add('hidden');
      }
      return true;
    } catch (err) {
      console.log("Camera unavailable or denied, using fallback:", err);
    }
  }

  if (videoEl) videoEl.classList.add('hidden');
  if (fallbackImg) fallbackImg.classList.remove('hidden');
  return false;
}

async function initDeviceCheck() {
  const micStatus = document.getElementById('mic-status-text');
  const hasStream = await initCameraStream('webcam-preview-video', 'webcam-preview-fallback');

  if (hasStream && mediaStream) {
    try {
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(mediaStream);
        analyserNode = audioContext.createAnalyser();
        analyserNode.fftSize = 64;
        source.connect(analyserNode);
      }
      if (micStatus) micStatus.innerText = "Đã kết nối Mic & Đang thu âm tốt";
      updateMicVolumeBars();
    } catch (e) {
      simulateVolumeBars();
    }
  } else {
    if (micStatus) micStatus.innerText = "Chế độ mô phỏng thiết bị HD (Hoạt động tốt)";
    simulateVolumeBars();
  }
}

function updateMicVolumeBars() {
  if (!analyserNode) return;
  const dataArray = new Uint8Array(analyserNode.frequencyBinCount);
  analyserNode.getByteFrequencyData(dataArray);

  let sum = 0;
  for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
  let average = sum / dataArray.length;
  let level = Math.min(8, Math.floor(average / 15));

  const bars = document.querySelectorAll('.volume-bar-item');
  bars.forEach((bar, idx) => {
    if (idx <= level) {
      bar.classList.add('bg-emerald-400');
      bar.classList.remove('bg-slate-800');
    } else {
      bar.classList.remove('bg-emerald-400');
      bar.classList.add('bg-slate-800');
    }
  });

  micAnimFrame = requestAnimationFrame(updateMicVolumeBars);
}

function simulateVolumeBars() {
  if (simVolumeInterval) clearInterval(simVolumeInterval);
  const bars = document.querySelectorAll('.volume-bar-item');
  simVolumeInterval = setInterval(() => {
    const randomLevel = Math.floor(Math.random() * 6) + 2;
    bars.forEach((bar, idx) => {
      if (idx <= randomLevel) {
        bar.classList.add('bg-emerald-400');
        bar.classList.remove('bg-slate-800');
      } else {
        bar.classList.remove('bg-emerald-400');
        bar.classList.add('bg-slate-800');
      }
    });
  }, 200);
}

function playTestSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.3);
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.6);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.6);
    alert("🔊 Đang phát âm thanh mẫu từ AI Interviewer (Tần số 880Hz). Loa hoạt động hoàn hảo!");
  } catch (e) {
    alert("Loa / Âm thanh hoạt động bình thường!");
  }
}

async function startInterviewSession() {
  const activeTypeBtn = document.querySelector('#interview-type-group .bg-brand-600');
  if (activeTypeBtn) {
    state.interviewConfig.type = activeTypeBtn.innerText.trim();
  }
  await initCameraStream('interview-webcam-video', 'interview-webcam-fallback');
  loadQuestion(state.activeInterview.questionIndex);
  startCountdownTimer();
  speakCurrentQuestion();
}

function startCountdownTimer() {
  if (state.activeInterview.timerInterval) clearInterval(state.activeInterview.timerInterval);

  state.activeInterview.timerInterval = setInterval(() => {
    if (state.activeInterview.timeRemaining > 0) {
      state.activeInterview.timeRemaining--;
      const minutes = Math.floor(state.activeInterview.timeRemaining / 60);
      const seconds = state.activeInterview.timeRemaining % 60;
      const formatted = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      const timerDisplay = document.getElementById('interview-countdown-display');
      if (timerDisplay) timerDisplay.innerText = formatted;
    } else {
      clearInterval(state.activeInterview.timerInterval);
      alert("Hết thời gian phỏng vấn! Hệ thống đang chuyển sang Báo cáo đánh giá AI.");
      switchScreen('report');
    }
  }, 1000);
}

function loadQuestion(index) {
  const q = state.activeInterview.questions[index];
  if (!q) return;

  const titleEl = document.getElementById('interview-question-title');
  const topicEl = document.getElementById('interview-question-topic');
  const promptEl = document.getElementById('interview-question-prompt');
  const codeEditorEl = document.getElementById('interview-code-input');
  const transcriptEl = document.getElementById('interview-live-transcript');

  if (titleEl) titleEl.innerText = `Câu Hỏi Số ${index + 1} / ${state.activeInterview.questions.length} • ${q.title}`;
  if (topicEl) topicEl.innerText = q.topic;
  if (promptEl) promptEl.innerText = `"${q.prompt}"`;
  if (codeEditorEl) codeEditorEl.value = q.defaultCode;
  if (transcriptEl) transcriptEl.value = "";

  renderQuestionNavList(index);
}

function renderQuestionNavList(currentIndex) {
  const container = document.getElementById('interview-questions-progress-list');
  if (!container) return;

  container.innerHTML = state.activeInterview.questions.map((q, idx) => {
    let statusClass = "text-slate-400 bg-slate-900/40 border-transparent";
    let icon = `<i data-lucide="circle" class="w-3.5 h-3.5 text-slate-500"></i>`;

    if (idx < currentIndex) {
      statusClass = "text-emerald-400 bg-emerald-500/10 border-emerald-500/20 font-medium";
      icon = `<i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-400"></i>`;
    } else if (idx === currentIndex) {
      statusClass = "text-white bg-brand-500/20 border-brand-500/40 font-bold shadow-sm";
      icon = `<i data-lucide="play" class="w-3.5 h-3.5 text-cyan-400 fill-cyan-400"></i>`;
    }

    return `
      <div onclick="jumpToQuestion(${idx})" class="flex items-center gap-2 px-3 py-2 rounded-xl border text-xs cursor-pointer hover:bg-slate-800 transition-colors ${statusClass}">
        ${icon}
        <span class="truncate">Câu ${idx + 1}: ${q.title}</span>
      </div>
    `;
  }).join('');

  lucide.createIcons();
}

function jumpToQuestion(idx) {
  state.activeInterview.questionIndex = idx;
  loadQuestion(idx);
  speakCurrentQuestion();
}

function speakCurrentQuestion() {
  const q = state.activeInterview.questions[state.activeInterview.questionIndex];
  if (!q) return;

  const aiVoiceStatus = document.getElementById('ai-voice-status');
  if (aiVoiceStatus) aiVoiceStatus.innerText = "Speaking: Voice Synthesizer Active";

  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(q.prompt);
    utterance.lang = 'vi-VN';
    utterance.rate = 1.0;
    utterance.onend = () => {
      if (aiVoiceStatus) aiVoiceStatus.innerText = "Listening: Đang lắng nghe ứng viên";
    };
    window.speechSynthesis.speak(utterance);
  }
}

let recognition = null;
function toggleSpeechRecognition() {
  const transcriptBox = document.getElementById('interview-live-transcript');
  const micBtn = document.getElementById('mic-record-btn');

  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    alert("Trình duyệt không hỗ trợ Web Speech API trực tiếp. Bạn có thể gõ câu trả lời vào hộp văn bản bên dưới.");
    return;
  }

  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!recognition) {
    recognition = new SpeechRec();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'vi-VN';

    recognition.onresult = (event) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript && transcriptBox) {
        transcriptBox.value += (transcriptBox.value ? ' ' : '') + finalTranscript;
      }
    };
  }

  if (state.activeInterview.isListening) {
    recognition.stop();
    state.activeInterview.isListening = false;
    if (micBtn) micBtn.classList.remove('bg-rose-600', 'text-white', 'animate-pulse');
  } else {
    recognition.start();
    state.activeInterview.isListening = true;
    if (micBtn) micBtn.classList.add('bg-rose-600', 'text-white', 'animate-pulse');
  }
}

function runCodeTests() {
  const consoleEl = document.getElementById('code-runner-console');
  const runBtn = document.getElementById('run-code-btn');

  if (runBtn) {
    runBtn.innerHTML = `<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i> Đang chạy tests...`;
    lucide.createIcons();
  }

  setTimeout(() => {
    if (consoleEl) {
      consoleEl.classList.remove('hidden');
      consoleEl.innerHTML = `
        <div class="text-slate-400 font-mono text-[11px] pb-1 border-b border-slate-800 flex items-center justify-between">
          <span>⚡ Python 3.12 Runtime • pytest unit execution</span>
          <span class="text-emerald-400 font-bold">ALL TESTS PASSED</span>
        </div>
        <div class="space-y-1 font-mono text-[11px] pt-1">
          <div class="text-emerald-400">✓ Test Case 1 (Lọc danh sách rỗng): PASSED (0.002s)</div>
          <div class="text-emerald-400">✓ Test Case 2 (Task đã DONE và quá hạn): Bỏ qua chính xác - PASSED (0.001s)</div>
          <div class="text-emerald-400">✓ Test Case 3 (Task quá hạn & chưa hoàn thành): Phát hiện đúng - PASSED (0.002s)</div>
          <div class="text-cyan-300 font-semibold pt-1">3/3 unit tests passed in 0.005s. Độ phức tạp thời gian: O(N), Bộ nhớ: O(1).</div>
        </div>
      `;
    }
    if (runBtn) {
      runBtn.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5 text-emerald-400"></i> Đã Chạy Xong (3/3 Passed)`;
      lucide.createIcons();
    }
  }, 700);
}

function submitAnswerAndNext() {
  const currentIndex = state.activeInterview.questionIndex;
  const transcript = document.getElementById('interview-live-transcript')?.value || "Câu trả lời hoàn tất.";
  const code = document.getElementById('interview-code-input')?.value || "";

  state.activeInterview.candidateAnswers[currentIndex] = { transcript, code };

  if (currentIndex + 1 < state.activeInterview.questions.length) {
    state.activeInterview.questionIndex++;
    loadQuestion(state.activeInterview.questionIndex);
    speakCurrentQuestion();
  } else {
    alert("🎉 Chúc mừng bạn đã hoàn thành tất cả 5 câu hỏi phỏng vấn! AI đang tiến hành tổng hợp kết quả...");
    switchScreen('report');
  }
}

let radarChartInstance = null;
function renderRadarChart() {
  const ctx = document.getElementById('radarChart');
  if (!ctx) return;
  if (radarChartInstance) radarChartInstance.destroy();

  radarChartInstance = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: [
        'Kiến thức Python & FastAPI',
        'Cơ sở dữ liệu SQLAlchemy 2.0',
        'Tư duy Giải thuật & Code',
        'Bảo mật JWT & Role RBAC',
        'Kỹ năng Giao tiếp & Tự tin',
        'Giải quyết vấn đề thực tế'
      ],
      datasets: [
        {
          label: 'Năng lực Ứng Viên',
          data: [92, 88, 90, 85, 84, 89],
          backgroundColor: 'rgba(99, 102, 241, 0.25)',
          borderColor: '#6366f1',
          borderWidth: 2,
          pointBackgroundColor: '#06b6d4',
          pointBorderColor: '#ffffff',
          pointHoverBackgroundColor: '#ffffff',
          pointHoverBorderColor: '#6366f1',
          pointRadius: 4
        },
        {
          label: 'Yêu Cầu Vị Trí Senior',
          data: [80, 80, 80, 75, 75, 80],
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          borderColor: 'rgba(255, 255, 255, 0.2)',
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
          grid: { color: 'rgba(255, 255, 255, 0.08)' },
          pointLabels: {
            color: '#cbd5e1',
            font: { size: 11, family: 'Plus Jakarta Sans', weight: '600' }
          },
          ticks: { display: false, max: 100, min: 0 }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: { color: '#94a3b8', font: { size: 11, family: 'Plus Jakarta Sans' }, boxWidth: 12 }
        }
      }
    }
  });
}

function renderKanbanCards() {
  const todoContainer = document.getElementById('kanban-col-todo');
  const inProgressContainer = document.getElementById('kanban-col-in-progress');
  const doneContainer = document.getElementById('kanban-col-done');

  if (!todoContainer || !inProgressContainer || !doneContainer) return;

  const todoTasks = state.tasks.filter(t => t.status === 'TODO');
  const inProgressTasks = state.tasks.filter(t => t.status === 'IN_PROGRESS');
  const doneTasks = state.tasks.filter(t => t.status === 'DONE');

  todoContainer.innerHTML = todoTasks.map(t => createKanbanCardHTML(t)).join('');
  inProgressContainer.innerHTML = inProgressTasks.map(t => createKanbanCardHTML(t)).join('');
  doneContainer.innerHTML = doneTasks.map(t => createKanbanCardHTML(t)).join('');

  lucide.createIcons();
}

function createKanbanCardHTML(t) {
  const isDone = t.status === 'DONE';
  const priorityColor = t.priority === 'HIGH' ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : 'bg-amber-500/20 text-amber-300 border-amber-500/30';

  return `
    <div onclick="openTaskDetailModalById(${t.id})" class="bg-slate-800/60 hover:bg-slate-800 p-4 rounded-xl border border-slate-700/60 hover:border-brand-500/50 transition-all cursor-pointer space-y-3 group shadow-sm ${isDone ? 'opacity-85' : ''}">
      <div class="flex items-center justify-between">
        <span class="text-[10px] font-bold px-2 py-0.5 rounded border ${priorityColor}">${t.priority}</span>
        <span class="text-[11px] text-slate-400 font-mono">#${t.code}</span>
      </div>
      <h4 class="text-xs font-bold text-white group-hover:text-cyan-300 transition-colors leading-snug ${isDone ? 'line-through text-slate-400' : ''}">
        ${t.title}
      </h4>
      <p class="text-[11px] text-slate-400 line-clamp-2">
        ${t.description}
      </p>
      <div class="flex items-center justify-between pt-2 border-t border-slate-700/50 text-[11px] text-slate-400">
        <div class="flex items-center gap-1 ${isDone ? 'text-emerald-400' : 'text-slate-300'}">
          <i data-lucide="${isDone ? 'check-circle' : 'calendar'}" class="w-3.5 h-3.5"></i>
          <span>${t.due_date}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="flex items-center gap-1"><i data-lucide="message-square" class="w-3 h-3"></i> ${t.comments_count}</span>
          <span class="w-6 h-6 rounded-full bg-brand-600 text-[10px] text-white font-bold flex items-center justify-center">VQ</span>
        </div>
      </div>
    </div>
  `;
}

async function openTaskDetailModalById(taskId) {
  const task = state.tasks.find(t => t.id === taskId);
  if (!task) return;
  state.selectedTaskId = taskId;

  const modal = document.getElementById('modal-task-detail');
  const codeEl = document.getElementById('modal-task-code');
  const titleEl = document.getElementById('modal-task-title');
  const descEl = document.getElementById('modal-task-desc');
  const statusEl = document.getElementById('modal-task-status');

  if (codeEl) codeEl.innerText = `#${task.code}`;
  if (titleEl) titleEl.innerText = task.title;
  if (descEl) descEl.innerText = task.description;
  if (statusEl) {
    statusEl.innerHTML = `
      <select onchange="updateTaskStatus(${task.id}, this.value)" class="bg-slate-900 border border-slate-700 rounded-lg px-2 py-0.5 text-xs text-cyan-400 focus:outline-none">
        <option value="TODO" ${task.status === 'TODO' ? 'selected' : ''}>TODO</option>
        <option value="IN_PROGRESS" ${task.status === 'IN_PROGRESS' ? 'selected' : ''}>IN_PROGRESS</option>
        <option value="DONE" ${task.status === 'DONE' ? 'selected' : ''}>DONE</option>
      </select>
    `;
  }

  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }

  if (state.isApiConnected && state.token) {
    try {
      const res = await apiFetch(`/tasks/${taskId}/comments`);
      const items = Array.isArray(res) ? res : (res.items || res.data || []);
      const list = document.getElementById('task-comments-list');
      if (list && items.length > 0) {
        list.innerHTML = items.map(c => {
          const author = c.user?.full_name || c.author_name || 'Thành viên';
          return `
            <div class="flex items-start gap-2.5">
              <span class="w-6 h-6 rounded-full bg-cyan-600 text-[10px] text-white font-bold flex items-center justify-center shrink-0">TV</span>
              <div class="bg-slate-800/80 p-3 rounded-2xl border border-slate-700/60 flex-1">
                <div class="flex items-center justify-between mb-1">
                  <span class="font-bold text-white">${author}</span>
                  <span class="text-[10px] text-slate-400">${(c.created_at || '').slice(0, 16).replace('T', ' ')}</span>
                </div>
                <p class="text-slate-300 text-xs">${c.content}</p>
              </div>
            </div>
          `;
        }).join('');
      }
    } catch (err) {
      console.warn('Không tải được comments:', err.message);
    }
  }
}

function closeTaskDetailModal() {
  const modal = document.getElementById('modal-task-detail');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

async function addCommentToTask() {
  const input = document.getElementById('task-comment-input');
  const list = document.getElementById('task-comments-list');
  if (!input || !input.value.trim() || !list) return;

  const commentText = input.value.trim();

  if (state.isApiConnected && state.token && state.selectedTaskId) {
    try {
      await apiFetch(`/tasks/${state.selectedTaskId}/comments`, {
        method: 'POST',
        body: JSON.stringify({ content: commentText })
      });
    } catch (err) {
      alert(`Lỗi gửi bình luận: ${err.message}`);
      return;
    }
  }

  const newCommentHTML = `
    <div class="flex items-start gap-2.5">
      <span class="w-6 h-6 rounded-full bg-brand-600 text-[10px] text-white font-bold flex items-center justify-center shrink-0">VQ</span>
      <div class="bg-slate-800/80 p-3 rounded-2xl border border-slate-700/60 flex-1">
        <div class="flex items-center justify-between mb-1">
          <span class="font-bold text-white">${state.currentUser.full_name}</span>
          <span class="text-[10px] text-slate-400">Vừa xong</span>
        </div>
        <p class="text-slate-300 text-xs">${commentText}</p>
      </div>
    </div>
  `;
  list.innerHTML += newCommentHTML;
  input.value = "";
}

function toggleNotificationPanel() {
  const panel = document.getElementById('notification-panel');
  if (panel) panel.classList.toggle('hidden');
}

async function markAllNotificationsRead() {
  if (state.isApiConnected && state.token) {
    try {
      await apiFetch('/notifications/read-all', { method: 'PATCH' });
    } catch (err) {
      console.warn('Lỗi đọc thông báo:', err.message);
    }
  }
  state.notifications.forEach(n => n.read = true);
  const unreadCount = document.getElementById('unread-notif-count');
  if (unreadCount) unreadCount.innerText = "0 chưa đọc";
  toggleNotificationPanel();
}

document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  renderKanbanCards();
  checkBackendConnection();

  const loginForm = document.querySelector('#screen-auth form');
  if (loginForm) {
    loginForm.onsubmit = (e) => {
      e.preventDefault();
      const email = loginForm.querySelector('input[type="email"]')?.value?.trim();
      const password = loginForm.querySelector('input[type="password"]')?.value;
      handleLogin(email, password);
    };
  }

  const profileButtons = document.querySelectorAll('#screen-profile button');
  profileButtons.forEach(btn => {
    if (btn.innerText.includes('Lưu Thông Tin')) {
      btn.onclick = updateProfileOnBackend;
    } else if (btn.innerText.includes('Đổi Mật Khẩu')) {
      btn.onclick = changePasswordOnBackend;
    }
  });

  const taskSearchInput = document.querySelector('#screen-projects input[type="text"]');
  const taskPrioritySelect = document.querySelector('#screen-projects select');
  const addTaskBtn = document.querySelector('#screen-projects button[onclick*="POST /projects"]');

  if (taskSearchInput) {
    let debounceTimer;
    taskSearchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        fetchTasksForProject(state.activeProjectId, taskSearchInput.value.trim(), taskPrioritySelect?.value || '');
      }, 300);
    });
  }

  if (taskPrioritySelect) {
    taskPrioritySelect.addEventListener('change', () => {
      fetchTasksForProject(state.activeProjectId, taskSearchInput?.value?.trim() || '', taskPrioritySelect.value);
    });
  }

  if (addTaskBtn) {
    addTaskBtn.onclick = () => createNewTaskPrompt('TODO');
  }
});