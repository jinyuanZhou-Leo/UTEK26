// AI-GENERATED FILE (Claude, 2026-11-21) | reviewed by: Angelia Li
// Shared types matching backend/src/sentinel/models.py (keep snake_case).

export type Level = 'low' | 'moderate' | 'high' | 'critical'

export interface ComponentScores {
  upper_extremity: number
  ocular: number
  postural: number
  cognitive: number
}

export interface Contribution {
  signal: string
  label: string
  delta: number
}

export interface FatigueState {
  timestamp: string
  seq: number
  systemic_fatigue_score: number
  level: Level
  components: ComponentScores
  top_contributors: Contribution[]
  calibrating: boolean
  sensors: Record<string, boolean>
}

export interface SentinelBridge {
  onMetrics: (cb: (state: FatigueState | null) => void) => () => void
}
