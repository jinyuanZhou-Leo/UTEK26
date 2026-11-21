# 接口规范 v1.1

这份文档规定各模块之间**怎么传数据**。只要每个人都按这里的字段名和函数签名写，最后拼在一起时就不用改代码。

- **12:00 冻结**。冻结后要改字段，先在群里说明原因，四个人都同意后，同时改 `models.py`、`frontend/src/shared/types.ts` 和本文档，版本号 +0.1。
- 字段名、单位、类型以本文档为准。代码和文档对不上时，以本文档为准，改代码。

---

## 1. 整体结构

程序分成两个进程：

| 进程 | 语言 | 作用 |
|---|---|---|
| 后端 `backend/` | Python 3.12 | 采集键盘、鼠标、摄像头数据，每 5 秒算一次疲劳分数，写入 JSON 文件，并通过 `127.0.0.1:8080` 提供数据 |
| 前端 `frontend/` | Electron + React | 托盘图标、Dashboard、提醒效果。只通过 HTTP / WebSocket 和后端说话 |

后端内部每 5 秒做一次下面的事情（称为一次 **tick**）：

```
1. 向 4 个 sensor 各要一份数据：keyboard / mouse / context / vision
2. 打包成 Features
3. FatigueModel.update(features)        → FatigueState（分数）
4. 写 metrics.json，更新 /metrics，通过 WebSocket 推给前端
5. InterventionEngine.evaluate(state)   → 需要提醒就返回 Intervention，推给前端
```

后端可以不开前端单独运行（`uv run python -m sentinel --headless`），评委只看 JSON 文件或端口也能看到分数。

---

## 2. 分工和文件归属

每个人只改自己名下的文件。四个人改的是不同文件夹，合并时不会冲突。

| 角色 | 负责的文件 | 第一阶段（11:30–13:30） | 第二阶段（13:30–16:30） |
|---|---|---|---|
| **Keyboard** | `sensors/keyboard/`、`scoring/` | 键盘数据采集 | 疲劳评分算法 |
| **Mouse** | `models.py`、`sensors/base.py`、`sensors/mouse/`、`sensors/context/`、`core/`、`api/`、`output/`、`config.py`、`__main__.py` | 共享数据结构、主循环和接口服务器（带假数据） | 鼠标和前台应用采集、整体联调 |
| **Webcam** | `sensors/vision/`、`intervention/` | 摄像头数据采集 | 提醒决策引擎 |
| **UI/UX** | `frontend/`（`src/renderer/src/ui/` 除外，那是 shadcn 生成的，禁止修改） | 用本地假数据做界面 | 接真实后端、托盘、通知、屏幕边缘光 |

上表的路径都在 `backend/src/sentinel/` 下（除了 `frontend/`）。

后端完整目录：

```
backend/src/sentinel/
  __init__.py
  __main__.py            入口，解析命令行参数                                  [Mouse]
  models.py              所有共享的数据结构（本文档第 3 节）                     [Mouse，12:00 后冻结]
  config.py              端口、间隔、文件路径                                   [Mouse]
  sensors/
    base.py              Sensor 协议                                           [Mouse]
    keyboard/            sensor.py  features.py  mock.py  __main__.py           [Keyboard]
    mouse/               sensor.py  features.py  mock.py  __main__.py           [Mouse]
    context/             sensor.py  apps.py      mock.py  __main__.py           [Mouse]
    vision/              sensor.py  camera.py  landmarks.py  features.py  mock.py  __main__.py   [Webcam]
  scoring/               model.py  baseline.py  config.py                       [Keyboard]
  intervention/          engine.py  config.py                                   [Webcam]
  core/                  loop.py                                                [Mouse]
  output/                json_writer.py                                         [Mouse]
  api/                   server.py                                              [Mouse]
backend/tests/           test_<模块>.py，谁的模块谁写测试
```

---

## 3. 共享数据结构（`models.py`）

**Mouse 在 11:30–12:00 照抄下面的代码写进 `models.py`。** 其他人在这半小时里先写不依赖 `models.py` 的计算函数（见 TODO.md）。

规则：
- 所有数据都用 `@dataclass`，不要在模块之间传 `dict`。
- 带单位的字段名加后缀：`_s` 秒、`_ms` 毫秒、`_px` 像素、`_deg` 角度、`_cm` 厘米、`_per_min` 每分钟。
- 标了 `= 0` / `= None` / `= False` 默认值的是**选做字段**，时间不够可以不算，保持默认值即可。

### 3.1 Sensor 协议（`sensors/base.py`）

每个 sensor（键盘、鼠标、前台应用、摄像头）都是一个类，都有下面三个方法：

```python
from typing import Protocol, Any

class Sensor(Protocol):
    name: str                    # "keyboard" | "mouse" | "context" | "vision"

    def start(self) -> None:
        """开始采集。在后台线程里运行，这个函数本身必须马上返回。"""

    def stop(self) -> None:
        """停止采集，释放资源（监听器、摄像头）。重复调用不能报错。"""

    def snapshot(self) -> Any:
        """返回从上一次调用到现在这段时间的数据，然后把"本窗口"计数清零。
        要求：
        - 5 毫秒内返回（不要在这里做慢操作）
        - 不抛异常（出错就返回 available=False 的数据）
        - 线程安全（用 threading.Lock 保护共享变量）"""
```

**"窗口"的意思**：`snapshot()` 每 5 秒被调用一次，"本窗口"就是这 5 秒。有些指标需要更长的时间才稳定，就用"最近 60 秒"，这类字段在注释里写了"60s"。

每个 sensor 文件夹必须有：
- `mock.py`：一个 `MockXxxSensor` 类，接口一样，返回编出来但合理的数据（数值要随时间变化，不要一直是常数）。
- `__main__.py`：让 `uv run python -m sentinel.sensors.<名字>` 可以单独运行，每 5 秒打印一次 `snapshot()` 的结果。

### 3.2 `KeyboardFeatures`（Keyboard 负责）

```python
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
```

### 3.3 `MouseFeatures`（Mouse 负责）

```python
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
```

### 3.4 `ContextFeatures`（Mouse 负责）

```python
@dataclass
class ContextFeatures:
    available: bool
    active_app: str                   # 前台应用名，如 "Code"、"zoom.us"。拿不到时为 ""
    app_category: str                 # "code" | "doc" | "browser" | "meeting" | "media" | "other"
    in_meeting: bool = False          # 选做：前台是会议软件
    is_fullscreen: bool = False       # 选做：前台窗口全屏
```

### 3.5 `VisionFeatures`（Webcam 负责）

```python
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
```

没有摄像头、用户关掉摄像头、摄像头被占用：返回 `available=False`，其他字段用 0 / None / 1.0。

### 3.6 `Features`（Mouse 在主循环里打包）

```python
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
```

### 3.7 `FatigueState`（Keyboard 的评分模块产出，也就是 `/metrics` 返回的内容）

```python
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
```

`activity_state` 的判断规则（Keyboard 实现）：

| 状态 | 条件（从上往下，先满足的算） |
|---|---|
| `away` | `idle_s > 120` 并且（摄像头不可用或没检测到脸） |
| `break` | `idle_s > 30` |
| `meeting` | `context.in_meeting` 或 `context.app_category == "meeting"` |
| `deep_work` | `flow == True` |
| `active` | `keys_per_min > 30` 或鼠标 `active_s > 1` |
| `light` | 其他情况 |

`flow` 的判断规则：`typing_burst_s > 120` 且 `iki_cv < 0.8` 且 `backspace_ratio < 0.15` 且 `app_category` 是 `code` 或 `doc`。阈值放在 `scoring/config.py`，联调时再调。

### 3.8 `Intervention`（Webcam 的提醒引擎产出）

```python
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
```

### 3.9 两个核心类的签名

**评分（Keyboard，`scoring/model.py`）**

```python
class FatigueModel:
    def __init__(self, baseline_path: Path | None = None) -> None: ...
    def update(self, features: Features) -> FatigueState:
        """每次 tick 调用一次。seq 和 timestamp 由主循环覆盖，这里随便填。"""
    def recalibrate(self) -> None:
        """清空个人基线，重新学习 10 分钟。"""
```

**提醒（Webcam，`intervention/engine.py`）**

```python
class InterventionEngine:
    def evaluate(self, state: FatigueState, features: Features) -> Intervention | None:
        """每次 tick 调用一次。需要提醒就返回 Intervention，否则返回 None。"""
    def check_resolved(self, features: Features) -> list[tuple[str, str]]:
        """检查之前发出的提醒是否完成。返回 [(intervention_id, result)]，
        result 为 "auto_verified" | "expired"。"""
    def feedback(self, intervention_id: str, result: str) -> None:
        """用户在界面上点了按钮。result 为 "done" | "snooze" | "dismiss"。"""
    def set_paused_until(self, ts: float | None) -> None: ...
```

---

## 4. HTTP 接口（Mouse 实现，`api/server.py`，FastAPI）

只监听 `127.0.0.1:8080`。

| 方法 | 路径 | 作用 | 返回 |
|---|---|---|---|
| GET | `/metrics` | 最新一次的 `FatigueState`（题目要求的端口） | `FatigueState` 的 JSON |
| GET | `/metrics/history?minutes=30` | 最近 N 分钟的历史（内存里最多存 2 小时） | `FatigueState` 数组 |
| GET | `/health` | 各 sensor 状态和本进程资源占用 | `{"ok": true, "uptime_s": 123.4, "cpu_percent": 1.2, "rss_mb": 85.0, "sensors": {"keyboard": true, ...}}` |
| GET | `/config` | 当前设置 | `UserConfig` |
| PUT | `/config` | 修改部分设置 | `UserConfig` |
| POST | `/control` | 控制命令 | `{"ok": true}` |
| WS | `/ws` | 实时推送，见第 6 节 | |

`UserConfig`：

```json
{"camera_enabled": true, "interventions_enabled": true, "glow_enabled": true,
 "toast_enabled": true, "paused_until": null}
```

`POST /control` 的请求体（每次发其中一种）：

```json
{"action": "pause", "minutes": 30}
{"action": "resume"}
{"action": "recalibrate"}
{"action": "intervention_feedback", "id": "<intervention id>", "result": "done"}
{"action": "self_report", "fatigue_1_10": 6}
```

`self_report` 是验证用的：用户给自己的疲劳打 1–10 分，后端记到日志里，最后和算出来的分数对比。

---

## 5. JSON 文件和 `/metrics` 示例

两者内容完全一样：

```json
{
  "schema_version": "1.1",
  "timestamp": "2026-11-21T14:05:10-05:00",
  "seq": 742,
  "interval_s": 5.0,
  "systemic_fatigue_score": 63.4,
  "level": "moderate",
  "trend_per_min": 0.8,
  "components": {"upper_extremity": 71.2, "ocular": 58.0, "postural": 66.5, "cognitive": 49.1},
  "top_contributors": [
    {"signal": "typing_burst_s", "label": "已经连续打字 48 分钟没停", "delta": 4.1},
    {"signal": "blink_rate_per_min", "label": "眨眼次数比你平时少 42%", "delta": 3.2}
  ],
  "activity_state": "deep_work",
  "flow": true,
  "calibrating": false,
  "sensors": {"keyboard": true, "mouse": true, "context": true, "vision": true},
  "signals": {"keys_per_min": 212, "backspace_ratio": 0.09, "mouse_speed_mean_px_s": 410,
              "blink_rate_per_min": 7.0, "face_distance_cm": 48.0, "head_pitch_deg": 14.0,
              "idle_s": 0.4, "app_category": "code"}
}
```

文件规则（Mouse 实现，`output/json_writer.py`）：
- 默认路径 `~/.utekinetics/metrics.json`，可以用 `--json-path` 改。
- **原子写入**：先写 `metrics.json.tmp`，写完再 `os.replace()` 成 `metrics.json`。这样别的程序读的时候不会读到写了一半的文件。
- 每次同时往 `~/.utekinetics/metrics.log.jsonl` 追加一行（一行一个 JSON），用于验证和回放。

定时规则（Mouse 实现，`core/loop.py`）：
- 不要写 `sleep(5)`，因为每次计算也要时间，会越来越慢。做法：记下开始时间 `t0`，第 n 次 tick 的目标时间是 `t0 + n * 5`，每次 sleep 到目标时间。用 `time.monotonic()`。
- 每次调用 sensor、评分、提醒都用 `try/except` 包住。任何一个模块出错，只记日志，主循环继续，`seq` 继续加 1。

---

## 6. WebSocket 消息（`ws://127.0.0.1:8080/ws`）

所有消息格式都是 `{"type": "...", "data": {...}}`。

**后端发给前端**

| type | data | 什么时候发 |
|---|---|---|
| `hello` | `{"schema_version": "1.1", "config": UserConfig, "history": FatigueState[]}` | 刚连上时 |
| `metrics` | `FatigueState` | 每 5 秒 |
| `intervention` | `Intervention` | 提醒引擎决定提醒时 |
| `intervention_resolved` | `{"id": "...", "result": "auto_verified" \| "done" \| "expired"}` | 提醒完成或过期 |
| `sensor_status` | `{"keyboard": bool, "mouse": bool, "context": bool, "vision": bool, "message": "..."}` | 有 sensor 状态变化时（比如 macOS 没给权限） |

**前端发给后端**：`{"type": "control", "data": <和 POST /control 的请求体一样>}`

---

## 7. 前端内部接口（UI/UX 实现）

**主进程（`src/main/`）**
- 启动后端：开发时运行 `uv run --project ../backend python -m sentinel`。每秒请求一次 `/health`，成功后再连 WebSocket（最多等 20 秒）。
- App 退出时关掉后端进程。后端意外退出，3 秒后重启，最多 3 次。
- WebSocket 只在主进程里连一次，收到的消息转发给页面和边缘光窗口。
- 托盘：图标颜色跟 `level` 变；菜单有"打开 Dashboard""暂停 30 分钟""开关摄像头""退出"。
- 关闭主窗口只是隐藏到托盘，不退出程序。
- `channel == "toast"`：用 Electron `Notification`，`silent: true`。
- `channel == "glow"`：一个全屏、透明、鼠标可穿透、置顶、不抢焦点的窗口，在屏幕四周显示柔和的光，几秒后淡出。

**preload（`src/preload/`）暴露给页面的 `window.sentinel`**

```ts
interface SentinelBridge {
  onMetrics(cb: (s: FatigueState) => void): () => void          // 返回取消订阅的函数
  onIntervention(cb: (i: Intervention) => void): () => void
  onInterventionResolved(cb: (r: { id: string; result: string }) => void): () => void
  control(cmd: ControlCommand): Promise<void>
  getConfig(): Promise<UserConfig>
  setConfig(patch: Partial<UserConfig>): Promise<UserConfig>
  getHistory(minutes: number): Promise<FatigueState[]>
}
```

TypeScript 类型写在 `frontend/src/shared/types.ts`，字段名和第 3 节**一模一样**（保持 `snake_case`，不要改成驼峰）。

---

## 8. 怎么做到四个人同时开工、互不等待

| 时间 | 谁提供 | 提供什么 | 谁用 |
|---|---|---|---|
| 12:00 | Mouse | `models.py` + `sensors/base.py` | 所有后端成员 |
| 12:20 | Keyboard / Mouse / Webcam | 各自的 `MockXxxSensor` | Mouse（主循环）、Keyboard（测试评分）、Webcam（测试提醒） |
| 12:20 | Keyboard | `scoring/model.py` 的临时版本：分数 = `keys_per_min / 3`，限制在 0–100，其他字段填固定值 | Mouse（主循环）、Webcam（测试提醒） |
| 12:20 | Webcam | `intervention/engine.py` 的临时版本：`evaluate` 永远返回 `None` | Mouse（主循环） |
| 13:00 | Mouse | `uv run python -m sentinel --mock` 能跑：真实的主循环、JSON、HTTP、WebSocket，数据来自 4 个 Mock | UI/UX |
| 13:30 | Keyboard | 真实 `KeyboardSensor` | Mouse |
| 14:00 | Webcam | 真实 `VisionSensor` | Mouse |
| 14:15 | Mouse | 真实 `MouseSensor`、`ContextSensor` | — |
| 14:30 | 全员 | **第一次联调**：真实 sensor + 临时评分 | |
| 15:30 | Keyboard / Webcam | 真实评分模型、真实提醒引擎 | |
| 15:30 | 全员 | **第二次联调**：全部真实模块 | |

在别人的东西到之前：
- UI/UX 用 `src/renderer/src/mock/` 里的本地假数据。
- Keyboard 写评分时，用 4 个 Mock sensor 造 `Features` 来测试。
- Webcam 写提醒引擎时，自己在测试里构造 `FatigueState`。
- Mouse 写主循环时，用 4 个 Mock + 临时评分 + 临时提醒引擎。

---

## 9. 命名约定（摘要，详见 CLAUDE.md）

- Python：变量和函数 `snake_case`，类 `PascalCase`，必须写类型注解。
- TypeScript：组件 `PascalCase`，hook 以 `use` 开头。和后端交互的字段保持 `snake_case`。
- 阈值、权重不要直接写在逻辑里，放到各自模块的 `config.py`。
