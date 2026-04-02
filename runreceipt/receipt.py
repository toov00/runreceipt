import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runreceipt.sign import sign_payload

_MD_BLOCK_MAX = 60000


def _slug_from_argv(argv: list[str]) -> str:
    if not argv:
        return "empty"
    raw = argv[0]
    base = Path(raw).name or raw
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", base).strip("_")
    return (s[:40] or "cmd")[:40]


def receipt_id(argv: list[str]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _slug_from_argv(argv)
    short = uuid.uuid4().hex[:8]
    return f"{ts}_{slug}_{short}"


def _truncate_for_md(text: str) -> tuple[str, bool]:
    if len(text) <= _MD_BLOCK_MAX:
        return text, False
    return text[:_MD_BLOCK_MAX] + "\n\n(truncated for this view; full text is in receipt.json)\n", True


def render_markdown(data: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Command receipt")
    lines.append("")
    lines.append(f"**When:** {data.get('started_at_utc', '')}")
    lines.append(f"**Receipt id:** `{data.get('receipt_id', '')}`")
    lines.append("")
    lines.append("## Where")
    lines.append("")
    lines.append(f"- **cwd:** `{data.get('cwd', '')}`")
    lines.append("")
    lines.append("## Command")
    lines.append("")
    lines.append("```")
    lines.append(" ".join(data.get("argv") or []))
    lines.append("```")
    lines.append("")
    git = data.get("git") or {}
    lines.append("## Git")
    lines.append("")
    lines.append(f"- **HEAD:** `{git.get('head') or 'n/a'}`")
    lines.append(f"- **branch:** `{git.get('branch') or 'n/a'}`")
    dirty = git.get("is_dirty")
    lines.append(f"- **dirty tree:** `{dirty if dirty is not None else 'n/a'}`")
    lines.append("")
    ex = data.get("exit") or {}
    lines.append("## Exit")
    lines.append("")
    lines.append(f"- **kind:** {ex.get('kind', '')}")
    lines.append(f"- **detail:** {ex.get('detail', '')}")
    lines.append(f"- **code:** {ex.get('code')}")
    lines.append("")
    ed = data.get("env_diff") or {}
    lines.append("## Environment changes")
    lines.append("")
    added = ed.get("added") or {}
    removed = ed.get("removed") or []
    changed = ed.get("changed") or {}
    lines.append(f"- **keys added:** {len(added)}")
    lines.append(f"- **keys removed:** {len(removed)}")
    lines.append(f"- **keys changed:** {len(changed)}")
    lines.append("")
    if added:
        lines.append("### Added keys")
        lines.append("")
        for k in sorted(added.keys()):
            lines.append(f"- `{k}`")
        lines.append("")
    if removed:
        lines.append("### Removed keys")
        lines.append("")
        for k in removed:
            lines.append(f"- `{k}`")
        lines.append("")
    if changed:
        lines.append("### Changed keys")
        lines.append("")
        for k in sorted(changed.keys()):
            lines.append(f"- `{k}`")
        lines.append("")
    out = data.get("outputs") or {}
    so = out.get("stdout") or ""
    se = out.get("stderr") or ""
    lines.append("## Stdout")
    lines.append("")
    block, _ = _truncate_for_md(so)
    lines.append("```")
    lines.append(block.rstrip("\n"))
    lines.append("```")
    lines.append("")
    lines.append("## Stderr")
    lines.append("")
    block, _ = _truncate_for_md(se)
    lines.append("```")
    lines.append(block.rstrip("\n"))
    lines.append("```")
    lines.append("")
    arts = data.get("artifacts") or []
    lines.append("## Artifacts")
    lines.append("")
    if not arts:
        lines.append("_none recorded_")
    else:
        for a in arts:
            lines.append(f"- `{a.get('stored_path', '')}` (from `{a.get('source_path', '')}`)")
    lines.append("")
    lines.append("## Signature")
    lines.append("")
    lines.append(f"HMAC-SHA256 over canonical JSON (payload without `signature`): `{data.get('signature', '')}`")
    lines.append("")
    return "\n".join(lines)


def copy_artifacts(
    artifact_sources: list[str],
    receipt_dir: Path,
    cwd: Path,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not artifact_sources:
        return result
    dest_root = receipt_dir / "artifacts"
    dest_root.mkdir(parents=True, exist_ok=True)
    for i, spec in enumerate(artifact_sources):
        p = Path(spec).expanduser()
        src = p.resolve() if p.is_absolute() else (cwd / p).resolve()
        if not src.is_file():
            result.append(
                {
                    "source_path": spec,
                    "stored_path": None,
                    "error": "not a file or missing",
                }
            )
            continue
        name = src.name
        dest_name = f"{i:02d}_{name}"
        dest = dest_root / dest_name
        shutil.copy2(src, dest)
        result.append(
            {
                "source_path": str(src),
                "stored_path": str(dest.relative_to(receipt_dir)),
            }
        )
    return result


def build_payload(
    *,
    receipt_id_value: str,
    cwd: Path,
    argv: list[str],
    git: dict[str, Any],
    env_diff: dict[str, Any],
    run: dict[str, Any],
    artifacts_meta: list[dict[str, Any]],
    started_at: str,
    finished_at: str,
) -> dict[str, Any]:
    return {
        "receipt_id": receipt_id_value,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "cwd": str(cwd),
        "argv": argv,
        "git": git,
        "env_diff": env_diff,
        "outputs": {
            "stdout": run.get("stdout", ""),
            "stderr": run.get("stderr", ""),
        },
        "exit": run.get("exit"),
        "returncode": run.get("returncode"),
        "artifacts": artifacts_meta,
    }


def finalize_and_write(
    payload: dict[str, Any],
    receipt_dir: Path,
    secret: bytes,
) -> dict[str, Any]:
    receipt_dir.mkdir(parents=True, exist_ok=True)
    sig = sign_payload(payload, secret)
    signed = {**payload, "signature": sig}
    json_path = receipt_dir / "receipt.json"
    json_path.write_text(
        json.dumps(signed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path = receipt_dir / "receipt.md"
    md_path.write_text(render_markdown(signed), encoding="utf-8")
    return signed
