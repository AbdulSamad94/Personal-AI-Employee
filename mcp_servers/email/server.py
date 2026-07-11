#!/usr/bin/env python3
"""
Email MCP Server for Personal AI Employee.

Provides tools for sending Gmail emails after human approval via the HITL workflow.
Uses Gmail SMTP via Python's smtplib — no extra library needed beyond python-dotenv.

Tools:
  - email_send        : Send an approved email via Gmail SMTP
  - email_send_reply  : Send a reply with In-Reply-To / References headers
  - email_list_approved : List files currently waiting in vault/Approved/

Transport: stdio (runs as Claude Code subprocess)
IMPORTANT: stdio servers must NOT write logs to stdout — only stderr.
"""

import os
import json
import smtplib
import sys
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP

# ── Environment ────────────────────────────────────────────────────────────────
# Load .env from project root (two levels up from mcp_servers/email/)
ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env")

DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() == "true"
VAULT = ROOT / "vault"

# Multiple Gmail accounts can be sent from: "default" (personal) is required,
# "work" is optional. Matches the account labels gmail_watcher.py tags incoming
# mail with (see the `account:` frontmatter field), so a reply to a work-inbox
# email can go out from the work address instead of the personal one.
ACCOUNTS: dict[str, dict[str, str]] = {
    "default": {
        "user": os.getenv("GMAIL_USER", ""),
        "app_password": os.getenv("GMAIL_APP_PASSWORD", ""),
    },
}
if os.getenv("GMAIL_USER_WORK"):
    ACCOUNTS["work"] = {
        "user": os.getenv("GMAIL_USER_WORK", ""),
        "app_password": os.getenv("GMAIL_APP_PASSWORD_WORK", ""),
    }

# ── Logging — stderr only (stdout is reserved for MCP protocol) ────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [email_mcp] %(levelname)s %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("email_mcp")

# ── MCP Server ─────────────────────────────────────────────────────────────────
mcp = FastMCP("email_mcp")


# ── Pydantic Input Models ──────────────────────────────────────────────────────


class SendEmailInput(BaseModel):
    """Input model for sending a new email."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    to: str = Field(
        ...,
        description="Recipient email address (e.g. 'client@example.com')",
        min_length=3,
        max_length=320,
    )
    subject: str = Field(
        ...,
        description="Email subject line",
        min_length=1,
        max_length=998,
    )
    body: str = Field(
        ...,
        description="Plain-text body of the email",
        min_length=1,
    )
    approval_file: Optional[str] = Field(
        default=None,
        description=(
            "Filename of the approval .md file in vault/Approved/ that authorises "
            "this send (e.g. 'EMAIL_John_20260308.md'). "
            "If provided, the file is moved to vault/Done/ after sending."
        ),
    )
    from_account: str = Field(
        default="default",
        description=(
            "Which configured Gmail account to send from — matches the `account:` "
            "field on the originating EMAIL_*.md task (e.g. 'default' for the "
            "personal inbox, 'work' for the job-related inbox). Falls back to "
            "'default' if not specified or if the named account isn't configured."
        ),
    )

    @field_validator("to")
    @classmethod
    def validate_email_address(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError(f"'{v}' does not look like a valid email address")
        return v.lower()


class SendReplyInput(BaseModel):
    """Input model for sending an email reply with proper threading headers."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    to: str = Field(
        ...,
        description="Recipient email address",
        min_length=3,
        max_length=320,
    )
    subject: str = Field(
        ...,
        description="Subject line — should start with 'Re: '",
        min_length=1,
        max_length=998,
    )
    body: str = Field(
        ...,
        description="Plain-text reply body",
        min_length=1,
    )
    in_reply_to: str = Field(
        ...,
        description=(
            "Message-ID of the original email to thread under "
            "(e.g. '<abc123@mail.gmail.com>')"
        ),
    )
    approval_file: Optional[str] = Field(
        default=None,
        description=(
            "Filename of the approval .md file in vault/Approved/ authorising this reply."
        ),
    )
    from_account: str = Field(
        default="default",
        description=(
            "Which configured Gmail account to send from — matches the `account:` "
            "field on the originating EMAIL_*.md task (e.g. 'default' for the "
            "personal inbox, 'work' for the job-related inbox). Falls back to "
            "'default' if not specified or if the named account isn't configured."
        ),
    )

    @field_validator("to")
    @classmethod
    def validate_email_address(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError(f"'{v}' does not look like a valid email address")
        return v.lower()


# ── Shared helpers ─────────────────────────────────────────────────────────────


def _resolve_account(from_account: str) -> dict[str, str]:
    """Return the credential dict for from_account, falling back to 'default'."""
    return ACCOUNTS.get(from_account, ACCOUNTS["default"])


def _check_credentials(from_account: str = "default") -> Optional[str]:
    """Return an error string if the requested account's Gmail credentials are missing."""
    creds = _resolve_account(from_account)
    if not creds["user"]:
        return f"Error: GMAIL_USER (account '{from_account}') is not set in .env"
    if not creds["app_password"]:
        return f"Error: GMAIL_APP_PASSWORD (account '{from_account}') is not set in .env"
    return None


def _send_via_smtp(
    to: str, subject: str, body: str, extra_headers: dict = {}, from_account: str = "default"
) -> dict:
    """
    Send an email via Gmail SMTP using the credentials for from_account.

    Returns a dict with keys: success (bool), message (str).
    Respects DRY_RUN — logs but does not connect when true.
    """
    creds = _resolve_account(from_account)
    gmail_user = creds["user"]
    gmail_app_password = creds["app_password"]

    if DRY_RUN:
        log.info(
            "[DRY RUN] Would send email from_account=%s to=%s subject=%s",
            from_account,
            to,
            subject,
        )
        return {
            "success": True,
            "message": f"[DRY RUN] Email to '{to}' (from account '{from_account}') logged but "
            "NOT sent (DRY_RUN=true). Set DRY_RUN=false in .env to enable live sending.",
        }

    msg = MIMEMultipart("alternative")
    msg["From"] = gmail_user
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    for header, value in extra_headers.items():
        msg[header] = value

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, [to], msg.as_string())
        log.info("Email sent from_account=%s to=%s subject=%s", from_account, to, subject)
        return {
            "success": True,
            "message": f"Email successfully sent to '{to}' from '{gmail_user}'.",
        }
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": (
                f"Error: Gmail authentication failed for account '{from_account}'. "
                "Check its GMAIL_USER/GMAIL_APP_PASSWORD in .env. "
                "Make sure you are using an App Password, not your account password."
            ),
        }
    except Exception as e:
        log.error("SMTP error: %s", e)
        return {"success": False, "message": f"Error: Failed to send email — {e}"}


def _move_approval_to_done(filename: str) -> str:
    """
    Move an approval file from vault/Approved/ to vault/Done/.
    Returns a status string.
    """
    approved_dir = VAULT / "Approved"
    done_dir = VAULT / "Done"
    done_dir.mkdir(exist_ok=True)

    src = approved_dir / filename
    if not src.exists():
        return f"Warning: Approval file '{filename}' not found in vault/Approved/"

    dst = done_dir / filename
    if dst.exists():
        # Avoid collision — append timestamp
        stem = src.stem
        dst = done_dir / f"{stem}_done_{datetime.now().strftime('%H%M%S')}.md"

    src.rename(dst)
    return f"Approval file '{filename}' moved to vault/Done/."


def _write_log(action: str, to: str, subject: str, result: str):
    """Append one line to today's daily log in vault/Logs/."""
    log_dir = VAULT / "Logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    entry = (
        f"{datetime.now().isoformat()} | {action} | to:{to} | "
        f"subject:{subject} | {result}\n"
    )
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)


# ── Tools ──────────────────────────────────────────────────────────────────────


@mcp.tool(
    name="email_send",
    annotations={
        "title": "Send an Approved Email",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def email_send(params: SendEmailInput) -> str:
    """
    Send a new outbound email via Gmail SMTP after human approval.

    IMPORTANT: Only call this tool after a human has approved the email by moving
    an approval file to vault/Approved/. Never call without explicit approval.

    Respects DRY_RUN=true in .env — will log but NOT send in dry-run mode.

    Args:
        params (SendEmailInput): Validated input parameters containing:
            - to (str): Recipient email address (e.g. 'client@example.com')
            - subject (str): Email subject line
            - body (str): Plain-text email body
            - approval_file (Optional[str]): Filename in vault/Approved/ to archive

    Returns:
        str: JSON with keys:
            - success (bool): Whether the email was sent
            - message (str): Human-readable result or error description
            - approval_archived (str): Status of archiving the approval file
            - dry_run (bool): Whether DRY_RUN mode was active

    Examples:
        - Use when: Human has moved EMAIL_John_20260308.md to vault/Approved/
        - Don't use when: No approval file exists in vault/Approved/
        - Don't use when: The approval has expired (check expires field first)
    """
    err = _check_credentials(params.from_account)
    if err:
        return json.dumps({"success": False, "message": err, "dry_run": DRY_RUN})

    result = _send_via_smtp(
        params.to, params.subject, params.body, from_account=params.from_account
    )

    archive_status = "No approval file specified."
    if params.approval_file and result["success"]:
        archive_status = _move_approval_to_done(params.approval_file)

    _write_log(
        "email_send",
        params.to,
        params.subject,
        "sent" if result["success"] else "failed",
    )

    return json.dumps(
        {
            "success": result["success"],
            "message": result["message"],
            "approval_archived": archive_status,
            "dry_run": DRY_RUN,
        },
        indent=2,
    )


@mcp.tool(
    name="email_send_reply",
    annotations={
        "title": "Send an Approved Email Reply",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def email_send_reply(params: SendReplyInput) -> str:
    """
    Send a reply email that threads correctly under the original message.

    Sets In-Reply-To and References headers so the reply appears in the same
    thread in the recipient's inbox. Only call after human approval.

    Args:
        params (SendReplyInput): Validated input parameters containing:
            - to (str): Recipient email address
            - subject (str): Subject line (should start with 'Re: ')
            - body (str): Plain-text reply body
            - in_reply_to (str): Message-ID of the original email for threading
            - approval_file (Optional[str]): Filename in vault/Approved/ to archive

    Returns:
        str: JSON with keys:
            - success (bool): Whether the reply was sent
            - message (str): Human-readable result or error
            - approval_archived (str): Status of approval file archiving
            - dry_run (bool): Whether DRY_RUN mode was active

    Examples:
        - Use when: Replying to a client email that arrived via gmail_watcher
        - Don't use when: You want to start a new thread (use email_send instead)
    """
    err = _check_credentials(params.from_account)
    if err:
        return json.dumps({"success": False, "message": err, "dry_run": DRY_RUN})

    extra_headers = {
        "In-Reply-To": params.in_reply_to,
        "References": params.in_reply_to,
    }

    result = _send_via_smtp(
        params.to, params.subject, params.body, extra_headers, from_account=params.from_account
    )

    archive_status = "No approval file specified."
    if params.approval_file and result["success"]:
        archive_status = _move_approval_to_done(params.approval_file)

    _write_log(
        "email_send_reply",
        params.to,
        params.subject,
        "sent" if result["success"] else "failed",
    )

    return json.dumps(
        {
            "success": result["success"],
            "message": result["message"],
            "approval_archived": archive_status,
            "dry_run": DRY_RUN,
        },
        indent=2,
    )


@mcp.tool(
    name="email_list_approved",
    annotations={
        "title": "List Approved Email Files",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def email_list_approved() -> str:
    """
    List all email approval files currently waiting in vault/Approved/.

    Use this before calling email_send to see what has been approved by the human.
    Returns file names, creation times, and a preview of each file's frontmatter.

    Returns:
        str: JSON with keys:
            - count (int): Number of approved email files found
            - files (list): Each item has:
                - name (str): Filename (e.g. 'EMAIL_John_20260308.md')
                - created (str): ISO timestamp of file creation
                - preview (str): First 300 characters of the file for context

    Examples:
        - Use when: Before sending to check if there are any approved emails
        - Use when: Auditing what approvals are pending execution
    """
    approved_dir = VAULT / "Approved"
    approved_dir.mkdir(exist_ok=True)

    files = sorted(approved_dir.glob("EMAIL_*.md"), key=lambda f: f.stat().st_mtime)

    items = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
            items.append(
                {
                    "name": f.name,
                    "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    "preview": text[:300].strip(),
                }
            )
        except Exception as e:
            items.append(
                {"name": f.name, "created": "unknown", "preview": f"Error reading: {e}"}
            )

    return json.dumps({"count": len(items), "files": items}, indent=2)


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info(
        "Email MCP Server starting | accounts=%s | dry_run=%s | vault=%s",
        list(ACCOUNTS.keys()),
        DRY_RUN,
        VAULT,
    )
    mcp.run()  # stdio transport (default)
