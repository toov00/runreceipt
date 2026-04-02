import hashlib
import hmac
import json
import os
from typing import Any

from runreceipt.paths import secret_path


def load_secret() -> bytes:
    env = os.environ.get("RUNRECEIPT_SECRET")
    if env:
        return env.encode("utf-8")
    p = secret_path()
    if p.is_file():
        return p.read_bytes().strip()
    raise RuntimeError(
        "Set RUNRECEIPT_SECRET or write a one-line secret to "
        + str(p)
        + " (e.g. python -c \"import secrets; print(secrets.token_hex(32))\")"
    )


def payload_for_signing(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if k != "signature"}


def canonical_json(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_payload(data: dict[str, Any], secret: bytes) -> str:
    body = payload_for_signing(data)
    msg = canonical_json(body)
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def verify_payload(data: dict[str, Any], secret: bytes) -> bool:
    sig = data.get("signature")
    if not sig or not isinstance(sig, str):
        return False
    expected = sign_payload(data, secret)
    return hmac.compare_digest(expected, sig)
