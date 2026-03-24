import time
import json
from datetime import datetime
from pynput import keyboard, mouse
import pygetwindow as gw
import psutil
import win32gui
import win32process

# ===== 전역 변수 =====
keyboard_count = 0
mouse_count = 0

last_input_time = time.time()
current_title = None
current_app = None

# ===== 키보드 이벤트 =====
def on_key_press(key):
    global keyboard_count, last_input_time
    keyboard_count += 1
    last_input_time = time.time()

# ===== 마우스 이벤트 =====
def on_click(x, y, button, pressed):
    global mouse_count, last_input_time
    if pressed:
        mouse_count += 1
        last_input_time = time.time()

# ==== 앱 이름 가져오기 ====
def get_process_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd is not None:
            thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            app_name = process.name()
            return app_name
       
        else:
            return "Unknown"
       
    except:
        return "Unknown"

# ==== 창 이름 가져오기 ====

def get_title_name():
    try:
        window = gw.getActiveWindow()
        title = window.title if window else "Unknown"
        return title
    except:
        return "Unknown"

# ==== 현재 정보  ====
prev_title = get_title_name()
prev_app = get_process_name()
present_time = time.time()


# ===== 리스너 시작 =====
keyboard.Listener(on_press=on_key_press).start()
mouse.Listener(on_click=on_click).start()


# ===== 메인 루프 =====
while True:
    current_title = get_title_name()
    current_app = get_process_name()

    # title이나 앱 달라질때
   
    if current_title != prev_title or current_app != prev_app:
        DURATION = round(time.time() - present_time, 2)
       
        # idle 계산
        idle_time = int(time.time() - last_input_time)
        is_idle = idle_time > 5
   
        # 로그 생성
        log = {
        "user_id": 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration": DURATION,
        "app": prev_app,
        "title": prev_title,
        "keyboard_count": keyboard_count,
        "mouse_count": mouse_count,
        "idle_time": idle_time,
        "is_idle": is_idle
    }

        print(json.dumps(log, indent=2, ensure_ascii=False))

   
    # 갱신
        prev_title = current_title
        prev_app = current_app
        present_time = time.time()

    # 카운트 초기화
        keyboard_count = 0
        mouse_count = 0

    time.sleep(0.5)
