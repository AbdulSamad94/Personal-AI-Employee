#!/usr/bin/env python3
"""
Watchdog Filesystem Watcher for Personal AI Employee.

This script leverages the `watchdog` library to provide event-driven, instantaneous
monitoring of the vault/Inbox folder. It replaces the old polling-based system.
When a new file is dropped into Inbox, it immediately creates an action file in
vault/Needs_Action and prompts the orchestrator/agent process.

"""

import time
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ── Environment ────────────────────────────────────────────────────────────────
VAULT_PATH = Path(__file__).parent.parent / "vault"
INBOX = VAULT_PATH / "Inbox"
NEEDS_ACTION = VAULT_PATH / "Needs_Action"
LOGS = VAULT_PATH / "Logs"

for d in [INBOX, NEEDS_ACTION, LOGS]:
    d.mkdir(exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS / "filesystem_watcher.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("fs_watch")

# ── Processing ────────────────────────────────────────────────────────────────


def create_action_file(file_path: Path):
    """Create a markdown action file for Claude to process."""
    if not file_path.is_file():
        return

    timestamp = datetime.now().isoformat()
    action_file = (
        NEEDS_ACTION
        / f'FILE_{file_path.stem}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    )

    # Note: Indentation intentionally kept flush left to prevent nested quoting errors
    content = f"""---
            type: file_drop
            original_name: {file_path.name}
            size: {file_path.stat().st_size} bytes
            received: {timestamp}
            status: pending
            ---

            ## New File Received

            A new file has been dropped into the Inbox folder.

            **File:** {file_path.name}
            **Received:** {timestamp}

            ## Suggested Actions
            - [ ] Review file contents
            - [ ] Determine if action is needed
            - [ ] Move to /Done when processed
            """
    action_file.write_text(content, encoding="utf-8")
    log.info("Created action file: %s", action_file.name)


class InboxEventHandler(FileSystemEventHandler):
    """Handler for file system events in the Inbox folder."""

    def on_created(self, event):
        """Triggered when a file or directory is created."""
        if not event.is_directory:
            filepath = Path(event.src_path)
            log.info("New file detected via event: %s", filepath.name)

            # Tiny delay to ensure the file is completely written by the OS before reading stats
            time.sleep(0.5)

            try:
                create_action_file(filepath)
            except Exception as e:
                log.error("Failed to create action file for %s: %s", filepath.name, e)


def main():
    log.info("Watchdog Event Watcher started. Monitoring %s", INBOX)

    event_handler = InboxEventHandler()
    observer = Observer()
    observer.schedule(event_handler, str(INBOX), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Watcher interrupted by user. Stopping...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
