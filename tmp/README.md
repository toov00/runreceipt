# <img src="crumb.png" alt="" width="70" /> crumb

Saves commands, snippets, and short notes as *breadcrumbs* you can search later. One JSON file in `~/.config/crumb/`, no DB or account.

(( I use this so I never forget that one command again! There's so much my brain can holddd ))

## What It Does

You add stuff from the terminal (or from scripts), search by keyword, filter by tag, copy by id, or export to Markdown. Everything lives in a single file. Set `CRUMB_DIR` if you want that file somewhere else (e.g. a synced folder). Tags and descriptions help you find things later (e.g. `git`, `docker`, `jq`). No signups, no API; it's just a small CLI and a JSON file you own.

## Installation

Need Python 3.10+.

```bash
git clone https://github.com/toov00/crumb.git
cd crumb
pip install .
# or for an isolated install:
pipx install .
```

To run from source (no install): from the repo root run `python -m core`. For development: `pip install -e ".[dev]"` then `ruff check .` and `pytest tests/`.

## Usage

Add stuff (with optional tags and a short description):

```bash
crumb add "docker ps -a"
crumb add "ffmpeg -i in.mp4 -vn out.mp3" --tag ffmpeg,audio --desc "strip audio from video"
crumb add "jq '.[].name' data.json" --tag jq
```

Search and list:

```bash
crumb search docker
crumb list
crumb list --tag git
crumb list -n 5
```

Copy a crumb to the clipboard (uses `pbcopy` / `xclip` / `clip`; if none found, it just prints), or export to Markdown:

```bash
crumb copy 3
crumb export
crumb export --out crumbs.md
```

Other: `crumb tags` for tag counts, `crumb edit 3 "new command"` (or `crumb edit 3 --desc "updated"`) to update one, `crumb delete 3` (or `crumb rm 3`) to remove one, `crumb clear` to remove all.

## Reference

Commands: `add`, `search` (alias `s`), `list` (alias `ls`), `copy` (alias `cp`), `edit` (alias `e`), `delete` (alias `rm`), `tags`, `clear`, `export`. On `edit`: optional new content, `--desc`, `--tag` (replaces tags). On `add`: `--tag` / `-t`, `--desc` / `-d`. On `list`: `--tag`, `-n`. On `export`: `--out` / `-o`.

Data lives in `~/.config/crumb/crumbs.json`. Override with `CRUMB_DIR`, e.g. `export CRUMB_DIR="$HOME/Dropbox/crumb"` in your shell rc.

## Limitations

No builtin sync; point `CRUMB_DIR` at a synced folder if you want the same file on multiple machines. `copy` needs `pbcopy`, `xclip`, or `clip` on the system; otherwise it just prints. One JSON file for everything; fine for hundreds of entries, could get slow if you go much bigger.

## Contributing

PRs and issues are very welcome! :-))

## License

MIT

## Resources

* [GitHub](https://github.com/toov00/crumb)
* [pipx](https://pypa.github.io/pipx/) for an isolated install
