import time
import json
from datetime import datetime
from pynput import keyboard, mouse
import pygetwindow as gw
import psutil
import win32gui
import win32process

 # 주요 변경점: app: current_window, title: current_window 중복 수정 만약 따로 두고 싶을 경우 (그냥 중복오류일시 하나 삭제하면 됩니다 따로를 생각해 수정했어요)


# ===== 전역 변수 =====
keyboard_count = 0
mouse_count = 0
switch_count = 0

last_input_time = time.time()
current_window = None
current_app = None

DURATION = 10  # 10초

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
def get_process_info():
        hwnd = win32gui.GetForegroundWindow()
        if hwnd is not None:
            thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            app_name = process.name()

            return app_name
        
        else:
            return None
        

# ===== 리스너 시작 =====
keyboard.Listener(on_press=on_key_press).start()
mouse.Listener(on_click=on_click).start()

# ===== 메인 루프 =====
while True:

    start_time = time.time()
    switch_count = 0  # 매 구간 초기화

    prev_window = None

    # 10초 동안 계속 체크
    while time.time() - start_time < DURATION:
        try:
            window = gw.getActiveWindow()
            title = window.title if window else "Unknown"
        except:
            title = "Unknown"
            
    # 현재 활성앱 이름 가져오기
    
        app = get_process_info()
        
        if prev_window is None:
            prev_window = title
        elif title != prev_window:
            switch_count += 1
            prev_window = title

        time.sleep(0.5)  # 0.5초마다 체크

    # 최종 창&앱정보
    current_window = prev_window
    current_app = app

    # idle 계산
    idle_time = int(time.time() - last_input_time)
    is_idle = idle_time > 5

    # 로그 생성
    log = {
        "user_id": 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration": DURATION,
        "app": current_app,
        "title": current_window,
        "keyboard_count": keyboard_count,
        "mouse_count": mouse_count,
        "switch_count": switch_count,
        "idle_time": idle_time,
        "is_idle": is_idle
    }

    print(json.dumps(log, indent=2, ensure_ascii=False))
