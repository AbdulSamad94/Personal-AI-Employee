import time
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
VAULT_PATH = Path(__file__).parent.parent.parent / "vault"
INBOX = VAULT_PATH / "Inbox"
NEEDS_ACTION = VAULT_PATH / "Needs_Action"
LOGS = VAULT_PATH / "Logs"

# Configure logging
LOGS.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.FileHandler(LOGS / "watcher.log"), logging.StreamHandler()],
)


def create_action_file(file_path: Path):
    """Create a markdown action file for Claude to process."""
    timestamp = datetime.now().isoformat()
    action_file = (
        NEEDS_ACTION
        / f'FILE_{file_path.stem}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    )

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
    action_file.write_text(content)
    logging.info(f"Created action file: {action_file.name}")


def watch_inbox():
    """Watch the Inbox folder for new files."""
    logging.info("Watcher started. Monitoring /Inbox folder...")
    seen_files = set()

    while True:
        try:
            current_files = set(INBOX.glob("*"))
            # ignore below error
            new_files = current_files - seen_files

            for file_path in new_files:
                if file_path.is_file():
                    logging.info(f"New file detected: {file_path.name}")
                    create_action_file(file_path)

            seen_files = current_files

        except Exception as e:
            logging.error(f"Error: {e}")

        time.sleep(10)  # Check every 10 seconds


if __name__ == "__main__":
    watch_inbox()
