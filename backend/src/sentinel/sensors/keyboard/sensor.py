import time
import threading
from collections import deque
from pynput import keyboard

from sentinel.models import KeyboardFeatures
from . import features

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
        #if listener is already running, do nothing
        return

    self.start_time=time.monotonic()
    self.last_key_time=self.start_time
    self.last_snapshot_time=self.start_time
    try: #try aq piece code that might fail
        self.listener=keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
        self.available=True
    except Exception:
            self.listener=None
            self.available=False



        