import math
import time
from sentinel.models import KeyboardFeatures

class MockKeyboardSensor:
    name = "mouse"

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def snapshot(self) -> KeyboardFeatures:
        return KeyboardFeatures(
            available=True,                 # listener is running; False if macOS permission is missing
            window_s=5,                # actual window length, ~5.0
            keystrokes=5,                   # key presses in this window; count only, never which key
            keys_per_min=5,               # 60s: key presses in the last 60 s
            backspace_ratio=0.3 ,           # 60s: (Backspace + Delete) / total keys, 0–1
            iki_mean_ms=1 ,             # 60s: mean inter-key interval, intervals < 2 s only
            iki_cv=1,                     # 60s: std / mean of intervals; higher = less steady rhythm
            typing_burst_s=3,             # seconds of continuous typing since the last pause (> 2 s)
            seconds_since_last_key=0.3,     # seconds since the last key press
            micro_pauses_per_min=0
        )