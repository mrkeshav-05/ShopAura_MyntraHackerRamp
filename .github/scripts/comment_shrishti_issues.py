#!/usr/bin/env python3
import os
import requests
import sys

UPSTREAM_PAT = os.getenv("UPSTREAM_PAT")
UPSTREAM_OWNER = os.getenv("UPSTREAM_OWNER")
UPSTREAM_REPO = os.getenv("UPSTREAM_REPO")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
COMMENT_BODY = os.getenv("COMMENT_BODY", "").strip()
TARGET_AUTHOR = os.getenv("TARGET_AUTHOR", "").strip()

if not all([UPSTREAM_PAT, UPSTREAM_OWNER, UPSTREAM_REPO, COMMENT_BODY, TARGET_AUTHOR]):
    print("Missing required environment variables.")
    sys.exit(1)

API_BASE = "https://api.github.com"
headers = {
    "Authorization": f"token {UPSTREAM_PAT}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "issue-comment-bot"
}

def list_recent_issues():
    """List open issues (latest first)"""
    url = f"{API_BASE}/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/issues"
    params = {"state": "open", "sort": "created", "direction": "desc", "per_page": 20}
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json()

def get_comments(issue_number):
    url = f"{API_BASE}/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/issues/{issue_number}/comments"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

def post_comment(issue_number, body):
    url = f"{API_BASE}/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/issues/{issue_number}/comments"
    r = requests.post(url, headers=headers, json={"body": body})
    r.raise_for_status()
    return r.json()

def already_commented(issue_number):
    comments = get_comments(issue_number)
    for c in comments:
        if BOT_USERNAME and c.get("user", {}).get("login", "").lower() == BOT_USERNAME.lower():
            if COMMENT_BODY in c.get("body", ""):
                return True
    return False

def main():
    issues = list_recent_issues()
    for issue in issues:
        if 'pull_request' in issue:
            continue  # skip PRs
        creator = issue.get("user", {}).get("login", "")
        number = issue.get("number")
        title = issue.get("title")
        print(f"Checking issue #{number} by {creator}: {title}")

        if creator.lower() != TARGET_AUTHOR.lower():
            print(f"Skipping #{number} (not created by {TARGET_AUTHOR})")
            continue

        if already_commented(number):
            print(f"Already commented on #{number}")
            continue

        print(f"Posting comment on issue #{number}")
        try:
            post_comment(number, COMMENT_BODY)
        except Exception as e:
            print(f"Failed to comment on #{number}: {e}")

    print("Done checking issues.")

if __name__ == "__main__":
    main()
