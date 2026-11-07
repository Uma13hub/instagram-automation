"""Instagram automation in Chrome: log in once, then run CRUD operations.

Setup:   pip install -r requirements.txt   and fill in config.json (see config.example.json)

READ
    python main.py read profile
    python main.py read posts     --limit 5
    python main.py read reels     --limit 5
    python main.py read followers --limit 20
    python main.py read comments  --url https://www.instagram.com/p/XXXX/
    python main.py read report    --limit 3            # profile + posts + reels + comments
CREATE
    python main.py create comment --url https://www.instagram.com/p/XXXX/ --text "Nice!"
    python main.py create message --to some_username --text "Hello!"
UPDATE
    python main.py update caption --url https://www.instagram.com/p/XXXX/ --text "New caption"
DELETE
    python main.py delete comment --url https://www.instagram.com/p/XXXX/ --text "part of my comment"
    python main.py delete post    --url https://www.instagram.com/p/XXXX/
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import web
from browser import load_credentials, open_and_login

OUTPUT_DIR = Path("output")

TARGETS = {
    "read": ["profile", "posts", "reels", "followers", "comments", "report"],
    "create": ["comment", "message"],
    "update": ["caption"],
    "delete": ["comment", "post"],
}


def parse_args() -> argparse.Namespace:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default="config.json", help="JSON file with login details")
    common.add_argument("--username", help="Profile to use (default: from config.json)")
    common.add_argument("--limit", type=int, default=5)
    common.add_argument("--url", help="Post or reel URL")
    common.add_argument("--to", help="Username to message")
    common.add_argument("--text", help="Comment / message / caption text")

    p = argparse.ArgumentParser(description="Instagram CRUD automation (Chrome + Selenium)")
    sub = p.add_subparsers(dest="operation", required=True)
    for op, targets in TARGETS.items():
        s = sub.add_parser(op, parents=[common])
        s.add_argument("target", choices=targets)
    return p.parse_args()


def need(args, *fields: str) -> None:
    missing = [f"--{f}" for f in fields if not getattr(args, f)]
    if missing:
        sys.exit(f"'{args.operation} {args.target}' needs: {', '.join(missing)}")


def save(name: str, data) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"{name}_{datetime.now():%Y%m%d_%H%M%S}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def execute(driver, args, me: str):
    op, target = args.operation, args.target
    if op == "read":
        if target == "profile":
            return web.read_profile(driver, me)
        if target in ("posts", "reels"):
            return web.read_links(driver, me, target, args.limit)
        if target == "followers":
            return web.read_followers(driver, me, args.limit)
        if target == "comments":
            need(args, "url")
            return web.read_comments(driver, args.url, args.limit)
        return web.read_report(driver, me, args.limit)
    if op == "create":
        if target == "comment":
            need(args, "url", "text")
            return web.create_comment(driver, args.url, args.text)
        need(args, "to", "text")
        return web.create_message(driver, args.to, args.text)
    if op == "update":
        need(args, "url", "text")
        return web.update_caption(driver, args.url, args.text)
    # delete
    need(args, "url")
    if target == "comment":
        need(args, "text")
        return web.delete_comment(driver, args.url, me, args.text)
    return web.delete_post(driver, args.url)


def main() -> None:
    args = parse_args()
    cfg = load_credentials(args.config)
    me = args.username or cfg.get("profile_username") or cfg["username"]

    driver = open_and_login(args.config)
    try:
        web.dismiss_popups(driver)
        result = execute(driver, args, me)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\nSaved to {save(f'{args.operation}_{args.target}', result)}")
    except Exception as exc:  # keep the window open so the page can be inspected
        print(f"\nStep failed: {type(exc).__name__}: {str(exc).splitlines()[0] if str(exc) else ''}")
        print("Instagram's page layout may have changed, or the URL/permissions are wrong.")
    finally:
        input("\nPress Enter to finish (Chrome stays open)...")


if __name__ == "__main__":
    main()
