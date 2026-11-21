import asyncio
import logging
import time
from collections import deque
from datetime import datetime

from sentinel import config
from sentinel.models import ContextFeatures, Features, FatigueState, KeyboardFeatures, MouseFeatures, VisionFeatures
from sentinel.output.json_writer import write_metrics, append_log

log = logging.getLogger(__name__)


class Engine:
    def __init__(self, keyboard, mouse, context, vision, model, interventions) -> None:
        self.keyboard = keyboard
        # TODO: store the other 5 the same way
        self.mouse = mouse
        self.context = context
        self.vision = vision
        self.model = model
        self.interventions = interventions
        self.last_intervention = None
        self.latest: FatigueState | None = None
        self.history: deque = deque(maxlen=config.HISTORY_MAX)
        self.seq = 0
        self.last_tick = time.monotonic()

    async def run(self) -> None:
        """Call tick() every 5 s without drifting."""
        t0 = time.monotonic()
        n = 0
        while True:
            n += 1
            # TODO: sleep until t0 + n * INTERVAL_S:
            target = t0 + n * config.INTERVAL_S
            await asyncio.sleep(max(0, target - time.monotonic()))
            self.tick()

    def tick(self) -> None:
        # 1. 
        try:
            kb = self.keyboard.snapshot()
        except Exception:
            log.exception("keyboard snapshot failed")
            kb = KeyboardFeatures(False, 5.0, 0, 0, 0, 0, 0, 0, 0)
        try:
            ms = self.mouse.snapshot()
        except Exception:
            log.exception("mouse snapshot failed")
            ms = MouseFeatures(False, 5.0, 0, 0, 0, 0, 0, 0)
        try:
            cx = self.context.snapshot()
        except Exception:
            log.exception("context snapshot failed")
            cx = ContextFeatures(False, "", "other")
        try:
            vs = self.vision.snapshot()
        except Exception:
            log.exception("vision snapshot failed")
            vs = VisionFeatures(False, False, 0, 0, 0, 0, 0, None, 1.0)
        # 2.
        now = time.monotonic()
        dt_s = now - self.last_tick
        self.last_tick = now
        features = Features(ts=time.time(), dt_s=dt_s, keyboard=kb, mouse=ms, context=cx,vision= vs)
        # 3.
        try: 
            state = self.model.update(features)
        except Exception:
            log.exception("scoring failed")
            return
        state.seq = self.seq
        self.seq += 1
        state.timestamp = datetime.now().astimezone().isoformat()
        self.latest = state
        self.history.append(state)

        # 4.
        try:
            write_metrics(state, config.METRICS_PATH)
            append_log(state, config.LOG_PATH)
        except Exception:
            log.exception("writing metrics failed")
        # 5. self.interventions.evaluate(state, features)
        try:
            self.last_intervention = self.interventions.evaluate(state, features)
        except Exception:
            log.exception("intervention failed")