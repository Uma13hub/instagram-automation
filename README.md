# Instagram CRUD Automation (Python + Selenium)

Logs in to Instagram in Chrome with credentials from a JSON file, then performs
create / read / update / delete operations on your own account.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy config.example.json config.json    # then add your username and password
python main.py read profile
```

All commands are listed in [RUN_COMMANDS.md](RUN_COMMANDS.md).

## Operations

| Operation | Command |
|-----------|---------|
| **Read** profile counts | `python main.py read profile` |
| **Read** posts / reels (links) | `python main.py read posts --limit 5` / `read reels` |
| **Read** followers (sample) | `python main.py read followers --limit 20` |
| **Read** comments of a post | `python main.py read comments --url <post-url>` |
| **Read** full report | `python main.py read report --limit 3` |
| **Create** a comment | `python main.py create comment --url <post-url> --text "Nice!"` |
| **Create** a direct message | `python main.py create message --to <username> --text "Hello!"` |
| **Update** a post caption | `python main.py update caption --url <post-url> --text "New caption"` |
| **Delete** your comment | `python main.py delete comment --url <post-url> --text "part of comment"` |
| **Delete** your post | `python main.py delete post --url <post-url>` |

Results are printed and saved as JSON in `output/`.

## Prerequisites
- Python 3.9+
- Google Chrome
- An Instagram account (use your own)
- `pip install -r requirements.txt` (only Selenium)

## Project structure

```
main.py               command-line entry point            -> docs/main.md
web.py                Instagram CRUD actions (Selenium)   -> docs/web.md
browser.py            Chrome launch and login             -> docs/browser.md
requirements.txt      Python packages
config.example.json   login template
RUN_COMMANDS.md       copy-paste commands
.gitignore            keeps secrets out of Git
docs/                 a short guide for each script
```

## Notes and limitations

- Instagram does not allow editing a comment, so "update" edits the post caption instead.
- Instagram changes its page layout often; selectors in `web.py` may need small updates.
- Randomised delays and low limits are used to reduce the chance of triggering security checks.
- Use only on your own account. Browser automation may conflict with Instagram's terms of use.
- Delete operations are permanent. Test on a throwaway post first.

## Security

`config.json` (password), `chrome_profile/` (saved session) and `output/` are in `.gitignore`.
Never commit them.
