# LED Matrix System Tray Profiles

This is a small Python script that drives one or two 9×34 LED matrices from the Windows system tray. It shows:

- A short **ripple** animation at startup.
- A **System Bars** view (CPU, RAM, battery).
- A **Waterfall Gradient** animation.
- A **Clock** (vertical `HH:MM`).
- A **Digital Rain** animation.
- A **Local Weather** view (current conditions + temperature).

The script adds an icon to the Windows system tray so you can switch between profiles from a menu.

If two matrices are connected, the script can control them independently as **left** and **right** panels. If only one matrix is connected, it will still run in single-panel mode.

---

## Files

You should have these files together in the same folder (for example `C:\\tools`):

- `led_tray_profiles.py` – the main Python script.
- `start_led_tray.bat` – optional batch file to launch the script.
- `led_matrix.py`
- (Optional) `framework_icon.png` – custom icon for the tray (otherwise a simple default icon is generated).

---

## Prerequisites

1. **Windows PC** with one or two attached LED matrices that work with the `led_matrix` Python module.
2. **Python 3.x** installed and on your PATH:
   - Download from [https://www.python.org/](https://www.python.org/) and check “Add Python to PATH” during install.
3. **Python packages**:
   - `psutil` – reads CPU, RAM, battery stats.
   - `pystray` – creates the system tray icon and menu.
   - `Pillow` – used to create the tray icon image (`PIL`).
4. **Internet connection** for the weather profile:
   - The **Local Weather** profile uses the Open-Meteo Forecast API to request current `temperature_2m` and `weather_code` data for the configured latitude and longitude.

> Note: the weather feature uses Python standard-library modules (`urllib.request` and `json`) in addition to the packages above, so you do **not** need to install an extra weather package.

---

## One-time setup

1. Create a folder for the project, e.g.:

   C:\\tools

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

## Matrix connection

The script supports:

- **One matrix connected** – the app will still start and run normally.
- **Two matrices connected** – the app will detect both and treat them as **left** and **right** panels.
- **No matrices connected** – the script will raise an error and exit.

By default, the script looks for:

- **Left matrix** on `COM3`
- **Right matrix** on `COM5`

If your hardware uses different COM ports, change the values near the top of `led_tray_profiles.py`:

```python
DEFAULT_PORTS = {
    "left": "COM3",
    "right": "COM5",
}
```

When the script starts, the tray app title changes depending on what it found:

- `LED Matrix - Dual Mode`
- `LED Matrix - Left Only (COM3)`
- `LED Matrix - Right Only (COM5)`

---

## How to run

### Option 1 – Run the Python script directly

1. Open **Command Prompt**.
2. Change to the folder where you put the files, for example:

   cd C:\\tools

3. Run:

   python led_tray_profiles.py

   or, if needed:

   py led_tray_profiles.py

4. After a moment:
   - The LED matrix will show a startup ripple.
   - A new icon will appear in the **system tray** (bottom-right of the Windows taskbar).
   - Right-click the icon to switch profiles or quit.

### Option 2 – Use the batch file

If `start_led_tray.bat` is set up like this (adjust the path if you used a different folder):

   @echo off
   cd /d C:\\tools
   python led_tray_profiles.py

You can:

1. Double-click `start_led_tray.bat` in Explorer.
2. The tray icon will appear and the LED matrix will start updating.

---

## Profiles

From the tray icon menu you can choose:

- **System Bars**  
  Shows CPU, RAM, and battery usage as thick vertical bars.

- **Waterfall Gradient**  
  Animated brightness gradient flowing down the matrix.

- **Clock**  
  12-hour time displayed as vertical digits in the center.

- **Digital Rain**  
  Matrix-style falling columns with a bright “head” and fading tail.

- **Local Weather**  
  Shows current weather conditions and temperature for the configured location. The script calls the Open-Meteo API using your latitude and longitude, reads `temperature_2m` and `weather_code`, and maps the weather code into a small icon set such as clear, cloudy, fog, rain, snow, or storm.

- **Quit**  
  Stops updating the LED matrix and exits the tray app.

> In dual-matrix mode, each side has its own submenu in the tray icon, so you can run different profiles on the left and right panels at the same time.

---

## Changing the weather location

The weather view uses two constants near the top of `led_tray_profiles.py`:

```python
WEATHER_LAT = 42.534901
WEATHER_LON = -92.445312
```

Change those values to the latitude and longitude of the place you want to use, then save the file and restart the script.

Example:

```python
WEATHER_LAT = 40.7128
WEATHER_LON = -74.0060
```

That would use New York City.

### How to find coordinates

- In **Google Maps**, right-click the spot you want and copy the latitude/longitude shown in the menu.
- You can also use the **Open-Meteo Geocoding API** to search for a city and get its coordinates.

---

## Weather notes

- The weather data refreshes periodically rather than every frame, so the display does not spam the API continuously.
- If the weather request fails and there is no cached result yet, the script falls back to a simple placeholder until a successful fetch is available.
- The weather profile currently requests Fahrenheit values.

---

## Autostart with Windows (optional)

If you want this to start automatically when you log in:

1. Make sure `start_led_tray.bat` works when you double-click it.
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
  - Verify the configured COM ports match your actual hardware.

- **Only one matrix is detected**
  - Check the USB/serial connection for the missing panel.
  - Confirm the correct COM port is assigned in `DEFAULT_PORTS`.

- **Weather profile does not update**
  - Confirm you have an active internet connection.
  - Check that `WEATHER_LAT` and `WEATHER_LON` are valid numbers in the script.
  - Make sure the Open-Meteo request URL in the script has not been edited incorrectly.

- **Multiple Python versions**
  - You may need to use `py -3 led_tray_profiles.py` or adjust the `python` call in the batch file to the correct interpreter.
