import math
import time
from sentinel.models import MouseFeatures

class MockMouseSensor:
    name = "mouse"

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def snapshot(self) -> MouseFeatures:
        t = time.time()
        return MouseFeatures(
            available=True,
            window_s=5.0,
            distance_px=3000 + 2000 * math.sin(t / 60),
            speed_mean_px_s=800 + 500 * math.sin(t / 45),
            clicks=int(5 + 4 * math.sin(t / 30)),
            scrolls=int(10 + 8 * math.sin(t / 50)),
            active_s=2.5 + 2 * math.sin(t / 40),
            seconds_since_last_event=0.5,
        )