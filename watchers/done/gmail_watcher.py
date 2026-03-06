import os, time, logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
VAULT = Path(__file__).parent.parent.parent / "vault"
NEEDS_ACTION = VAULT / "Needs_Action"
LOGS = VAULT / "Logs"

LOGS.mkdir(exist_ok=True)
NEEDS_ACTION.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(LOGS / "gmail_watcher.log"), logging.StreamHandler()],
)


def get_service():
    creds = None
    token = VAULT.parent / "token.json"
    creds_file = VAULT.parent / "credentials.json"

    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def make_action_file(service, msg_id):
    msg = (
        service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    )
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    snippet = msg.get("snippet", "")
    ts = datetime.now()
    out = NEEDS_ACTION / f'EMAIL_{msg_id[:10]}_{ts.strftime("%Y%m%d_%H%M%S")}.md'

    out.write_text(
        f"""---
        type: email
        from: {headers.get('From', 'Unknown')}
        subject: {headers.get('Subject', 'No Subject')}
        received: {ts.isoformat()}
        status: pending
        ---

        ## Email Summary
        {snippet}

        ## Suggested Actions
        - [ ] Draft a reply following Company_Handbook.md
        - [ ] Create approval file in /Pending_Approval if sending
        """,
        encoding="utf-8",
    )
    logging.info(f"New email saved: {out.name}")


def run():
    service = get_service()
    processed = set()

    # Load already processed IDs from file so restarts don't reprocess
    processed_file = VAULT / "Logs" / "processed_emails.txt"
    if processed_file.exists():
        processed = set(processed_file.read_text().splitlines())

    logging.info("Gmail Watcher running... checking every 2 minutes")

    while True:
        try:
            res = (
                service.users()
                .messages()
                .list(userId="me", q="is:unread is:important", maxResults=10)
                .execute()
            )
            msgs = res.get("messages", [])

            for m in msgs:
                if m["id"] not in processed:
                    make_action_file(service, m["id"])
                    processed.add(m["id"])
                    # Save to file immediately
                    processed_file.write_text("\n".join(processed))
                    logging.info(f'Processed email: {m["id"]}')

        except Exception as e:
            logging.error(f"Gmail error: {e}")

        time.sleep(120)


if __name__ == "__main__":
    run()
