from __future__ import annotations
from dataclasses import dataclass, field, asdict

@dataclass
class KeyboardFeatures:
    available: bool                   # listener is running; False if macOS permission is missing
    window_s: float                   # actual window length, ~5.0
    keystrokes: int                   # key presses in this window; count only, never which key
    keys_per_min: float               # 60s: key presses in the last 60 s
    backspace_ratio: float            # 60s: (Backspace + Delete) / total keys, 0–1
    iki_mean_ms: float                # 60s: mean inter-key interval, intervals < 2 s only
    iki_cv: float                     # 60s: std / mean of intervals; higher = less steady rhythm
    typing_burst_s: float             # seconds of continuous typing since the last pause (> 2 s)
    seconds_since_last_key: float     # seconds since the last key press
    micro_pauses_per_min: float = 0   # 60s: number of 2–10 s pauses

@dataclass
class MouseFeatures:
    available: bool
    window_s: float
    distance_px: float                # total mouse travel in this window
    speed_mean_px_s: float            # mean speed while moving in this window
    clicks: int                       # clicks in this window (left + right)
    scrolls: int                      # scroll events in this window
    active_s: float                   # time the mouse was moving in this window
    seconds_since_last_event: float   # seconds since the last mouse event
    speed_p95_px_s: float = 0         # 95th percentile speed
    direction_changes_per_s: float = 0  # direction reversals per second (tremor, target hunting)
    static_hold_s: float = 0          # duration of the latest hold-still-on-mouse period

@dataclass
class ContextFeatures:
    available: bool
    active_app: str                   # foreground app, e.g. "Code", "zoom.us"; "" if unknown
    app_category: str                 # "code" | "doc" | "browser" | "meeting" | "media" | "other"
    in_meeting: bool = False          # foreground app is a meeting app
    is_fullscreen: bool = False       # foreground window is fullscreen

@dataclass
class VisionFeatures:
    available: bool                   # camera opened and a frame was processed in the last 30 s
    face_present: bool                # face detected in most frames of this window
    fps_effective: float              # average processed fps in this window
    blinks: int                       # blinks in this window
    blink_rate_per_min: float         # 60s: blinks per minute, scaled by actual sampling time
    gaze_away_s: float                # seconds not looking at the screen (no face, or head turned > 30°)
    head_pitch_deg: float             # head pitch, positive = looking down
    face_distance_cm: float | None    # estimated face-to-screen distance; None if unknown
    forward_head_ratio: float         # face width / calibrated width; > 1 = leaning in; 1.0 if uncalibrated
    perclos: float = 0                # 60s: fraction of time eyes are mostly closed (drowsiness)
    head_yaw_deg: float = 0           # head yaw (left/right turn)
    head_roll_deg: float = 0          # head roll (side tilt)
    ambient_light: float | None = None  # mean frame brightness, 0–1
    yawns: int = 0

@dataclass
class Features:
    ts: float                         # time.time()
    dt_s: float                       # seconds since the last tick, ~5.0
    keyboard: KeyboardFeatures
    mouse: MouseFeatures
    context: ContextFeatures
    vision: VisionFeatures

    @property
    def idle_s(self) -> float:
        """Time since the last keyboard or mouse activity."""
        return min(self.keyboard.seconds_since_last_key, self.mouse.seconds_since_last_event)
    
@dataclass
class ComponentScores:
    upper_extremity: float            # 0–100 wrists and arms (RSI)
    ocular: float                     # 0–100 eyes (computer vision syndrome)
    postural: float                   # 0–100 neck and posture
    cognitive: float                  # 0–100 mental fatigue

@dataclass
class Contribution:
    signal: str                       # field name, e.g. "blink_rate_per_min"
    label: str                        # user-facing text, e.g. "Blinking 42% less than usual"
    delta: float                      # change this signal caused in the total score (+/-)

@dataclass
class FatigueState:
    schema_version: str               # "1.1"
    timestamp: str                    # ISO 8601 with offset, e.g. "2026-11-21T14:05:10-05:00"
    seq: int                          # starts at 0, +1 per tick (set by the main loop)
    interval_s: float                 # 5.0
    systemic_fatigue_score: float     # 0–100, 1 decimal place
    level: str                        # "low"(<40) | "moderate"(40–65) | "high"(65–80) | "critical"(≥80)
    trend_per_min: float              # score change per minute over the last 5 min
    components: ComponentScores
    top_contributors: list[Contribution]  # 1–3 most influential signals
    activity_state: str               # "deep_work" | "active" | "light" | "meeting" | "break" | "away"
    flow: bool                        # user is in focused typing; interventions are deferred
    calibrating: bool                 # first 10 min: learning the user's baseline
    sensors: dict[str, bool]          # {"keyboard": True, "mouse": True, "context": True, "vision": False}
    signals: dict[str, float | str | None]  # key raw values, see INTERFACE.md §5

@dataclass
class Intervention:
    id: str                           # str(uuid.uuid4())
    kind: str                         # "eye_break" | "wrist_stretch" | "posture_reset" | "stand_up"
    channel: str                      # "tray" (icon color) | "glow" (screen edge) | "toast" (silent notification)
    severity: int                     # 1 mild / 2 moderate / 3 severe
    title: str                        # "Rest your eyes for 20 seconds"
    body: str                         # "Look at something about 6 m away. The camera will confirm it."
    target_component: str             # ComponentScores field, e.g. "ocular"
    duration_s: int                   # suggested duration
    auto_verify: bool                 # True: completion confirmed by camera or idle time, no click needed
    reason: list[Contribution]        # why now (copied from FatigueState.top_contributors)
    created_at: str                   # ISO 8601

def to_json_dict(obj) -> dict:
    return asdict(obj)