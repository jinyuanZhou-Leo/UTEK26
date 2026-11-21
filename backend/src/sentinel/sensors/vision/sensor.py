from __future__ import annotations

import logging
import math
import threading
import time

from sentinel.models import VisionFeatures
from sentinel.sensors.vision import camera
from sentinel.sensors.vision.face_landmark import detect, get_landmarker

logger = logging.getLogger(__name__)

FPS = 10
BLINK_THRESHOLD = 0.5     # eyeBlink score > 0.5 = eye closed 
PERCLOS_THRESHOLD = 0.8   # P80: eyelid > 80% closed 
YAWN_THRESHOLD = 0.6      # jawOpen score
YAWN_MIN_S = 1.5          # mouth open at least this long = yawn
GAZE_AWAY_YAW_DEG = 30.0  # head turned more than this = not looking at screen


class VisionSensor:
    name = "vision"

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self._stop_event = threading.Event()  # must not be named `stop`, it would hide stop()
        self.ok = False  # if the sensor is working
        self.last_face_timestamp = time.monotonic()  # last time the user was looking at the screen
        self.eye_closed = False
        self.mouth_open_since: float | None = None
        self.pitch_deg = 0.0
        self.yaw_deg = 0.0
        self.roll_deg = 0.0
        self.distance_cm: float | None = None
        self._reset()

    def _reset(self) -> None:
        self.win_start = time.monotonic()
        self.frames = 0
        self.face_frames = 0
        self.blinks = 0
        self.yawns = 0
        self.closed_frames = 0  # frames with eye > PERCLOS_THRESHOLD
        self.light_sum = 0.0

    def start(self) -> None:
        # run this sensor in background
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self) -> None:
        self._stop_event.set()  # terminate the thread

    def snapshot(self) -> VisionFeatures:
        with self.lock:
            now = time.monotonic()
            time_elapsed = max(now - self.win_start, 1e-6)
            snapshot = VisionFeatures(
                available=self.ok,
                face_present=self.face_frames * 2 > self.frames,
                fps_effective=self.frames / time_elapsed,
                blinks=self.blinks,
                blink_rate_per_min=self.blinks / time_elapsed * 60,
                gaze_away_s=now - self.last_face_timestamp,
                head_pitch_deg=self.pitch_deg,
                face_distance_cm=self.distance_cm,
                forward_head_ratio=1.0,
                perclos=self.closed_frames / self.face_frames if self.face_frames else 0.0,
                head_yaw_deg=self.yaw_deg,
                head_roll_deg=self.roll_deg,
                ambient_light=self.light_sum / self.frames if self.frames else None,
                yawns=self.yawns,
            )
            self._reset()  # the data has been taken away, reset for the next window
            return snapshot

    def _run(self) -> None:
        try:
            cap = camera.open_cam()
            landmarker = get_landmarker()
        except Exception:
            logger.warning("webcam unavailable, vision disabled")
            return

        self.ok = True
        while not self._stop_event.is_set():
            # Reference: https://opencv.org/reading-and-writing-videos-using-opencv/
            frame_valid, frame = cap.read()
            if frame_valid:
                light = float(frame.mean()) / 255  # average brightness 0-1, dim light worsens eye strain
                self._update(detect(landmarker, camera.convert_bgr2rgb(frame)), light)
            self._stop_event.wait(1 / FPS)
        cap.release()
        landmarker.close()
        self.ok = False

    def _update(self, result, light: float) -> None:
        now = time.monotonic()
        with self.lock:
            self.frames += 1
            self.light_sum += light

            # face_blendshapes is 52 facial expression coefficients (https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker)
            if not result.face_blendshapes:
                return
            self.face_frames += 1

            # the data structure shown in the example is not correct
            # check this up instead: https://developers.google.com/edge/api/mediapipe/python/mp/tasks/vision/FaceLandmarkerResult
            s = {c.category_name: c.score for c in result.face_blendshapes[0]}

            # categories definition; https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Blendshape%20V2.pdf
            # Google's Documentation does NOT list the definition of 52 categories, however Apple does.
            # Therefore ..., check this up instead: https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation (This reference is found using AI, model: Claude Opus 5.5)
            eye = (s["eyeBlinkLeft"] + s["eyeBlinkRight"]) / 2
            closed = eye > BLINK_THRESHOLD
            if closed and not self.eye_closed:  # eyes change from open (last frame) to closed (this frame)
                self.blinks += 1
            self.eye_closed = closed

            # >>> AI-GENERATED (Claude Opus 5.5, 2026-11-21) | reviewed by: Jinyuan Zhou | purpose: VisionSensor (yawn, PERCLOS, head pose, distance, light)
            # PERCLOS: share of time the eyes are mostly closed, a standard drowsiness measure
            if eye > PERCLOS_THRESHOLD:
                self.closed_frames += 1

            # yawn: mouth open >= YAWN_MIN_S, counted once when the mouth closes
            if s["jawOpen"] > YAWN_THRESHOLD:
                if self.mouth_open_since is None:
                    self.mouth_open_since = now
            else:
                if self.mouth_open_since is not None and now - self.mouth_open_since >= YAWN_MIN_S:
                    self.yawns += 1
                self.mouth_open_since = None

            # head pose: Euler angles (x-y-z order) from the 3x3 rotation part of the 4x4 matrix
            # signs must be checked on camera (looking down should give positive pitch)
            m = result.facial_transformation_matrixes[0]
            self.pitch_deg = math.degrees(math.atan2(-m[1][2], m[2][2]))
            self.yaw_deg = math.degrees(math.asin(max(-1.0, min(1.0, m[0][2]))))  # clamp: float error could exceed [-1, 1]
            self.roll_deg = math.degrees(math.atan2(-m[0][1], m[0][0]))

            # distance: z of the translation part; MediaPipe's metric space is in cm (rough estimate)
            self.distance_cm = abs(float(m[2][3]))

            # looking at the screen = face found and head not turned away too far
            if abs(self.yaw_deg) <= GAZE_AWAY_YAW_DEG:
                self.last_face_timestamp = now
            # <<< AI-GENERATED


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    s = VisionSensor()
    s.start()
    for _ in range(10):
        time.sleep(10)
        print(s.snapshot())
    s.stop()
