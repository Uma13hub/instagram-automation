# main.py

## What it does
The command-line entry point. It reads your command, logs in to Instagram through
`browser.py`, runs the matching action from `web.py`, prints the result and saves it
as JSON in the `output/` folder.

## Commands
```
python main.py read   profile | posts | reels | followers | comments | report
python main.py create comment | message
python main.py update caption
python main.py delete comment | post
```

## Options
| Option | Meaning |
|--------|---------|
| `--config` | Login JSON file (default `config.json`) |
| `--username` | Profile to use (default: from the config file) |
| `--limit` | How many items to read (default 5) |
| `--url` | Post or reel link |
| `--to` | Username to message |
| `--text` | Comment, message or caption text |

If a required option is missing, it tells you which one.

## Prerequisites
- Python 3.9 or newer
- Google Chrome installed
- `pip install -r requirements.txt`
- `config.json` filled in (see `docs/browser.md`)
- Files `web.py` and `browser.py` in the same folder
