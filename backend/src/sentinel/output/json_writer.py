import json
import os
from pathlib import Path

from sentinel.models import FatigueState, to_json_dict


def write_metrics(state: FatigueState, path: Path) -> None:
    """Write the latest state to path atomically (tmp file + rename)."""
    # 1. create the folder
    path.parent.mkdir(parents=True, exist_ok=True)
    # 2. make the tmp path
    tmp = path.with_suffix(".json.tmp")
    # 3. write the JSON text into tmp
    tmp.write_text(json.dumps(to_json_dict(state), ensure_ascii=False), encoding="utf-8")
    # 4. os.replace tmp -> path
    os.replace(tmp, path)


def append_log(state: FatigueState, path: Path) -> None:
    """Append one JSON line to the history log."""
    
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(to_json_dict(state), ensure_ascii=False) + "\n")