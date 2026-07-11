# AGENTS.md

This file provides guidance to AI coding agents (OpenCode, and any other tool that follows the AGENTS.md convention) when working with code in this repository.

This project's actual agent runtime is [OpenCode](https://opencode.ai), which reads this file. `CLAUDE.md` exists alongside it for Claude Code and is kept in sync intentionally — the same way `.agents/skills/` and `.claude/skills/` are duplicated so each tool finds what it needs natively. If you update one, update the other. (OpenCode ignores `CLAUDE.md` entirely whenever this file is present, per OpenCode's rules precedence.)

## What this project is

A local-first, human-in-the-loop autonomous agent system ("Personal AI Employee") that triages email, manages LinkedIn, and drafts business actions for human approval. See the README's "Project Status" table for what's actually working vs. scaffolding before relying on any given component. It follows a Perception → Reasoning → Action loop:

- **Watchers** (`watchers/*.py`) poll Gmail, LinkedIn, and the local filesystem, dropping Markdown task files into `vault/Needs_Action/`. `gmail_watcher.py` supports multiple Gmail accounts via the `GMAIL_ACCOUNT_LABEL` env var (`orchestrator.py` launches one process per account — currently `default`/personal and `work`/job-search); each account gets its own `token_<label>.json`, `processed_emails_<label>.txt`, and `gmail_watcher_<label>.log`, and generated task files carry an `account:` frontmatter field so downstream skills know which inbox — and which address to reply from — a given email came from.
- **Reasoning**: an LLM agent runs via the OpenCode CLI, reads the vault, uses Agent Skills in `.agents/skills/` (OpenCode discovers these natively), and drafts actions. Configured in `opencode.json` at the repo root, currently pointed at OpenCode Zen's free `opencode/big-pickle` model.
- **Action**: MCP servers in `mcp_servers/` execute approved actions. Everything irreversible (sending email, posting socially, financial writes) is meant to go through a Human-in-the-Loop gate: agent drafts to `vault/Pending_Approval/`, a human approves it, and `watchers/approval_watcher.py` executes it and moves the file to `vault/Done/`. Approval has three independent paths into `vault/Approved/`: manually dragging the file (Obsidian), `telegram_approval_watcher.py`, or `discord_approval_watcher.py` — the latter two both ping their respective platform with Approve/Reject/Request Changes buttons the moment a file lands in `Pending_Approval/` (Discord exists as a redundant channel because Telegram is intermittently blocked in Pakistan; both notify independently for the same files and re-check file existence before acting, so acting from one makes the other's buttons harmlessly no-op with "already handled"). "Request Changes" on either platform appends the human's free-text reply to the file and moves it to `vault/Needs_Action/` with `status: needs_revision` for the next OpenCode pass to redraft.

The Obsidian vault (`vault/`) is the system's state machine, config layer, and audit log — not just docs. Read `vault/Company_Handbook.md` (rules of engagement) and `vault/Business_Goals.md` (KPIs/targets) before making behavioral changes to any skill or watcher; skills are expected to comply with the Handbook's approval thresholds.

## Commands

There is no build step, linter, or test suite in this repo.

Install dependencies:
```bash
uv sync                        # uses pyproject.toml + uv.lock
```

Run the system:
```bash
python orchestrator.py         # boots all watchers (2x gmail, linkedin, filesystem, approval, telegram_approval, discord_approval), auto-restarts on crash
opencode                       # second terminal: starts the reasoning agent (interactive TUI)
opencode run "<prompt>" --auto # non-interactive, unattended run — used by scheduler/run_agent.ps1 and scripts/ralph_loop.ps1
```

Run a single watcher directly (useful for isolated debugging):
```bash
python watchers/gmail_watcher.py                 # GMAIL_ACCOUNT_LABEL=work env var selects the second account
python watchers/linkedin_watcher.py
python watchers/filesystem_watcher.py
python watchers/approval_watcher.py
python watchers/telegram_approval_watcher.py      # idles (no crash) until TELEGRAM_BOT_TOKEN/CHAT_ID are set
python watchers/discord_approval_watcher.py       # idles (no crash) until discord.py installed + DISCORD_BOT_TOKEN/CHANNEL_ID are set
```

Run an MCP server standalone:
```bash
uv run mcp_servers/email/server.py
python mcp_servers/odoo_mcp.py
python mcp_servers/socials_mcp.py
```

Local Odoo instance for accounting integration testing:
```bash
docker-compose up -d           # odoo:latest on :8069 + postgres:15
```

Windows Task Scheduler wiring: `scheduler/setup_task.ps1` registers `scheduler/run_agent.ps1` as a recurring job; `scripts/ralph_loop.ps1` implements the "Ralph Wiggum" retry loop (creates a task file, polls until it's moved to `vault/Done/` or `MaxIterations` is hit).

## Safety model

- `.env`'s `DRY_RUN` flag gates whether watchers/MCP servers perform real side effects (send email, post socially) vs. log-only. **Check `.env` for the current value before testing anything that hits a live API.**
- `.env`, `token*.json` (one per Gmail account — `token.json`, `token_work.json`, etc.), `credentials.json` hold real secrets and are gitignored — never read their values into responses or logs, never commit them.
- MCP servers are registered in `opencode.json`'s `mcp` key. Only `mcp_servers/email/server.py` is currently registered there. `odoo_mcp.py` and `socials_mcp.py` exist but aren't wired into `opencode.json` — they aren't reachable by the agent as currently configured.
- `opencode.json`'s `permission` block allows `edit`/`bash` by default (needed for vault file operations) but explicitly denies `rm -rf *` and requires confirmation on `git push`/`git reset --hard` as defense-in-depth. The real HITL safety boundary is still the vault's `Pending_Approval` → `Approved` file-move gate, not tool permissions.
- **Most `vault/` subdirectories (`Needs_Action`, `Logs`, `Pending_Approval`, `Approved`, `Done`, `Rejected`, `Briefings`, `Plans`) are gitignored but re-included for tool visibility via `.rgignore`** (OpenCode's Glob/Grep tools are ripgrep-backed and silently respect `.gitignore` otherwise — see Known Issues). Only `Company_Handbook.md`, `Business_Goals.md`, `Dashboard.md`, and `.obsidian/` config stay tracked in git — everything else fills up with real runtime data (actual email content, client/business specifics) that shouldn't enter git history. If you can't see files somewhere under `vault/` via Glob, check `.rgignore` before assuming the directory is empty.

## Known issues / gaps (read before making changes here)

This audit reflects the state as of 2026-07-09. Re-verify anything load-bearing before relying on it, since the codebase is about to change substantially.

- **`odoo_mcp.py` has no code-level safety gate** — `odoo_execute_kw` is a generic ORM executor (create/write/unlink on any model) with no `DRY_RUN` check and no approval-file requirement, unlike every other action path in the system. The only guard is a prompt-level instruction in the `odoo-accounting` skill. Treat this as the highest-priority item to fix before enabling real Odoo writes.
- **`socials_mcp.py` is a stub**, not a real integration — it logs posts to a local JSON file and returns hardcoded fake metrics. No real Facebook/Instagram/Twitter API calls exist despite README claims.
- **`scripts/post.ps1`** posts live to the LinkedIn API with no dry-run gate; treat it as a manual, deliberately-live test script, not something to run casually.
- **Fixed 2026-07-11: removed `requirements.txt`**, which had drifted out of sync with `pyproject.toml` (missing `discord-py` before removal — proof the two-manifest setup wasn't being kept in sync in practice). `pyproject.toml` + `uv.lock` (via `uv sync`) is now the only dependency path.
- **Fixed 2026-07-11: removed `filesystem_watcher_basic.py`** (dead code, fully superseded by the watchdog-based `filesystem_watcher.py`) and flattened `watchers/done/*.py` → `watchers/*.py` (the `done`/`todo` split was vestigial — `watchers/todo/` never existed on disk). Every watcher's root-path calculation (`Path(__file__).parent.parent...`) was updated from 3 levels to 2 to match the new depth.
- `scripts/watchdog.py` is a second, undocumented supervisor that restarts `orchestrator.py` itself; it isn't referenced by anything else in the repo and may be orphaned — confirm intent before relying on or removing it.
- `gmail_watcher.py`'s generated frontmatter format and `approval_watcher.py`'s regex-based recipient extraction are loosely coupled and not covered by tests — changes to one's output format can silently break the other's parsing.
- `docs/SETUP.md` references a Playwright-based WhatsApp watcher that was never built (matches the empty `whatsapp_session/` gitignore entry). The README's "Project Status" table is the current source of truth for what's real vs. stub.
- **Agent runtime was switched from Qwen Code (via a `claude` CLI + local Ollama `qwen2.5:3b` hack) to OpenCode on 2026-07-09**, because Ollama wasn't even running locally and the 3B model was unreliable at tool calling. `opencode.json` now pins `model` to `opencode/big-pickle`, a free model on the OpenCode Zen gateway. Zen's free-model lineup rotates (models get pulled or start being billed with little notice) — if the agent starts erroring or being billed, run `opencode models` to see what's currently free and update `model`/`small_model` in `opencode.json`. Zen requires a card on file even for $0 models (never charged as long as you stick to free-labeled ones).
- Leftover artifacts from the prior Qwen Code setup (`QWEN.md`, `.qwen/`) were removed on 2026-07-09 as part of the OpenCode switch.
- **OpenCode's Glob/Grep tools are ripgrep-backed and respect `.gitignore` by default** (upstream limitation, no config toggle — see opencode issue #31994). Since most `vault/` runtime subdirectories are intentionally gitignored (see Safety model), the agent couldn't see files in them via Glob until a root-level **`.rgignore`** was added to re-include those paths for tool visibility without changing what git tracks. If you add another gitignored-but-agent-needs-to-read directory under `vault/`, add it to `.rgignore` too, or the agent will silently see it as empty.
- Rapid back-to-back `opencode run` invocations (or one running while an interactive `opencode` TUI session is still open) can intermittently fail with `Error: Unexpected error / Failed query: PRAGMA wal_checkpoint(PASSIVE)` — a local SQLite session-DB lock collision. It's transient; retrying the command succeeds. Close stray interactive `opencode` sessions before relying on scheduled `opencode run --auto` jobs to avoid this.
- **Fixed 2026-07-09/10: `scheduler/run_agent.ps1` had a check-then-act race that let two scheduled ticks both pass the "orchestrator not running" check and each spawn a full orchestrator + 4-watcher tree simultaneously.** This is almost certainly what caused the "6 duplicate CEO Briefing task files" bug. Fixed with a named `System.Threading.Mutex` guarding the whole script (a second concurrent invocation now exits immediately instead of duplicating work) plus a PID-lock-file check for the orchestrator specifically. Validated in production across multiple real scheduled cycles since the fix.
- **Fixed 2026-07-09/10: `run_agent.ps1`'s `Start-Process -FilePath "opencode"` failed on every single scheduled run** with `%1 is not a valid Win32 application` — npm's Windows install also creates an `opencode.ps1` shim, and `Start-Process` uses raw `CreateProcess`, which can't execute a `.ps1` directly (unlike interactive PowerShell command resolution). Fixed by targeting `opencode.cmd` explicitly. This means every scheduled OpenCode run before this fix silently did nothing.
- **`orchestrator.py`'s watcher-restart loop has no backoff or retry limit** — a crashed watcher (e.g. `gmail_watcher.py` hitting an expired OAuth token) gets relaunched every 10 seconds forever. In practice this produced 185,000+ log lines and an 18MB `orchestrator.log` over about four months before being noticed (the Gmail token has since been fixed). Adding exponential backoff or a give-up-and-alert threshold is a good-first-contribution (see `CONTRIBUTING.md`).
- **`telegram_approval_watcher.py`** pings a Telegram chat for every new `vault/Pending_Approval/` file and handles Approve/Reject/Request Changes replies (see CONTRIBUTING.md for bot setup). Deliberately does *not* crash-exit when `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` are unset — it idles and logs a reminder every ~10 minutes instead, specifically to avoid repeating the gmail_watcher.py crash-loop failure mode above.
- **`discord_approval_watcher.py`** is a second, redundant approval channel (same Approve/Reject/Request Changes UX) added because Telegram is intermittently blocked in Pakistan by PTA. Uses `discord.py`'s Gateway client (websocket, outbound-only — no port forwarding needed), not raw REST like the Telegram watcher, since receiving button interactions requires either a Gateway connection or a publicly reachable webhook URL. Same "idle, don't crash" guard applies if `discord.py` isn't installed or `DISCORD_BOT_TOKEN`/`DISCORD_CHANNEL_ID` are unset.
