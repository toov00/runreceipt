# runreceipt

Wraps commands you care about and drops a signed receipt next to your other files: cwd, git HEAD, a diff of process environment variables around the run, captured stdout and stderr, optional file copies, and a clear exit reason. HMAC-SHA256 ties the JSON together so you can spot tampering later.

(( This is my paper trail without another SaaS account :') ))

## What It Does

`runreceipt run` executes a command in a directory you choose (or the current one), compares the process environment immediately before and after the child, records git metadata when you are inside a repo, stores full stdout and stderr, and writes `receipt.json` plus a readable `receipt.md` under your receipts folder. You can attach files (build outputs, configs) with `--artifact`. Each payload is signed with a secret from `RUNRECEIPT_SECRET` or a small `secret` file next to your data dir. `runreceipt verify` recomputes the HMAC and tells you if the JSON still matches.

## Environment Capture

The receipt records process environment variables only: the same key/value pairs Python exposes as `os.environ` while `runreceipt` is running. It does not dump your whole shell profile, disk `PATH`, installed toolchains, limits, or running services unless those happen to show up as env vars at capture time.

For each run it takes a copy of the environment before starting the child and another after the child exits. The saved `env_diff` in `receipt.json` is the delta between those two copies, not two full snapshots:

* `added`: keys that exist only in the after copy  
* `removed`: keys that existed only in the before copy  
* `changed`: keys present in both but with different values, with `before` and `after` strings  

Variables that stay the same are omitted. Anything the child (or libraries in this process) never adds, removes, or changes will not appear in `env_diff`. Changes you make only in your interactive shell **after** `runreceipt` returns are not visible to this mechanism.

## Installation

You need Python 3.10 or newer.

```bash
git clone https://github.com/youruser/runreceipt.git
cd runreceipt
pip install .
```

For an isolated install:

```bash
pipx install .
```

To run from the repo without installing, use `python -m runreceipt` from the project root. For development, run `pip install -e ".[dev]"`, then `ruff check .` and `pytest`.

## Usage

One-time secret (pick one approach and keep it stable):

```bash
export RUNRECEIPT_SECRET="$(python -c "import secrets; print(secrets.token_hex(32))")"
```

Or put the same string in `~/.local/share/runreceipt/secret` (or `$RUNRECEIPT_DIR/secret` if you set `RUNRECEIPT_DIR`). The directory is created when you save receipts; create the file yourself the first time.

Run something and keep a receipt (prints child output by default):

```bash
runreceipt run pytest -q
runreceipt run --cwd ~/work/app -- npm run build
runreceipt run --artifact dist/bundle.js --artifact reports/summary.txt -- ./scripts/release.sh
```

Quiet the meta line, or keep output only in the receipt:

```bash
runreceipt run --quiet -- git status
runreceipt run --no-forward -- ./noisy-tool
```

Check that a receipt was not edited after the fact:

```bash
runreceipt verify ~/.local/share/runreceipt/receipts/some_id
runreceipt verify /path/to/receipt.json
```

Compare two receipts (exit, git, and which env keys moved in each run):

```bash
runreceipt diff ~/.local/share/runreceipt/receipts/old_id ~/.local/share/runreceipt/receipts/new_id
runreceipt diff ./r1/receipt.json ./r2/receipt.json
```

Lines marked with `*` differ between the two files.

Open a receipt as Markdown (uses `PAGER` / `less` on a tty; pipe or use `--no-pager` for plain stdout):

```bash
runreceipt show 20260402T120000Z_pytest_a1b2c3d4
runreceipt show ~/.local/share/runreceipt/receipts/some_id
runreceipt show /path/to/receipt.md
runreceipt show --no-pager some_id | head -n 40
```

## Reference

Subcommands: `run`, `verify`, `diff`, `show`.

`diff` takes two paths; each may be a receipt directory (uses `receipt.json` inside) or a direct path to `receipt.json`. Signatures are not checked; load untrusted JSON carefully.

`show` resolves `target` in order: path to `receipt.md`, path to `receipt.json` (sibling `receipt.md`), directory containing `receipt.md`, else `receipt_id` under `$RUNRECEIPT_DIR/receipts/`. Options: `--receipt-root`, `--no-pager`.

`run` options: `--cwd` (working directory for the child), `--artifact PATH` (repeatable, file copied under `artifacts/` in the receipt folder; path can be absolute or relative to cwd), `--receipt-root` (same effect as setting `RUNRECEIPT_DIR` for that invocation only), `--no-forward` (do not stream stdout/stderr to the terminal), `--quiet` (do not print where the receipt was written). Everything after `run` is the argv passed to `subprocess` (leading `--` is stripped if you needed it for your shell).

Environment: `RUNRECEIPT_SECRET` is the signing key as plain text. `RUNRECEIPT_DIR` overrides the storage root (default `~/.local/share/runreceipt`); receipts live in `$RUNRECEIPT_DIR/receipts/<receipt_id>/` with `receipt.json`, `receipt.md`, and optional `artifacts/`.

Exit status from `runreceipt run` matches the child when the child exits with a non-negative code; signals are reported as `128 + signal` like many shells. If the child never starts, `runreceipt` exits `1`. `runreceipt diff` exits `0` when both inputs are read successfully, `2` if a path is missing or JSON is invalid. `runreceipt show` exits `0` after printing, `2` if `receipt.md` cannot be resolved.

## Limitations

See [Environment Capture](#environment-capture) for what env data is and is not included. Git fields are best effort and empty outside a repo. Very large stdout or stderr still land in full JSON, which can get big; the Markdown view truncates long streams with a pointer to the JSON. Signing is HMAC with a shared secret, not a public-key notary.

## Contributing

Pull requests and issues are very welcome! :-)

## License

MIT
