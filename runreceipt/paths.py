from __future__ import annotations

import os
from pathlib import Path


def default_receipt_root() -> Path:
    base = os.environ.get("RUNRECEIPT_DIR")
    if base:
        return Path(base).expanduser().resolve()
    return Path.home() / ".local" / "share" / "runreceipt"


def receipts_dir(root: Path | None = None) -> Path:
    r = root if root is not None else default_receipt_root()
    return r / "receipts"


def secret_path() -> Path:
    base = os.environ.get("RUNRECEIPT_DIR")
    if base:
        return Path(base).expanduser().resolve() / "secret"
    return Path.home() / ".local" / "share" / "runreceipt" / "secret"
