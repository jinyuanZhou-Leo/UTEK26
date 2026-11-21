import { useEffect, useState } from "react"
import { TrendingDown, TrendingUp } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/ui/card"
import { Progress } from "@/ui/progress"
import { Badge } from "@/ui/badge"
import { Button } from "@/ui/button"
import { Label } from "@/ui/label"
import { Item, ItemContent, ItemTitle } from "@/ui/item"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/ui/empty"

// ---------- Data shape (same field names as the backend) ----------
type Components = { upper_extremity: number; ocular: number; postural: number; cognitive: number }
type Alert = { target: string; message: string }
type State = {
  systemic_fatigue_score: number
  level: string
  trend_per_min: number
  components: Components
  reasons: string[]
  alert: Alert | null
}

const PART_NAMES: Record<keyof Components, string> = {
  upper_extremity: "Wrist and arm",
  ocular: "Eyes",
  postural: "Neck and posture",
  cognitive: "Mental",
}

function levelOf(score: number) {
  if (score < 40) return "low"
  if (score < 70) return "moderate"
  if (score < 85) return "high"
  return "critical"
}

// ---------- Mock data: score goes 20 -> 90 -> 20 slowly ----------
function makeMock(tick: number): State {
  const score = Math.round(55 + 35 * Math.sin(tick / 12))
  const prev = Math.round(55 + 35 * Math.sin((tick - 1) / 12))
  const parts: Components = {
    upper_extremity: Math.min(100, score + 8),
    ocular: Math.max(0, score - 5),
    postural: Math.max(0, score - 15),
    cognitive: Math.max(0, score - 25),
  }
  return {
    systemic_fatigue_score: score,
    level: levelOf(score),
    trend_per_min: (score - prev) * 12,
    components: parts,
    reasons: score > 50
      ? ["Typing for 48 min without a break", "Blinking 42% less than usual"]
      : ["Working normally"],
    alert: score >= 70 ? { target: "ocular", message: "Look at something away for 20 seconds." } : null,
  }
}

export default function Dashboard() {
  const [state, setState] = useState<State | null>(null)   // null = backend not connected yet
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    let tick = 0
    const timer = setInterval(() => {
      tick += 1
      setState(makeMock(tick))
    }, 2000) // mock: 2 s so the demo moves faster; real backend is every 5 s
    return () => clearInterval(timer)
  }, [])

  // ---------- Module 5: waiting for backend ----------
  if (state === null) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background text-foreground">
        <Empty>
          <EmptyHeader>
            <EmptyTitle>Waiting for the sensor service</EmptyTitle>
            <EmptyDescription>The fatigue score appears here once the backend is running.</EmptyDescription>
          </EmptyHeader>
        </Empty>
      </main>
    )
  }

  const score = state.systemic_fatigue_score
  const rising = state.trend_per_min >= 0
  const showAlert = state.alert !== null && !dismissed

  return (
    <main className="min-h-screen space-y-4 bg-background p-6 text-foreground">
      {/* ---------- Module 4: alert card (only when there is an alert) ---------- */}
      {showAlert && state.alert && (
        <Card>
          <CardHeader>
            <CardTitle>Time for a short break</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-between gap-4">
            <p>{state.alert.message}</p>
            <div className="flex gap-2">
              <Button onClick={() => setDismissed(true)}>Done</Button>
              <Button variant="outline" onClick={() => setDismissed(true)}>Later</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-4">
        {/* ---------- Module 1: big score ---------- */}
        <Card>
          <CardHeader>
            <CardTitle>Fatigue score</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-end gap-3">
              <p className={`text-6xl font-semibold text-level-${state.level}`}>{score}</p>
              {rising ? <TrendingUp className="mb-2" /> : <TrendingDown className="mb-2" />}
            </div>
            <Badge variant="outline">{state.level}</Badge>
            <Progress value={score} />
          </CardContent>
        </Card>

        {/* ---------- Module 2: four body parts ---------- */}
        <Card>
          <CardHeader>
            <CardTitle>Body parts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {(Object.keys(PART_NAMES) as (keyof Components)[]).map((key) => (
              <div key={key} className="space-y-1">
                <div className="flex justify-between">
                  <Label>{PART_NAMES[key]}</Label>
                  <span className={`text-sm text-level-${levelOf(state.components[key])}`}>
                    {state.components[key]}
                  </span>
                </div>
                <Progress value={state.components[key]} />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* ---------- Module 3: reasons ---------- */}
      <Card>
        <CardHeader>
          <CardTitle>Why this score</CardTitle>
        </CardHeader>
        <CardContent>
          {state.reasons.map((reason) => (
            <Item key={reason} variant="muted" size="sm" className="mb-2">
              <ItemContent>
                <ItemTitle>{reason}</ItemTitle>
              </ItemContent>
            </Item>
          ))}
        </CardContent>
      </Card>
    </main>
  )
}
