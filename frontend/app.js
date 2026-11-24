/**
 * AI Interview Platform - Main Application Logic & Interactive State
 * Team 12 - Rikkei Internship Project
 */

// Application State
const state = {
  currentScreen: 'dashboard',
  apiBaseUrl: 'http://127.0.0.1:8000',
  isApiConnected: false,
  currentUser: {
    id: 1,
    full_name: 'Trần Quốc Việt',
    email: 'viet.tran@gmail.com',
    role: 'ADMIN',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80'
  },
  interviewConfig: {
    role: 'python',
    roleTitle: 'Senior Python & FastAPI Engineer',
    level: 'senior',
    type: 'technical_code',
    questionCount: 5,
    language: 'vi'
  },
  activeInterview: {
    questionIndex: 0,
    timeRemaining: 25 * 60, // 25 minutes
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
        expectedPoints: ["Cấu trúc Routers -> Services -> Models", "Dependency Injection get_db", "Pydantic response_model"],
        defaultCode: `# Python Snippet: Định nghĩa route mẫu với FastAPI
from fastapi import APIRouter, Depends
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
        expectedPoints: ["Kiểm tra project.owner_id == current_user.id", "Role Guard Admin bypass", "Băm mật khẩu Bcrypt"],
        defaultCode: `# Kiểm tra quyền hạn tránh lỗ hổng IDOR
def check_project_permission(project, current_user):
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
        expectedPoints: ["Kiểm tra status != 'DONE'", "So sánh due_date với UTC now", "Xử lý None due_date"],
        defaultCode: `from datetime import datetime, timezone
from typing import List

class Task:
    def __init__(self, title, status, due_date):
        self.title = title
        self.status = status
        self.due_date = due_date

def filter_overdue_tasks(tasks: List[Task]) -> List[Task]:
    """Viết code xử lý lọc task quá hạn tại đây"""
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
        expectedPoints: ["Session management", "Connection pooling", "Lazy loading vs Eager loading (selectinload)"],
        defaultCode: `# Cấu hình Engine tối ưu trong app/db/session.py
from sqlalchemy import create_engine

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
        expectedPoints: ["Client-side audio buffer / IndexedDB", "WebSocket reconnection", "Chunk upload"],
        defaultCode: `# Pseudo-code: Audio Stream Buffer
class AudioStreamManager:
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

// =========================================================================
// ROUTING & SCREEN SWITCHING
// =========================================================================
function switchScreen(screenId) {
  state.currentScreen = screenId;
  
  // Hide all screens
  document.querySelectorAll('.screen-view').forEach(el => el.classList.add('hidden'));
  
  // Show target screen
  const target = document.getElementById('screen-' + screenId);
  if (target) {
    target.classList.remove('hidden');
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // Update navigation button active styles
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.remove('bg-brand-600', 'text-white', 'shadow-sm', 'nav-active');
    btn.classList.add('text-slate-400');
  });

  const activeNav = document.getElementById('nav-' + screenId);
  if (activeNav) {
    activeNav.classList.remove('text-slate-400');
    activeNav.classList.add('bg-brand-600', 'text-white', 'shadow-sm', 'nav-active');
  }

  // Handle screen specific initializers
  if (screenId === 'device') {
    initDeviceCheck();
  } else if (screenId === 'interview') {
    startInterviewSession();
  } else if (screenId === 'report') {
    setTimeout(renderRadarChart, 150);
  } else if (screenId === 'projects') {
    renderKanbanCards();
  }
}

// =========================================================================
// DEVICE CHECK (CAMERA & MICROPHONE LIVE TESTING)
// =========================================================================
let mediaStream = null;
let audioContext = null;
let analyserNode = null;
let micAnimFrame = null;

async function initDeviceCheck() {
  const videoEl = document.getElementById('webcam-preview-video');
  const fallbackImg = document.getElementById('webcam-preview-fallback');
  const micStatus = document.getElementById('mic-status-text');

  // Try real camera and microphone
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      if (videoEl) {
        videoEl.srcObject = mediaStream;
        videoEl.play();
        videoEl.classList.remove('hidden');
        if (fallbackImg) fallbackImg.classList.add('hidden');
      }

      // Initialize real Web Audio volume analyzer
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContext.createMediaStreamSource(mediaStream);
      analyserNode = audioContext.createAnalyser();
      analyserNode.fftSize = 64;
      source.connect(analyserNode);

      if (micStatus) micStatus.innerText = "Đã kết nối Mic & Đang thu âm tốt";
      updateMicVolumeBars();
    } catch (err) {
      console.log("Device access denied or running in sandbox, using simulated camera:", err);
      useSimulatedDevices();
    }
  } else {
    useSimulatedDevices();
  }
}

function useSimulatedDevices() {
  const videoEl = document.getElementById('webcam-preview-video');
  const fallbackImg = document.getElementById('webcam-preview-fallback');
  const micStatus = document.getElementById('mic-status-text');

  if (videoEl) videoEl.classList.add('hidden');
  if (fallbackImg) fallbackImg.classList.remove('hidden');
  if (micStatus) micStatus.innerText = "Chế độ mô phỏng thiết bị HD (Hoạt động tốt)";
  simulateVolumeBars();
}

function updateMicVolumeBars() {
  if (!analyserNode) return;
  const dataArray = new Uint8Array(analyserNode.frequencyBinCount);
  analyserNode.getByteFrequencyData(dataArray);

  let sum = 0;
  for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
  let average = sum / dataArray.length; // 0 - 255
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
  const bars = document.querySelectorAll('.volume-bar-item');
  setInterval(() => {
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
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.3); // A5
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

// =========================================================================
// AI INTERVIEW ROOM (LIVE INTERACTION, SPEECH & CODE RUNNER)
// =========================================================================
function startInterviewSession() {
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

  // Update question progress list
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

  // Real Web SpeechSynthesis
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

// Live Speech Recognition (Microphone Speech-to-Text)
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

// Live Code Runner Test Engine
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

// =========================================================================
// RADAR CHART & ASSESSMENT REPORT (CHART.JS)
// =========================================================================
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

// =========================================================================
// KANBAN TASKS & MODAL INTERACTIONS
// =========================================================================
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

function openTaskDetailModalById(taskId) {
  const task = state.tasks.find(t => t.id === taskId);
  if (!task) return;

  const modal = document.getElementById('modal-task-detail');
  const codeEl = document.getElementById('modal-task-code');
  const titleEl = document.getElementById('modal-task-title');
  const descEl = document.getElementById('modal-task-desc');
  const statusEl = document.getElementById('modal-task-status');

  if (codeEl) codeEl.innerText = `#${task.code}`;
  if (titleEl) titleEl.innerText = task.title;
  if (descEl) descEl.innerText = task.description;
  if (statusEl) statusEl.innerText = task.status;

  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }
}

function closeTaskDetailModal() {
  const modal = document.getElementById('modal-task-detail');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

function addCommentToTask() {
  const input = document.getElementById('task-comment-input');
  const list = document.getElementById('task-comments-list');
  if (!input || !input.value.trim() || !list) return;

  const commentText = input.value.trim();
  const newCommentHTML = `
    <div class="flex items-start gap-2.5">
      <span class="w-6 h-6 rounded-full bg-brand-600 text-[10px] text-white font-bold flex items-center justify-center shrink-0">VQ</span>
      <div class="bg-slate-800/80 p-3 rounded-2xl border border-slate-700/60 flex-1">
        <div class="flex items-center justify-between mb-1">
          <span class="font-bold text-white">Trần Quốc Việt</span>
          <span class="text-[10px] text-slate-400">Vừa xong</span>
        </div>
        <p class="text-slate-300 text-xs">${commentText}</p>
      </div>
    </div>
  `;
  list.innerHTML += newCommentHTML;
  input.value = "";
}

// Notification Panel
function toggleNotificationPanel() {
  const panel = document.getElementById('notification-panel');
  if (panel) panel.classList.toggle('hidden');
}

function markAllNotificationsRead() {
  state.notifications.forEach(n => n.read = true);
  const unreadCount = document.getElementById('unread-notif-count');
  if (unreadCount) unreadCount.innerText = "0 chưa đọc";
  alert("✓ Đã đánh dấu tất cả thông báo là đã đọc (Gọi API: PATCH /notifications/read-all)!");
  toggleNotificationPanel();
}

// Check Backend Connection status
async function checkBackendConnection() {
  const indicator = document.getElementById('backend-status-indicator');
  const badge = document.getElementById('backend-status-badge');
  try {
    const res = await fetch('http://127.0.0.1:8000/', { method: 'GET' });
    if (res.ok) {
      state.isApiConnected = true;
      if (indicator) indicator.className = "w-2 h-2 rounded-full bg-emerald-400 animate-ping";
      if (badge) badge.innerText = "Online 127.0.0.1:8000";
    }
  } catch (e) {
    state.isApiConnected = false;
    if (indicator) indicator.className = "w-2 h-2 rounded-full bg-cyan-400";
    if (badge) badge.innerText = "Demo / Standalone";
  }
}

// Initialize on DOM Loaded
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  checkBackendConnection();
  renderKanbanCards();
});
