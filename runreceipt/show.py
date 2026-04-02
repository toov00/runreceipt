from __future__ import annotations

import pydoc
import sys
from pathlib import Path

from runreceipt.paths import receipts_dir


def resolve_receipt_md(spec: str, receipt_root: Path | None) -> Path:
    p = Path(spec).expanduser()
    if p.is_file():
        if p.name == "receipt.md":
            return p.resolve()
        if p.name == "receipt.json":
            cand = p.parent / "receipt.md"
            if cand.is_file():
                return cand.resolve()
            raise FileNotFoundError(str(cand))
        raise FileNotFoundError(
            f"not receipt.md or receipt.json: {p.resolve()}",
        )
    if p.is_dir():
        cand = p / "receipt.md"
        if cand.is_file():
            return cand.resolve()
    rid = receipts_dir(receipt_root) / spec / "receipt.md"
    if rid.is_file():
        return rid.resolve()
    raise FileNotFoundError(str(rid))


def display_receipt_md(md_path: Path, use_pager: bool) -> None:
    text = md_path.read_text(encoding="utf-8")
    if use_pager and sys.stdout.isatty():
        pydoc.pager(text)
    else:
        sys.stdout.write(text)
        if text and not text.endswith("\n"):
            sys.stdout.write("\n")
