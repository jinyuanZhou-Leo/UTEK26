// AI-GENERATED FILE (Claude, 2026-11-21) | reviewed by: Angelia Li | purpose: latest FatigueState from the main process
import { useEffect, useState } from 'react'
import type { FatigueState } from '../../../shared/types'

export function useFatigue(): FatigueState | null {
  const [state, setState] = useState<FatigueState | null>(null)
  useEffect(() => window.sentinel.onMetrics(setState), [])
  return state
}
