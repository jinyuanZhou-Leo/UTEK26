# 环境安装文档（Windows + macOS）

按顺序做完 **第 1 步（全员）**，再做自己角色对应的部分。每一步后面都有 **✅ 检查**，通过了再往下走。
大约需要 **10–15 分钟**（大部分时间在下载）。卡住超过 10 分钟直接在群里喊。

| 角色 | 需要做的部分 |
|---|---|
| Keyboard / Mouse / Webcam | 第 1、2 步 |
| UI/UX | 第 1、2、3 步（前端要启动后端，所以 Python 环境也要装） |

---

## 第 1 步：安装基础工具（全员）

### 1.1 Git
- **macOS**：终端输入 `git --version`，没装会自动弹窗让你装 Command Line Tools，点 "安装"。
- **Windows**：下载 https://git-scm.com/download/win ，一路默认下一步。

✅ 检查：`git --version` 能显示版本号。

### 1.2 uv（Python 环境管理工具）
不需要自己装 Python，uv 会自动下载正确的版本（3.12）。

- **macOS**（终端）：
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  装完**关掉终端重新打开**。（有 Homebrew 的也可以 `brew install uv`）
- **Windows**（打开 **PowerShell**，不是 CMD）：
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  装完**关掉 PowerShell 重新打开**。

✅ 检查：`uv --version` 能显示版本号。

### 1.3 Node.js（只有 UI/UX 必须装，其他人建议也装上）
- 版本要求：**≥ 22.12**，推荐 **24 LTS**。
- 两个系统都可以去 https://nodejs.org 下载 LTS 安装包，一路默认。

✅ 检查：`node --version` 显示 `v22.12` 以上，`npm --version` 能显示版本号。

### 1.4 Windows 额外：VC++ 运行库
mediapipe / OpenCV 在 Windows 上需要它。下载安装 **Microsoft Visual C++ Redistributable (x64)**：
https://aka.ms/vs/17/release/vc_redist.x64.exe （已经装过会提示 "已安装"，直接关掉即可）

### 1.5 拿到代码
```bash
git clone https://github.com/jinyuanZhou-Leo/UTEK26.git
cd UTEK26
```

---

## 第 2 步：Python 后端环境（全员）

### 2.1 安装依赖
```bash
cd backend
uv sync
```
uv 会自动：下载 Python 3.12 → 创建 `backend/.venv` → 按 `uv.lock` 安装**完全一样版本**的所有库。全队的环境因此保持一致。

> **规则**：不要用 `pip install`。要加新库，用 `uv add <包名>`，然后在群里说一声（`pyproject.toml` 和 `uv.lock` 会变，需要 commit）。

✅ 检查：`uv run python --version` 显示 `Python 3.12.x`。

### 2.2 运行自检脚本
```bash
uv run python scripts/check_env.py
```
这个脚本会检查：Python 版本、所有库能不能 import、mediapipe 新版 API、模型文件、FaceLandmarker 能不能跑。
✅ 检查：最后一行显示 `12/12 checks passed.`

**Webcam 同学**再跑：
```bash
uv run python scripts/check_env.py --camera
```
✅ 检查：`[OK ] webcam frame`

**Keyboard 和 Mouse 同学**再跑（运行后 5 秒内打几个字、动动鼠标）：
```bash
uv run python scripts/check_env.py --input
```
✅ 检查：`[OK ] keyboard/mouse events`

### 2.3 macOS 权限（Mac 用户必做）
系统设置 → **隐私与安全性**，在下面三个地方把你用的终端打开（Terminal / iTerm / VS Code / Cursor，用哪个开哪个）：
1. **辅助功能**（Accessibility）：pynput 和 pywinctl 需要
2. **输入监控**（Input Monitoring）：pynput 监听键盘需要
3. **摄像头**（Camera）：OpenCV 需要

改完权限后**一定要完全退出终端（⌘Q）再打开**，否则不生效。

> 用 `npm run dev` 从终端启动 Electron 时，Python 后端是终端的子进程，权限算在**终端**头上，所以给终端授权就够了。

### 2.4 Windows 权限
- 设置 → 隐私和安全性 → **相机** → 打开 "允许桌面应用访问相机"。
- 键盘鼠标监听在 Windows 上不需要额外权限。
- 如果杀毒软件 / Windows Defender 提示 Python 在监听键盘，选 "允许"。

---

## 第 3 步：前端环境（UI/UX）

### 3.1 安装依赖
```bash
cd frontend
npm ci
```
- `npm ci` 会严格按照 `package-lock.json` 装，版本和队友完全一致。**不要用 `npm install`**（它可能升级版本）。
- 要加新包：`npm install <包名> --save-exact`，然后在群里说一声（`package.json` 和 `package-lock.json` 都要 commit）。

**Electron 下载很慢或卡住**（它要下载约 100MB 的 Electron 程序）：
- macOS：`ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/" npm ci`
- Windows PowerShell：`$env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"; npm ci`

✅ 检查：`npx electron --version` 显示 `v45.x`。

### 3.2 运行三个检查
```bash
npm run typecheck   # TypeScript 类型检查，应该没有输出
npm run lint        # oxlint，应该 0 warnings / 0 errors
npm run dev         # 弹出一个窗口，显示 "UTEKinetics: environment OK"
```
✅ 检查：三个命令都没报错，窗口能弹出来。

### 3.3 加 shadcn 组件
```bash
CI=1 npx shadcn@latest add button --yes </dev/null
```
（Windows PowerShell 不支持 `</dev/null`，用：`$env:CI=1; npx shadcn@latest add button --yes`）
- 配置已经写在 `components.json` 里（Base UI 版本，style `base-luma`，天蓝主色），**不需要再跑 `shadcn init`**。
- 组件会生成到 **`src/renderer/src/ui/`**，代码里用 `import { Button } from '@/ui/button'`。
- **`src/renderer/src/ui/` 里的文件禁止修改**（包括加注释、格式化），引用登记在 `AI_USAGE.md` 和 README 里。规则见 CLAUDE.md §9。
- **只加用得到的组件**，它们都算外部代码。

### 3.4 前端技术栈版本（已锁定）
| 包 | 版本 |
|---|---|
| electron | 45.4.1 |
| electron-vite | 6.0.0 |
| vite | 8.3.8 |
| @vitejs/plugin-react | 6.3.0 |
| react / react-dom | 19.3.1 |
| typescript | 7.0.2 |
| tailwindcss / @tailwindcss/vite | 4.3.5 |
| @base-ui/react | 1.9.0 |
| oxlint | 1.94.0 |
| 其他 | shadcn、clsx、tailwind-merge、class-variance-authority、lucide-react、tw-animate-css（shadcn 组件需要）；@fontsource-variable/inter、figtree（字体） |

**TypeScript 7 注意**：`tsconfig.json` 里**不要加 `baseUrl`**（会报错）；不要装 typescript-eslint。详见 CLAUDE.md §4。

---

## 第 4 步：一起跑起来（14:00 联调时用）

终端 1（后端）：
```bash
cd backend
uv run python -m sentinel --mock      # 真实 sensor 写好之前用 --mock
```
浏览器打开 http://127.0.0.1:8080/metrics ，每 5 秒刷新能看到 `seq` 变化。

终端 2（前端）：
```bash
cd frontend
npm run dev
```

---

## 项目里环境相关的文件（都要 commit）
| 文件 | 作用 |
|---|---|
| `backend/pyproject.toml` | Python 依赖列表，锁定 Python 3.12 |
| `backend/uv.lock` | 所有 Python 库的精确版本（Win / Mac Intel / Mac Apple Silicon 都包含） |
| `backend/.python-version` | 告诉 uv 用 3.12 |
| `backend/models/face_landmarker.task` | MediaPipe 人脸模型（3.8MB，Apache 2.0，来源：Google MediaPipe），提前放进 repo，免得现场下载失败 |
| `backend/scripts/check_env.py` | 环境自检脚本 |
| `frontend/package.json` + `package-lock.json` | 前端依赖，版本全部精确锁定 |
| `frontend/tsconfig.json`、`electron.vite.config.ts`、`.oxlintrc.json`、`components.json` | 前端配置 |

**不要 commit**：`backend/.venv/`、`frontend/node_modules/`、`frontend/out/`（已写进 `.gitignore`）。

---

## 常见问题

| 现象 | 原因 / 解决 |
|---|---|
| `uv: command not found` / `无法识别 uv` | 装完 uv 没重开终端。关掉终端重开；还不行就重新跑 1.2 的安装命令 |
| `uv sync` 很慢 | 第一次要下载 Python 和 mediapipe（约 100MB），正常。比赛 Wi-Fi 慢就连手机热点 |
| Windows 上 `import mediapipe` 报 DLL load failed | 没装 VC++ 运行库，做 1.4 |
| `AttributeError: module 'mediapipe' has no attribute 'solutions'` | 用了旧教程的写法。mediapipe 1.x 只能用 Tasks API（`FaceLandmarker`），见 TODO.md 第 3 节 |
| Intel Mac 上 mediapipe 版本是 0.10.21 | 正常。mediapipe 1.x 没有 Intel Mac 版本，uv 自动换成 0.10.21，Tasks API 用法一样 |
| Mac 上 `keyboard/mouse events` 一直是 0 | 权限没给或没重启终端，见 2.3 |
| Mac 上摄像头打不开 / 画面全黑 | 摄像头权限，见 2.3；或者摄像头被 Zoom / FaceTime 占用 |
| Windows 上摄像头打不开 | 见 2.4；或者被 Teams / 相机 App 占用 |
| `npm ci` 报 lock 文件不一致 | 有人用 `npm install` 改了 `package.json` 但没更新 lock 文件。从 `main` 分支拿最新的 `package-lock.json` |
| `npm ci` 卡在 electron | 用 3.1 里的 `ELECTRON_MIRROR` |
| `tsc` 报 `Option 'baseUrl' has been removed` | 删掉 tsconfig 里的 `baseUrl`（TS 7 已移除） |
| 端口 8080 被占用 | macOS：`lsof -i :8080` 找到进程后 `kill <PID>`；Windows：`netstat -ano \| findstr 8080` 后 `taskkill /PID <PID> /F` |
