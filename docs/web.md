# web.py

## What it does
Contains the Instagram actions, performed in a real Chrome window with Selenium.
It is used by `main.py`; you don't run it directly.

| Type | Function | What happens |
|------|----------|--------------|
| Read | `read_profile` | Followers, following and post counts |
| Read | `read_links` | Links to your posts or reels |
| Read | `read_comments` | Comments shown on a post |
| Read | `read_followers` | A sample of follower usernames |
| Read | `read_report` | Profile + posts + reels + comments together |
| Create | `create_comment` | Posts a comment on a post or reel |
| Create | `create_message` | Sends a direct message to a user |
| Update | `update_caption` | Edits the caption of your own post |
| Delete | `delete_comment` | Deletes one of your comments (matched by text) |
| Delete | `delete_post` | Deletes one of your posts |

## Notes
- Instagram does not allow editing comments, so "update" edits the post caption.
- Random pauses between steps are added on purpose to look less robotic.
- Instagram changes its page layout often; selectors in this file may need small updates.
- Delete actions are permanent.

## Prerequisites
- A logged-in Chrome session from `browser.py`
- `selenium` installed (`pip install -r requirements.txt`)
- Your own Instagram account, and posts/URLs that belong to it for update and delete
