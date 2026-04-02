from typing import Any


def diff_env(before: dict[str, str], after: dict[str, str]) -> dict[str, Any]:
    added: dict[str, str] = {}
    removed: list[str] = []
    changed: dict[str, dict[str, str]] = {}
    before_keys = set(before)
    after_keys = set(after)
    for k in sorted(after_keys - before_keys):
        added[k] = after[k]
    for k in sorted(before_keys - after_keys):
        removed.append(k)
    for k in sorted(before_keys & after_keys):
        if before[k] != after[k]:
            changed[k] = {"before": before[k], "after": after[k]}
    return {"added": added, "removed": removed, "changed": changed}


def snapshot_env() -> dict[str, str]:
    import os

    return dict(os.environ)
