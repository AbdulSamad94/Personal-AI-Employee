# Personal AI Employee - Hackathon 0

Current Tier: **Silver (In Progress)**

This project turns your digital life into an autonomous operation using Claude Code and a local-first memory vault.

## Prerequisites

- **Python**: 3.11+
- **Node.js**: 18+
- **Claude Code**: Properly configured and logged in.
- **Chrome/Chromium**: Required for Playwright.

## Setup Instructions

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install Playwright browser:
   ```bash
   playwright install chromium
   ```
3. Configure your credentials in `.env`:
   - `GMAIL_USER`, `GMAIL_APP_PASSWORD`
   - `LINKEDIN_TOKEN`, `LINKEDIN_PERSON_ID`
4. Start the background orchestrator:
   ```bash
   python orchestrator.py
   ```

## Folder Structure

- `vault/`: Single Obsidian vault source of truth.
  - `Needs_Action/`: Entry point for all watcher tasks.
  - `Skills/`: Detailed reasoning instructions for Claude.
- `watchers/`:
  - `done/`: Fully functional background monitors.
  - `todo/`: Templates for upcoming integrations.
- `config/`: System configuration.
- `docs/`: Technical documentation and setup guides.

## Environment Variables

| Variable             | Purpose                                         |
| -------------------- | ----------------------------------------------- |
| `GMAIL_USER`         | Your email address for Gmail watcher            |
| `GMAIL_APP_PASSWORD` | App-specific password for OAuth/SMTP            |
| `LINKEDIN_TOKEN`     | OAuth2 Bearer token for LinkedIn API            |
| `LINKEDIN_PERSON_ID` | Your unique LinkedIn member ID                  |
| `DRY_RUN`            | If "true", will not perform destructive actions |
