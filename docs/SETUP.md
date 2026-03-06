# Project Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Claude Code
- Obsidian (for vault management)

## Installation

1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright:
   ```bash
   playwright install chromium
   ```

## Configuration

1. **Environment Variables**: Create a `.env` file in the root directory (see `README.md` for required variables).
2. **Gmail OAuth**: Place `credentials.json` in the root and run `watchers/done/gmail_watcher.py` once manually to generate `token.json`.

## Usage

Start the background watchers using the orchestrator:

```bash
python orchestrator.py
```

## Folder Structure

- `vault/`: The Obsidian memory vault.
- `watchers/`: Background scripts for data ingestion.
- `mcp_servers/`: Custom MCP servers for Claude Code.
- `scripts/`: Test and utility scripts.
- `docs/`: Project documentation.
