import { Card, CardContent, CardHeader, CardTitle } from "@/ui/card"
import { Progress } from "@/ui/progress"
import { Badge } from "@/ui/badge"
import { Label } from "@/ui/label"
import { Item, ItemContent, ItemTitle } from "@/ui/item"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/ui/empty"
// >>> AI-GENERATED (Claude, 2026-11-21) | reviewed by: Angelia Li | purpose: use real backend data instead of mock
import type { ComponentScores, Level } from "../../shared/types"
import { useFatigue } from "./hooks/use-fatigue"

// Full class names so Tailwind can find them at build time (no `text-level-${x}`)
const LEVEL_TEXT: Record<Level, string> = {
  low: "text-level-low",
  moderate: "text-level-moderate",
  high: "text-level-high",
  critical: "text-level-critical",
}
// <<< AI-GENERATED

const PART_NAMES: Record<keyof ComponentScores, string> = {
  upper_extremity: "Wrist and arm",
  ocular: "Eyes",
  postural: "Neck and posture",
  cognitive: "Mental",
}

export default function Dashboard() {
  const state = useFatigue()   // null = backend not connected yet

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

  return (
    <main className="min-h-screen space-y-4 bg-background p-6 text-foreground">
      <div className="grid grid-cols-2 gap-4">
        {/* ---------- Module 1: big score ---------- */}
        <Card>
          <CardHeader>
            <CardTitle>Fatigue score</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className={`text-6xl font-semibold ${LEVEL_TEXT[state.level]}`}>{score.toFixed(1)}</p>
            <Badge variant="outline">{state.level}</Badge>
            {state.calibrating && (
              <p className="text-sm text-muted-foreground">Learning your normal patterns (first 10 minutes)</p>
            )}
            <Progress value={score} />
          </CardContent>
        </Card>

        {/* ---------- Module 2: four body parts ---------- */}
        <Card>
          <CardHeader>
            <CardTitle>Body parts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {(Object.keys(PART_NAMES) as (keyof ComponentScores)[]).map((key) => (
              <div key={key} className="space-y-1">
                <div className="flex justify-between">
                  <Label>{PART_NAMES[key]}</Label>
                  <span className="text-sm text-muted-foreground">
                    {state.components[key].toFixed(1)}
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
          {/* >>> AI-GENERATED (Claude, 2026-11-21) | reviewed by: Angelia Li | purpose: list top_contributors */}
          {state.top_contributors.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing stands out right now.</p>
          ) : (
            state.top_contributors.map((c) => (
              <Item key={c.signal} variant="muted" size="sm" className="mb-2">
                <ItemContent>
                  <ItemTitle>{PART_NAMES[c.signal as keyof ComponentScores] ?? c.label}</ItemTitle>
                </ItemContent>
              </Item>
            ))
          )}
          {/* <<< AI-GENERATED */}
        </CardContent>
      </Card>

      {/* >>> AI-GENERATED (Claude, 2026-11-21) | reviewed by: Angelia Li | purpose: sensor status badges */}
      <Card>
        <CardHeader>
          <CardTitle>Sensors</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {Object.entries(state.sensors).map(([name, on]) => (
            <Badge key={name} variant={on ? "default" : "outline"}>
              {name}: {on ? "on" : "off"}
            </Badge>
          ))}
        </CardContent>
      </Card>
      {/* <<< AI-GENERATED */}
    </main>
  )
}
