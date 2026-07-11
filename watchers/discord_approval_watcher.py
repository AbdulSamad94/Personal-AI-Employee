#!/usr/bin/env python3
"""
Discord Approval Watcher for Personal AI Employee.

Redundant approval channel alongside telegram_approval_watcher.py — Telegram
is intermittently blocked in Pakistan (PTA), so this runs in parallel and
notifies via a Discord channel instead. Both watchers independently notify
for the same vault/Pending_Approval/ files; whichever platform is reachable,
you can Approve/Reject/Request Changes from it. Both re-check file existence
before acting, so if you approve from one, the other's buttons just report
"already handled" instead of erroring.

Requires DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID in .env, and the bot needs
"Message Content Intent" enabled in the Discord Developer Portal (Bot tab) so
free-text "Request Changes" replies are readable. See CONTRIBUTING.md.
"""

import os
import re
import json
import time
import uuid
import logging
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

try:
    import discord
    from discord.ext import tasks

    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

# ── Environment ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")

VAULT = ROOT / "vault"
PENDING_DIR = VAULT / "Pending_Approval"
APPROVED_DIR = VAULT / "Approved"
REJECTED_DIR = VAULT / "Rejected"
NEEDS_ACTION_DIR = VAULT / "Needs_Action"
LOGS_DIR = VAULT / "Logs"
STATE_FILE = LOGS_DIR / "discord_state.json"

for d in [PENDING_DIR, APPROVED_DIR, REJECTED_DIR, NEEDS_ACTION_DIR, LOGS_DIR]:
    d.mkdir(exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "discord_approval_watcher.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("discord_approval")

SCAN_INTERVAL = 10  # seconds between Pending_Approval/ scans


# ── State persistence (separate file from Telegram's — each channel tracks its
# own "have I notified about this file yet" set independently) ──────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            log.warning("discord_state.json is corrupt — starting fresh.")
    return {"notified": {}, "awaiting_edit": {}}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def parse_markdown_frontmatter(content: str) -> dict:
    """Same lightweight parser used by approval_watcher.py / telegram_approval_watcher.py."""
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


def handle_approve(short_id: str, state: dict) -> str:
    entry = state["notified"].get(short_id)
    if not entry:
        return "Already handled or unknown."
    filename = entry["file"]
    src = PENDING_DIR / filename
    if src.exists():
        src.rename(APPROVED_DIR / filename)
        log.info("Approved via Discord: %s", filename)
        del state["notified"][short_id]
        return f"Approved ✅ — {filename}"
    del state["notified"][short_id]
    return f"{filename} was already handled elsewhere (e.g. Telegram)."


def handle_reject(short_id: str, state: dict) -> str:
    entry = state["notified"].get(short_id)
    if not entry:
        return "Already handled or unknown."
    filename = entry["file"]
    src = PENDING_DIR / filename
    if src.exists():
        src.rename(REJECTED_DIR / filename)
        log.info("Rejected via Discord: %s", filename)
        del state["notified"][short_id]
        return f"Rejected ❌ — {filename}"
    del state["notified"][short_id]
    return f"{filename} was already handled elsewhere (e.g. Telegram)."


def handle_edit_reply(channel_id: str, text: str, state: dict) -> str | None:
    pending = state["awaiting_edit"].pop(channel_id, None)
    if not pending:
        return None  # no edit was pending in this channel — ignore stray messages
    filename = pending["file"]
    src = PENDING_DIR / filename
    if not src.exists():
        return f"Couldn't find {filename} anymore — it may have already been handled."

    content = src.read_text(encoding="utf-8")
    content = re.sub(r"^status:\s*pending", "status: needs_revision", content, flags=re.MULTILINE)
    content += f"\n\n## Human Feedback (via Discord, {datetime.now().isoformat()})\n\n{text}\n"

    (NEEDS_ACTION_DIR / filename).write_text(content, encoding="utf-8")
    src.unlink()
    state["notified"].pop(pending["short_id"], None)
    log.info("Edit feedback captured for %s via Discord, moved back to Needs_Action", filename)
    return f"Got it — queued **{filename}** for revision. I'll re-draft it and ask again next check-in."


def _build_bot():
    """Deferred so this module still imports cleanly if discord.py isn't installed."""
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    state = load_state()

    class ApprovalView(discord.ui.View):
        def __init__(self, short_id: str):
            super().__init__(timeout=None)
            self.short_id = short_id

        def _lock(self):
            """Disable all three buttons so a second click on this message is impossible."""
            for child in self.children:
                child.disabled = True

        @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success)
        async def approve_btn(self, interaction: "discord.Interaction", _button):
            msg = handle_approve(self.short_id, state)
            save_state(state)
            self._lock()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(msg, ephemeral=True)

        @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger)
        async def reject_btn(self, interaction: "discord.Interaction", _button):
            msg = handle_reject(self.short_id, state)
            save_state(state)
            self._lock()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(msg, ephemeral=True)

        @discord.ui.button(label="✏️ Request Changes", style=discord.ButtonStyle.secondary)
        async def edit_btn(self, interaction: "discord.Interaction", _button):
            entry = state["notified"].get(self.short_id)
            self._lock()
            await interaction.response.edit_message(view=self)
            if not entry:
                await interaction.followup.send("Already handled.", ephemeral=True)
                return
            state["awaiting_edit"][str(interaction.channel_id)] = {
                "short_id": self.short_id,
                "file": entry["file"],
            }
            save_state(state)
            await interaction.followup.send(
                f"Reply in this channel with what you'd like changed about **{entry['file']}**."
            )

    @tasks.loop(seconds=SCAN_INTERVAL)
    async def scan_pending():
        channel = client.get_channel(int(CHANNEL_ID))
        if channel is None:
            # get_channel only checks the local cache; fall back to an API fetch
            # (per discord.py's own guidance) in case the cache hasn't warmed up yet.
            try:
                channel = await client.fetch_channel(int(CHANNEL_ID))
            except Exception as e:
                log.error("Discord channel %s not found or inaccessible: %s", CHANNEL_ID, e)
                return
        already_notified = {v["file"] for v in state["notified"].values()}
        for f in sorted(PENDING_DIR.glob("*.md")):
            if f.name in already_notified:
                continue
            content = f.read_text(encoding="utf-8")
            data = parse_markdown_frontmatter(content)
            short_id = uuid.uuid4().hex[:8]
            text = (
                f"\U0001f4dd **New approval request**\n\n"
                f"**Action:** {data.get('action', 'unknown_action')}\n"
                f"**To:** {data.get('to', '?')}\n"
                f"**Subject:** {data.get('subject', f.name)}\n\n"
                f"{data.get('_body', '')[:800]}\n\n"
                f"_File: {f.name}_"
            )
            try:
                await channel.send(text[:2000], view=ApprovalView(short_id))
                state["notified"][short_id] = {"file": f.name}
                save_state(state)
                log.info("Notified Discord about new pending approval: %s", f.name)
            except Exception as e:
                log.error("Failed to send Discord notification for %s: %s", f.name, e)

    @client.event
    async def on_ready():
        log.info("Discord Approval Watcher connected as %s", client.user)
        if not scan_pending.is_running():
            scan_pending.start()

    @client.event
    async def on_message(message):
        if message.author.bot:
            return
        reply = handle_edit_reply(str(message.channel.id), message.content, state)
        if reply:
            save_state(state)
            await message.channel.send(reply)

    return client


def main():
    # Wait rather than exit when unconfigured/uninstalled, so orchestrator.py's
    # crash-restart loop doesn't spin on this every 10 seconds — the same failure
    # mode that turned an expired Gmail OAuth token into 185,000+ log lines
    # (see AGENTS.md Known Issues). Logs a reminder every ~10 minutes instead.
    warn_counter = 0
    while not DISCORD_AVAILABLE or not BOT_TOKEN or not CHANNEL_ID:
        if warn_counter % 60 == 0:
            if not DISCORD_AVAILABLE:
                log.warning("discord.py is not installed — run `uv sync` after pulling this change. Waiting.")
            else:
                log.warning(
                    "DISCORD_BOT_TOKEN and/or DISCORD_CHANNEL_ID not set in .env — "
                    "waiting. See CONTRIBUTING.md for setup steps."
                )
        warn_counter += 1
        time.sleep(10)

    log.info("Starting Discord Approval Watcher...")
    client = _build_bot()
    client.run(BOT_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
