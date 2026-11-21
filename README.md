# Blinky

Blinky is an invisible ergonomic sentinel for desktop work. It runs in the background and every 5 seconds computes a **Systemic Fatigue Score (0–100)** from keyboard, mouse and webcam signals. The score is written to a local JSON file and served at `http://127.0.0.1:8080/metrics`. Blinky only nudges you when your body actually needs a break, and waits until you are out of flow (no fixed timers, no modal pop-ups, silent during meetings and full-screen apps).

Privacy: keystroke content is never recorded (counts and timing only), video frames are never saved, and all data stays on your machine in `~/.utekinetics/`.

## Architecture

| Part        | Stack                                                          | Role                                                                                          |
| ----------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `backend/`  | Python 3.12, uv, FastAPI, pynput, pywinctl, OpenCV + MediaPipe | Collects signals, scores fatigue every 5 s, writes JSON, serves HTTP/WebSocket on `127.0.0.1` |
| `frontend/` | Electron 45, React 19, Vite, Tailwind 4, shadcn/ui             | Tray icon, dashboard and gentle reminders; talks to the backend over HTTP/WebSocket only      |

The backend runs fine on its own; the desktop app is optional.

## Requirements

- Windows 10/11 or macOS
- [uv](https://docs.astral.sh/uv/) (Python 3.12)
- Node.js ≥ 22, only for the desktop app

## 1. Install and run the backend

```bash
cd backend
uv sync --extra input --extra vision   # or: uv sync --all-extras
uv run python scripts/check_env.py     # optional self-check
uv run python -m sentinel
```

Dependency groups: `input` = keyboard/mouse/foreground app (pynput, pywinctl), `vision` = webcam (numpy, opencv-python, mediapipe). Plain `uv sync` installs only the core. If a group is missing, Blinky still starts and marks that sensor as unavailable.

> **Intel Mac:** MediaPipe has no Intel-Mac build, so `vision` is skipped automatically. Everything else works; webcam data shows as unavailable.

Command-line flags:

| Flag          | Effect                                                 |
| ------------- | ------------------------------------------------------ |
| `--mock`      | Use fake sensor data (no permissions or camera needed) |
| `--no-camera` | Disable the webcam                                     |
| `--headless`  | Run without the desktop app                            |
| `--port N`    | Change the port (default 8080)                         |

Check the output:

- `http://127.0.0.1:8080/metrics`: latest score (refreshes every 5 s)
- `http://127.0.0.1:8080/health`: health check
- `ws://127.0.0.1:8080/ws`: live updates
- `~/.utekinetics/metrics.json`: same data on disk (written atomically)

### OS permissions

- **macOS:** System Settings → Privacy & Security → enable your terminal under **Accessibility**, **Input Monitoring** and **Camera**, then fully quit (⌘Q) and reopen the terminal.
- **Windows:** Settings → Privacy & security → Camera → allow desktop apps. Keyboard/mouse need no extra permission.

## 2. Run the desktop app

Start the backend first (step 1), then in a second terminal:

```bash
cd frontend
npm ci            # installs exact versions from package-lock.json
npm run dev       # opens the Blinky window
```

If Electron fails to start with *"Electron failed to install correctly"* (the binary download was skipped or interrupted), run:

```bash
node node_modules/electron/install.js
```

Slow Electron download: set `ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"` before `npm ci`.

## 3. Deploy

**Headless (judging / server-style):**

```bash
cd backend
uv sync --extra input --extra vision
uv run python -m sentinel --headless
```

Leave it running; read the score from `~/.utekinetics/metrics.json` or `http://127.0.0.1:8080/metrics`. The service only listens on `127.0.0.1`.

**Desktop app (production build):**

```bash
cd frontend
npm ci
npm run build     # bundles main, preload and renderer into frontend/out/
npm run preview   # runs the built app
```

The app connects to the backend on `127.0.0.1:8080`, so keep `uv run python -m sentinel` running alongside it.

## Development

| Task                      | Command                                                                                  |
| ------------------------- | ---------------------------------------------------------------------------------------- |
| Backend tests / lint      | `cd backend && uv run pytest` / `uv run ruff check .`                                    |
| Test a single sensor      | `uv run python -m sentinel.sensors.keyboard` (or `mouse`, `context`, `vision --preview`) |
| Frontend lint / typecheck | `cd frontend && npm run lint` / `npm run typecheck`                                      |

More detail: [`docs/SETUP.md`](docs/SETUP.md) (setup), [`docs/INTERFACE.md`](docs/INTERFACE.md) (data contract), [`docs/DESIGN.md`](docs/DESIGN.md) (design).

## Team

- Keyboard sensor and scoring: _Holly Liu_
- Mouse sensor, core loop and API: _Yifan Zhou_
- Webcam sensor: _Jinyuan Zhou_
- UI/UX + Scoring + Logo: _Angelia Li_

## AI usage and attributions

AI-generated code is marked in-file (`>>> AI-GENERATED` blocks) and listed in [`AI_USAGE.md`](AI_USAGE.md). AI plus external code is kept within 30% of the codebase.

Libraries and resources:

- [FastAPI](https://fastapi.tiangolo.com/) , [Uvicorn](https://www.uvicorn.org/) , [psutil](https://github.com/giampaolo/psutil)
- [pynput](https://github.com/moses-palmer/pynput) , [PyWinCtl](https://github.com/Kalmat/PyWinCtl)
- [OpenCV](https://opencv.org/) , [NumPy](https://numpy.org/), [MediaPipe](https://github.com/google-ai-edge/mediapipe) and the `face_landmarker.task` 
- [Electron](https://www.electronjs.org/), [electron-vite](https://electron-vite.org/), [Vite](https://vite.dev/), [React](https://react.dev/), [Tailwind CSS](https://tailwindcss.com/), [Base UI](https://base-ui.com/), [lucide-react](https://lucide.dev/), [Recharts](https://recharts.org/)
- [shadcn/ui](https://ui.shadcn.com/) : components in `frontend/src/renderer/src/ui/` are generated by the shadcn CLI. This module is the UI Component Library of the project frontend
