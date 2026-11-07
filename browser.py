"""Selenium helper: open Instagram in Chrome and log in from a JSON file."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

REQUIRED_KEYS = ("url", "username", "password")

# Instagram changes its login form often, so several selectors are tried in order.
USER_SELECTORS = [
    "input[name='username']",
    "input[name='email']",
    "input[autocomplete='username']",
    "input[aria-label*='username' i]",
    "input[aria-label*='email' i]",
    "input[type='text']",
]
PASS_SELECTORS = [
    "input[name='password']",
    "input[name='pass']",
    "input[autocomplete='current-password']",
    "input[type='password']",
]
LOGIN_BUTTON_XPATH = (
    "//button[@type='submit'] | //button[normalize-space()='Log in'] | "
    "//div[@role='button' and normalize-space()='Log in']"
)


def load_credentials(path: str) -> dict:
    file = Path(path)
    if not file.exists():
        raise SystemExit(f"Credentials file not found: {file.resolve()}\n"
                         f"Copy config.example.json to {file.name} and fill it in.")
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON in {file}: {e}")
    missing = [k for k in REQUIRED_KEYS if not data.get(k)]
    if missing:
        raise SystemExit(f"Missing keys in {file}: {', '.join(missing)}")
    data.setdefault("timeout", 20)
    return data


def _click_if_present(driver, xpath: str, wait: int = 5) -> bool:
    try:
        WebDriverWait(driver, wait).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
        return True
    except TimeoutException:
        return False


def _find_first(driver, selectors: list[str], timeout: int):
    """Return the first visible element matching any selector, or None."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for sel in selectors:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                if el.is_displayed() and el.is_enabled():
                    return el
        time.sleep(0.5)
    return None


def _on_login_form(driver) -> bool:
    return _find_first(driver, PASS_SELECTORS, timeout=1) is not None


def _is_logged_in(driver) -> bool:
    """Logged in = no password field on the page and not on a login/challenge URL."""
    url = driver.current_url
    if "accounts/login" in url or "challenge" in url:
        return False
    return not _on_login_form(driver)


def _type(element, text: str) -> None:
    element.click()
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(Keys.DELETE)
    element.send_keys(text)


def default_profile_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:  # Windows: C:\Users\<you>\AppData\Local
        return Path(base) / "instagram_automation_chrome"
    return Path.home() / ".instagram_automation_chrome"


def _start_chrome(profile_dir: Path) -> webdriver.Chrome:
    profile_dir.mkdir(parents=True, exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=0")  # let Chrome pick a free port
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_experimental_option("detach", True)  # keep Chrome open
    return webdriver.Chrome(options=options)


def open_and_login(config_path: str = "config.json") -> webdriver.Chrome:
    cfg = load_credentials(config_path)

    if str(cfg["username"]).startswith("your_") or str(cfg["password"]).startswith("your_"):
        print("WARNING: config.json still has the placeholder username/password. "
              "Edit it with your real Instagram login first.")

    # Dedicated Chrome profile: the Instagram session is saved here, so after one
    # successful login the script is already logged in on the next run.
    # Default is a LOCAL folder (not OneDrive / not inside the project), because Chrome
    # often crashes when its profile lives in a synced or oddly named path.
    profile_dir = Path(cfg.get("chrome_profile_dir") or default_profile_dir()).resolve()
    try:
        driver = _start_chrome(profile_dir)
    except Exception as exc:
        first = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
        print(f"Chrome could not start with the saved profile ({first}).")
        print("Retrying once with a temporary profile (your login will NOT be remembered).")
        print("Tip: close every Chrome window and run 'taskkill /F /IM chrome.exe' to fix this.")
        profile_dir = Path(tempfile.mkdtemp(prefix="ig_chrome_"))
        try:
            driver = _start_chrome(profile_dir)
        except Exception as exc2:
            raise SystemExit(
                "Chrome still could not start.\n"
                "1) Close ALL Chrome windows (Task Manager > end every chrome.exe).\n"
                "2) Update Google Chrome (chrome://settings/help) and run: pip install -U selenium\n"
                f"Details: {str(exc2).splitlines()[0] if str(exc2) else type(exc2).__name__}")

    driver.get(cfg["url"])
    time.sleep(4)
    _click_if_present(
        driver,
        "//button[contains(., 'Allow all cookies') or contains(., 'Accept all') "
        "or contains(., 'Allow essential and optional cookies')]", wait=4)

    if _is_logged_in(driver):
        print(f"Already logged in (saved session): {driver.current_url}")
        return driver

    user_box = _find_first(driver, USER_SELECTORS, timeout=cfg["timeout"])
    pass_box = _find_first(driver, PASS_SELECTORS, timeout=5)

    if user_box is None or pass_box is None:
        print("Could not find the username/password boxes automatically.")
    else:
        print("Typing credentials from config.json ...")
        _type(user_box, str(cfg["username"]))
        _type(pass_box, str(cfg["password"]))
        time.sleep(1)
        pass_box.send_keys(Keys.ENTER)
        time.sleep(4)
        if "accounts/login" in driver.current_url and _on_login_form(driver):
            # Enter did not submit: click the Log in button as well
            _click_if_present(driver, LOGIN_BUTTON_XPATH, wait=3)
            time.sleep(5)

        page = driver.page_source.lower()
        if "incorrect" in page or "wrong password" in page or "isn't correct" in page:
            print("Instagram says the username or password is incorrect. "
                  "Check config.json (or log in manually in the window).")

    for _ in range(2):  # "Save login info?" / "Turn on notifications?"
        _click_if_present(driver, "//button[contains(., 'Not now') or contains(., 'Not Now')]", wait=4)

    if not _is_logged_in(driver):
        # Wrong password, 2FA, "suspicious login" or a bot check: let the person finish it.
        input("\nLogin is not complete yet. In the Chrome window, finish logging in "
              "(type credentials / code / checkpoint), then press Enter here...")
        for _ in range(2):
            _click_if_present(driver, "//button[contains(., 'Not now') or contains(., 'Not Now')]", wait=3)

    if _is_logged_in(driver):
        print(f"Logged in: {driver.current_url} (session saved in {profile_dir.name}/)")
    else:
        print("Still not logged in - check username/password in config.json.")
    return driver