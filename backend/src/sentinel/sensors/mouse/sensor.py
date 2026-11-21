import logging
import math
import threading
import time

from pynput import mouse

from sentinel.models import MouseFeatures

log = logging.getLogger(__name__)

MOVE_GAP_S = 0.2  # moves closer together than this count as continuous motion


class MouseSensor:
    name = "mouse"

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.listener = None
        self.available = False
        self.distance_px = 0.0
        self.active_s = 0.0
        self.clicks = 0
        self.scrolls = 0
        self.last_x = None
        self.last_y = None
        self.last_move_time = 0.0
        self.last_event_time = time.monotonic()
        self.last_snapshot_time = time.monotonic()

    def start(self) -> None:
        if self.listener is not None:
            return
        try:
            self.listener = mouse.Listener(
                on_move=self._on_move, on_click=self._on_click, on_scroll=self._on_scroll
            )
            self.listener.start()
            self.available = True
        except Exception:
            log.exception("mouse listener failed to start")
            self.listener = None
            self.available = False

    def stop(self) -> None:
        if self.listener is not None:
            self.listener.stop()
            self.listener = None
        self.available = False

    # Listener callbacks: only count and timestamp, nothing slow.
    def _on_move(self, x, y) -> None:
        now = time.monotonic()
        with self.lock:
            if self.last_x is not None:
                self.distance_px += math.hypot(x - self.last_x, y - self.last_y)
                gap = now - self.last_move_time
                if gap < MOVE_GAP_S:
                    self.active_s += gap
            self.last_x = x
            self.last_y = y
            self.last_move_time = now
            self.last_event_time = now

    def _on_click(self, x, y, button, pressed) -> None:
        with self.lock:
            if pressed:
                self.clicks += 1
            self.last_event_time = time.monotonic()

    def _on_scroll(self, x, y, dx, dy) -> None:
        with self.lock:
            self.scrolls += 1
            self.last_event_time = time.monotonic()

    def snapshot(self) -> MouseFeatures:
        now = time.monotonic()
        with self.lock:
            distance = self.distance_px
            active = self.active_s
            clicks = self.clicks
            scrolls = self.scrolls
            self.distance_px = 0.0
            self.active_s = 0.0
            self.clicks = 0
            self.scrolls = 0
            window = now - self.last_snapshot_time
            self.last_snapshot_time = now
            idle = now - self.last_event_time
        speed = distance / active if active > 0 else 0.0
        return MouseFeatures(
            available=self.available,
            window_s=window,
            distance_px=distance,
            speed_mean_px_s=speed,
            clicks=clicks,
            scrolls=scrolls,
            active_s=active,
            seconds_since_last_event=idle,
        )