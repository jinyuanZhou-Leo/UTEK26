from __future__ import annotations
from dataclasses import dataclass, field, asdict

@dataclass
class KeyboardFeatures:
    available: bool                   # 监听器在正常工作。macOS 没给权限时为 False
    window_s: float                   # 本窗口实际长度（秒），约 5.0
    keystrokes: int                   # 本窗口按键次数。只计数，绝不记录按了哪个键
    keys_per_min: float               # 60s：最近 60 秒按键次数
    backspace_ratio: float            # 60s：(Backspace + Delete 次数) / 总按键次数，0–1
    iki_mean_ms: float                # 60s：相邻两次按键的平均间隔，只算小于 2 秒的间隔
    iki_cv: float                     # 60s：间隔的标准差 / 平均值。越大说明打字节奏越乱
    typing_burst_s: float             # 从上一次停顿（2 秒以上没按键）到现在，连续打了多少秒
    seconds_since_last_key: float     # 距离最后一次按键多少秒
    micro_pauses_per_min: float = 0   # 60s，选做：2–10 秒停顿的次数

@dataclass
class MouseFeatures:
    available: bool
    window_s: float
    distance_px: float                # 本窗口鼠标移动的总距离
    speed_mean_px_s: float            # 本窗口内，鼠标移动时的平均速度
    clicks: int                       # 本窗口点击次数（左右键都算）
    scrolls: int                      # 本窗口滚轮事件次数
    active_s: float                   # 本窗口内鼠标在动的总时长
    seconds_since_last_event: float   # 距离最后一次鼠标事件多少秒
    speed_p95_px_s: float = 0         # 选做：速度的 95 分位
    direction_changes_per_s: float = 0  # 选做：移动中方向反转的频率（手抖、来回找目标）
    static_hold_s: float = 0          # 选做：最近一次"手握鼠标但几乎不动"的持续时间

@dataclass
class ContextFeatures:
    available: bool
    active_app: str                   # 前台应用名，如 "Code"、"zoom.us"。拿不到时为 ""
    app_category: str                 # "code" | "doc" | "browser" | "meeting" | "media" | "other"
    in_meeting: bool = False          # 选做：前台是会议软件
    is_fullscreen: bool = False       # 选做：前台窗口全屏

@dataclass
class VisionFeatures:
    available: bool                   # 摄像头打开成功，并且最近 30 秒内处理过画面
    face_present: bool                # 本窗口大部分帧里检测到人脸
    fps_effective: float              # 本窗口实际处理的平均帧率
    blinks: int                       # 本窗口眨眼次数
    blink_rate_per_min: float         # 60s：每分钟眨眼次数（按实际采样时间折算）
    gaze_away_s: float                # 当前已经连续多少秒没看屏幕（没检测到脸，或头转开超过 30°）
    head_pitch_deg: float             # 低头角度，低头为正
    face_distance_cm: float | None    # 估算的脸到屏幕距离。算不出来为 None
    forward_head_ratio: float         # 当前脸宽 / 校准时的脸宽。大于 1 说明往前凑了。未校准时为 1.0
    perclos: float = 0                # 选做，60s：眼睛基本闭合的时间占比（困倦指标）
    head_yaw_deg: float = 0           # 选做
    head_roll_deg: float = 0          # 选做
    ambient_light: float | None = None  # 选做：画面平均亮度 0–1
    yawns: int = 0

@dataclass
class Features:
    ts: float                         # time.time()
    dt_s: float                       # 距离上一次 tick 的秒数，约 5.0
    keyboard: KeyboardFeatures
    mouse: MouseFeatures
    context: ContextFeatures
    vision: VisionFeatures

    @property
    def idle_s(self) -> float:
        """键盘和鼠标都没动的时间。"""
        return min(self.keyboard.seconds_since_last_key, self.mouse.seconds_since_last_event)
    
@dataclass
class ComponentScores:
    upper_extremity: float            # 0–100 手腕、手臂（重复劳损 RSI）
    ocular: float                     # 0–100 眼睛（电脑视觉综合征 CVS）
    postural: float                   # 0–100 颈椎和坐姿
    cognitive: float                  # 0–100 精神疲劳

@dataclass
class Contribution:
    signal: str                       # 字段名，如 "blink_rate_per_min"
    label: str                        # 给用户看的一句话，如 "眨眼次数比你平时少 42%"
    delta: float                      # 这个信号让总分变化了多少（可正可负）

@dataclass
class FatigueState:
    schema_version: str               # "1.1"
    timestamp: str                    # ISO 8601 带时区，如 "2026-11-21T14:05:10-05:00"
    seq: int                          # 从 0 开始，每次 tick 加 1（由主循环填写）
    interval_s: float                 # 5.0
    systemic_fatigue_score: float     # 0–100，保留 1 位小数
    level: str                        # "low"(<40) | "moderate"(40–65) | "high"(65–80) | "critical"(≥80)
    trend_per_min: float              # 最近 5 分钟分数每分钟变化多少
    components: ComponentScores
    top_contributors: list[Contribution]  # 影响最大的 1–3 个信号
    activity_state: str               # "deep_work" | "active" | "light" | "meeting" | "break" | "away"
    flow: bool                        # 用户是否在专注打字（提醒引擎据此推迟提醒）
    calibrating: bool                 # 前 10 分钟在学习用户的正常水平
    sensors: dict[str, bool]          # {"keyboard": True, "mouse": True, "context": True, "vision": False}
    signals: dict[str, float | str | None]  # 几个关键原始值，见第 5 节示例

@dataclass
class Intervention:
    id: str                           # str(uuid.uuid4())
    kind: str                         # "eye_break" | "wrist_stretch" | "posture_reset" | "stand_up"
    channel: str                      # "tray"（托盘变色）| "glow"（屏幕边缘光）| "toast"（静音通知）
    severity: int                     # 1 轻 / 2 中 / 3 重
    title: str                        # "Rest your eyes for 20 seconds"
    body: str                         # "Look at something about 6 m away. The camera will confirm it."
    target_component: str             # 对应 ComponentScores 的字段名，如 "ocular"
    duration_s: int                   # 建议做多久
    auto_verify: bool                 # True：由摄像头或空闲时间自动确认完成，用户不用点按钮
    reason: list[Contribution]        # 为什么现在提醒（直接用 FatigueState.top_contributors）
    created_at: str                   # ISO 8601

def to_json_dict(obj) -> dict:
    return asdict(obj)