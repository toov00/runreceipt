import json

from runreceipt.diff_receipts import format_receipt_diff, load_receipt, resolve_receipt_json


def test_resolve_receipt_json_dir(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    f = d / "receipt.json"
    f.write_text("{}", encoding="utf-8")
    assert resolve_receipt_json(d) == f


def test_resolve_receipt_json_file(tmp_path):
    f = tmp_path / "receipt.json"
    f.write_text("{}", encoding="utf-8")
    assert resolve_receipt_json(f) == f.resolve()


def test_format_receipt_diff_smoke():
    a = {
        "receipt_id": "a1",
        "started_at_utc": "t0",
        "returncode": 0,
        "exit": {"kind": "success", "code": 0, "detail": "ok"},
        "git": {"head": "aaa", "branch": "main", "is_dirty": False},
        "env_diff": {
            "added": {"X": "1"},
            "removed": [],
            "changed": {},
        },
    }
    b = {
        "receipt_id": "b1",
        "started_at_utc": "t1",
        "returncode": 1,
        "exit": {"kind": "failure", "code": 1, "detail": "bad"},
        "git": {"head": "bbb", "branch": "main", "is_dirty": True},
        "env_diff": {
            "added": {},
            "removed": ["Y"],
            "changed": {"Z": {"before": "0", "after": "1"}},
        },
    }
    text = format_receipt_diff(a, b, "/a.json", "/b.json")
    assert "returncode" in text
    assert "aaa" in text and "bbb" in text
    assert "X" in text and "Y" in text
    assert "keys touched only in a's run:" in text


def test_load_receipt_roundtrip(tmp_path):
    d = tmp_path / "rid"
    d.mkdir()
    body = {"receipt_id": "x", "started_at_utc": "t"}
    (d / "receipt.json").write_text(json.dumps(body), encoding="utf-8")
    got = load_receipt(d)
    assert got["receipt_id"] == "x"
