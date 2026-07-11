"""
Tests for the coupling between what email-skill (an LLM skill, .agents/skills/email-skill/SKILL.md)
generates as an approval-request file and what watchers/approval_watcher.py's regex/frontmatter
parser expects when it executes that file. This coupling is flagged as a real risk in AGENTS.md's
Known Issues — a format change on either side can silently break the other with no schema
validation to catch it. These tests pin down the current actual behavior so a future change gets
caught here instead of failing silently in production.
"""

from datetime import datetime, timedelta

import pytest

from watchers import approval_watcher as aw

FAR_FUTURE = (datetime.now() + timedelta(days=3650)).isoformat()
FAR_PAST = (datetime.now() - timedelta(days=1)).isoformat()

# Matches .agents/skills/email-skill/SKILL.md's actual "Create Approval Request" template.
WELL_FORMED_APPROVAL = f"""---
type: approval_request
action: email_send
to: jane@example.com
subject: Re: Question about pricing
task_source: EMAIL_default_abc123_20260101_120000.md
from_account: work
created: 2026-01-01T12:00:00
expires: {FAR_FUTURE}
status: pending
---

## Email to Send

**To:** jane@example.com
**Subject:** Re: Question about pricing

---

## Draft Response

Hi Jane,

Thanks for reaching out! Our pricing starts at $99/month.

Best regards,
AI Employee

## Original Message Summary

Jane asked about pricing tiers.

## Why This Response

Directly answers her question per Company_Handbook tone rules.
"""


@pytest.fixture
def vault(tmp_path, monkeypatch):
    """Point approval_watcher's module-level dir constants at an isolated tmp vault."""
    approved = tmp_path / "Approved"
    done = tmp_path / "Done"
    rejected = tmp_path / "Rejected"
    for d in (approved, done, rejected):
        d.mkdir()
    monkeypatch.setattr(aw, "APPROVED_DIR", approved)
    monkeypatch.setattr(aw, "DONE_DIR", done)
    monkeypatch.setattr(aw, "REJECTED_DIR", rejected)
    return {"approved": approved, "done": done, "rejected": rejected}


@pytest.fixture
def mock_send_email(monkeypatch):
    """Replace the real SMTP-sending function with a recorder — no network calls in tests."""
    calls = []

    def fake_send_email(to, subject, body, from_account="default"):
        calls.append(
            {"to": to, "subject": subject, "body": body, "from_account": from_account}
        )
        return True, "mocked send"

    monkeypatch.setattr(aw, "send_email", fake_send_email)
    return calls


def test_parse_markdown_frontmatter_extracts_all_fields():
    data = aw.parse_markdown_frontmatter(WELL_FORMED_APPROVAL)
    assert data["to"] == "jane@example.com"
    assert data["subject"] == "Re: Question about pricing"
    assert data["from_account"] == "work"
    assert data["expires"] == FAR_FUTURE
    assert "## Draft Response" in data["_body"]


def test_well_formed_approval_sends_with_correct_recipient_and_account(vault, mock_send_email):
    f = vault["approved"] / "EMAIL_jane_20260101.md"
    f.write_text(WELL_FORMED_APPROVAL, encoding="utf-8")

    aw.process_email_approval(f)

    assert len(mock_send_email) == 1
    call = mock_send_email[0]
    assert call["to"] == "jane@example.com"
    assert call["subject"] == "Re: Question about pricing"
    assert call["from_account"] == "work"
    # Only the Draft Response section's content, not the surrounding sections.
    assert "Hi Jane," in call["body"]
    assert "Best regards" in call["body"]
    assert "Original Message Summary" not in call["body"]
    assert "Why This Response" not in call["body"]


def test_well_formed_approval_moves_to_done_on_success(vault, mock_send_email):
    f = vault["approved"] / "EMAIL_jane_20260101.md"
    f.write_text(WELL_FORMED_APPROVAL, encoding="utf-8")

    aw.process_email_approval(f)

    assert not f.exists()
    assert (vault["done"] / "EMAIL_jane_20260101.md").exists()


def test_expired_approval_moves_to_rejected_without_sending(vault, mock_send_email):
    content = WELL_FORMED_APPROVAL.replace(FAR_FUTURE, FAR_PAST)
    f = vault["approved"] / "EMAIL_expired.md"
    f.write_text(content, encoding="utf-8")

    aw.process_email_approval(f)

    assert len(mock_send_email) == 0
    assert not f.exists()
    assert (vault["rejected"] / "EXPIRED_EMAIL_expired.md").exists()


def test_from_account_defaults_to_default_when_absent(vault, mock_send_email):
    content = WELL_FORMED_APPROVAL.replace("from_account: work\n", "")
    f = vault["approved"] / "EMAIL_no_account.md"
    f.write_text(content, encoding="utf-8")

    aw.process_email_approval(f)

    assert mock_send_email[0]["from_account"] == "default"


def test_regex_fallback_extracts_recipient_when_frontmatter_missing_to(vault, mock_send_email):
    """
    approval_watcher.py's fallback regex looks for `- From: Name <email>` and
    `- Subject: ...` bullets in the body when frontmatter lacks `to`/`subject`.
    This confirms that fallback path works *when the body actually contains those
    bullets* — see the next test for whether real generated files ever do.
    """
    content = f"""---
type: approval_request
action: email_send
expires: {FAR_FUTURE}
status: pending
---

## Draft Response

Following up as requested.

- From: Jane Doe <jane@example.com>
- Subject: Question about pricing
"""
    f = vault["approved"] / "EMAIL_fallback.md"
    f.write_text(content, encoding="utf-8")

    aw.process_email_approval(f)

    assert len(mock_send_email) == 1
    assert mock_send_email[0]["to"] == "jane@example.com"
    assert mock_send_email[0]["subject"] == "Re: Question about pricing"


def test_gmail_watcher_generated_frontmatter_does_not_satisfy_regex_fallback(vault, mock_send_email):
    """
    Documents a real coupling gap (not fixed here — test-only per scope): gmail_watcher.py's
    make_action_file() writes `from: X` and `subject: X` as frontmatter *fields* on the raw
    inbound EMAIL_*.md task file, not as `- From: ... <...>` / `- Subject: ...` bullets in a
    body. If an approval file were ever missing `to`/`subject` in its own frontmatter and only
    carried gmail_watcher.py's original frontmatter-style fields in its body text (rather than
    the `- From:`/`- Subject:` bullet format approval_watcher.py's fallback regex expects),
    the fallback would NOT match, and the file is safely left in place (not sent, not crashed)
    rather than silently mis-sent. This test locks in that safe-failure behavior.
    """
    content = f"""---
type: approval_request
action: email_send
expires: {FAR_FUTURE}
status: pending
---

## Draft Response

from: Jane Doe <jane@example.com>
subject: Question about pricing

Following up as requested.
"""
    f = vault["approved"] / "EMAIL_mismatched_format.md"
    f.write_text(content, encoding="utf-8")

    aw.process_email_approval(f)

    # Safe failure: nothing sent, file untouched (stuck for a human to notice/fix),
    # not crashed and not silently mis-sent to a wrong/empty recipient.
    assert len(mock_send_email) == 0
    assert f.exists()
