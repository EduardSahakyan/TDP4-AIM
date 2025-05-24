import tkinter as tk
import threading
import time
import cv2
import numpy as np
import mss
from ultralytics import YOLO
import win32gui
import win32con
import win32api
import torch
import ctypes
import pyautogui


# === Модель ===
model = YOLO("runs/detect/train5/weights/best.pt")
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# === Параметры ===
RESIZED_WIDTH = 640
RESIZED_HEIGHT = 360
window_title = "OverlayAimbot"

# === Overlay окно ===
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

# === Прозрачность окна ===
hwnd = win32gui.FindWindow(None, window_title)
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                       win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) |
                       win32con.WS_EX_LAYERED |
                       win32con.WS_EX_TRANSPARENT |
                       win32con.WS_EX_TOOLWINDOW)
win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 255, win32con.LWA_COLORKEY)

# === Захват экрана ===
def get_frame():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = np.array(sct.grab(monitor))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

# === Проверка нажатия ПКМ ===
VK_RBUTTON = 0x02
def is_right_mouse_pressed():
    return ctypes.windll.user32.GetAsyncKeyState(VK_RBUTTON) & 0x8000

# === Рисуем боксы ===
def draw_boxes(results, ratio_x, ratio_y):
    canvas.delete("all")
    mouse_x, mouse_y = pyautogui.position()
    closest_target = None
    min_distance = 200  # максимум в пикселях

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            if cls == 0:
                x1, y1, x2, y2 = map(float, box.xyxy[0])
                x1 = int(x1 * ratio_x)
                y1 = int(y1 * ratio_y)
                x2 = int(x2 * ratio_x)
                y2 = int(y2 * ratio_y)

                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2)

                # расстояние от мышки до центра врага
                distance = ((mouse_x - cx) ** 2 + (mouse_y - cy) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    closest_target = (cx, cy)

    # если нашли цель — наводим
    if closest_target:
        pyautogui.moveTo(closest_target[0], closest_target[1], duration=0)

# === Основной цикл ===
def yolo_loop():
    while True:
        if is_right_mouse_pressed():
            frame = get_frame()
            resized = cv2.resize(frame, (RESIZED_WIDTH, RESIZED_HEIGHT))

            results = model.predict(source=resized, imgsz=RESIZED_WIDTH,
                                    stream=True, verbose=False, device=device)

            ratio_x = frame.shape[1] / RESIZED_WIDTH
            ratio_y = frame.shape[0] / RESIZED_HEIGHT

            root.after(0, draw_boxes, list(results), ratio_x, ratio_y)
        else:
            canvas.delete("all")  # если не нажата — очищаем

        time.sleep(0.005)

# === Запуск ===
threading.Thread(target=yolo_loop, daemon=True).start()
root.mainloop()
