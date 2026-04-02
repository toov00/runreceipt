import json
from pathlib import Path

import pytest

from runreceipt.receipt import build_payload, finalize_and_write
from runreceipt.sign import load_secret, sign_payload, verify_payload


@pytest.fixture
def secret(monkeypatch, tmp_path):
    p = tmp_path / "secret"
    p.write_text("test-secret-value", encoding="utf-8")
    monkeypatch.setenv("RUNRECEIPT_DIR", str(tmp_path))
    monkeypatch.delenv("RUNRECEIPT_SECRET", raising=False)
    return b"test-secret-value"


def test_sign_roundtrip(secret):
    data = {"a": 1, "b": [2, 3]}
    sig = sign_payload(data, secret)
    signed = {**data, "signature": sig}
    assert verify_payload(signed, secret)
    signed["signature"] = "deadbeef"
    assert not verify_payload(signed, secret)


def test_load_secret_env(monkeypatch, tmp_path):
    monkeypatch.setenv("RUNRECEIPT_SECRET", "from-env")
    monkeypatch.delenv("RUNRECEIPT_DIR", raising=False)
    assert load_secret() == b"from-env"


def test_finalize_writes_verifiable_json(secret, tmp_path):
    out = tmp_path / "receipts" / "r1"
    payload = build_payload(
        receipt_id_value="r1",
        cwd=Path("/tmp"),
        argv=["echo", "hi"],
        git={},
        env_diff={},
        run={
            "stdout": "hi\n",
            "stderr": "",
            "returncode": 0,
            "exit": {"kind": "success", "code": 0, "detail": "ok"},
        },
        artifacts_meta=[],
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:00:01Z",
    )
    finalize_and_write(payload, out, secret)
    raw = json.loads((out / "receipt.json").read_text(encoding="utf-8"))
    assert verify_payload(raw, secret)
    assert (out / "receipt.md").is_file()
