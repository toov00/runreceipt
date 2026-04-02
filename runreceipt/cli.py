import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from runreceipt.capture import forward_streams, run_command
from runreceipt.diff_receipts import format_receipt_diff, load_receipt, resolve_receipt_json
from runreceipt.env_diff import diff_env, snapshot_env
from runreceipt.git_info import git_snapshot
from runreceipt.paths import receipts_dir
from runreceipt.receipt import (
    build_payload,
    copy_artifacts,
    finalize_and_write,
    receipt_id,
)
from runreceipt.show import display_receipt_md, resolve_receipt_md
from runreceipt.sign import load_secret, verify_payload


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_run(args: argparse.Namespace) -> int:
    argv = list(args.cmd or [])
    while argv and argv[0] == "--":
        argv = argv[1:]
    cwd = Path(args.cwd).expanduser().resolve() if args.cwd else Path.cwd()
    root = Path(args.receipt_root).expanduser().resolve() if args.receipt_root else None
    out_dir = receipts_dir(root)
    rid = receipt_id(argv)
    receipt_path = out_dir / rid
    started = _utc_now_iso()
    env_before = snapshot_env()
    git = git_snapshot(cwd)
    run = run_command(argv, cwd)
    env_after = snapshot_env()
    ed = diff_env(env_before, env_after)
    artifacts_meta = copy_artifacts(list(args.artifact or []), receipt_path, cwd)
    finished = _utc_now_iso()
    payload = build_payload(
        receipt_id_value=rid,
        cwd=cwd,
        argv=argv,
        git=git,
        env_diff=ed,
        run=run,
        artifacts_meta=artifacts_meta,
        started_at=started,
        finished_at=finished,
    )
    secret = load_secret()
    finalize_and_write(payload, receipt_path, secret)
    if not args.quiet:
        print(f"runreceipt: wrote {receipt_path}", file=sys.stderr)
    if not args.no_forward:
        forward_streams(run)
    rc = run.get("returncode")
    if rc is None:
        return 1
    if rc < 0:
        return 128 + (-rc)
    return rc


def cmd_verify(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if target.is_dir():
        json_path = target / "receipt.json"
    else:
        json_path = target
    if not json_path.is_file():
        print("runreceipt: receipt.json not found", file=sys.stderr)
        return 2
    data = json.loads(json_path.read_text(encoding="utf-8"))
    try:
        secret = load_secret()
    except RuntimeError as e:
        print(f"runreceipt: {e}", file=sys.stderr)
        return 2
    ok = verify_payload(data, secret)
    if ok:
        print("runreceipt: signature ok")
        return 0
    print("runreceipt: signature mismatch or missing", file=sys.stderr)
    return 1


def cmd_diff(args: argparse.Namespace) -> int:
    pa = Path(args.a).expanduser()
    pb = Path(args.b).expanduser()
    try:
        ja = resolve_receipt_json(pa)
        jb = resolve_receipt_json(pb)
        data_a = load_receipt(pa)
        data_b = load_receipt(pb)
    except FileNotFoundError as e:
        print(f"runreceipt: not found: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"runreceipt: invalid json: {e}", file=sys.stderr)
        return 2
    out = format_receipt_diff(data_a, data_b, str(ja), str(jb))
    print(out)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    root = Path(args.receipt_root).expanduser().resolve() if args.receipt_root else None
    try:
        md = resolve_receipt_md(args.target, root)
    except FileNotFoundError as e:
        print(f"runreceipt: receipt.md not found ({e})", file=sys.stderr)
        return 2
    use_pager = not args.no_pager
    display_receipt_md(md, use_pager)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="runreceipt", description="Signed receipts for shell commands")
    sub = p.add_subparsers(dest="command", required=True)
    pr = sub.add_parser("run", help="run a command and save a receipt")
    pr.add_argument(
        "--cwd",
        default=None,
        help="working directory for the child process (default: current directory)",
    )
    pr.add_argument(
        "--artifact",
        action="append",
        default=[],
        metavar="PATH",
        help="file to copy into the receipt (relative to cwd); repeatable",
    )
    pr.add_argument(
        "--receipt-root",
        default=None,
        help="override RUNRECEIPT_DIR / default storage root",
    )
    pr.add_argument(
        "--no-forward",
        action="store_true",
        help="do not print the command stdout and stderr to the terminal",
    )
    pr.add_argument(
        "--quiet",
        action="store_true",
        help="do not print the receipt path on stderr",
    )
    pr.add_argument(
        "cmd",
        nargs=argparse.REMAINDER,
        help="command and arguments (use -- before flags if the command starts with -)",
    )
    pr.set_defaults(func=cmd_run)
    pv = sub.add_parser("verify", help="check receipt.json HMAC signature")
    pv.add_argument("path", help="path to receipt directory or receipt.json")
    pv.set_defaults(func=cmd_verify)
    pd = sub.add_parser("diff", help="compare two receipt.json files (exit, git, env deltas)")
    pd.add_argument("a", help="receipt directory or path to receipt.json")
    pd.add_argument("b", help="receipt directory or path to receipt.json")
    pd.set_defaults(func=cmd_diff)
    ps = sub.add_parser("show", help="print receipt.md (paged on a tty)")
    ps.add_argument(
        "target",
        help="receipt id under receipts/, or path to receipt dir, receipt.md, or receipt.json",
    )
    ps.add_argument(
        "--receipt-root",
        default=None,
        help="override RUNRECEIPT_DIR for id lookup only",
    )
    ps.add_argument(
        "--no-pager",
        action="store_true",
        help="write to stdout only (no less/PAGER)",
    )
    ps.set_defaults(func=cmd_show)
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    code = args.func(args)
    raise SystemExit(code)
