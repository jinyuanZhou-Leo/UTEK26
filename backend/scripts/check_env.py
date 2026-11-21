# AI-GENERATED FILE (Claude, 2026-11-21) | purpose: environment self-check for all backend scopes
"""Environment self-check.

Only checks the extras that are installed (core / input / vision).

Usage (from backend/):
    uv run python scripts/check_env.py            # libraries + model file
    uv run python scripts/check_env.py --camera   # also try to open the webcam
    uv run python scripts/check_env.py --input    # also listen 5 s for keyboard/mouse events
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import platform
import sys
import time
import urllib.request
from pathlib import Path

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "face_landmarker.task"

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"[{'OK ' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))


def check_python() -> None:
    v = sys.version_info
    record("Python 3.12", (v.major, v.minor) == (3, 12), platform.python_version())


GROUPS = {
    "core": ["fastapi", "uvicorn", "psutil"],
    "input": ["pynput", "pywinctl"],
    "vision": ["numpy", "cv2", "mediapipe"],
}


def installed(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


def check_imports() -> None:
    for group, mods in GROUPS.items():
        if group != "core" and not any(installed(m) for m in mods):
            print(f"[SKIP] {group} extra not installed (uv sync --extra {group})")
            continue
        for mod in mods:
            try:
                m = importlib.import_module(mod)
                record(f"import {mod}", True, getattr(m, "__version__", ""))
            except Exception as e:  # noqa: BLE001 - we want to report any failure
                record(f"import {mod}", False, f"{type(e).__name__}: {e}")


def check_mediapipe_tasks() -> None:
    try:
        from mediapipe.tasks.python import vision  # noqa: F401

        record("mediapipe Tasks API (FaceLandmarker)", hasattr(vision, "FaceLandmarker"))
    except Exception as e:  # noqa: BLE001
        record("mediapipe Tasks API (FaceLandmarker)", False, str(e))


def check_model() -> None:
    if not MODEL_PATH.exists():
        print(f"       downloading model to {MODEL_PATH} ...")
        try:
            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        except Exception as e:  # noqa: BLE001
            record("face_landmarker.task", False, f"download failed: {e}")
            return
    size_mb = MODEL_PATH.stat().st_size / 1e6
    record("face_landmarker.task", size_mb > 1, f"{size_mb:.1f} MB")


def check_face_landmarker() -> None:
    try:
        import mediapipe as mp
        import numpy as np
        from mediapipe.tasks.python import BaseOptions, vision

        opts = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=vision.RunningMode.IMAGE,
            output_face_blendshapes=True,
            num_faces=1,
        )
        with vision.FaceLandmarker.create_from_options(opts) as lm:
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.zeros((240, 320, 3), np.uint8))
            lm.detect(img)
        record("FaceLandmarker runs", True)
    except Exception as e:  # noqa: BLE001
        record("FaceLandmarker runs", False, f"{type(e).__name__}: {e}")


def check_camera() -> None:
    import cv2

    cap = cv2.VideoCapture(0)
    ok, frame = cap.read() if cap.isOpened() else (False, None)
    cap.release()
    hint = "" if ok else "macOS: 隐私与安全性→摄像头; Windows: 设置→隐私→相机"
    record("webcam frame", bool(ok), f"{frame.shape}" if ok else hint)


def check_input() -> None:
    from pynput import keyboard, mouse

    count = {"n": 0}

    def bump(*_args: object) -> None:
        count["n"] += 1

    print("       请在 5 秒内随便打几个字、动一下鼠标 ...")
    kl = keyboard.Listener(on_press=bump)
    ml = mouse.Listener(on_move=bump)
    kl.start()
    ml.start()
    time.sleep(5)
    kl.stop()
    ml.stop()
    hint = "" if count["n"] else "macOS: 隐私与安全性→辅助功能 + 输入监控，给终端授权后重启终端"
    record("keyboard/mouse events", count["n"] > 0, f"{count['n']} events" if count["n"] else hint)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", action="store_true")
    parser.add_argument("--input", action="store_true")
    args = parser.parse_args()

    print(f"Platform: {platform.system()} {platform.machine()}\n")
    check_python()
    check_imports()
    if installed("mediapipe"):
        check_mediapipe_tasks()
        check_model()
        check_face_landmarker()
        if args.camera:
            check_camera()
    elif args.camera:
        print("[SKIP] --camera: vision extra not installed")
    if args.input:
        if installed("pynput"):
            check_input()
        else:
            print("[SKIP] --input: input extra not installed")

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
