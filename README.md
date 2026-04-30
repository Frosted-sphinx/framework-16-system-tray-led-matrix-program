# LED Matrix System Tray App

This repository contains two ways to run the LED Matrix tray app:

- **v2 – Open-source Python scripts** you can run and modify yourself.
- **v2.5 – Packaged Windows app with installer** for an easier, no-Python setup.

Both versions drive one or two 9×34 LED matrices from the Windows system tray and support these profiles:

- A short **ripple** animation at startup.
- **System Bars** (CPU, RAM, battery).
- **Waterfall Gradient** animation.
- **Clock** (vertical `HH:MM` style).
- **Digital Rain** animation.
- **Local Weather** (current conditions + temperature).

If two matrices are connected, the app can control them independently as **left** and **right** panels. If only one matrix is connected, it runs in single-panel mode.

---

## Quick start

You can either:

- Use the **v2.5 installer** (recommended for most users), or  
- Keep using the **v2 open-source Python files** if you want to edit the code directly.

### Option A – v2.5 installer (no Python required)

The v2.5 app is a packaged Windows tray application:

- No need to install Python or any packages.
- Includes an integrated **Settings** window:
  - Select left/right COM ports.
  - Choose default profiles per side.
  - Configure weather location and units.
  - Control startup behavior.

#### Install

1. Go to the **Releases** page on this repo and download the latest `LEDMatrixTraySetup-vX.Y.exe`.  
2. Run the installer and follow the prompts.
3. After installation, launch **LED Matrix Tray** from the Start Menu (or let it auto-start if you enable that).

When running:

- The LED matrix will show a startup ripple.
- A tray icon will appear in the Windows taskbar.
- Right-click the icon to switch profiles, open Settings, or quit.

> Note: The v2.5 app is open source. You’re allowed to use it and modiy it, but you **may not sell** it or any product based on it without my permission (see `LICENSE`).

---

### Option B – v2 open-source Python scripts

The v2 scripts remain in this repo for anyone who wants to:

- Read or modify the source code.
- Run the tray app directly via Python.
- Build their own variations.

These files live in the repo as:

- `v2/led_tray_profiles.py` – main Python script.
- `v2/start_led_tray.bat` – optional batch file to launch the script.
- `v2/led_matrix.py` – LED matrix driver.
- Optional: `framework_icon.png` – custom tray icon (otherwise a simple default icon is generated).

#### Prerequisites

1. **Windows PC** with one or two supported 9×34 LED matrices.
2. **Python 3.x** installed and on your PATH:
   - Download from [https://www.python.org/](https://www.python.org/) and check “Add Python to PATH” during install.
3. Python packages:
   - `psutil` – CPU, RAM, battery stats.
   - `pystray` – system tray icon and menu.
   - `Pillow` – tray icon image (`PIL`).
4. **Internet connection** for the weather profile (Open-Meteo API).

The weather feature uses `urllib.request` and `json` from Python’s standard library, so you don’t need any extra weather-specific packages.

#### One-time setup

1. Create a folder for the project, e.g.:

   ```text
   C:\tools\led-matrix-tray-v2
   ```

2. Copy these files from the repo’s `v2` folder into that folder:

   - `led_tray_profiles.py`
   - `start_led_tray.bat`
   - `led_matrix.py`
   - Optional: `framework_icon.png`

3. Install the required Python packages:

   ```text
   pip install psutil pystray Pillow
   ```

   If you have multiple Python versions:

   ```text
   py -m pip install psutil pystray Pillow
   ```

#### COM port configuration

The v2 script supports:

- **One matrix** – runs in single-panel mode.
- **Two matrices** – treats them as **left** and **right**.
- **No matrices** – exits with an error.

By default, it uses:

- Left matrix – `COM3`
- Right matrix – `COM5`

Edit `DEFAULT_PORTS` near the top of `led_tray_profiles.py` if your ports are different:

```python
DEFAULT_PORTS = {
    "left": "COM3",
    "right": "COM5",
}
```

When the script starts, the tray title reflects what was detected:

- `LED Matrix - Dual Mode`
- `LED Matrix - Left Only (COM3)`
- `LED Matrix - Right Only (COM5)`

#### Running v2

**Option 1 – Directly via Python**

```text
cd C:\tools\led-matrix-tray-v2
python led_tray_profiles.py
```

(or `py led_tray_profiles.py`)

**Option 2 – Using the batch file**

If `start_led_tray.bat` looks like:

```bat
@echo off
cd /d C:\tools\led-matrix-tray-v2
python led_tray_profiles.py
```

you can just double-click the batch file.

Once running:

- The matrix shows a startup ripple.
- A tray icon appears in the Windows taskbar.
- Right-click the icon to switch profiles or quit.

---

## Profiles (both v2 and v2.5)

- **System Bars**  
  CPU, RAM, and battery usage as vertical bars.

- **Waterfall Gradient**  
  Animated vertical brightness gradient.

- **Clock**  
  12-hour time shown as vertical digits.

- **Digital Rain**  
  Matrix-style falling columns with a bright head and fading tail.

- **Local Weather**  
  Shows an icon for current weather (clear, cloudy, fog, rain, snow, storm) plus the current temperature, using the Open-Meteo API and your configured latitude/longitude.

In dual-matrix mode, each side has its own submenu in the tray icon, so you can run different profiles on the left and right panels at the same time.

---

## Weather configuration

### v2

In `led_tray_profiles.py`, adjust:

```python
WEATHER_LAT = 42.534901
WEATHER_LON = -92.445312
```

to match your location (for example, New York City):

```python
WEATHER_LAT = 40.7128
WEATHER_LON = -74.0060
```

### v2.5

Use the **Settings** window:

- Set latitude and longitude.
- Choose Fahrenheit or Celsius.
- Set the refresh interval in seconds.

> Tip: In Google Maps you can right-click a point and copy its latitude/longitude.

---

## Autostart with Windows

### v2.5

Use the **Start with Windows** option in the Settings window (recommended).

### v2

1. Verify `start_led_tray.bat` works when double-clicked.
2. Press `Win + R`, type `shell:startup`, and press Enter.
3. Place a shortcut to `start_led_tray.bat` in the Startup folder.

---

## Troubleshooting

- **Tray icon does not appear**
  - For v2: Check Python is installed and that `psutil`, `pystray`, and `Pillow` are installed.
  - For v2.5: Try reinstalling from the latest installer and check antivirus/SmartScreen prompts.

- **No output on the LED matrix**
  - Confirm the matrices are connected and on the COM ports you configured.
  - Make sure any required USB/serial drivers are installed.

- **Only one matrix detected**
  - Check the cable and port for the missing panel.
  - Make sure its COM port is different from the other and correctly configured.

- **Weather does not update**
  - Confirm you have internet access.
  - Ensure latitude/longitude are set correctly.
  - For v2, verify the Open-Meteo URL in the script has not been altered incorrectly.

---

## Contributing / Feedback

- For v2 script changes, feel free to open a PR or fork and experiment.
- For v2.5 feature requests or bug reports, open an issue and include:
  - App version.
  - Description of the problem and steps to reproduce.
 
  or email: CJVsolutions2026@outlook.com
