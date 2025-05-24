import tkinter as tk

import cv2
from PIL import Image, ImageTk
import mss
import numpy as np
from ultralytics import YOLO
import win32gui
import win32con
import win32api
import time

model = YOLO("best.pt")  # путь к твоей обученной модели

# Создаём overlay окно
root = tk.Tk()
window_title = "OverlayAimbot"
root.title(window_title)  # <-- Устанавливаем имя окна

root.attributes("-topmost", True)
root.overrideredirect(True)
root.geometry(f"{win32api.GetSystemMetrics(0)}x{win32api.GetSystemMetrics(1)}+0+0")
root.wm_attributes("-transparentcolor", "black")

canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight(), bg='black', highlightthickness=0)
canvas.pack()

# Дадим время на инициализацию окна
root.update_idletasks()
time.sleep(0.1)

# Получаем дескриптор окна по названию
hwnd = win32gui.FindWindow(None, window_title)

# Устанавливаем параметры прозрачности
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
        # Удаляем альфа-канал: из BGRA → RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        return img


# Основной цикл
def update_overlay():
    canvas.delete("all")
    frame = get_frame()
    results = model(frame)[0]

    for box in results.boxes:
        cls = int(box.cls[0])
        if cls == 0:  # класс "enemy"
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2)

    root.after(50, update_overlay)

update_overlay()
root.mainloop()
