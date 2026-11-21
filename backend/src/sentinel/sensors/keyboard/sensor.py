import time
import threading
from collections import deque
from pynput import keyboard

from sentinel.models import KeyboardFeatures
from . import features
from sentinel.scoring.config import TYPING_PAUSE_S

class KeyboardSensor:
    name = "keyboard"
    def __init__(self):
        self.timestamps=deque()  # Store timestamps of key presses
        self.backspace_timestamps=deque()  # Store timestamps of backspace/delete presses
        self.keystrokes=0
        self.start_time=time.monotonic()  # Record the start time of the sensor
        self.last_key_time=self.start_time  # Initialize last key time to start time
        self.last_snapshot_time=self.start_time
        self.burst_start=None  # Start time of the current typing burst
        self.available=False
        self.listener=None
        self.lock=threading.Lock()  # Lock for thread-safe access to shared data


    def start(self)->None:
       if self.listener is not None:
           return#if listener is already running, do nothing
       self.start_time=time.monotonic()
       self.last_key_time=self.start_time
       self.last_snapshot_time=self.start_time
       try: #try an piece code that might fail
           self.listener=keyboard.Listener(on_press=self._on_press)
           self.listener.start()
           self.available=True
       except Exception:
           self.listener=None
           self.available=False

    def _on_press(self, key) -> None:
        with self.lock:
            now = time.monotonic()

            if self.burst_start is None or now - self.last_key_time > TYPING_PAUSE_S:# If this is the first key press or if the last key press was more than 2 seconds ago, start a new burst
                self.burst_start = now

            self.timestamps.append(now)
            self.keystrokes += 1

            if key in (keyboard.Key.backspace, keyboard.Key.delete):#detect key presses for backspace or delete
                self.backspace_timestamps.append(now)

            self.last_key_time = now



    def stop(self) -> None:
        try:
            if self.listener is not None:
                self.listener.stop()
        except Exception:
            pass
        finally:
            self.listener = None
            self.available = False



    def snapshot(self) -> KeyboardFeatures:
        with self.lock:
            now = time.monotonic()
            cutoff = now - 60#define the starting point for the 60-second window

            while self.timestamps and self.timestamps[0] < cutoff:#remove expired timestamps of all key presses
                self.timestamps.popleft()

            while self.backspace_timestamps and self.backspace_timestamps[0] < cutoff:#remove expired timestamps of all backspace/delete presses
                self.backspace_timestamps.popleft()
                
            timestamps = list(self.timestamps)#convert the deque into a list for feature calculations
            intervals = features.inter_key_intervals(timestamps) #calculate intervals between consecutive key presses, and excluding intervals of 2 seconds or longer.

            window_s = now - self.last_snapshot_time #calculate the actual duration of the current sampling window.
            idle_s = now - self.last_key_time#calculate the time since the last key press to determine if the user is idle.

            # Calculate the duration of the current typing burst.
            # If the user has been idle for more than 2 seconds,
            # the current typing burst has ended.
            burst_s = 0.0
            if self.burst_start is not None and idle_s <= TYPING_PAUSE_S:
                burst_s = now - self.burst_start

      # package the calculated features into a KeyboardFeatures object.
            result = KeyboardFeatures(
            available=self.available and self.listener is not None and self.listener.is_alive(),#check whether the keyboard listener is available and running
            window_s=window_s,
            keystrokes=self.keystrokes,
            keys_per_min=features.keys_per_min(timestamps, now),
            backspace_ratio=features.backspace_ratio(len(self.backspace_timestamps),len(timestamps)),#proportion of deletion keys within the last 60 sec
            iki_mean_ms=features.iki_mean_ms(intervals),
            iki_cv=features.iki_cv(intervals),
            typing_burst_s=burst_s,#duration of continuous trping in sec
            seconds_since_last_key=idle_s)
        # reset the key counter for the next sampling window.
        # preserve the rolling history for 60-second calculations.
            self.keystrokes=0
            self.last_snapshot_time=now#update the snapshot timestamp for the next window
            return result
           
