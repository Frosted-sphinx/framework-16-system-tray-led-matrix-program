import threading
import time
import math
import random
import psutil  # type: ignore
import led_matrix
import pystray
from pystray import MenuItem as item, Menu
from PIL import Image, ImageDraw
from datetime import datetime
import os

X_MAX = 9
Y_MAX = 34

m = led_matrix.Matrix(default_brightness=255)

active_profile = "bars"   # "bars", "gradient", "clock", "rain"
running = True


def level_from_pct(pct: float) -> int:
    lvl = int(pct / 100.0 * X_MAX + 0.5)
    return max(0, min(X_MAX, lvl))


# -------- Profile 1: CPU/RAM/Battery bars (thick) --------

def draw_bars_step() -> None:
    cpu = psutil.cpu_percent(interval=None)  # CPU percent via psutil [web:86][web:423]
    ram = psutil.virtual_memory().percent    # RAM percent via psutil [web:259][web:432]
    b = psutil.sensors_battery()
    batt = b.percent if b is not None else 0.0

    cpu_h = level_from_pct(cpu)
    ram_h = level_from_pct(ram)
    batt_h = level_from_pct(batt)

    m.reset(0)

    bottom_x = X_MAX - 1

    batt_center_y = 4
    ram_center_y = Y_MAX // 2
    cpu_center_y = Y_MAX - 5

    thickness = 2

    def draw_vertical_bar(center_y: int, height: int, value: float) -> None:
        if height <= 0:
            return
        brightness = 128 + int(value / 100.0 * 127)
        for i in range(height):
            x = bottom_x - i
            for offset in range(-thickness // 2, thickness // 2 + 1):
                y = center_y + offset
                if 0 <= y < Y_MAX:
                    m.set_matrix(x, y, brightness)

    draw_vertical_bar(batt_center_y, batt_h, batt)
    draw_vertical_bar(ram_center_y, ram_h, ram)
    draw_vertical_bar(cpu_center_y, cpu_h, cpu)

    m.csend()


# -------- Profile 2: Downward "waterfall" gradient --------

def draw_gradient_step(t: float) -> None:
    m.reset(0)

    for x in range(X_MAX):
        for y in range(Y_MAX):
            ny_raw = y / (Y_MAX - 1)
            ny = 1.0 - ny_raw
            nx = x / (X_MAX - 1)

            v1 = math.sin(2 * math.pi * (ny + t))
            v2 = math.sin(4 * math.pi * (ny + t * 1.5))
            h1 = math.sin(2 * math.pi * (nx + t * 0.7))

            val = 0.5 + 0.35 * v1 + 0.25 * v2 + 0.15 * h1
            val = max(0.0, min(1.0, val))

            brightness = int(255 * val)
            m.set_matrix(x, y, brightness)

    m.csend()


# -------- Profile 3: Clock (HH:MM, vertical digits, no leading 0) --------

FONT_3x5 = {
    "0": [0b111, 0b101, 0b101, 0b101, 0b111],
    "1": [0b010, 0b110, 0b010, 0b010, 0b111],
    "2": [0b111, 0b001, 0b111, 0b100, 0b111],
    "3": [0b111, 0b001, 0b111, 0b001, 0b111],
    "4": [0b101, 0b101, 0b111, 0b001, 0b001],
    "5": [0b111, 0b100, 0b111, 0b001, 0b111],
    "6": [0b111, 0b100, 0b111, 0b101, 0b111],
    "7": [0b111, 0b001, 0b010, 0b010, 0b010],
    "8": [0b111, 0b101, 0b111, 0b101, 0b111],
    "9": [0b111, 0b101, 0b111, 0b001, 0b111],
    ":": [0b000, 0b010, 0b000, 0b010, 0b000],
    " ": [0b000, 0b000, 0b000, 0b000, 0b000],
}

def draw_char_3x5_vertical(ch: str, top_y: int, left_x: int, brightness: int) -> None:
    pattern = FONT_3x5.get(ch, FONT_3x5[" "])
    for row in range(5):
        bits = pattern[row]
        for col in range(3):
            if bits & (1 << (2 - col)):
                x = left_x + col
                y = top_y + row
                if 0 <= x < X_MAX and 0 <= y < Y_MAX:
                    m.set_matrix(x, y, brightness)

def draw_clock_step() -> None:
    now = datetime.now()
    hour_24 = now.hour
    minute = now.minute

    hour_12 = hour_24 % 12 or 12
    time_str = f"{hour_12}:{minute:02d}"

    m.reset(0)

    char_height = 5
    spacing = 1
    total_chars = len(time_str)
    total_height = total_chars * char_height + (total_chars - 1) * spacing

    start_y = (Y_MAX - total_height) // 2
    left_x = (X_MAX - 3) // 2

    brightness = 255

    y = start_y
    for ch in time_str:
        draw_char_3x5_vertical(ch, y, left_x, brightness)
        y += char_height + spacing

    m.csend()


# -------- Profile 4: Digital rain --------

rain_columns = [
    {"y": random.randint(-Y_MAX, 0), "length": random.randint(6, 14), "speed": random.randint(1, 2)}
    for _ in range(X_MAX)
]

def reset_rain_column(col_index: int) -> None:
    rain_columns[col_index]["y"] = random.randint(-Y_MAX, 0)
    rain_columns[col_index]["length"] = random.randint(6, 14)
    rain_columns[col_index]["speed"] = random.randint(1, 2)

def draw_digital_rain_step() -> None:
    m.reset(0)

    for x in range(X_MAX):
        col = rain_columns[x]
        col["y"] += col["speed"]

        if col["y"] - col["length"] > Y_MAX:
            reset_rain_column(x)

        head_y = col["y"]
        length = col["length"]

        for i in range(length):
            y = head_y - i
            if 0 <= y < Y_MAX:
                if i == 0:
                    brightness = 255
                else:
                    fade = 1.0 - (i / max(length, 1))
                    brightness = int(80 + 120 * fade)
                m.set_matrix(x, y, brightness)

    m.csend()


# -------- Startup ripple (15 bands, faster) --------

def play_startup_ripple() -> None:
    m.reset(255)
    m.csend()

    cx = (X_MAX - 1) / 2.0
    cy = (Y_MAX - 1) / 2.0
    max_dist = math.hypot(cx, cy)  # Euclidean distance [web:369]

    steps = 9
    band_count = 15

    band_brightness = []
    for i in range(band_count):
        level = int(255 * (1.0 - i / (band_count - 1)))
        band_brightness.append(level)

    for frame in range(steps):
        if not running:
            return

        t = frame / steps
        radius = t * max_dist

        for x in range(X_MAX):
            for y in range(Y_MAX):
                dx = x - cx
                dy = y - cy
                dist = math.hypot(dx, dy)

                delta = dist - radius

                if delta < 0:
                    brightness = 0
                else:
                    band_pos = delta / max_dist
                    band_index = int(band_pos * band_count)
                    if band_index >= band_count:
                        band_index = band_count - 1

                    inv_index = (band_count - 1) - band_index
                    brightness = band_brightness[inv_index]

                m.set_matrix(x, y, brightness)

        m.csend()
        time.sleep(0.008)  # fast but reasonable timing on typical OSes [web:363][web:434]

    m.reset(0)
    m.csend()


# -------- Worker loop --------

def worker_loop():
    t = 0.0

    play_startup_ripple()

    while running:
        if active_profile == "bars":
            draw_bars_step()
            time.sleep(0.2)
        elif active_profile == "gradient":
            draw_gradient_step(t)
            time.sleep(0.04)
            t += 0.05
        elif active_profile == "clock":
            draw_clock_step()
            time.sleep(0.5)
        elif active_profile == "rain":
            draw_digital_rain_step()
            time.sleep(0.06)
        else:
            time.sleep(0.2)


# -------- Tray icon helpers --------

def load_framework_icon():
    icon_path = os.path.join(os.path.dirname(__file__), "framework_icon.png")
    if os.path.exists(icon_path):
        return Image.open(icon_path)
    size = 16
    image = Image.new("RGB", (size, size), (0, 0, 0))
    d = ImageDraw.Draw(image)
    d.rectangle((2, 2, 6, 14), fill=(0, 255, 0))
    d.rectangle((9, 4, 13, 14), fill=(0, 128, 255))
    return image


def set_profile_bars(icon, menu_item):
    global active_profile
    active_profile = "bars"


def set_profile_gradient(icon, menu_item):
    global active_profile
    active_profile = "gradient"


def set_profile_clock(icon, menu_item):
    global active_profile
    active_profile = "clock"


def set_profile_rain(icon, menu_item):
    global active_profile
    active_profile = "rain"


def on_quit(icon, menu_item):
    global running
    running = False
    icon.stop()


def main():
    thread = threading.Thread(target=worker_loop, daemon=True)
    thread.start()

    menu = Menu(
        item("System Bars", set_profile_bars, checked=lambda _: active_profile == "bars"),
        item("Waterfall Gradient", set_profile_gradient, checked=lambda _: active_profile == "gradient"),
        item("Clock (HH:MM vertical)", set_profile_clock, checked=lambda _: active_profile == "clock"),
        item("Digital Rain", set_profile_rain, checked=lambda _: active_profile == "rain"),
        item("Quit", on_quit)
    )

    icon_image = load_framework_icon()
    icon = pystray.Icon("LEDMatrix", icon_image, "LED Matrix Profiles", menu)  # tray via pystray pattern [web:201][web:435]
    icon.run()


if __name__ == "__main__":
    main()
