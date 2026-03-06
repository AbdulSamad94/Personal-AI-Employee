# linkedin_watcher.py
# Watches vault/Approved/ for LinkedIn post files and publishes them

import os
import time
import logging
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import sys

# Load .env from project root
ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env")

VAULT = ROOT / "vault"
APPROVED = VAULT / "Approved"
PENDING = VAULT / "Pending_Approval"
DONE = VAULT / "Done"
LOGS = VAULT / "Logs"

TOKEN = os.getenv("LINKEDIN_TOKEN")
PERSON_ID = os.getenv("LINKEDIN_PERSON_ID")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

LOGS.mkdir(exist_ok=True)
APPROVED.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler(LOGS / "linkedin_watcher.log", encoding="utf-8"),
        logging.StreamHandler(
            open(os.devnull, "w")
        ),  # suppress emoji errors on Windows
    ],
)

# Add a separate console handler that handles encoding gracefully
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.stream = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
logging.getLogger().addHandler(console)


def extract_post_content(file_text: str) -> str:
    """Extract post content from approval file."""
    # Look for content after ## Post Content marker
    if "## Post Content" in file_text:
        content = file_text.split("## Post Content")[1]
        # Stop at next ## section if exists
        if "\n## " in content:
            content = content.split("\n## ")[0]
        return content.strip()

    # Fallback — return everything after frontmatter
    if "---" in file_text:
        parts = file_text.split("---")
        if len(parts) >= 3:
            return parts[2].strip()

    return file_text.strip()


def is_expired(file_text: str) -> bool:
    """Check if approval file has expired."""
    for line in file_text.splitlines():
        if line.startswith("expires:"):
            try:
                from datetime import timezone

                expires_str = line.split("expires:")[1].strip()
                expires = datetime.fromisoformat(expires_str)
                now = datetime.now()
                return now > expires
            except:
                return False
    return False


def post_to_linkedin(text: str) -> bool:
    """Publish post to LinkedIn."""
    if not TOKEN or not PERSON_ID:
        logging.error("LINKEDIN_TOKEN or LINKEDIN_PERSON_ID not set in .env")
        return False

    if DRY_RUN:
        logging.info(f"[DRY RUN] Would post to LinkedIn:")
        logging.info(f"{text[:150]}...")
        return True

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # Build JSON as string to avoid nesting issues
    import json

    body = json.dumps(
        {
            "author": f"urn:li:person:{PERSON_ID}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
    )

    try:
        r = requests.post(
            "https://api.linkedin.com/v2/ugcPosts", headers=headers, data=body
        )
        if r.status_code == 201:
            logging.info(f'LinkedIn post published! ID: {r.json().get("id")}')
            return True
        else:
            logging.error(f"LinkedIn API error: {r.status_code} — {r.text}")
            return False
    except Exception as e:
        logging.error(f"LinkedIn post failed: {e}")
        return False


def log_action(action: str, filename: str, result: str):
    """Append action to daily log."""
    log_file = LOGS / f'{datetime.now().strftime("%Y-%m-%d")}.md'
    entry = f"{datetime.now().isoformat()} | {action} | {filename} | {result}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)


def process_approved_file(file_path: Path):
    """Process a LinkedIn approval file from vault/Approved/."""
    content = file_path.read_text(encoding="utf-8")

    # Check expiry
    if is_expired(content):
        logging.warning(f"Approval expired: {file_path.name} — skipping")
        file_path.rename(DONE / file_path.name)
        log_action("linkedin_expired", file_path.name, "expired_moved_to_done")
        return

    # Extract post text
    post_text = extract_post_content(content)

    if not post_text:
        logging.error(f"No post content found in {file_path.name}")
        return

    logging.info(f"Publishing LinkedIn post from: {file_path.name}")

    # Post to LinkedIn
    success = post_to_linkedin(post_text)

    if success:
        # Log the published post
        log_file = LOGS / f'linkedin_{datetime.now().strftime("%Y%m%d")}.md'
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(
                f"\n---\n**Published: {datetime.now().isoformat()}**\n{post_text}\n"
            )

        # Move to Done
        file_path.rename(DONE / file_path.name)
        logging.info(f"Moved to Done: {file_path.name}")
        log_action("linkedin_posted", file_path.name, "success")
    else:
        log_action("linkedin_failed", file_path.name, "failed_check_logs")


def run():
    processed = set()
    mode = "[DRY RUN]" if DRY_RUN else "[LIVE]"

    logging.info(f"LinkedIn Watcher running {mode}...")
    logging.info(f"Watching: {APPROVED}")
    logging.info(f'Token loaded: {"Yes" if TOKEN else "NO - check .env"}')
    logging.info(f'Person ID loaded: {"Yes" if PERSON_ID else "NO - check .env"}')

    while True:
        try:
            # Check Approved/ for LinkedIn files
            for f in APPROVED.glob("LINKEDIN_*.md"):
                if f.name not in processed:
                    logging.info(f"Approved LinkedIn post detected: {f.name}")
                    process_approved_file(f)
                    processed.add(f.name)

            # Also notify about pending posts waiting for approval
            pending_posts = list(PENDING.glob("LINKEDIN_*.md"))
            if pending_posts:
                logging.info(
                    f"{len(pending_posts)} LinkedIn post(s) waiting for approval "
                    f"in vault/Pending_Approval/"
                )

        except Exception as e:
            logging.error(f"LinkedIn watcher error: {e}")

        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    run()
