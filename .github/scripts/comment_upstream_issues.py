#!/usr/bin/env python3
import os
import requests
import sys

UPSTREAM_PAT = os.getenv("UPSTREAM_PAT")
UPSTREAM_OWNER = os.getenv("UPSTREAM_OWNER")
UPSTREAM_REPO = os.getenv("UPSTREAM_REPO")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
COMMENT_BODY = os.getenv("COMMENT_BODY", "").strip()

if not all([UPSTREAM_PAT, UPSTREAM_OWNER, UPSTREAM_REPO, COMMENT_BODY]):
    print("Missing environment variables. Set UPSTREAM_PAT, UPSTREAM_OWNER, UPSTREAM_REPO, COMMENT_BODY.")
    sys.exit(1)

API_BASE = "https://api.github.com"
headers = {
    "Authorization": f"token {UPSTREAM_PAT}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "upstream-issue-bot"
}

def list_issues(page=1, per_page=100):
    url = f"{API_BASE}/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/issues"
    params = {
        "state": "open",
        "page": page,
        "per_page": per_page
    }
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json()

def get_comments(issue_number, page=1, per_page=100):
    url = f"{API_BASE}/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/issues/{issue_number}/comments"
    params = {"page": page, "per_page": per_page}
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json()

def post_comment(issue_number, body):
    url = f"{API_BASE}/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/issues/{issue_number}/comments"
    r = requests.post(url, headers=headers, json={"body": body})
    r.raise_for_status()
    return r.json()

def already_commented(issue_number):
    # Check comments for a comment with same body by the bot (if BOT_USERNAME provided)
    page = 1
    while True:
        comments = get_comments(issue_number, page=page)
        if not comments:
            return False
        for c in comments:
            if BOT_USERNAME:
                if c.get("user", {}).get("login", "").lower() == BOT_USERNAME.lower():
                    # check if body contains our phrase to avoid collision
                    if COMMENT_BODY in c.get("body", ""):
                        return True
            else:
                if COMMENT_BODY in c.get("body", ""):
                    return True
        if len(comments) < 100:
            break
        page += 1
    return False

def main():
    page = 1
    any_errors = False
    while True:
        issues = list_issues(page=page)
        if not issues:
            break
        for issue in issues:
            # Skip pull requests (they show up in issues API)
            if 'pull_request' in issue:
                continue
            number = issue.get('number')
            title = issue.get('title')
            print(f"Checking issue #{number}: {title}")
            try:
                if not already_commented(number):
                    print(f"Posting comment on issue #{number}")
                    post_comment(number, COMMENT_BODY)
                else:
                    print(f"Already commented on #{number}")
            except Exception as e:
                print(f"Error handling issue #{number}: {e}")
                any_errors = True
        if len(issues) < 100:
            break
        page += 1

    if any_errors:
        sys.exit(1)
    print("Done.")

if __name__ == "__main__":
    main()
