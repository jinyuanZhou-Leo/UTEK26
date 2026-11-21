// AI-GENERATED FILE (Claude, 2026-11-21) | reviewed by: Angelia Li | purpose: Electron main process: window + poll backend /metrics every 5 s
import { join } from 'node:path'
import { app, BrowserWindow } from 'electron'

const METRICS_URL = 'http://127.0.0.1:8080/metrics'
const POLL_MS = 5000

// Fetch in the main process (no CORS limits), then forward to the page over IPC.
async function pollMetrics(win: BrowserWindow): Promise<void> {
  try {
    const res = await fetch(METRICS_URL)
    const data = await res.json()
    // Backend returns {"status": "starting"} before the first tick
    win.webContents.send('metrics', 'systemic_fatigue_score' in data ? data : null)
  } catch {
    win.webContents.send('metrics', null) // backend not running yet
  }
}

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1000,
    height: 700,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })
  // electron-vite sets ELECTRON_RENDERER_URL in dev mode
  if (process.env['ELECTRON_RENDERER_URL']) {
    win.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    win.loadFile(join(__dirname, '../renderer/index.html'))
  }
  win.webContents.on('did-finish-load', () => void pollMetrics(win))
  const timer = setInterval(() => void pollMetrics(win), POLL_MS)
  win.on('closed', () => clearInterval(timer))
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
