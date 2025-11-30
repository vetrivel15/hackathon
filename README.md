# Robot Control System 

A lightweight local demo that simulates a robot, serves a single-page control and monitoring UI (`interface.html`), and exposes simple HTTP endpoints for commands and system actions. The backend is implemented in Python and writes live state to `mqtt_live_data.json`; the frontend polls that file (or `/get_live_data`) to render telemetry and a movement tracker.

## Prerequisites
- Python 3.8 or newer (3.9 recommended)
- Git (optional, for cloning)
- A modern web browser (Chrome, Edge, Firefox)

Optional (for generating Word `.docx` documents):
- `python-docx` (install with `pip install python-docx`)

## Files of interest
- `interface.html` – Single-page web UI (open in browser)
- `run_system.py` – Starts the robot simulator and the simple web server
- `mqtt_server.py` – Robot simulator that updates `mqtt_live_data.json`
- `robot_system.py` – Kinematics and teleoperation logic
- `mqtt_live_data.json` – Live data file written by the simulator (created at runtime)
- `generate_all_docx.py` / `generate_docx.py` – Scripts to produce Word `.docx` documents if desired
- `Product_Requirements.doc.rtf`, `High_Level_Design.doc.rtf`, `Component_Module_TestPlan.doc.rtf` – RTF docs included in the repo

## Quick start (Windows PowerShell)
Open PowerShell and change to the project folder (replace path if needed):

```powershell
cd C:\Divya\live_mqtt_demo
```

1) (Optional) Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) (Optional) Install python-docx only if you want to generate `.docx` files from the included scripts:

```powershell
pip install python-docx
```

3) Start the system (this starts the simulator and the web server on port 8100):

```powershell
python run_system.py
```

You should see console output saying the system is running and a line like:

```
🔗 Interface: http://localhost:8100/interface.html
```

If the script attempts to auto-open the browser it may do so; otherwise open the URL manually in your browser.

4) Use the UI
- Robot Control page: send drive commands (Forward, Back, Left, Right, Rotate Left/Right), adjust speed, and view the movement tracker.
- System Status page: view diagnostics, check for updates (simulated), and run system actions.
- The top banner shows connection status and a `Last:` time indicating the most recent live-data poll/update.

## Useful commands and endpoints
- GET live data (JSON): `http://localhost:8100/get_live_data` or fetch `mqtt_live_data.json` directly
- POST send command: `POST http://localhost:8100/send_command` with JSON body `{ "direction": "forward", "speed": 0.5 }` (speed is 0.1..1.0 in backend normalization)
- POST system action: `POST http://localhost:8100/system_action` with JSON body `{ "type": "reset_position" }` to reset kinematics to origin

Example PowerShell curl (invoke-webrequest) to send a command:

```powershell
$body = '{"direction":"forward","speed":0.5}'
Invoke-WebRequest -Uri http://localhost:8100/send_command -Method POST -Body $body -ContentType 'application/json'
```

## Demo sequence (manual)
1. Open the UI at `http://localhost:8100/interface.html`.
2. Click `🔄 Reset Position` (or use the reset action) to ensure starting at origin.
3. Set speed to 50% and click `⬆️ Forward` — observe the movement tracker and position X value increase.
4. Click `↪️ Rot L` then `🔍` (or send another forward) — verify orientation arrow rotates (even if X/Y unchanged). Check activity log for entries.

## Generating Word documents (optional)
Two options are included:

- Single generator (all docs):

```powershell
pip install python-docx
python generate_all_docx.py
```

- Single document generator (example):

```powershell
pip install python-docx
python generate_docx.py
```

Both scripts write `.docx` files to the repository root. If you don't want to install packages, the repo already contains `.doc.rtf` files that Word opens.

## Stopping the server
- If started in a console, press `Ctrl+C` to stop.
- To kill any stray Python processes (use with caution):

```powershell
taskkill /F /IM python.exe
```

## Troubleshooting
- "Cannot set properties of null" in the browser console: this used to happen if UI JS attempted to update DOM elements that were removed; the UI now guards DOM writes, but if you see this error, please reload the page and send me the first console error line.
- `Address already in use` when starting: ensure no other server is running on port 8100. Either stop the other process or change `PORT` in `run_system.py` and restart.
- If `mqtt_live_data.json` is missing or stale: ensure the simulator started successfully. Look for startup logs in the terminal where you ran `python run_system.py`.

## Development notes
- The backend uses a simple file-based flow for demo simplicity. A future improvement is replacing polling with WebSocket or MQTT over WebSocket for lower-latency updates.
- Theta in JSON is in radians. The frontend converts to degrees for display and converts to radians when drawing orientation.

## Tests
- The repo includes a test plan document and notes for unit/integration tests. To add tests, create a `tests/` directory and use `pytest` to author/execute unit tests for `robot_system.py` and integration tests for `mqtt_server.py` and `run_system.py`.

## Contact / Next steps
If you want, I can:
- Run the `.docx` generator here and attach files (requires installing `python-docx` in this environment) — say "please run generators here".
- Help add unit tests and CI configuration.
- Improve the UI styling or convert to a simple build toolchain.

---
README generated by the project tooling on November 30, 2025.
