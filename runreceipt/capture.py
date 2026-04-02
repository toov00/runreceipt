from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any


def exit_reason(returncode: int | None) -> dict[str, Any]:
    if returncode is None:
        return {"kind": "unknown", "code": None, "detail": "no return code"}
    if returncode < 0:
        sig = -returncode
        return {
            "kind": "signal",
            "code": returncode,
            "signal_number": sig,
            "detail": f"terminated by signal {sig}",
        }
    if returncode == 0:
        return {"kind": "success", "code": 0, "detail": "exited normally with code 0"}
    return {
        "kind": "failure",
        "code": returncode,
        "detail": f"exited with code {returncode}",
    }


def run_command(argv: list[str], cwd: Path) -> dict[str, Any]:
    if not argv:
        return {
            "argv": [],
            "returncode": None,
            "stdout": "",
            "stderr": "no command given",
            "exit": exit_reason(None),
        }
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=False,
            timeout=None,
        )
    except OSError as e:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": "",
            "stderr": str(e),
            "exit": {"kind": "os_error", "code": None, "detail": str(e)},
        }
    stdout_b = proc.stdout or b""
    stderr_b = proc.stderr or b""
    stdout = stdout_b.decode("utf-8", errors="replace")
    stderr = stderr_b.decode("utf-8", errors="replace")
    return {
        "argv": argv,
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "exit": exit_reason(proc.returncode),
    }


def forward_streams(run_result: dict[str, Any]) -> None:
    sys.stdout.write(run_result.get("stdout") or "")
    sys.stderr.write(run_result.get("stderr") or "")
