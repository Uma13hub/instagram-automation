"""Instagram actions performed in a real Chrome window (Selenium).

CRUD overview
    Create : post a comment, send a direct message
    Read   : profile stats, posts, reels, followers, comments
    Update : edit the caption of your own post
    Delete : delete your own comment, delete your own post

Instagram changes its page layout often, so selectors may need small tweaks.
Delays are randomised and limits kept low on purpose. Use only on your own account.
"""

from __future__ import annotations

import random
import re
import time

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE = "https://www.instagram.com"


# ------------------------------------------------------------------ helpers
def pause(low: float = 1.5, high: float = 3.5) -> None:
    time.sleep(random.uniform(low, high))


def wait_for(driver, xpath: str, timeout: int = 15, clickable: bool = False):
    cond = EC.element_to_be_clickable if clickable else EC.presence_of_element_located
    return WebDriverWait(driver, timeout).until(cond((By.XPATH, xpath)))


RETRY_ERRORS = (StaleElementReferenceException, ElementClickInterceptedException,
                ElementNotInteractableException)


def click_xpath(driver, xpath: str, timeout: int = 15, tries: int = 4) -> None:
    """Find the element again on every attempt, so a page re-draw cannot make it stale."""
    last: Exception | None = None
    for _ in range(tries):
        try:
            el = wait_for(driver, xpath, timeout=timeout, clickable=True)
            try:
                el.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", el)
            return
        except RETRY_ERRORS as exc:
            last = exc
            time.sleep(1)
    assert last is not None
    raise last


def type_into(driver, xpath: str, text: str, press_enter: bool = False,
              timeout: int = 15, tries: int = 4) -> None:
    """Click a text box, clear it, type text (optionally press Enter); retries on stale elements."""
    last: Exception | None = None
    for _ in range(tries):
        try:
            box = wait_for(driver, xpath, timeout=timeout, clickable=True)
            box.click()
            box.send_keys(Keys.CONTROL, "a")
            box.send_keys(Keys.DELETE)
            box.send_keys(text)
            if press_enter:
                pause(1, 2)
                box.send_keys(Keys.ENTER)
            return
        except RETRY_ERRORS as exc:
            last = exc
            time.sleep(1)
    assert last is not None
    raise last


def dismiss_popups(driver) -> None:
    for _ in range(2):
        try:
            click_xpath(driver, "//button[normalize-space()='Not Now' or normalize-space()='Not now']",
                        timeout=3, tries=2)
        except (TimeoutException, *RETRY_ERRORS):
            break


def _open_post_menu(driver) -> None:
    """Click the '...' (More options) button on a post page."""
    click_xpath(driver,
                "//*[local-name()='svg' and @aria-label='More options']"
                "/ancestor::*[@role='button' or self::button][1]")
    pause(1, 2)


# ------------------------------------------------------------------- READ
def read_profile(driver, username: str) -> dict:
    driver.get(f"{BASE}/{username}/")
    pause(3, 5)
    dismiss_popups(driver)
    stats = {"username": username, "followers": None, "following": None, "posts": None}
    try:
        desc = driver.find_element(
            By.CSS_SELECTOR, "meta[property='og:description']").get_attribute("content")
        m = re.search(r"([\d.,KMkm]+)\s+Followers?,\s+([\d.,KMkm]+)\s+Following,"
                      r"\s+([\d.,KMkm]+)\s+Posts?", desc or "")
        if m:
            stats["followers"], stats["following"], stats["posts"] = m.groups()
    except NoSuchElementException:
        pass
    return stats


def read_links(driver, username: str, kind: str = "posts", limit: int = 10) -> list[str]:
    """Links to your posts (kind='posts') or reels (kind='reels')."""
    path = "reels/" if kind == "reels" else ""
    marker = "/reel/" if kind == "reels" else "/p/"
    driver.get(f"{BASE}/{username}/{path}")
    pause(3, 5)
    links: list[str] = []
    stalls = 0
    while len(links) < limit and stalls < 3:
        before = len(links)
        for a in driver.find_elements(By.CSS_SELECTOR, f"a[href*='{marker}']"):
            href = a.get_attribute("href")
            if href and href not in links:
                links.append(href)
        stalls = stalls + 1 if len(links) == before else 0
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        pause(2, 3)
    return links[:limit]


def read_comments(driver, url: str, limit: int = 20) -> list[dict]:
    driver.get(url)
    pause(3, 5)
    comments: list[dict] = []
    for li in driver.find_elements(By.XPATH, "//ul//li[.//a[@role='link']]"):
        lines = [ln.strip() for ln in li.text.split("\n") if ln.strip()]
        if len(lines) >= 2:
            comments.append({"username": lines[0], "text": lines[1]})
        if len(comments) >= limit:
            break
    return comments


def read_followers(driver, username: str, limit: int = 30) -> list[str]:
    """Usernames in a profile's followers list (works for any public/visible profile)."""
    return _read_user_list(driver, username, "followers", limit)


def read_following(driver, username: str, limit: int = 30) -> list[str]:
    """Usernames a profile is following (works for any public/visible profile)."""
    return _read_user_list(driver, username, "following", limit)


def latest_post_url(driver, username: str) -> str | None:
    """Link to the most recent post of a profile, or None if nothing is visible."""
    links = read_links(driver, username, "posts", 1)
    return links[0] if links else None


def _read_user_list(driver, username: str, which: str, limit: int) -> list[str]:
    driver.get(f"{BASE}/{username}/{which}/")
    pause(3, 5)
    dialog = wait_for(driver, "//div[@role='dialog']")
    names: list[str] = []
    stalls = 0
    scroll_js = ("const els=arguments[0].querySelectorAll('div');"
                 "for(const e of els){if(e.scrollHeight>e.clientHeight+20 &&"
                 "getComputedStyle(e).overflowY!=='visible'){e.scrollTop=e.scrollHeight;return true;}}"
                 "return false;")
    while len(names) < limit and stalls < 4:
        before = len(names)
        for a in dialog.find_elements(By.XPATH, ".//a[@role='link']"):
            href = (a.get_attribute("href") or "").rstrip("/")
            handle = href.split("/")[-1]
            if handle and handle != username and handle not in names and "instagram.com" in href:
                names.append(handle)
        stalls = stalls + 1 if len(names) == before else 0
        driver.execute_script(scroll_js, dialog)
        pause(1.5, 3)
    return names[:limit]


def read_report(driver, username: str, limit: int = 5) -> dict:
    report = {"profile": read_profile(driver, username)}
    for kind in ("posts", "reels"):
        items = []
        for link in read_links(driver, username, kind, limit):
            items.append({"url": link, "comments": read_comments(driver, link, 10)})
        report[kind] = items
    return report


# ----------------------------------------------------------------- CREATE
def create_comment(driver, url: str, text: str) -> dict:
    driver.get(url)
    pause(3, 5)
    type_into(driver,
              "//textarea[contains(@aria-label,'comment') or contains(@placeholder,'comment')]",
              text, press_enter=True)
    pause(2, 3)
    return {"created": "comment", "url": url, "text": text}


def create_message(driver, to_username: str, text: str) -> dict:
    driver.get(f"{BASE}/{to_username}/")
    pause(3, 5)
    dismiss_popups(driver)
    click_xpath(driver,
                "//div[@role='button' and normalize-space()='Message'] | //button[normalize-space()='Message']")
    pause(3, 5)
    dismiss_popups(driver)
    type_into(driver, "//div[@role='textbox' and @contenteditable='true']", text, press_enter=True)
    pause(2, 3)
    return {"created": "message", "to": to_username, "text": text}


# ----------------------------------------------------------------- UPDATE
def update_caption(driver, url: str, new_caption: str) -> dict:
    """Edit the caption of one of your own posts. (Instagram cannot edit comments.)"""
    driver.get(url)
    pause(3, 5)
    _open_post_menu(driver)
    click_xpath(driver, "//button[normalize-space()='Edit']")
    pause(2, 3)
    type_into(driver,
              "//div[@role='textbox' and @contenteditable='true'] | "
              "//textarea[contains(@aria-label,'caption')]",
              new_caption)
    pause(1, 2)
    click_xpath(driver,
                "//div[@role='button' and normalize-space()='Done'] | //button[normalize-space()='Done']")
    pause(2, 3)
    return {"updated": "caption", "url": url, "caption": new_caption}


# ----------------------------------------------------------------- DELETE
def delete_comment(driver, url: str, my_username: str, match_text: str) -> dict:
    """Delete one of YOUR comments on a post whose text contains match_text."""
    driver.get(url)
    pause(3, 5)
    for li in driver.find_elements(By.XPATH, "//ul//li[.//a[@role='link']]"):
        lines = [ln.strip() for ln in li.text.split("\n") if ln.strip()]
        if len(lines) < 2:
            continue
        if lines[0].lower() == my_username.lower() and match_text.lower() in lines[1].lower():
            ActionChains(driver).move_to_element(li).perform()
            pause(1, 2)
            li.find_element(
                By.XPATH,
                ".//*[local-name()='svg' and contains(@aria-label,'Comment Options')]"
                "/ancestor::*[@role='button' or self::button][1]").click()
            pause(1, 2)
            click_xpath(driver, "//button[normalize-space()='Delete']")
            pause(1, 2)
            try:  # some versions ask for a second confirmation
                click_xpath(driver, "//button[normalize-space()='Delete']", timeout=3, tries=2)
            except (TimeoutException, *RETRY_ERRORS):
                pass
            pause(2, 3)
            return {"deleted": "comment", "url": url, "matched": match_text}
    return {"deleted": None, "reason": "no matching comment of yours found", "url": url}


def delete_post(driver, url: str) -> dict:
    driver.get(url)
    pause(3, 5)
    _open_post_menu(driver)
    click_xpath(driver, "//button[normalize-space()='Delete']")
    pause(1, 2)
    click_xpath(driver, "//button[normalize-space()='Delete']")  # confirm
    pause(2, 3)
    return {"deleted": "post", "url": url}