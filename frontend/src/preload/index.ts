// AI-GENERATED FILE (Claude, 2026-11-21) | reviewed by: Angelia Li | purpose: expose window.sentinel.onMetrics to the renderer
import { contextBridge, ipcRenderer, type IpcRendererEvent } from 'electron'
import type { FatigueState, SentinelBridge } from '../shared/types'

const bridge: SentinelBridge = {
  onMetrics: (cb) => {
    const listener = (_e: IpcRendererEvent, state: FatigueState | null): void => cb(state)
    ipcRenderer.on('metrics', listener)
    return () => ipcRenderer.removeListener('metrics', listener)
  }
}

contextBridge.exposeInMainWorld('sentinel', bridge)
