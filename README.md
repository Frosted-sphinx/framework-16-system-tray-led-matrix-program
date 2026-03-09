# LED Matrix System Tray Profiles

This is a small Python script that drives a 9×34 LED matrix from the Windows system tray. It shows:

- A short **ripple** animation at startup.
- A **System Bars** view (CPU, RAM, battery).
- A **Waterfall Gradient** animation.
- A **Clock** (vertical `HH:MM`).
- A **Digital Rain** animation.

The script adds an icon to the Windows system tray so you can switch between profiles from a menu.

---

## Files

You should have these files together in the same folder (for example `C:\tools`):

- `led_tray_profiles.py` – the main Python script.
- `start_led_tray.bat` – optional batch file to launch the script.
- `led_matrix.py` 
- (Optional) `framework_icon.png` – custom icon for the tray (otherwise a simple default icon is generated).

---

## Prerequisites

1. **Windows PC** with an attached LED matrix that works with the `led_matrix` Python module.
2. **Python 3.x** installed and on your PATH:
   - Download from https://www.python.org/ and check “Add Python to PATH” during install.
3. **Python packages**:
   - `psutil` – reads CPU, RAM, battery stats.[web:423][web:86][web:259]
   - `pystray` – creates the system tray icon and menu.[web:490][web:435]
   - `Pillow` – used to create the tray icon image (`PIL`).[web:485][web:488]

---

## One‑time setup

1. Create a folder for the project, e.g.:

   C:\tools

2. Copy these files into that folder:

   - `led_tray_profiles.py`
   - `start_led_tray.bat`
   - `led_matrix.py` 
   - Optional: `framework_icon.png`

3. Open **Command Prompt** and install the required Python packages:

   pip install psutil pystray Pillow

   If you have multiple Python versions, you may need:

   py -m pip install psutil pystray Pillow

---

## How to run

### Option 1 – Run the Python script directly

1. Open **Command Prompt**.
2. Change to the folder where you put the files, for example:

   cd C:\tools

3. Run:

   python led_tray_profiles.py

   or, if needed:

   py led_tray_profiles.py

4. After a moment:
   - The LED matrix will show a startup ripple.
   - A new icon will appear in the **system tray** (bottom‑right of the Windows taskbar).
   - Right‑click the icon to switch profiles or quit.

### Option 2 – Use the batch file

If `start_led_tray.bat` is set up like this (adjust the path if you used a different folder):

   @echo off
   cd /d C:\tools
   python led_tray_profiles.py

You can:

1. Double‑click `start_led_tray.bat` in Explorer.
2. The tray icon will appear and the LED matrix will start updating.

---

## Profiles

From the tray icon menu you can choose:

- **System Bars**
  Shows CPU, RAM, and battery usage as thick vertical bars.[web:423][web:259]

- **Waterfall Gradient**
  Animated brightness gradient flowing down the matrix.

- **Clock (HH:MM vertical)**
  12‑hour time displayed as vertical digits in the center.

- **Digital Rain**
  Matrix‑style falling columns with a bright “head” and fading tail.[web:453][web:446]

- **Quit**
  Stops updating the LED matrix and exits the tray app.

---

## Autostart with Windows (optional)

If you want this to start automatically when you log in:

1. Make sure `start_led_tray.bat` works when you double‑click it.
2. Press `Win + R`, type:

   shell:startup

   and press Enter. This opens your **Startup** folder.

3. Copy a **shortcut** to `start_led_tray.bat` into this Startup folder.

Next time you log in, Windows will run the batch file, which launches the Python script and shows the tray icon.

---

## Troubleshooting

- **Tray icon does not appear**
  - Make sure Python is installed and accessible from the command line.
  - Confirm `psutil`, `pystray`, and `Pillow` are installed with `pip list`.

- **No output on the LED matrix**
  - Confirm your `led_matrix` module is present in the same folder and correctly configured for your hardware.
  - Ensure any required drivers or permissions for the LED device are installed.

- **Multiple Python versions**
  - You may need to use `py -3 led_tray_profiles.py` or adjust the `python` call in the batch file to the correct interpreter.
