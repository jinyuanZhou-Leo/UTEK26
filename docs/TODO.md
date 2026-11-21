# 分工和任务清单

## 怎么用这份清单

- 按顺序做。做完一项，把 `[ ]` 改成 `[x]`。
- 每项后面的 **检查** 是自测方法。检查通过再做下一项。
- 标了 **（选做）** 的，必做项全部完成后再做。
- 一个问题卡了 15 分钟还没解决，就在群里问。
- 时间都是多伦多时间。**17:45 停止写代码，18:00 repo 截止**（看最后一次 commit 的时间）。
- 字段名、函数签名一律看 [INTERFACE.md](./INTERFACE.md)。环境安装看 [SETUP.md](./SETUP.md)。代码规范看 [../CLAUDE.md](../CLAUDE.md)。

## 分工

| 角色 | 做什么 | AI 能用多少 |
|---|---|---|
| **Keyboard** | 统计打字情况；之后写疲劳评分算法 | 尽量手写。评分算法评委会重点看 |
| **Mouse** | 写共享数据结构和后端主循环、HTTP 接口；之后统计鼠标和前台应用；负责后端联调 | 尽量手写 |
| **Webcam** | 用摄像头数眨眼、估算离屏幕多远、看头有没有往前探；之后写"什么时候提醒"的决策引擎 | 可以用，约 250 行以内，必须标注 |
| **UI/UX** | 桌面 App：Dashboard、托盘图标、通知、屏幕边缘光 | 可以用，约 400 行以内，必须标注 |

**为什么限制 AI 行数**：AI 生成的代码加上外部代码，不能超过全部代码的 30%。预计全部代码约 3,800 行，所以 AI 和外部代码加起来最多约 1,100 行。shadcn 组件也算外部代码。

**为什么四个人能同时开工**：每个人改不同的文件夹；需要别人的东西时，先用对方提供的假数据（Mock）。具体时间表见 INTERFACE.md 第 8 节。

**Git 用法**：每人在自己的分支上写（`feat/keyboard`、`feat/mouse`、`feat/webcam`、`feat/ui`），写完一个阶段就 push，由 Repo Owner 合并到 `main`。别人的改动合并后，用 `git pull origin main` 拿到自己的分支上。

---

## 第 0 步：全员（11:00–11:30）

- [ ] 按 SETUP.md 装好环境。
  检查：`cd backend && uv run python scripts/check_env.py` 最后显示全部通过。
- [ ] 四个人一起把 INTERFACE.md 第 3 节过一遍。对字段有意见现在提，**12:00 之后不改**。
- [ ] 建好自己的分支：`git checkout -b feat/<你的角色>`。
- [ ] macOS 同学：确认已经给终端开了"辅助功能""输入监控""摄像头"权限（SETUP.md 2.3）。

---

## 1. Keyboard

你要用的库是 `pynput`。先读官方文档的 "Monitoring the keyboard" 一节：https://pynput.readthedocs.io/en/latest/keyboard.html

### 1.1 先写计算函数（11:30–12:00，不依赖别人）

这一步只写"给一串时间戳，算出一个数"的函数，不碰键盘监听。这样不用真打字就能测试。

- [ ] 新建 `backend/src/sentinel/sensors/keyboard/features.py`，写这几个函数（参数都是按键时间戳列表，单位秒，从小到大排好）：
  - `keys_per_min(timestamps, now)`：最近 60 秒里有几个时间戳。
  - `inter_key_intervals(timestamps)`：相邻两个时间戳的差，**只保留小于 2 秒的**（大于 2 秒说明人停下来了，不算打字节奏）。
  - `iki_mean_ms(intervals)`：间隔的平均值，换算成毫秒。列表为空时返回 0。
  - `iki_cv(intervals)`：标准差 ÷ 平均值。用 `statistics.stdev` 和 `statistics.mean`。少于 2 个间隔时返回 0。
  - `typing_burst_s(timestamps, now)`：从后往前找，找到第一个"和后一个时间戳相差超过 2 秒"的位置，从那里到 `now` 是多少秒。如果最后一次按键离 `now` 已经超过 2 秒，返回 0。
- [ ] 新建 `backend/tests/test_keyboard_features.py`，每个函数至少一个测试。例子：时间戳 `[0, 0.2, 0.4, 3.0, 3.2]`，间隔应该是 `[0.2, 0.2, 0.2]`（2.6 被去掉了）。
  检查：`uv run pytest tests/test_keyboard_features.py` 全部通过。

### 1.2 Mock（12:00–12:20）

`models.py` 12:00 由 Mouse 推上来。`git pull origin main` 拿到它。

- [ ] 新建 `sensors/keyboard/mock.py`，写 `MockKeyboardSensor`：有 `name = "keyboard"`、`start()`、`stop()`、`snapshot()`。`snapshot()` 返回 `KeyboardFeatures`，数值随时间慢慢变化，比如 `keys_per_min` 用 `150 + 80 * math.sin(time.time() / 60)`。
- [ ] 新建 `scoring/model.py` 的**临时版本**：`FatigueModel.update()` 里分数 = `keys_per_min / 3`，限制在 0–100，其他字段填固定值，能返回一个完整的 `FatigueState` 就行。
- [ ] push。在群里说"keyboard mock 和临时评分好了"。

### 1.3 真实键盘采集（12:20–13:30）

- [ ] 新建 `sensors/keyboard/sensor.py`，写 `KeyboardSensor` 类。
- [ ] 在 `__init__` 里准备：
  - 一个 `threading.Lock()`
  - 一个 `collections.deque` 存按键时间戳
  - 两个计数器：本窗口按键次数、本窗口退格次数
  - 一个 deque 存最近 60 秒的退格时间戳
- [ ] `start()`：创建 `pynput.keyboard.Listener(on_press=self._on_press)` 并 `start()`。
- [ ] `_on_press(key)` 里**只做这些**：加锁 → 把 `time.time()` 放进 deque → 计数器加 1 → 如果 `key` 是 `Key.backspace` 或 `Key.delete`，退格计数加 1 → 解锁。**不要记录按的是哪个键，不要 print。** 这个函数每次按键都会调用，必须很快。
- [ ] 删除 deque 里 60 秒以前的时间戳（在 `snapshot()` 里删就行）。
- [ ] `snapshot()`：加锁，复制一份时间戳列表，读取计数器并清零，解锁。然后用 1.1 写的函数算出所有字段，返回 `KeyboardFeatures`。整个函数套 `try/except`，出错就返回 `available=False`。
- [ ] macOS 没有权限时 pynput 收不到任何事件。判断方法：pynput 在 macOS 上有 `listener.IS_TRUSTED` 属性，为 `False` 时把 `available` 设为 `False`，并用 `logging.warning` 提示"请在 系统设置 → 隐私与安全性 → 输入监控 中授权终端"。
- [ ] 新建 `sensors/keyboard/__main__.py`：创建 `KeyboardSensor`，`start()`，然后每 5 秒打印一次 `snapshot()`。
  检查：`uv run python -m sentinel.sensors.keyboard`，快速打字时 `keys_per_min` 变大，停下来 `typing_burst_s` 归 0，`seconds_since_last_key` 一直涨。
- [ ] push，群里说"真实键盘好了"。

### 1.4 疲劳评分算法（13:30–15:30）

这是整个项目最核心的部分。先读 DESIGN.md 的"疲劳模型"一节。

- [ ] `scoring/config.py`：把下面用到的所有阈值、权重、时间常数写成常量。
- [ ] `scoring/baseline.py`：个人基线。
  - 前 10 分钟只学习，不判断。对每个信号（`keys_per_min`、`iki_mean_ms`、`backspace_ratio`、`mouse.speed_mean_px_s`、`blink_rate_per_min`、`face_distance_cm`）记录平均值和标准差。
  - 简单做法：每个信号存一个列表，10 分钟后算 `mean` 和 `stdev`，存到 `~/.utekinetics/baseline.json`。下次启动时如果文件存在就直接读，不用重新学。
  - 提供 `z(signal_name, value)`：返回 `(value - mean) / stdev`。还没学完时返回 0。
- [ ] `scoring/model.py` 正式版，按这个顺序算：
  1. **4 个部位的负荷**（每个 0–1）：
     - 手腕 `upper_extremity`：打字越快、连续打字越久、鼠标点击越多、移动越多，负荷越高。
     - 眼睛 `ocular`：眨眼越少（相对基线）、离屏幕越近、连续看屏越久，负荷越高。摄像头不可用时，只用"连续看屏时间"（`idle_s` 小于 30 秒就算在看屏）。
     - 颈椎 `postural`：低头角度越大、`forward_head_ratio` 越大、越久没动，负荷越高。摄像头不可用时，用"连续工作时间"粗略估计。
     - 精神 `cognitive`：`iki_cv` 越高、`backspace_ratio` 越高（都相对基线），负荷越高。
     - 每一项都用 `min(1, max(0, ...))` 限制在 0–1。
  2. **累积和恢复**：每个部位维护一个疲劳值 `F`（0–100）。每次 tick：
     `F = F * exp(-dt_s / tau) + gain * load * dt_s`
     `tau` 是恢复时间常数：休息或离开（`activity_state` 是 `break` / `away`）时用小值（比如 300 秒，恢复快），工作时用大值（比如 3600 秒，几乎不恢复）。`gain` 控制涨多快，联调时调。
  3. **总分**：`S = 0.7 * 加权平均(四个F) + 0.3 * max(四个F)`，限制在 0–100，保留 1 位小数。加 max 那一项，是为了某一个部位特别累时，总分不会被其他正常的部位拉低。
  4. 按 INTERFACE.md 3.7 的表算 `flow` 和 `activity_state`。
  5. `level`：<40 low，40–65 moderate，65–80 high，≥80 critical。
  6. `trend_per_min`：保存最近 5 分钟的分数，用（最新 − 最早）÷ 分钟数。
  7. `top_contributors`：记下每个信号对负荷的贡献，取最大的 3 个，写成中文或英文的一句话，比如 `f"眨眼次数比你平时少 {pct:.0f}%"`。
- [ ] 每个公式旁边写一行注释，说明依据（比如"眨眼减少会导致干眼，见 DESIGN.md 参考文献"）。
- [ ] `tests/test_scoring.py`，至少 4 个测试：
  - 连续 60 次 tick 都是高强度打字，分数持续上升。
  - 之后连续 60 次 tick 都是休息，分数下降。
  - 任何输入下，分数都在 0–100。
  - `vision.available = False` 时不报错，分数照常算。
  检查：`uv run pytest tests/test_scoring.py` 通过。
- [ ] push，群里说"评分模型好了"。

### 1.5 联调和收尾（15:30–17:30）

- [ ] 实际用电脑 20 分钟，看分数变化是否合理，调 `scoring/config.py` 里的参数。
- [ ] `tools/count_ai.py`：统计 CLAUDE.md §6 标注块里的行数，以及 `frontend/src/renderer/src/ui/` 下的全部行数，输出占总行数的百分比。
- [ ] （选做）`micro_pauses_per_min`。
- [ ] （选做）`tools/replay.py`：读 `~/.utekinetics/metrics.log.jsonl`，用 matplotlib 画分数曲线，图片存到 `docs/validation/`，slides 上用。
- [ ] 准备 slides 的"评分算法"页：公式、每个信号的依据。

---

## 2. Mouse

你有两块工作：先写后端的骨架（别人都要用），再写鼠标和前台应用的采集。

### 2.1 共享数据结构（11:30–12:00，最优先）

- [ ] 把 INTERFACE.md 第 3.2–3.8 节的所有 dataclass 照抄进 `backend/src/sentinel/models.py`。顶部加 `from __future__ import annotations` 和 `from dataclasses import dataclass, field, asdict`。`list` 类型的默认值要用 `field(default_factory=list)`。
- [ ] 加一个函数 `to_json_dict(obj) -> dict`，内部就是 `dataclasses.asdict(obj)`。
- [ ] 把 INTERFACE.md 3.1 的 `Sensor` 协议写进 `sensors/base.py`。
- [ ] 每个子文件夹（`sensors/keyboard`、`sensors/mouse`、`sensors/context`、`sensors/vision`、`scoring`、`intervention`、`core`、`output`、`api`）放一个空的 `__init__.py`。
  检查：`uv run python -c "from sentinel.models import FatigueState, Features"` 不报错。
- [ ] **12:00 前 push**，群里说"models.py 好了，可以 pull"。

### 2.2 Mock（12:00–12:20）

- [ ] `sensors/mouse/mock.py`：`MockMouseSensor`，数值随时间变化。
- [ ] `sensors/context/mock.py`：`MockContextSensor`，`app_category` 每分钟在 `code` / `browser` / `meeting` 之间换。

### 2.3 主循环、JSON、HTTP（12:20–13:00）

- [ ] `config.py`：`HOST = "127.0.0.1"`、`PORT = 8080`、`INTERVAL_S = 5.0`、`DATA_DIR = Path.home() / ".utekinetics"`。
- [ ] `output/json_writer.py`：
  - `write_metrics(state, path)`：`json.dumps` 后写入 `path.with_suffix(".json.tmp")`，再 `os.replace(tmp, path)`。目录不存在就先 `mkdir(parents=True, exist_ok=True)`。
  - `append_log(state, path)`：以追加模式打开 `metrics.log.jsonl`，写一行 JSON + `\n`。
- [ ] `core/loop.py`，写一个 `Engine` 类：
  - 构造时传入 4 个 sensor、`FatigueModel`、`InterventionEngine`。
  - `async def run()`：`t0 = time.monotonic()`，`n = 0`，循环：`n += 1`，`await asyncio.sleep(max(0, t0 + n * 5 - time.monotonic()))`，然后调用 `tick()`。
  - `tick()`：按 INTERFACE.md 第 1 节的 5 步做。每一步单独 `try/except`，出错 `logging.exception(...)` 后继续。
  - 每个 sensor 的 `snapshot()` 失败时，用一个 `available=False` 的空对象代替。
  - 保存最新的 `FatigueState` 和最近 2 小时的历史（`deque(maxlen=1440)`）。
- [ ] `api/server.py`：用 FastAPI 写 INTERFACE.md 第 4 节的接口。先做 `/metrics`、`/health`、`/ws`，其他的后面补。
  - WebSocket：维护一个已连接客户端的列表；`tick()` 结束后给每个客户端发 `{"type": "metrics", "data": ...}`。发送失败的客户端从列表里删掉。
  - 主循环用 FastAPI 的 `lifespan` 启动：`asyncio.create_task(engine.run())`。
- [ ] `__main__.py`：用 `argparse` 支持 `--mock`、`--no-camera`、`--headless`、`--json-path`、`--port`。`--mock` 时用 4 个 Mock sensor。最后 `uvicorn.run(app, host=HOST, port=PORT)`。
  检查：`uv run python -m sentinel --mock` 启动后，浏览器打开 http://127.0.0.1:8080/metrics 能看到 JSON；每 5 秒刷新一次，`seq` 加 1；`~/.utekinetics/metrics.json` 也在更新。
- [ ] **13:00 前 push**，群里告诉 UI/UX "可以连后端了"。

### 2.4 真实鼠标采集（13:00–13:45）

pynput 鼠标文档：https://pynput.readthedocs.io/en/latest/mouse.html

- [ ] `sensors/mouse/sensor.py`，`MouseSensor` 类。结构和键盘一样：一个 Lock、几个计数器、一个 `pynput.mouse.Listener(on_move=..., on_click=..., on_scroll=...)`。
- [ ] `_on_move(x, y)`：这个函数一秒会被调用几十上百次，里面只做：用 `math.hypot(x - 上一个x, y - 上一个y)` 算距离，加到本窗口总距离；记下 `time.time()`；如果离上一次移动不到 0.2 秒，把这段时间加到 `active_s`。不要 print，不要做别的计算。
- [ ] `_on_click(x, y, button, pressed)`：`pressed` 为 True 时点击数加 1。
- [ ] `_on_scroll(...)`：滚轮计数加 1。
- [ ] 每个事件都更新"最后一次鼠标事件时间"。
- [ ] `snapshot()`：读取并清零计数器，`speed_mean_px_s = distance_px / active_s`（`active_s` 为 0 时速度为 0）。
- [ ] `sensors/mouse/__main__.py`，每 5 秒打印。
  检查：`uv run python -m sentinel.sensors.mouse`，甩鼠标时距离和速度变大；不动时 `seconds_since_last_event` 一直涨。疯狂甩鼠标 30 秒，活动监视器 / 任务管理器里 Python 的 CPU 没有明显升高。

### 2.5 前台应用（13:45–14:15）

- [ ] `sensors/context/apps.py`：一个字典，把应用名映射到类别：
  - `code`：Code、Cursor、PyCharm、IntelliJ IDEA、Xcode、Terminal、iTerm2、Windows Terminal
  - `meeting`：zoom.us、Zoom、Microsoft Teams、Webex，或窗口标题包含 "Meet"
  - `browser`：Google Chrome、Safari、Firefox、Microsoft Edge、Arc
  - `doc`：Microsoft Word、Pages、Notion、Obsidian、PowerPoint、Keynote
  - `media`：Spotify、Music、VLC、YouTube（标题）
  - 都不是就是 `other`
- [ ] `sensors/context/sensor.py`：`snapshot()` 里调用 `pywinctl.getActiveWindow()`，读 `getAppName()` 和 `title`，查字典得到类别。**只在 `snapshot()` 里调用**，这个函数在 macOS 上要几十毫秒。拿不到窗口时 `available=False`。
- [ ] （选做）`in_meeting`：类别是 `meeting` 就为 True。`is_fullscreen`：窗口尺寸和屏幕尺寸差不多就为 True。
  检查：`uv run python -m sentinel.sensors.context`，切换不同软件，`app_category` 跟着变。**Windows 和 macOS 各测一次。**

### 2.6 联调（14:15–15:30）

- [ ] `__main__.py` 默认使用真实的 4 个 sensor；`--no-camera` 时 vision 用一个永远 `available=False` 的对象。
- [ ] 14:30 第一次联调：拉取所有人的分支，`uv run python -m sentinel` 跑通。
- [ ] 补全 `/metrics/history`、`/config`、`/control`、WebSocket 的 `hello`、`intervention`、`intervention_resolved`、`sensor_status` 消息。
- [ ] `/health` 里用 `psutil.Process().cpu_percent()` 和 `memory_info().rss` 报告本进程资源。
- [ ] `tests/test_output.py`：测原子写入（写完文件能被 `json.load` 读出来）。
- [ ] `tests/test_timing.py`：用 Mock 跑 30 秒，检查 `seq` 连续、相邻时间戳间隔在 4.9–5.1 秒之间。

### 2.7 收尾（15:30–17:45）

- [ ] 15:30 第二次联调，全部真实模块。
- [ ] 写 README：项目简介、架构图（可以画在 slides 里截图）、安装（链接 SETUP.md）、运行方式（后端单独跑 / 和前端一起跑）、macOS 权限、API 说明（链接 INTERFACE.md）、**Attributions**（所有用到的库、模型文件来源、参考的论文和网页）、**AI 使用说明**（链接 AI_USAGE.md，写明百分比）、团队成员。
- [ ] 在一个新文件夹里重新 `git clone`，按 README 从头跑一遍，确认能跑。
- [ ] 17:45 前通知 Repo Owner 做最后一次合并和 push。

---

## 3. Webcam

你要用的库：`opencv-python`（开摄像头、读画面）和 `mediapipe`（找脸上的点）。

**注意：mediapipe 1.x 删掉了 `mp.solutions`。** 网上大部分教程和 AI 给的代码都还在用 `mp.solutions.face_mesh`，在我们的版本上会直接报错。一律用 Tasks API 的 `FaceLandmarker`。官方指南：https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python

模型文件已经在 `backend/models/face_landmarker.task`，不用下载。

### 3.1 打开摄像头（11:30–12:00，不依赖别人）

- [ ] 写一个临时脚本 `sensors/vision/camera.py`：`cv2.VideoCapture(0)` 打开摄像头，循环 `read()`，用 `cv2.resize` 缩到 320×240，`cv2.imshow` 显示。按 q 退出。
- [ ] 打不开时（`isOpened()` 为 False）打印一行提示，不要崩溃。
  检查：能看到自己的画面。

### 3.2 Mock（12:00–12:20）

- [ ] `sensors/vision/mock.py`：`MockVisionSensor`。`blink_rate_per_min` 在 6–18 之间变化，`face_distance_cm` 在 45–65 之间变化，每隔一分钟有 25 秒 `gaze_away_s` 增长（模拟看别处）。
- [ ] `intervention/engine.py` 的**临时版本**：类 `InterventionEngine`，`evaluate` 永远返回 `None`，`check_resolved` 返回 `[]`，其他方法什么都不做。
- [ ] push，群里说"vision mock 和临时提醒引擎好了"。

### 3.3 找到人脸上的点（12:20–13:00）

- [ ] `sensors/vision/landmarks.py`：按官方指南创建 `FaceLandmarker`，参数：
  - `running_mode = vision.RunningMode.VIDEO`
  - `num_faces = 1`
  - `output_face_blendshapes = True`（会直接给出"眨眼程度"）
  - `output_facial_transformation_matrixes = True`（会直接给出头的旋转矩阵）
- [ ] 每一帧：OpenCV 读到的是 BGR，先 `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)`，再包成 `mp.Image`，调用 `detect_for_video(image, timestamp_ms)`。`timestamp_ms` 必须一直变大。
  检查：在预览窗口上把 478 个点画出来，点跟着脸动。

### 3.4 算特征（13:00–14:00）

在 `sensors/vision/features.py` 里，每个特征写成一个函数，方便测试：

- [ ] **眨眼**：从 blendshapes 里找 `eyeBlinkLeft` 和 `eyeBlinkRight`，取平均值（0 睁眼，1 闭眼）。用两个阈值：大于 0.5 记为"闭眼"，之后小于 0.3 记为"睁开"，闭→开算一次眨眼。用两个阈值是为了防止数值在 0.5 附近抖动时被重复计数。
- [ ] **眨眼频率**：记录最近 60 秒（**实际在拍的时间**，不是钟表时间）里的眨眼次数，换算成每分钟。正常人每分钟 15–20 次，盯着屏幕时会明显减少。
- [ ] **有没有人脸**：这一帧 `face_landmarks` 是否为空。
- [ ] **没看屏幕多久** `gaze_away_s`：连续没检测到脸，或者头左右转超过 30°，累计多少秒。
- [ ] **低头角度** `head_pitch_deg`：从变换矩阵算欧拉角。这一小段可以让 AI 写，记得按 CLAUDE.md §6 标注。
- [ ] **离屏幕距离** `face_distance_cm`：人的虹膜直径大约 11.7mm，个体差异很小。478 个点里 468–477 是虹膜点，量出虹膜在画面里有多少像素宽。距离 ≈ 焦距(像素) × 11.7 ÷ 虹膜像素 ÷ 10。焦距先按 `图像宽度 × 0.9` 估计，3.7 节再校准。
- [ ] **前倾比例** `forward_head_ratio`：现在的脸宽（左右脸颊两个点的距离）÷ 校准时的脸宽。没校准时为 1.0。
- [ ] `tests/test_vision_features.py`：给一串眨眼数值 `[0.1, 0.6, 0.7, 0.2, 0.1, 0.55, 0.25]`，应该数出 2 次眨眼。
  检查：预览窗口上实时显示这些数字。眨眼时计数加 1；凑近屏幕距离变小。

### 3.5 真实 sensor（14:00 前交付）

- [ ] `sensors/vision/sensor.py`，`VisionSensor` 类。摄像头的读取和处理放在**自己的线程**里（`threading.Thread(daemon=True)`）一直跑，算好的结果存在成员变量里。`snapshot()` 只加锁读结果，不做任何计算。
- [ ] **省 CPU 的拍法**：每 12 秒为一轮，前 4 秒每秒拍约 15 帧（数眨眼需要，一次眨眼只有 0.1–0.3 秒），后 8 秒每秒只拍 1 帧（只看人在不在、坐姿）。
- [ ] 正式运行时**不显示任何窗口**。预览窗口只在命令行加 `--preview` 时显示。
- [ ] 没有摄像头、摄像头被别的软件占用、`stop()` 被调用：释放摄像头，`available = False`，不抛异常。
- [ ] `sensors/vision/__main__.py`：`uv run python -m sentinel.sensors.vision --preview`。
  检查：能单独运行，每 5 秒打印一次数据；活动监视器 / 任务管理器里 CPU 不超过 10%。
- [ ] push，群里说"真实摄像头好了"。

### 3.6 提醒决策引擎（14:00–15:30）

先读 DESIGN.md 的"什么时候提醒"一节。

- [ ] `intervention/config.py`：所有阈值写成常量。
- [ ] `intervention/engine.py` 正式版，`evaluate()` 按顺序判断：
  1. 暂停中、`interventions_enabled` 为 False、`activity_state` 是 `meeting`、`is_fullscreen`：不提醒。
  2. 分数低于 75：不提醒。分数降到 60 以下时，才允许下一次提醒（防止分数在 75 附近上下跳时反复提醒）。
  3. `flow` 为 True（用户在专注打字）：先不提醒，记一个"待提醒"。等到用户停下来（`idle_s > 20`，或者 `app_category` 变了）再提醒。分数 ≥ 90 时例外。
  4. 选 `components` 里最高的那个部位，决定 `kind`：眼睛 → `eye_break`（看远处 20 秒），手腕 → `wrist_stretch`（30 秒），颈椎 → `posture_reset`，分数 ≥ 85 → `stand_up`。
  5. 同一种 `kind` 20 分钟内不重复。
  6. `channel` 按严重程度：分数 75–80 用 `tray`，80–90 用 `glow`，≥90 用 `toast`。
- [ ] `check_resolved()`：
  - `eye_break` 发出后，如果 `vision.gaze_away_s >= 20`，返回 `(id, "auto_verified")`。
  - 其他种类：`idle_s >= duration_s` 也算自动完成。
  - 发出超过 5 分钟没完成：返回 `(id, "expired")`。
- [ ] `tests/test_intervention.py`，至少 4 个测试：flow 中不提醒；停下来后提醒；20 分钟内同类不重复；开会时不提醒。
- [ ] push，群里说"提醒引擎好了"。

### 3.7 校准和收尾（15:30–17:30）

- [ ] 校准：用户坐正、看屏幕 5 秒，记录这时的脸宽、虹膜像素、低头角度，存到 `~/.utekinetics/vision_baseline.json`。和 UI/UX 商量怎么触发（建议走 `POST /control` 的 `recalibrate`）。
- [ ] Windows 和 macOS 各测一次。
- [ ] （选做）`perclos`、`ambient_light`、站立检测（脸在画面里的位置明显变高）。
- [ ] AI 写的代码全部按 CLAUDE.md §6 标注，并登记到 `AI_USAGE.md`。
- [ ] 准备 demo：凑近屏幕、不眨眼让分数上升；看远处 20 秒，提醒自动消失。

---

## 4. UI/UX

技术栈：Electron 45 + electron-vite 6 + Vite 8 + React 19 + TypeScript 7 + Tailwind 4 + shadcn（Base UI 版本，`base-luma` 风格）+ oxlint。项目骨架已经搭好（`frontend/`）。

**开始前读 CLAUDE.md §9（UI 规范）。** 最重要的三条：
1. `src/renderer/src/ui/` 是 shadcn 生成的组件，**任何人和 AI 都不能改**。组件不合用，就改你自己的代码。
2. 直接用 shadcn 组件，不要再包一层（不要写 `MyButton`、`AppCard`）。用之前先查文档：Context7 或 https://ui.shadcn.com
3. 颜色只用令牌（`bg-primary`、`text-level-high`），不要写 `#ff0000`、`red-500`。

### 4.1 跑起来（11:30–11:50）

- [ ] 按 SETUP.md 第 3 步：`cd frontend`、`npm ci`、`npm run dev`。
- [ ] 认识项目结构：
  - `src/main/index.ts`：主进程。管窗口、托盘、启动 Python 后端。运行在 Node.js 里。
  - `src/preload/index.ts`：桥。把主进程的功能安全地交给页面用。
  - `src/renderer/src/`：页面（React）。`App.tsx` 是入口。运行在浏览器环境里，**不能直接用 Node.js 的东西**。
  - `src/renderer/src/ui/`：shadcn 组件（只读）。
  - `src/renderer/src/index.css`：颜色和字体令牌。主色天蓝，正文 Inter，标题 Figtree，疲劳等级 4 种颜色。
- [ ] 加第一批组件：`CI=1 npx shadcn@latest add button card badge switch label progress tooltip empty --yes </dev/null`
  （Windows PowerShell：`$env:CI=1; npx shadcn@latest add button card badge switch label progress tooltip empty --yes`）
  检查：在 `App.tsx` 里放一个 `Button` 和一个 `Card`，窗口里能看到。

### 4.2 类型和假数据（11:50–12:30）

- [ ] `src/shared/types.ts`：照着 INTERFACE.md 3.7、3.8、第 4 节，写 `FatigueState`、`ComponentScores`、`Contribution`、`Intervention`、`UserConfig`、`ControlCommand` 的 TypeScript 类型。字段名和后端一模一样，保持 `snake_case`。
- [ ] `src/renderer/src/mock/fatigue.ts`：写一个函数，每 5 秒生成一个假的 `FatigueState`，分数慢慢上升到 85 再降回去。
- [ ] 写一个 hook `useFatigue()`：现在先用假数据，返回最新的 state 和最近 30 分钟的历史。之后换成真实数据时，只改这个 hook。
  检查：页面上的分数每 5 秒变一次。

### 4.3 Dashboard（12:30–14:30，先用假数据做）

按顺序做，前 3 项必做。括号里是建议用的组件。

- [ ] **大分数**：页面中间显示分数，颜色按 `level` 用 `text-level-low` / `text-level-moderate` / `text-level-high` / `text-level-critical`；旁边用箭头表示 `trend_per_min` 是升是降（`Card`、lucide-react 的图标）。
- [ ] **为什么是这个分数**：把 `top_contributors` 的 `label` 列出来（`Card` 或 `Item`）。
- [ ] **提醒卡片**：收到提醒时显示 `title`、`body`，"Done" 和 "Later" 两个按钮；收到 `intervention_resolved` 后显示"已确认"，3 秒后消失（`Card`、`Button`、`Badge`）。
- [ ] **身体部位图**：用 SVG 画一个简单的人形（头、脖子、手腕、腰），四个区域按 `components` 的分数用 `fill-level-*` 上色。这部分尽量自己画。
- [ ] **30 分钟趋势图**：可以 `add chart`，或者自己用 SVG 画折线。
- [ ] **设置页**：
  - 摄像头开关、暂停提醒：用 `Switch` + `Label`（这类立即生效的开关不要用 Toggle 按钮）。
  - 重新校准：`destructive` 样式的按钮，点了弹 `AlertDialog` 确认。
  - 隐私说明：按键内容从不记录；视频画面从不保存；数据只存在这台电脑上。
- [ ] **还没连上后端时**：用 `Empty` 组件显示"Waiting for the sensor service"，不要自己拼一个居中的灰色文字。
- [ ] **首次校准引导**：弹一个 `Dialog`，"请坐正、看着屏幕"，配 5 秒的 `Progress`。
- [ ] 暗色模式下也能正常显示（`<html class="dark">`）。

### 4.4 接真实后端（14:30–15:30）

13:00 之后 Mouse 会提供 `uv run python -m sentinel --mock`，你可以随时开始接。

- [ ] 主进程 `src/main/index.ts`：
  - 用 Node 的 `child_process.spawn('uv', ['run', '--project', '../backend', 'python', '-m', 'sentinel'])` 启动后端。开发时可以加环境变量跳过这一步，自己在另一个终端开后端。
  - 每秒 `fetch('http://127.0.0.1:8080/health')`，成功后再连 WebSocket。最多等 20 秒。
  - 用 Node 自带的 `WebSocket`（Node 22 起内置）连 `ws://127.0.0.1:8080/ws`。收到消息后 `mainWindow.webContents.send('metrics', data)` 转给页面。
  - App 退出（`before-quit`）时 `child.kill()`。
- [ ] preload `src/preload/index.ts`：用 `contextBridge.exposeInMainWorld('sentinel', {...})` 实现 INTERFACE.md 第 7 节的 `SentinelBridge`。页面调用 `control()` 时，用 `ipcRenderer.invoke` 交给主进程，主进程再 `fetch` 后端。
- [ ] 把 `useFatigue()` 从假数据换成 `window.sentinel.onMetrics`。
  检查：先开 `uv run python -m sentinel --mock`，再 `npm run dev`，页面上的分数和浏览器里 `/metrics` 的一样。

### 4.5 托盘和通知（15:30–16:15）

- [ ] 准备 4 个托盘小图标（16×16 和 32×32 的 PNG），颜色和 4 个 level 令牌一致，放在 `frontend/resources/`。
- [ ] 主进程创建 `Tray`，收到 `metrics` 时按 `level` 换图标。
- [ ] 托盘菜单：Open dashboard、Pause for 30 minutes、Camera on/off、Quit。
- [ ] 点窗口关闭按钮：`event.preventDefault()` + `win.hide()`，程序不退出。
- [ ] 收到 `channel == "toast"` 的提醒：`new Notification({ title, body, silent: true }).show()`。
  检查：Windows 和 macOS 上托盘图标都能看到、会变色。

### 4.6 屏幕边缘光和收尾（16:15–17:30）

- [ ] （选做，演示效果好）边缘光窗口：`new BrowserWindow({ transparent: true, frame: false, alwaysOnTop: true, focusable: false, skipTaskbar: true })`，大小设成整个屏幕，再调用 `win.setIgnoreMouseEvents(true)`。页面里用 CSS 在屏幕四周画一圈半透明的渐变光，收到 `channel == "glow"` 时淡入，5 秒后淡出。
- [ ] `npm run lint` 和 `npm run typecheck` 都没有报错。
- [ ] 你写的文件里，AI 写的部分按 CLAUDE.md §6 标注；在 `AI_USAGE.md` 登记 AI 部分和用到的 shadcn 组件（**不在 `ui/` 的文件里加标注**）。
- [ ] 按 DESIGN.md 的演示流程录 demo 视频，放进 repo。

---

## 5. 18:00 以后（全员）

- [ ] 做 slides（.pptx），自己写（slides 也算在 30% 里）。建议顺序：问题 → 系统结构 → 评分算法 → 提醒时机 → 验证结果 → demo → JSON 文件和端口两种输出 → 资源占用数据 → 参考资料。
- [ ] 排练，控制在 10 分钟内。每个人准备回答自己模块的问题。
- [ ] 23:59 前提交。
