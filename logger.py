import time
import json
from datetime import datetime
from pynput import keyboard, mouse
import pygetwindow as gw
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

# ===== 앱 이름 =====
def get_process_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name()
    except Exception as e:
        print("get_process_name error:", e)
    return "Unknown"

# ===== 창 제목 =====
def get_title_name():
    try:
        window = gw.getActiveWindow()
        if window and window.title:
            return window.title
    except Exception as e:
        print("get_title_name error:", e)
    return None

# ===== 초기 상태 =====
initial_title = get_title_name()
prev_title = initial_title if initial_title else "Unknown"
prev_app = get_process_name()
segment_start_time = time.time()

# ===== 리스너 시작 =====
keyboard.Listener(on_press=on_key_press).start()
mouse.Listener(on_click=on_click).start()

print("Logger started...")

# ===== 메인 루프 =====
while True:
    time.sleep(0.2)

    # ===== 현재 상태 =====
    title = get_title_name()
    current_title = title if title else prev_title
    current_app = get_process_name()
    now = time.time()

    # ===== 이벤트 판단 =====
    is_app_changed = (current_app != prev_app)
    is_title_changed = (current_title != prev_title)

    
    is_switch = is_app_changed
 

    is_periodic = (now - segment_start_time) >= 10

    # ===== 로그 생성 =====
    if is_switch or is_periodic:

        duration = round(now - segment_start_time, 2)

        with lock:
            k_count = keyboard_count
            m_count = mouse_count

        # ===== idle 계산 =====
        idle_time = int(now - max(last_input_time, segment_start_time))
        is_idle = idle_time >= 5

        log = {
            "user_id": 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            "duration": duration,
            "is_periodic": is_periodic,

            "app": prev_app,
            "title": prev_title,

            "keyboard_count": k_count,
            "mouse_count": m_count,

            "idle_time": idle_time,
            "is_idle": is_idle,

            "is_switch": is_switch,

            #나중에 필터링용
            "long_idle": idle_time >= 30
        }

        print(json.dumps(log, indent=2, ensure_ascii=False))

        # ===== 상태 업데이트 =====
        prev_title = current_title
        prev_app = current_app

        # 구간 리셋
        segment_start_time = now

        # 카운트 초기화 (구간 기준)
        with lock:
            keyboard_count = 0
            mouse_count = 0