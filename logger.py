import time
import json
import sqlite3
from datetime import datetime
from pynput import keyboard, mouse
import psutil
import win32gui
import win32process
from threading import Lock

# ===== 전역 변수 =====
keyboard_count = 0
mouse_count = 0
last_input_time = time.time()

prev_title = None
prev_app = None
segment_start_time = time.time()

lock = Lock()

session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")


# ===== DB 초기화  =====
def init_db():
    conn = sqlite3.connect("activity_logs.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_raw_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        duration REAL NOT NULL,
        app TEXT,
        title TEXT,
        keyboard_count INTEGER DEFAULT 0,
        mouse_count INTEGER DEFAULT 0,
        idle_time REAL DEFAULT 0,
        is_idle INTEGER DEFAULT 0,
        is_periodic INTEGER DEFAULT 0,
        is_switch INTEGER DEFAULT 0,
        long_idle INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def save_raw_log(log):
    conn = sqlite3.connect("activity_logs.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO activity_raw_log (
        session_id, user_id,
        start_time, end_time, duration,
        app, title,
        keyboard_count, mouse_count,
        idle_time, is_idle,
        is_periodic, is_switch, long_idle
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        log["session_id"],
        log["user_id"],
        log["start_time"],
        log["end_time"],
        log["duration"],
        log["app"],
        log["title"],
        log["keyboard_count"],
        log["mouse_count"],
        log["idle_time"],
        int(log["is_idle"]),
        int(log["is_periodic"]),
        int(log["is_switch"]),
        int(log["long_idle"])
    ))

    conn.commit()
    conn.close()


# ===== 키보드 이벤트 =====
def on_key_press(key):
    global keyboard_count, last_input_time
    with lock:
        keyboard_count += 1
        last_input_time = time.time()


# ===== 마우스 이벤트 =====
def on_click(x, y, button, pressed):
    global mouse_count, last_input_time
    if pressed:
        with lock:
            mouse_count += 1
            last_input_time = time.time()


# ===== 앱 이름 & 창 제목  =====
def get_window_info():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return "Unknown", "Unknown"

        # 창 제목
        title = win32gui.GetWindowText(hwnd)
        title = title if title else "Unknown"

        # 프로세스 이름
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            app = process.name()
        except:
            app = "Unknown"
        return app, title

    except Exception as e:
        print("get_process_name error:", e)
    return "Unknown", "Unknown"


# ===== 초기 상태 =====
init_db()

initial_app, initial_title = get_window_info()
prev_title = initial_title if initial_title else "Unknown"
prev_app = initial_app if initial_app else "Unknown"
segment_start_time = time.time()
# 로그 출력용
start_time = datetime.now()

# ===== 리스너 시작 =====
keyboard.Listener(on_press=on_key_press).start()
mouse.Listener(on_click=on_click).start()

print("Logger started...")

# ===== 메인 루프 =====
while True:
    time.sleep(0.5)

    # ===== 현재 상태 =====
    current_app, current_title = get_window_info()
    now = time.time()

    # ===== 이벤트 판단 =====
    is_app_changed = (current_app != prev_app)
    is_title_changed = (current_title != prev_title)

    is_switch = is_app_changed

    is_periodic = (now - segment_start_time) >= 10

    # ===== 로그 생성 =====
    if is_switch or is_periodic:
        duration = round(now - segment_start_time, 2)
        end_time = datetime.now()

        with lock:
            k_count = keyboard_count
            m_count = mouse_count

        # ===== idle 계산 =====
        idle_time = int(now - max(last_input_time, segment_start_time))
        is_idle = idle_time >= 5

        log = {
            "session_id": session_id,
            "user_id": 1,

            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),

            "duration": duration,
            "is_periodic": is_periodic,

            "app": prev_app,
            "title": prev_title,

            "keyboard_count": k_count,
            "mouse_count": m_count,

            "idle_time": idle_time,
            "is_idle": is_idle,

            "is_switch": is_switch,

            # 나중에 필터링용
            "long_idle": idle_time >= 30
        }

        save_raw_log(log)
        print(json.dumps(log, indent=2, ensure_ascii=False))

        # ===== 상태 업데이트 =====
        prev_title = current_title
        prev_app = current_app

        # 구간 리셋
        segment_start_time = now
        start_time = end_time

        # 카운트 초기화 (구간 기준)
        with lock:
            keyboard_count = 0
            mouse_count = 0