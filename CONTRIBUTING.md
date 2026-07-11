# Contributing

This started as a personal automation project and is shared as-is under the MIT license. There's no CI, no test suite, and no linter configured yet — contributions are welcome, but keep that in mind: verify changes by actually running the relevant watcher/skill/MCP server, not by assuming a check will catch mistakes.

## Dev setup

```bash
git clone https://github.com/AbdulSamad94/Personal-AI-Employee.git
cd Personal-AI-Employee
uv sync
```

Create a `.env` with your own credentials (see README's Setup section for the required variables) and keep `DRY_RUN=true` while you're developing — it stops watchers/MCP servers from actually sending anything.

Run a single watcher in isolation instead of the full `orchestrator.py` while iterating:
```bash
python watchers/gmail_watcher.py
```

Test an OpenCode-driven change without waiting for the 30-minute scheduled task:
```bash
opencode run "<your prompt>" --auto
```

## Telegram approval bot setup

`telegram_approval_watcher.py` replaces manually dragging files from `vault/Pending_Approval/` to `vault/Approved/` with a single push notification (Approve / Reject / Request Changes buttons). To enable it:

1. Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`, follow the prompts (pick any name/username). It replies with a bot token — copy it into `.env` as `TELEGRAM_BOT_TOKEN`.
2. Open a chat with your new bot and send it any message (e.g. "hi") — Telegram won't let a bot message you first, so this step is required.
3. Find your chat ID by visiting `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser right after step 2 — look for `"chat":{"id":...}` in the response and put that number in `.env` as `TELEGRAM_CHAT_ID`.
4. Restart `orchestrator.py` so it picks up the new `.env` values.

Without both values set, the watcher logs a reminder and idles rather than crash-looping — it won't block the rest of the system.

## Discord approval bot setup

`discord_approval_watcher.py` is a second, redundant approval channel alongside Telegram — useful if Telegram is blocked (it's intermittently blocked in Pakistan by PTA). Both watchers notify independently for the same `Pending_Approval/` files; whichever one you can actually reach, you can act from — the other just reports "already handled" if you use both.

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) → New Application → give it any name.
2. Bot tab → Reset Token, copy it into `.env` as `DISCORD_BOT_TOKEN`. On the same tab, enable **Message Content Intent** (required for reading "Request Changes" text replies) and disable Public Bot if you don't want anyone else able to invite it.
3. OAuth2 → URL Generator → check `bot` scope and `Send Messages` + `Read Message History` permissions → open the generated URL and invite the bot to a server you control (a private server with just you is fine).
4. In Discord, enable Developer Mode (User Settings → Advanced), right-click the channel you want pings in → Copy Channel ID → paste into `.env` as `DISCORD_CHANNEL_ID`.
5. Restart `orchestrator.py`.

Same crash-safety as the Telegram watcher: if `discord.py` isn't installed yet (`uv sync`) or the env vars are missing, it idles and logs a reminder instead of crash-looping.

## Where things live

- **Watchers** (`watchers/*.py`) — perception. Each one polls a source and writes a Markdown task file into `vault/Needs_Action/`. Keep frontmatter formats consistent with what `approval_watcher.py` and the relevant skill expect to parse — there's no schema validation, just an ad-hoc regex/frontmatter parser, so a format change in one place can silently break another (see `CLAUDE.md`'s Known Issues for a live example of this coupling).
- **Skills** (`.agents/skills/*/SKILL.md`, mirrored in `.claude/skills/`) — reasoning. These are plain-language instructions the agent reads, not code. If you add or change a skill, keep both copies in sync (they're duplicated on purpose so both OpenCode and Claude Code can discover them).
- **MCP servers** (`mcp_servers/`) — action. Anything that calls an external API and has side effects belongs here. Register new servers in `opencode.json`'s `mcp` key, or the agent can't reach them.

## The one rule that matters most

**Any new action path that does something irreversible (sends a message, moves money, deletes something, posts publicly) must route through the vault's HITL gate** — draft to `vault/Pending_Approval/`, wait for a human to move it to `vault/Approved/`, only then execute. Don't add a code path that bypasses this, even for "obviously safe" cases. `mcp_servers/odoo_mcp.py` is the current counterexample to avoid repeating: it can write/delete Odoo records with no code-level check, relying only on the agent following a prompt instruction. That's the highest-priority thing to fix if you're touching the accounting integration.

## Good first contributions

- **Fix the Odoo MCP safety gate** — add a `DRY_RUN` check and require an approval file before `odoo_execute_kw` performs a write/delete, matching the pattern already used in `mcp_servers/email/server.py` and `approval_watcher.py`.
- **Build a real social media integration** — `mcp_servers/socials_mcp.py` is currently a stub that fakes success; wire it up to actual Facebook/Instagram/Twitter APIs behind the same `DRY_RUN` gate.
- **Add a Linux/Mac scheduler equivalent** — `scheduler/*.ps1` only works on Windows (Task Scheduler + WMI process checks). A cron or launchd-based runner would make this usable off Windows.
- **Add a backoff/circuit-breaker to `orchestrator.py`'s restart logic** — it currently retries a crashed watcher every 10 seconds forever with no limit. This is exactly what turned an expired Gmail OAuth token into 185,000+ log lines in under 24 hours (see `AGENTS.md` Known Issues). An exponential backoff, or giving up after N attempts and writing an `ALERT_HUMAN.md`, would catch this class of bug much earlier.
- **Confirm intent behind `scripts/watchdog.py`** — a second, undocumented supervisor that restarts `orchestrator.py` itself. Nothing else in the repo references it; either document why it exists or remove it.
- **Add tests for the frontmatter parsing coupling** — `gmail_watcher.py`'s generated frontmatter and `approval_watcher.py`'s regex-based extraction are loosely coupled with no schema validation; a small test asserting round-trip compatibility would catch format drift before it silently breaks approvals.

## Pull requests

Small, focused PRs are easier to review than large ones, especially since there's no automated test coverage to lean on. Describe what you tested manually (which watcher/skill/script you ran, and what you observed) in the PR description.
