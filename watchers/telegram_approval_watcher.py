#!/usr/bin/env python3
"""
Telegram Approval Watcher for Personal AI Employee.

Replaces "drag the file to vault/Approved yourself" with a single push
notification: whenever a new file lands in vault/Pending_Approval/, this
watcher sends a Telegram message summarizing the draft with three buttons —
Approve / Reject / Request Changes. Tapping a button (or replying with free
text after "Request Changes") is all that's needed; no Obsidian, no manual
file moves.

- Approve  -> moves the file to vault/Approved/ (approval_watcher.py then
              executes it, same as a manual drag-and-drop would).
- Reject   -> moves the file to vault/Rejected/.
- Request Changes -> prompts for a text reply; the reply is appended to the
              file as human feedback and the file is moved back to
              vault/Needs_Action/ with status: needs_revision, so the next
              scheduled OpenCode run redrafts it with that feedback in hand.

Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env. Uses raw Telegram
Bot API calls via `requests` — no extra SDK dependency.
"""

import os
import re
import json
import time
import uuid
import logging
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

# ── Environment ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
API = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None

VAULT = ROOT / "vault"
PENDING_DIR = VAULT / "Pending_Approval"
APPROVED_DIR = VAULT / "Approved"
REJECTED_DIR = VAULT / "Rejected"
NEEDS_ACTION_DIR = VAULT / "Needs_Action"
LOGS_DIR = VAULT / "Logs"
STATE_FILE = LOGS_DIR / "telegram_state.json"

for d in [PENDING_DIR, APPROVED_DIR, REJECTED_DIR, NEEDS_ACTION_DIR, LOGS_DIR]:
    d.mkdir(exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "telegram_approval_watcher.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("telegram_approval")

POLL_INTERVAL = 5  # seconds between checks of Pending_Approval/
LONG_POLL_TIMEOUT = 20  # seconds Telegram holds getUpdates open waiting for new events


# ── State persistence ────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            log.warning("telegram_state.json is corrupt — starting fresh.")
    return {"notified": {}, "awaiting_edit": {}, "update_offset": 0}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ── Telegram API helpers ─────────────────────────────────────────────────────────
def tg_call(method: str, **params):
    try:
        resp = requests.post(f"{API}/{method}", json=params, timeout=LONG_POLL_TIMEOUT + 10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log.error("Telegram API call %s failed: %s", method, e)
        return None


def send_notification(short_id: str, file_path: Path, data: dict) -> str | None:
    action = data.get("action", "unknown_action")
    to = data.get("to", "?")
    subject = data.get("subject", file_path.name)
    body_preview = data.get("_body", "")[:800]

    text = (
        f"\U0001f4dd *New approval request*\n\n"
        f"*Action:* {action}\n"
        f"*To:* {to}\n"
        f"*Subject:* {subject}\n\n"
        f"{body_preview}\n\n"
        f"_File: {file_path.name}_"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve", "callback_data": f"approve:{short_id}"},
                {"text": "❌ Reject", "callback_data": f"reject:{short_id}"},
                {"text": "✏️ Request Changes", "callback_data": f"edit:{short_id}"},
            ]
        ]
    }

    result = tg_call(
        "sendMessage",
        chat_id=CHAT_ID,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    if result and result.get("ok"):
        return str(result["result"]["message_id"])
    log.error("Failed to send Telegram notification for %s: %s", file_path.name, result)
    return None


def parse_markdown_frontmatter(content: str) -> dict:
    """Same lightweight parser approval_watcher.py uses, kept local to avoid a cross-file import."""
    data = {}
    if not content.startswith("---"):
        return data
    parts = content.split("---", 2)
    if len(parts) < 3:
        return data
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()
    data["_body"] = parts[2].strip()
    return data


# ── Core actions ──────────────────────────────────────────────────────────────────
def handle_approve(short_id: str, state: dict):
    filename = state["notified"].get(short_id, {}).get("file")
    if not filename:
        return
    src = PENDING_DIR / filename
    if src.exists():
        dest = APPROVED_DIR / filename
        src.rename(dest)
        log.info("Approved via Telegram: %s", filename)
    del state["notified"][short_id]


def handle_reject(short_id: str, state: dict):
    filename = state["notified"].get(short_id, {}).get("file")
    if not filename:
        return
    src = PENDING_DIR / filename
    if src.exists():
        dest = REJECTED_DIR / filename
        src.rename(dest)
        log.info("Rejected via Telegram: %s", filename)
    del state["notified"][short_id]


def handle_edit_request(short_id: str, state: dict, chat_id: str):
    filename = state["notified"].get(short_id, {}).get("file")
    if not filename:
        return
    state["awaiting_edit"][str(chat_id)] = {"short_id": short_id, "file": filename}
    tg_call(
        "sendMessage",
        chat_id=chat_id,
        text=f"Reply with what you'd like changed about *{filename}* — "
        "I'll fold it into the draft on the next check-in.",
        parse_mode="Markdown",
    )


def handle_edit_reply(chat_id: str, text: str, state: dict):
    pending = state["awaiting_edit"].pop(str(chat_id), None)
    if not pending:
        return  # no edit was pending for this chat — ignore stray messages
    filename = pending["file"]
    src = PENDING_DIR / filename
    if not src.exists():
        tg_call("sendMessage", chat_id=chat_id, text=f"Couldn't find {filename} anymore — it may have already been handled.")
        return

    content = src.read_text(encoding="utf-8")
    content = re.sub(r"^status:\s*pending", "status: needs_revision", content, flags=re.MULTILINE)
    content += (
        f"\n\n## Human Feedback (via Telegram, {datetime.now().isoformat()})\n\n{text}\n"
    )

    dest = NEEDS_ACTION_DIR / filename
    dest.write_text(content, encoding="utf-8")
    src.unlink()

    short_id = pending["short_id"]
    state["notified"].pop(short_id, None)

    tg_call(
        "sendMessage",
        chat_id=chat_id,
        text=f"Got it — queued *{filename}* for revision. I'll re-draft it and ask again next check-in.",
        parse_mode="Markdown",
    )
    log.info("Edit feedback captured for %s, moved back to Needs_Action", filename)


# ── Main loop ──────────────────────────────────────────────────────────────────
def scan_pending(state: dict):
    """Notify for any file in Pending_Approval/ that hasn't been notified yet."""
    already_notified_files = {v["file"] for v in state["notified"].values()}
    for f in sorted(PENDING_DIR.glob("*.md")):
        if f.name in already_notified_files:
            continue
        content = f.read_text(encoding="utf-8")
        data = parse_markdown_frontmatter(content)
        short_id = uuid.uuid4().hex[:8]
        message_id = send_notification(short_id, f, data)
        if message_id:
            state["notified"][short_id] = {"file": f.name, "message_id": message_id}
            log.info("Notified Telegram about new pending approval: %s", f.name)


def poll_updates(state: dict):
    # On a fresh state (update_offset still 0 — no telegram_state.json yet, or it was
    # cleared), skip straight to the latest update instead of pulling up to 24h of
    # backlog. Callback/message handlers already no-op safely on unknown short_ids/
    # chat_ids, so this isn't a correctness fix, just avoids wasted API calls on first run.
    if state["update_offset"] == 0:
        init_result = tg_call("getUpdates", offset=-1, limit=1)
        if init_result and init_result.get("ok") and init_result["result"]:
            state["update_offset"] = init_result["result"][0]["update_id"]

    result = tg_call(
        "getUpdates",
        offset=state["update_offset"] + 1,
        timeout=LONG_POLL_TIMEOUT,
        allowed_updates=["message", "callback_query"],
    )
    if not result or not result.get("ok"):
        return

    for update in result["result"]:
        state["update_offset"] = max(state["update_offset"], update["update_id"])

        if "callback_query" in update:
            cq = update["callback_query"]
            data = cq.get("data", "")
            chat_id = cq["message"]["chat"]["id"]
            if ":" not in data:
                continue
            action, short_id = data.split(":", 1)

            if action == "approve":
                handle_approve(short_id, state)
                tg_call("answerCallbackQuery", callback_query_id=cq["id"], text="Approved ✅")
            elif action == "reject":
                handle_reject(short_id, state)
                tg_call("answerCallbackQuery", callback_query_id=cq["id"], text="Rejected ❌")
            elif action == "edit":
                handle_edit_request(short_id, state, chat_id)
                tg_call("answerCallbackQuery", callback_query_id=cq["id"], text="Waiting for your reply…")

        elif "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            if text:
                handle_edit_reply(chat_id, text, state)


def main():
    # Wait rather than exit when unconfigured, so orchestrator.py's crash-restart loop
    # doesn't spin on this every 10 seconds (that exact failure mode cost hours to
    # debug for gmail_watcher.py's expired-token case — see AGENTS.md Known Issues).
    # Logs the reminder once every ~10 minutes instead of on every poll.
    warn_counter = 0
    while not BOT_TOKEN or not CHAT_ID:
        if warn_counter % 120 == 0:
            log.warning(
                "TELEGRAM_BOT_TOKEN and/or TELEGRAM_CHAT_ID not set in .env — "
                "waiting. See CONTRIBUTING.md / AGENTS.md for setup steps."
            )
        warn_counter += 1
        time.sleep(5)

    log.info("Telegram Approval Watcher running (chat_id=%s)", CHAT_ID)
    state = load_state()

    while True:
        try:
            scan_pending(state)
            poll_updates(state)
            save_state(state)
        except Exception as e:
            log.error("Main loop error: %s", e)
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
