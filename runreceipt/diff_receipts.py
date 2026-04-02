from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def resolve_receipt_json(path: Path) -> Path:
    p = path.expanduser().resolve()
    if p.is_dir():
        return p / "receipt.json"
    return p


def load_receipt(path: Path) -> dict[str, Any]:
    jp = resolve_receipt_json(path)
    if not jp.is_file():
        raise FileNotFoundError(str(jp))
    return json.loads(jp.read_text(encoding="utf-8"))


def _sets_for_env_diff(ed: dict[str, Any] | None) -> tuple[set[str], set[str], set[str]]:
    if not ed:
        return set(), set(), set()
    added = set((ed.get("added") or {}).keys())
    removed = set(ed.get("removed") or [])
    changed = set((ed.get("changed") or {}).keys())
    return added, removed, changed


def _all_touched(ed: dict[str, Any] | None) -> set[str]:
    a, r, c = _sets_for_env_diff(ed)
    return a | r | c


def _fmt_val(v: Any) -> str:
    if v is None:
        return "null"
    return str(v)


def _pair_lines(label: str, left: Any, right: Any) -> list[str]:
    ls = _fmt_val(left)
    rs = _fmt_val(right)
    same = ls == rs
    mark = " " if same else "*"
    return [
        f"  {mark} {label}:",
        f"      a: {ls}",
        f"      b: {rs}",
    ]


def format_receipt_diff(data_a: dict[str, Any], data_b: dict[str, Any], path_a: str, path_b: str) -> str:
    lines: list[str] = []
    lines.append("runreceipt diff")
    lines.append("")
    lines.append(f"a: {path_a}")
    lines.append(f"  receipt_id: {data_a.get('receipt_id', '')}")
    lines.append(f"  when: {data_a.get('started_at_utc', '')}")
    lines.append(f"b: {path_b}")
    lines.append(f"  receipt_id: {data_b.get('receipt_id', '')}")
    lines.append(f"  when: {data_b.get('started_at_utc', '')}")
    lines.append("")
    lines.append("Exit")
    lines.append("")
    lines.extend(_pair_lines("returncode", data_a.get("returncode"), data_b.get("returncode")))
    exa = data_a.get("exit") or {}
    exb = data_b.get("exit") or {}
    lines.extend(_pair_lines("exit.kind", exa.get("kind"), exb.get("kind")))
    lines.extend(_pair_lines("exit.code", exa.get("code"), exb.get("code")))
    lines.extend(_pair_lines("exit.detail", exa.get("detail"), exb.get("detail")))
    lines.append("")
    lines.append("Git")
    lines.append("")
    ga = data_a.get("git") or {}
    gb = data_b.get("git") or {}
    lines.extend(_pair_lines("head", ga.get("head"), gb.get("head")))
    lines.extend(_pair_lines("branch", ga.get("branch"), gb.get("branch")))
    lines.extend(_pair_lines("is_dirty", ga.get("is_dirty"), gb.get("is_dirty")))
    lines.append("")
    lines.append("Env delta (what moved during each run)")
    lines.append("")
    eda = data_a.get("env_diff") or {}
    edb = data_b.get("env_diff") or {}
    aa, ar, ac = _sets_for_env_diff(eda)
    ba, br, bc = _sets_for_env_diff(edb)
    lines.append(f"  a: added {len(aa)}, removed {len(ar)}, changed {len(ac)}")
    lines.append(f"  b: added {len(ba)}, removed {len(br)}, changed {len(bc)}")
    lines.append("")
    ta = _all_touched(eda)
    tb = _all_touched(edb)
    only_a = sorted(ta - tb)
    only_b = sorted(tb - ta)
    both = sorted(ta & tb)
    lines.append("  keys touched only in a's run:")
    if only_a:
        for k in only_a:
            lines.append(f"    - {k}")
    else:
        lines.append("    (none)")
    lines.append("")
    lines.append("  keys touched only in b's run:")
    if only_b:
        for k in only_b:
            lines.append(f"    - {k}")
    else:
        lines.append("    (none)")
    lines.append("")
    lines.append("  keys touched in both runs (name only; values may differ):")
    if both:
        for k in both:
            lines.append(f"    - {k}")
    else:
        lines.append("    (none)")
    lines.append("")
    return "\n".join(lines)
