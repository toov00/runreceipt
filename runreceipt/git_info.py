import subprocess
from pathlib import Path
from typing import Any


def git_snapshot(cwd: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "head": None,
        "branch": None,
        "is_dirty": None,
        "inside_work_tree": False,
    }
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0:
            out["head"] = r.stdout.strip()
            out["inside_work_tree"] = True
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0:
            out["branch"] = r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode == 0:
            out["is_dirty"] = len(r.stdout.strip()) > 0
    except (OSError, subprocess.TimeoutExpired):
        pass
    return out
