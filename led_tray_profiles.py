import threading
import time
import math
import random
import os
import urllib.request
import json
from datetime import datetime

import psutil  # type: ignore
import pystray
from pystray import MenuItem as item, Menu
from PIL import Image, ImageDraw

import led_matrix

X_MAX = 9
Y_MAX = 34

DEFAULT_PORTS = {
    "left": "COM3",
    "right": "COM5",
}


# Change these to your location for weather data
WEATHER_LAT = 42.534901
WEATHER_LON = -92.445312
WEATHER_REFRESH_SECONDS = 900

left_matrix = None
right_matrix = None
connected_sides = []

active_profiles = {
    "left": "bars",
    "right": "clock",
}

running = True

rain_state = {
    "left": [{"y": random.randint(-Y_MAX, 0), "length": random.randint(6, 14), "speed": random.randint(1, 2)} for _ in range(X_MAX)],
    "right": [{"y": random.randint(-Y_MAX, 0), "length": random.randint(6, 14), "speed": random.randint(1, 2)} for _ in range(X_MAX)],
}

weather_cache = {
    "temperature": 0,
    "weather_code": 0,
    "last_fetch": 0.0,
    "ok": False,
}

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
    "-": [0b000, 0b000, 0b111, 0b000, 0b000],
    " ": [0b000, 0b000, 0b000, 0b000, 0b000],
}


def try_open_matrix(port: str):
    try:
        return led_matrix.Matrix(default_brightness=255, serial_port=port)
    except Exception:
        return None


def init_matrices() -> None:
    global left_matrix, right_matrix, connected_sides

    left_matrix = try_open_matrix(DEFAULT_PORTS["left"])
    right_matrix = try_open_matrix(DEFAULT_PORTS["right"])

    connected_sides = []
    if left_matrix is not None:
        connected_sides.append("left")
    if right_matrix is not None:
        connected_sides.append("right")

    if not connected_sides:
        raise RuntimeError(
            f"No LED matrix modules found on {DEFAULT_PORTS['left']} or {DEFAULT_PORTS['right']}"
        )

    if left_matrix is None:
        active_profiles["right"] = "bars"
    if right_matrix is None:
        active_profiles["left"] = "bars"


def get_matrix(side: str):
    return left_matrix if side == "left" else right_matrix


def active_matrices():
    matrices = []
    if left_matrix is not None:
        matrices.append(left_matrix)
    if right_matrix is not None:
        matrices.append(right_matrix)
    return matrices


def level_from_pct(pct: float) -> int:
    lvl = int(pct / 100.0 * X_MAX + 0.5)
    return max(0, min(X_MAX, lvl))


def reset_side(side: str, brightness: int = 0) -> None:
    m = get_matrix(side)
    if m is not None:
        m.reset(brightness)


def set_side_pixel(side: str, x: int, y: int, brightness: int) -> None:
    m = get_matrix(side)
    if m is not None and 0 <= x < X_MAX and 0 <= y < Y_MAX:
        m.set_matrix(x, y, brightness)


def send_side(side: str) -> None:
    m = get_matrix(side)
    if m is not None:
        m.csend()


def reset_all(brightness: int = 0) -> None:
    for m in active_matrices():
        m.reset(brightness)


def send_all() -> None:
    for m in active_matrices():
        m.csend()


def draw_vertical_bar(side: str, center_y: int, height: int, value: float) -> None:
    if height <= 0:
        return

    brightness = 128 + int(value / 100.0 * 127)
    bottom_x = X_MAX - 1
    thickness = 2

    for i in range(height):
        x = bottom_x - i
        for offset in range(-thickness // 2, thickness // 2 + 1):
            y = center_y + offset
            if 0 <= y < Y_MAX:
                set_side_pixel(side, x, y, brightness)


def draw_bars_on_side(side: str, cpu: float, ram: float, batt: float) -> None:
    cpu_h = level_from_pct(cpu)
    ram_h = level_from_pct(ram)
    batt_h = level_from_pct(batt)

    reset_side(side, 0)

    batt_center_y = 4
    ram_center_y = Y_MAX // 2
    cpu_center_y = Y_MAX - 5

    draw_vertical_bar(side, batt_center_y, batt_h, batt)
    draw_vertical_bar(side, ram_center_y, ram_h, ram)
    draw_vertical_bar(side, cpu_center_y, cpu_h, cpu)

    send_side(side)


def draw_bars_step(side: str) -> None:
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    b = psutil.sensors_battery()
    batt = b.percent if b is not None else 0.0
    draw_bars_on_side(side, cpu, ram, batt)


def draw_gradient_panel(side: str, t: float, phase: float) -> None:
    reset_side(side, 0)

    for x in range(X_MAX):
        for y in range(Y_MAX):
            ny_raw = y / (Y_MAX - 1)
            ny = 1.0 - ny_raw
            nx = x / (X_MAX - 1)

            v1 = math.sin(2 * math.pi * (ny + t + phase))
            v2 = math.sin(4 * math.pi * (ny + t * 1.5 + phase))
            h1 = math.sin(2 * math.pi * (nx + t * 0.7 + phase * 0.5))

            val = 0.5 + 0.35 * v1 + 0.25 * v2 + 0.15 * h1
            val = max(0.0, min(1.0, val))

            brightness = int(255 * val)
            set_side_pixel(side, x, y, brightness)

    send_side(side)


def draw_gradient_step(side: str, t: float) -> None:
    phase = 0.0 if side == "left" else 0.18
    draw_gradient_panel(side, t, phase)


def draw_char_3x5_vertical(side: str, ch: str, top_y: int, left_x: int, brightness: int) -> None:
    pattern = FONT_3x5.get(ch, FONT_3x5[" "])

    for row in range(5):
        bits = pattern[row]
        for col in range(3):
            if bits & (1 << (2 - col)):
                x = left_x + col
                y = top_y + row
                set_side_pixel(side, x, y, brightness)


def draw_text_vertical_centered(side: str, text: str, top_limit: int, bottom_limit: int, brightness: int = 255) -> None:
    char_height = 5
    spacing = 1
    total_chars = len(text)
    total_height = total_chars * char_height + max(0, total_chars - 1) * spacing
    region_height = bottom_limit - top_limit + 1
    start_y = top_limit + max(0, (region_height - total_height) // 2)
    left_x = (X_MAX - 3) // 2

    y = start_y
    for ch in text:
        draw_char_3x5_vertical(side, ch, y, left_x, brightness)
        y += char_height + spacing


def draw_clock_step(side: str) -> None:
    now = datetime.now()
    hour_12 = now.hour % 12 or 12
    minute_str = f"{now.minute:02d}"

    if left_matrix is not None and right_matrix is not None:
        if side == "left":
            time_str = str(hour_12)
        else:
            time_str = minute_str
    else:
        time_str = f"{hour_12}:{minute_str}"

    reset_side(side, 0)
    draw_text_vertical_centered(side, time_str, 0, Y_MAX - 1, 255)
    send_side(side)


def reset_rain_column(side: str, col_index: int) -> None:
    rain_state[side][col_index]["y"] = random.randint(-Y_MAX, 0)
    rain_state[side][col_index]["length"] = random.randint(6, 14)
    rain_state[side][col_index]["speed"] = random.randint(1, 2)


def draw_digital_rain_panel(side: str, offset_bias: int = 0) -> None:
    reset_side(side, 0)

    for x in range(X_MAX):
        col = rain_state[side][x]
        col["y"] += col["speed"]

        if col["y"] - col["length"] > Y_MAX:
            reset_rain_column(side, x)
            col = rain_state[side][x]

        head_y = col["y"] + offset_bias
        length = col["length"]

        for i in range(length):
            y = head_y - i
            if 0 <= y < Y_MAX:
                if i == 0:
                    brightness = 255
                else:
                    fade = 1.0 - (i / max(length, 1))
                    brightness = int(80 + 120 * fade)

                set_side_pixel(side, x, y, brightness)

    send_side(side)


def draw_digital_rain_step(side: str) -> None:
    offset_bias = 0 if side == "left" else -1
    draw_digital_rain_panel(side, offset_bias)


def fetch_weather_if_needed() -> None:
    now = time.time()
    if now - weather_cache["last_fetch"] < WEATHER_REFRESH_SECONDS and weather_cache["ok"]:
        return

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={WEATHER_LAT}"
        f"&longitude={WEATHER_LON}"
        "&current=temperature_2m,weather_code"
        "&temperature_unit=fahrenheit"
    )

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        current = data.get("current", {})
        weather_cache["temperature"] = int(round(current.get("temperature_2m", 0)))
        weather_cache["weather_code"] = int(current.get("weather_code", 0))
        weather_cache["last_fetch"] = now
        weather_cache["ok"] = True
    except Exception:
        if not weather_cache["ok"]:
            weather_cache["temperature"] = 0
            weather_cache["weather_code"] = 3
        weather_cache["last_fetch"] = now


def weather_group_from_code(code: int) -> str:
    if code == 0:
        return "clear"
    if code in (1, 2, 3):
        return "cloud"
    if code in (45, 48):
        return "fog"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "storm"
    return "cloud"


def cloud_scroll_offset(frame: int) -> int:
    travel_width = X_MAX + 9
    return (frame // 8) % travel_width - 8


def draw_base_cloud(side: str, frame: int):
    main_cloud = [
        (1, 2), (2, 1), (3, 0), (4, 0), (5, 0), (6, 1), (7, 2),
        (0, 3), (1, 3), (2, 3), (3, 2), (4, 2), (5, 2), (6, 3), (7, 3), (8, 3),
        (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4),
        (2, 2), (5, 1)
    ]

    offset_x = cloud_scroll_offset(frame)
    top_y = 5

    for px, py in main_cloud:
        set_side_pixel(side, px + offset_x - 6, py + top_y - 1, 180)

    for px, py in main_cloud:
        set_side_pixel(side, px + offset_x, py + top_y, 230)

    return offset_x, top_y


def draw_weather_clear(side: str, frame: int) -> None:
    cx = 4
    cy = 6

    sun_pixels = [
        (cx, cy), (cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1),
        (cx - 1, cy - 1), (cx + 1, cy - 1), (cx - 1, cy + 1), (cx + 1, cy + 1),
    ]
    for x, y in sun_pixels:
        set_side_pixel(side, x, y, 220)

    rays_a = [(cx, cy - 3), (cx, cy + 3), (cx - 3, cy), (cx + 3, cy)]
    rays_b = [(cx - 2, cy - 2), (cx + 2, cy - 2), (cx - 2, cy + 2), (cx + 2, cy + 2)]

    rays = rays_a if (frame % 20) < 10 else rays_b
    for x, y in rays:
        set_side_pixel(side, x, y, 255)


def draw_weather_cloud(side: str, frame: int) -> None:
    draw_base_cloud(side, frame)


def draw_weather_fog(side: str, frame: int) -> None:
    offset = (frame // 6) % 6
    rows = [4, 7, 10]

    for idx, row in enumerate(rows):
        start = (offset + idx * 2) % 6
        for x in range(start, X_MAX, 2):
            set_side_pixel(side, x, row, 180)
            if row + 1 < 14:
                set_side_pixel(side, x, row + 1, 90)


def draw_weather_rain(side: str, frame: int) -> None:
    cloud_offset, _ = draw_base_cloud(side, frame)

    rain_cols_main = [2, 4, 6]
    rain_cols_left = [-4, -2]

    for i, x in enumerate(rain_cols_main):
        y = 10 + ((frame + i) % 4)
        rx = x + cloud_offset
        if 10 <= y <= 13:
            set_side_pixel(side, rx, y, 255)
        if 9 <= y - 1 <= 13:
            set_side_pixel(side, rx, y - 1, 120)

    for i, x in enumerate(rain_cols_left):
        y = 9 + ((frame + i + 1) % 4)
        rx = x + cloud_offset
        if 9 <= y <= 13:
            set_side_pixel(side, rx, y, 220)
        if 8 <= y - 1 <= 13:
            set_side_pixel(side, rx, y - 1, 90)


def draw_weather_snow(side: str, frame: int) -> None:
    cloud_offset, _ = draw_base_cloud(side, frame)

    snow_cols_main = [2, 4, 6]
    snow_cols_left = [-4, -2]

    for i, x in enumerate(snow_cols_main):
        y = 10 + ((frame + i) % 4)
        rx = x + cloud_offset
        if 10 <= y <= 13:
            set_side_pixel(side, rx, y, 255)
            set_side_pixel(side, rx - 1, y, 120)
            set_side_pixel(side, rx + 1, y, 120)
            set_side_pixel(side, rx, y - 1, 120)
            set_side_pixel(side, rx, y + 1, 120)

    for i, x in enumerate(snow_cols_left):
        y = 9 + ((frame + i + 1) % 4)
        rx = x + cloud_offset
        if 9 <= y <= 13:
            set_side_pixel(side, rx, y, 220)
            set_side_pixel(side, rx - 1, y, 80)
            set_side_pixel(side, rx + 1, y, 80)
            set_side_pixel(side, rx, y - 1, 80)
            set_side_pixel(side, rx, y + 1, 80)


def draw_weather_storm(side: str, frame: int) -> None:
    cloud_offset, _ = draw_base_cloud(side, frame)

    bolt_main = [(4, 9), (5, 9), (4, 10), (3, 11), (4, 11), (3, 12)]
    bolt_left = [(-3, 9), (-2, 9), (-3, 10), (-4, 11)]
    flash = 255 if (frame % 12) < 3 else 80

    for x, y in bolt_main:
        set_side_pixel(side, x + cloud_offset, y, flash)

    for x, y in bolt_left:
        set_side_pixel(side, x + cloud_offset, y, 180 if flash == 255 else 60)


def draw_weather_icon(side: str, weather_code: int, frame: int) -> None:
    group = weather_group_from_code(weather_code)

    if group == "clear":
        draw_weather_clear(side, frame)
    elif group == "cloud":
        draw_weather_cloud(side, frame)
    elif group == "fog":
        draw_weather_fog(side, frame)
    elif group == "rain":
        draw_weather_rain(side, frame)
    elif group == "snow":
        draw_weather_snow(side, frame)
    elif group == "storm":
        draw_weather_storm(side, frame)
    else:
        draw_weather_cloud(side, frame)


def draw_weather_temperature(side: str, temperature: int) -> None:
    temp_str = str(int(round(temperature)))
    if len(temp_str) > 2:
        temp_str = temp_str[-2:]

    if temperature < 0 and len(temp_str) == 1:
        temp_str = "-" + temp_str

    draw_text_vertical_centered(side, temp_str, 18, 33, 255)


def draw_weather_panel(side: str, weather_code: int, temperature: int, frame: int) -> None:
    reset_side(side, 0)
    draw_weather_icon(side, weather_code, frame)
    draw_weather_temperature(side, temperature)
    send_side(side)


def draw_weather_step(side: str, frame: int) -> None:
    fetch_weather_if_needed()

    if not weather_cache["ok"]:
        reset_side(side, 0)
        draw_text_vertical_centered(side, "--", 18, 33, 255)
        send_side(side)
        return

    draw_weather_panel(side, weather_cache["weather_code"], weather_cache["temperature"], frame)


def play_startup_ripple() -> None:
    reset_all(255)
    send_all()

    cx = (X_MAX - 1) / 2.0
    cy = (Y_MAX - 1) / 2.0
    max_dist = math.hypot(cx, cy)

    steps = 9
    band_count = 15
    band_brightness = [int(255 * (1.0 - i / (band_count - 1))) for i in range(band_count)]

    for frame in range(steps):
        if not running:
            return

        t = frame / steps
        radius = t * max_dist

        for side in connected_sides:
            reset_side(side, 0)

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

                    set_side_pixel(side, x, y, brightness)

            send_side(side)

        time.sleep(0.008)

    reset_all(0)
    send_all()


def draw_side_profile(side: str, tick: int, t: float) -> None:
    profile = active_profiles[side]

    if profile == "bars":
        draw_bars_step(side)
    elif profile == "gradient":
        draw_gradient_step(side, t)
    elif profile == "clock":
        draw_clock_step(side)
    elif profile == "rain":
        draw_digital_rain_step(side)
    elif profile == "weather":
        draw_weather_step(side, tick)
    else:
        reset_side(side, 0)
        send_side(side)


def worker_loop():
    t = 0.0
    tick = 0

    play_startup_ripple()

    while running:
        for side in connected_sides:
            draw_side_profile(side, tick, t)

        tick += 1
        t += 0.05
        time.sleep(0.08)


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


def make_set_profile(side: str, profile: str):
    def _set_profile(icon, menu_item):
        active_profiles[side] = profile
    return _set_profile


def profile_checked(side: str, profile: str):
    return lambda _: active_profiles[side] == profile


def on_quit(icon, menu_item):
    global running
    running = False
    icon.stop()


def build_side_menu(side: str):
    return Menu(
        item("System Bars", make_set_profile(side, "bars"), checked=profile_checked(side, "bars")),
        item("Waterfall Gradient", make_set_profile(side, "gradient"), checked=profile_checked(side, "gradient")),
        item("Clock", make_set_profile(side, "clock"), checked=profile_checked(side, "clock")),
        item("Digital Rain", make_set_profile(side, "rain"), checked=profile_checked(side, "rain")),
        item("Local Weather", make_set_profile(side, "weather"), checked=profile_checked(side, "weather")),
    )


def main():
    init_matrices()

    thread = threading.Thread(target=worker_loop, daemon=True)
    thread.start()

    menu_items = []

    if left_matrix is not None:
        menu_items.append(item("Left Matrix", build_side_menu("left")))

    if right_matrix is not None:
        menu_items.append(item("Right Matrix", build_side_menu("right")))

    menu_items.append(item("Quit", on_quit))

    menu = Menu(*menu_items)

    icon_image = load_framework_icon()

    title = "LED Matrix"
    if left_matrix is not None and right_matrix is not None:
        title = "LED Matrix - Dual Mode"
    elif left_matrix is not None:
        title = f"LED Matrix - Left Only ({DEFAULT_PORTS['left']})"
    elif right_matrix is not None:
        title = f"LED Matrix - Right Only ({DEFAULT_PORTS['right']})"

    icon = pystray.Icon("LEDMatrix", icon_image, title, menu)
    icon.run()


if __name__ == "__main__":
    main()
