# CLAUDE.md：UTEK26 项目规范

本文件是团队和 AI 助手共同遵守的规范。**有冲突时以本文件为准**；接口细节以 `docs/INTERFACE.md` 为准。

## 1. 项目是什么
UTEK 2026 Programming 赛题：做一个后台运行的 "invisible sentinel"。它持续根据键盘、鼠标、摄像头等信号计算 **Systemic Fatigue Score (0–100)**，**每 5 秒**写入本地 JSON 文件并通过 `localhost:8080/metrics` 提供；只在生理上需要时、在不打断 flow 的时机提醒用户。
- 赛题原文：`Programming Kompetitions Package.pdf`（项目共享文件）
- 文档：`docs/SETUP.md`（环境安装）、`docs/INTERFACE.md`（接口）、`docs/DESIGN.md`（设计说明）、`docs/TODO.md`（分工 todolist）

## 2. 比赛硬规则（违反会扣分或 DQ）
| 规则 | 要求 |
|---|---|
| 截止 | **18:00（多伦多时间）**，按最后一次 commit 时间戳，10 分钟 grace。团队内部 **17:45 code freeze** |
| AI + 外部代码 | 合计 **≤ 30%**（代码和 slides 都算） |
| AI 生成代码 | **必须标注**（格式见 §6），并登记到 `AI_USAGE.md` |
| 外部代码 / 资源 | **必须引用**：代码注释 + README "Attributions" + slides 引用页 |
| 进入 Day 2 | 前 8 名**只看代码**决定，代码质量、模块化、注释都很重要 |
| README | 必须写清楚运行方式、部署方式、团队成员和引用 |

## 3. Git 规则
- **AI 助手（Claude 等）不 commit、不 push、不开 PR。** 只改工作区文件，由 Repo Owner 本人 commit。
- 每人在自己的分支开发：`feat/keyboard`、`feat/mouse`、`feat/webcam`、`feat/ui`，由 Repo Owner 合并到 `main`。
- 只改自己负责的目录；要改别人的目录或共享文件（`models.py`、`docs/INTERFACE.md`、`frontend/src/shared/types.ts`），先在和团队成员沟通再开始。
- 不要 commit：`.venv/`、`node_modules/`、`out/`、`dist/`、`*.log`、`metrics.json`、个人数据文件。

## 4. 技术栈与版本（已实测兼容）

### 后端（Python）
| 项 | 版本 / 选择 | 说明 |
|---|---|---|
| Python | **3.12**（`requires-python = ">=3.12,<3.13"`，`.python-version` = 3.12） | 3.12 是唯一能让所有库在 Windows、Apple Silicon Mac、Intel Mac 上都装得上的版本（Intel Mac 上 mediapipe 最高只支持到 3.12） |
| 环境管理 | **uv**（`backend/pyproject.toml` + `uv.lock`） | 不要用 pip / conda；加库用 `uv add <包名>` |
| Web/API | FastAPI + uvicorn | `/metrics`、WebSocket `/ws` |
| 键盘、鼠标 | pynput 1.8 | |
| 前台窗口 | pywinctl | |
| 系统资源 | psutil | |
| 摄像头 | opencv-python + mediapipe（Win / Apple Silicon 用 1.2.x，Intel Mac 自动用 0.10.21） | **只用 Tasks API**（`mediapipe.tasks.python.vision.FaceLandmarker`）。1.x **已删除 `mp.solutions`**，网上教程的旧写法会报错 |
| 测试 / lint | pytest、ruff | |

### 前端（Electron 桌面 App）
| 包 | 版本 |
|---|---|
| Node.js | **≥ 22.12**（推荐 24 LTS） |
| electron | 45.x |
| electron-vite | 6.x |
| vite | 8.x |
| @vitejs/plugin-react | 6.x |
| react / react-dom | 19.x |
| typescript | **7.x** |
| tailwindcss / @tailwindcss/vite | 4.x |
| @base-ui/react | 1.x |
| shadcn（CLI） | 4.x，style `base-luma`（Base UI 版本），组件目录 `src/renderer/src/ui/` |
| 字体 | @fontsource-variable/inter + figtree（本地打包，不依赖网络） |
| oxlint | 1.x |

**TypeScript 7 注意事项（已实测）：**
- `baseUrl` 已移除，写了会报错。路径别名只用 `"paths": {"@/*": ["./src/renderer/src/*"]}`。
- renderer 的 tsconfig `types` 里要有 `"vite/client"`，否则 CSS import 报 TS2882。
- TS 7 没有 JS API：**不要用** typescript-eslint、vite-plugin-checker 等依赖 `typescript` 包 API 的工具。lint 只用 oxlint，类型检查用 `tsc --noEmit`。

## 5. 目录结构与常用命令
```
UTEK26/
  CLAUDE.md  README.md  AI_USAGE.md
  backend/                     # Python 后端（uv 项目）
    pyproject.toml  uv.lock  .python-version
    models/face_landmarker.task
    src/sentinel/{core,api,output,scoring,intervention,sensors/{keyboard,mouse,context,vision}}/   # 各文件夹归属见 docs/INTERFACE.md 第 2 节
    tests/
  frontend/                    # Electron + React
    src/{main,preload,renderer,shared}/
    src/renderer/src/ui/       # shadcn 生成的组件，禁止手改
  docs/  tools/
```
| 做什么 | 命令 |
|---|---|
| 装/同步 Python 依赖 | `cd backend && uv sync` |
| 环境自检 | `uv run python scripts/check_env.py [--camera] [--input]` |
| 运行后端 | `uv run python -m sentinel`（`--mock` 假数据，`--no-camera`，`--headless`） |
| 单独测某个 sensor | `uv run python -m sentinel.sensors.keyboard`（或 `mouse`、`context`、`vision --preview`） |
| Python 测试 / lint | `uv run pytest` / `uv run ruff check .` |
| 装前端依赖 | `cd frontend && npm ci`（不要用 `npm install`，加包用 `npm install <包> --save-exact`） |
| 前端开发 | `npm run dev` |
| 前端检查 | `npm run lint`（oxlint）/ `npm run typecheck`（tsc --noEmit） |
| 统计 AI 占比 | `uv run python tools/count_ai.py` |

## 6. AI 标注与引用格式（必须照抄）

**AI 生成的代码块**（Python 用 `#`，TS 用 `//`）：
```python
# >>> AI-GENERATED (Claude, 2026-11-21) | reviewed by: <姓名> | purpose: <一句话>
...代码...
# <<< AI-GENERATED
```
**整个文件都是 AI 生成**：文件第一行写 `# AI-GENERATED FILE (Claude, 2026-11-21) | reviewed by: <姓名>`。

**外部代码**（抄或改编自网上 / 文档 / 开源项目）：
```python
# >>> EXTERNAL: <来源 URL> | license: <MIT/Apache-2.0/...> | modified: yes/no
...代码...
# <<< EXTERNAL
```
- shadcn 组件（`frontend/src/renderer/src/ui/` 整个目录）：**不在文件里加标注**（这个目录禁止修改，见 §9），而是在 `AI_USAGE.md` 和 README Attributions 里整体登记为 External（shadcn/ui, MIT）。`tools/count_ai.py` 把这个目录全部算作外部代码。
- 只是 `import` 一个库（pynput、mediapipe 等）不需要块标注，但 README Attributions 要列出来。
- 每次标注后在 `AI_USAGE.md` 里加一行：`文件 | 行数 | AI/External | 用途 | 负责人`。
- `tools/count_ai.py` 按上面的标记统计行数，所以**标记格式不能改**。

**AI 预算分配**：AI 主要用在 Webcam（约 250 行以内）和 UI/UX（约 400 行以内）。Keyboard（键盘采集、评分算法）和 Mouse（鼠标采集、主循环、接口）尽量手写。

## 7. 工程限制（必须满足）

**功能 / 稳定性**
1. 分数**每 5 秒**输出一次，按单调时钟的目标时间调度（第 n 次 = 开始时间 + n×5 秒），不能越跑越漂。`seq` 连续递增。
2. **主循环永远不能崩**：每个 sensor 调用都包 try/except，失败就用 `available=False` 的空数据继续跑。
3. JSON 文件**原子写入**：先写 `.tmp` 再 `os.replace`。默认路径 `~/.utekinetics/metrics.json`。
4. 后端必须能**脱离 Electron 独立运行**（`--headless`），评委只看 JSON / 端口也要能拿满分。
5. 服务只监听 **127.0.0.1**，不对外网开放。
6. 没有摄像头、没有权限（macOS）、摄像头被占用时都要能正常运行，自动降级。

**性能（Efficiency 评分项）**
7. 后端进程目标：平均 **CPU < 5%**（不开摄像头 < 1%），**内存 < 300MB**。
8. 键盘、鼠标监听回调里**只做计数和记时间戳**，不 print、不做复杂计算、不调用慢 API（如 `pywinctl`）。
9. 所有计算在每 5 秒的 tick 里做一次，不要开忙循环（`while True` 不 sleep）。
10. 摄像头 320×240，burst 采样（每 12 秒：4 秒约 15fps + 8 秒 1fps），平均 ≤ 5fps，不用时 release。

**隐私**
11. **绝不记录按键内容**，只记次数和时间。
12. **绝不保存视频帧或图片**，只保留算出来的数值。
13. 所有数据只存在本机 `~/.utekinetics/`，不联网上传。

**UX（Invisibility 评分项）**
14. 不弹模态窗口、不出声、不用固定时间间隔提醒。
15. 提醒必须经过干预引擎：flow 中推迟、会议/全屏静默、迟滞（75 触发 / 60 重置）、同类 20 分钟冷却。
16. 关闭主窗口 = 隐藏到托盘，不退出。

**跨平台**
17. 必须在 **Windows 和 macOS** 上都能跑。路径用 `pathlib.Path`，不要写死 `/` 或 `\`。平台相关代码用 `sys.platform` 分支并写注释。

## 8. 代码风格
**Python**
- 必写类型注解；模块之间用 `models.py` 里的 dataclass 传数据，不要传裸 dict。
- 带单位的变量 / 字段名加后缀：`_s`、`_ms`、`_px`、`_deg`、`_cm`、`_per_min`。
- 阈值、权重、端口全部放 `config.py`，不要写死在逻辑里。
- 计算逻辑写成**纯函数**（输入数据 → 输出数字），和线程 / 监听器分开，方便写测试。
- 每个公式旁边写注释说明**生理依据**或来源（评委会看）。
- 用 `logging`，不要到处 `print`（sensor 的 `__main__` 自测除外）。

**TypeScript / React**
- 函数组件 + hooks；组件 PascalCase，hooks `useXxx`。
- 与后端交互的类型统一放 `src/shared/types.ts`，字段名**保持 snake_case**，与后端完全一致。
- renderer 不直接访问 Node / 后端，统一通过 preload 暴露的 `window.sentinel`。
- `contextIsolation: true`、`nodeIntegration: false`。

## 9. UI/UX 规范

**shadcn 组件目录：禁止修改**
- shadcn 组件统一放在 **`frontend/src/renderer/src/ui/`**（`components.json` 的 `aliases.ui` = `@/ui`），只能由 shadcn CLI 生成。
- **任何人和任何 AI agent 都禁止手动修改 `src/renderer/src/ui/` 里的文件**，包括格式化、加注释、改样式、修类型错误。组件不合用就改调用方。
- 这个目录不跑 oxlint（已在 `.oxlintrc.json` 忽略）。
- 加组件：在 `frontend/` 下运行 `CI=1 npx shadcn@latest add <组件> --yes </dev/null`（不加 `CI=1 ... </dev/null` 可能会卡住等输入）。加完检查文件确实在 `src/renderer/src/ui/`。
- 组件出了问题或合并冲突：用 `CI=1 npx shadcn@latest add <组件> --overwrite --yes </dev/null` 重新生成官方版本，不要手动合并。

**组件使用**
- 用 shadcn 组件之前，先用 Context7（或官方文档 https://ui.shadcn.com）查这个组件的用法。
- **直接用 shadcn 官方组件，不要做薄封装**（不要写 `MyButton`、`AppCard` 这类只换个名字或改一点样式的包装）。只有带真实行为（状态、数据、业务逻辑）的组件才放 `src/renderer/src/components/`。
- 不要手写 shadcn 已有的同类控件。常用对应：表单字段 `Field` + `Input` + `FieldError`；空状态 `Empty`；列表行 `Item`；2–5 个选项 `ToggleGroup`；进度 `Progress`；加载 `Spinner` / `Skeleton`；出错 `Alert`；状态标签 `Badge`；提示 `Tooltip`。
- **立即生效的开关**（摄像头开关、暂停提醒）用 `Switch` + `Label`，不要用 `Toggle` 按钮；表单里提交时才生效的选项用 `Checkbox`。
- 删除 / 重置 / 退出一类按钮用 `destructive` variant，并用确认对话框二次确认（如"重置校准数据"）。

**视觉**
- 主题预设：`components.json` 的 `style` 为 **`base-luma`**，主色天蓝（`oklch(0.5 0.134 242.749)`），字体 **Inter（正文）+ Figtree（标题）**，`--radius: 0.625rem`。令牌定义在 `src/renderer/src/index.css`。
- **颜色只用令牌，不写死颜色值**：用 `bg-primary`、`text-muted-foreground`、`text-level-high` 等；不要写 `#ff0000`、`oklch(...)`、`sky-500`、`red-500`。
- 疲劳等级颜色用专门的令牌：`level-low` / `level-moderate` / `level-high` / `level-critical`（对应 `FatigueState.level`），托盘图标、Body Map、分数颜色都用它们。
- 支持暗色模式（`<html class="dark">`）。
- 英文文案用 sentence case（"Take a short break"），不用 `uppercase` 样式。
- 空状态用 `Empty`：标题写状态（"No data yet"），按钮写动词，不用感叹号；不要手写 `text-center text-sm text-muted-foreground` 的空状态。

## 10. 接口变更流程
`docs/INTERFACE.md` 在 **12:00 冻结**。之后要改：① 群里说明原因 → ② 四个人都同意 → ③ 同时改 `models.py`、`types.ts`、`INTERFACE.md` 并把版本号 +0.1。

## 11. 给 AI 助手的额外说明
- 遵守 §3：**不 commit、不 push、不开 PR**。
- 生成代码时**自动加上 §6 的标注**，并提醒用户登记 `AI_USAGE.md`。
- 用户在 Keyboard 或 Mouse 负责的模块（键盘、鼠标、前台应用采集，评分算法，主循环，接口服务器）求助时，**优先解释思路、指出 API 和文档**，而不是直接写整段代码（这些模块要手写）。
- mediapipe 只用 Tasks API，不要生成 `mp.solutions` 的代码。
- 前端遵守 §4 的 TypeScript 7 注意事项和 §9 的 UI 规范。
- **禁止修改 `frontend/src/renderer/src/ui/`（shadcn 组件目录）中的任何文件**；需要不同行为时改调用方，或用 shadcn CLI 重新生成。
- 使用 shadcn 组件前先用 Context7 查文档。
- 回复用中文（用户中英混写，技术名词保留英文）。
