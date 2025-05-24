import tkinter as tk
import numpy as np
import cv2
import mss
import time
import threading
import win32gui
import win32con
import win32api

# Название overlay окна
window_title = "OverlayRedDetector"

# Создаём overlay
root = tk.Tk()
root.title(window_title)
root.attributes("-topmost", True)
root.overrideredirect(True)
root.geometry(f"{win32api.GetSystemMetrics(0)}x{win32api.GetSystemMetrics(1)}+0+0")
root.wm_attributes("-transparentcolor", "black")

canvas = tk.Canvas(root,
                   width=win32api.GetSystemMetrics(0),
                   height=win32api.GetSystemMetrics(1),
                   bg='black', highlightthickness=0)
canvas.pack()

root.update_idletasks()
time.sleep(0.1)

# Прозрачность
hwnd = win32gui.FindWindow(None, window_title)
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                       win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) |
                       win32con.WS_EX_LAYERED |
                       win32con.WS_EX_TRANSPARENT |
                       win32con.WS_EX_TOOLWINDOW)
win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 255, win32con.LWA_COLORKEY)

# Захват экрана
def get_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = np.array(sct.grab(monitor))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

# Отрисовка
def draw_boxes(bboxes):
    canvas.delete("all")
    for (x, y, w, h) in bboxes:
        canvas.create_rectangle(x, y, x + w, y + h, outline="red", width=2)
        canvas.create_text(x + w // 2, y - 12, text="ENEMY", fill="red", font=("Arial", 10, "bold"))

# Поток обнаружения
def detect_loop():
    screen_h = win32api.GetSystemMetrics(1)

    # 🎯 Новый точный диапазон HSV с твоих скринов
    lower_red = np.array([0, 0, 0])
    upper_red = np.array([45, 173, 239])

    while True:
        img = get_screen()
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_red, upper_red)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bboxes = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            aspect_ratio = w / h if h != 0 else 0
            roi = hsv[y:y + h, x:x + w]
            v_mean = np.mean(roi[:, :, 2])

            # 🎯 Фильтрация мусора
            if 2 < aspect_ratio < 5 and 300 < area < 4000 and y > screen_h * 0.15 and v_mean > 110:
                bboxes.append((x, y, w, h))

        root.after(0, draw_boxes, bboxes)
        time.sleep(0.01)

# Запуск
threading.Thread(target=detect_loop, daemon=True).start()
root.mainloop()
