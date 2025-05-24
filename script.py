import tkinter as tk
import threading
import time

import cv2
import numpy as np
import mss
from PIL import Image, ImageTk
from ultralytics import YOLO

import win32gui
import win32con
import win32api

# Загружаем модель
model = YOLO("best.pt")

# Параметры ресайза (ускоряет YOLO)
RESIZED_WIDTH = 640
RESIZED_HEIGHT = 360

# Создаём overlay окно
root = tk.Tk()
window_title = "OverlayAimbot"
root.title(window_title)

root.attributes("-topmost", True)
root.overrideredirect(True)
root.geometry(f"{win32api.GetSystemMetrics(0)}x{win32api.GetSystemMetrics(1)}+0+0")
root.wm_attributes("-transparentcolor", "black")

canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight(),
                   bg='black', highlightthickness=0)
canvas.pack()

# Подключение к overlay
root.update_idletasks()
time.sleep(0.1)
hwnd = win32gui.FindWindow(None, window_title)
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                       win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) |
                       win32con.WS_EX_LAYERED |
                       win32con.WS_EX_TRANSPARENT |
                       win32con.WS_EX_TOOLWINDOW)
win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 255, win32con.LWA_COLORKEY)

# Захват экрана
def get_frame():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = np.array(sct.grab(monitor))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        return img

# Рисуем боксы (из основного потока)
def draw_boxes(results, original_shape):
    canvas.delete("all")
    ratio_x = original_shape[1] / RESIZED_WIDTH
    ratio_y = original_shape[0] / RESIZED_HEIGHT

    for box in results.boxes:
        cls = int(box.cls[0])
        if cls == 0:
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            x1 = int(x1 * ratio_x)
            y1 = int(y1 * ratio_y)
            x2 = int(x2 * ratio_x)
            y2 = int(y2 * ratio_y)
            canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2)

# Поток для YOLO-инференса
def yolo_loop():
    while True:
        frame = get_frame()
        resized = cv2.resize(frame, (RESIZED_WIDTH, RESIZED_HEIGHT))
        results = model(resized, verbose=False)[0]
        root.after(0, draw_boxes, results, frame.shape)
        time.sleep(0.001)  # ограничение частоты

# Запускаем поток
threading.Thread(target=yolo_loop, daemon=True).start()
root.mainloop()
