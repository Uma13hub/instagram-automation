# browser.py (and config.example.json)

## What it does
Opens Chrome and logs in to Instagram using the username and password from your JSON file.
It uses its own Chrome profile folder (`chrome_profile/`), so after one successful login the
session is reused and it says "Already logged in". If Instagram asks for a code or a
security check, it pauses so you can finish it in the Chrome window and press Enter.

It is used by `main.py`; you don't run it directly.

## config.json (copy from config.example.json)
```json
{
  "url": "https://www.instagram.com/accounts/login/",
  "username": "your_instagram_username",
  "password": "your_instagram_password",
  "timeout": 20
}
```

| Key | Required | Meaning |
|-----|----------|---------|
| `url` | yes | Instagram login page |
| `username` | yes | Your login username (or email) |
| `password` | yes | Your password |
| `timeout` | no | Seconds to wait for pages (default 20) |
| `profile_username` | no | Your profile handle, if you log in with an email |
| `chrome_profile_dir` | no | Folder for the saved session (default `chrome_profile`) |

## Prerequisites
- Google Chrome installed
- `selenium` installed (version 4.6+ downloads the matching ChromeDriver automatically)
- Internet connection
- A real `config.json` (never commit it to GitHub)
- Two-factor code or phone nearby, in case Instagram asks for verification
