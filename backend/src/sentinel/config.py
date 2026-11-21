from pathlib import Path

HOST = "127.0.0.1"
PORT = 8080
INTERVAL_S = 5.0

DATA_DIR = Path.home() / ".utekinetics"
METRICS_PATH = DATA_DIR / "metrics.json"
LOG_PATH = DATA_DIR / "metrics.log.jsonl"

HISTORY_MAX = 1440   # 2 hours of 5-second ticks