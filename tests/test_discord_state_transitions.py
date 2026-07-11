"""
Tests for the Approve/Reject/Request-Changes state transitions in
watchers/discord_approval_watcher.py. These are pure functions (state dict + filesystem),
so they're tested directly without needing a real Discord connection.
"""

import pytest

from watchers import discord_approval_watcher as daw


@pytest.fixture
def vault(tmp_path, monkeypatch):
    pending = tmp_path / "Pending_Approval"
    approved = tmp_path / "Approved"
    rejected = tmp_path / "Rejected"
    needs_action = tmp_path / "Needs_Action"
    for d in (pending, approved, rejected, needs_action):
        d.mkdir()
    monkeypatch.setattr(daw, "PENDING_DIR", pending)
    monkeypatch.setattr(daw, "APPROVED_DIR", approved)
    monkeypatch.setattr(daw, "REJECTED_DIR", rejected)
    monkeypatch.setattr(daw, "NEEDS_ACTION_DIR", needs_action)
    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "needs_action": needs_action,
    }


@pytest.fixture
def state():
    return {"notified": {}, "awaiting_edit": {}}


def test_handle_approve_moves_file_and_clears_state(vault, state):
    (vault["pending"] / "EMAIL_x.md").write_text("draft", encoding="utf-8")
    state["notified"]["abc123"] = {"file": "EMAIL_x.md"}

    result = daw.handle_approve("abc123", state)

    assert (vault["approved"] / "EMAIL_x.md").exists()
    assert not (vault["pending"] / "EMAIL_x.md").exists()
    assert "abc123" not in state["notified"]
    assert "Approved" in result


def test_handle_reject_moves_file_and_clears_state(vault, state):
    (vault["pending"] / "EMAIL_x.md").write_text("draft", encoding="utf-8")
    state["notified"]["abc123"] = {"file": "EMAIL_x.md"}

    result = daw.handle_reject("abc123", state)

    assert (vault["rejected"] / "EMAIL_x.md").exists()
    assert "abc123" not in state["notified"]
    assert "Rejected" in result


def test_handle_approve_unknown_short_id_is_a_safe_noop(vault, state):
    result = daw.handle_approve("never-notified", state)
    assert "Already handled" in result
    assert list(vault["approved"].iterdir()) == []


def test_handle_approve_when_file_already_moved_by_other_channel(vault, state):
    """Simulates the Telegram bot having already approved the same file first."""
    state["notified"]["abc123"] = {"file": "EMAIL_x.md"}
    # File is NOT in pending — as if Telegram already moved it.

    result = daw.handle_approve("abc123", state)

    assert "abc123" not in state["notified"]
    assert "already handled elsewhere" in result


def test_handle_edit_reply_moves_to_needs_action_with_feedback(vault, state):
    (vault["pending"] / "EMAIL_x.md").write_text(
        "---\nstatus: pending\n---\n\nOriginal draft.\n", encoding="utf-8"
    )
    state["awaiting_edit"]["channel-1"] = {"short_id": "abc123", "file": "EMAIL_x.md"}
    state["notified"]["abc123"] = {"file": "EMAIL_x.md"}

    result = daw.handle_edit_reply("channel-1", "Make it shorter please", state)

    assert not (vault["pending"] / "EMAIL_x.md").exists()
    moved = vault["needs_action"] / "EMAIL_x.md"
    assert moved.exists()
    content = moved.read_text(encoding="utf-8")
    assert "status: needs_revision" in content
    assert "Make it shorter please" in content
    assert "channel-1" not in state["awaiting_edit"]
    assert "abc123" not in state["notified"]
    assert result is not None and "queued" in result


def test_handle_edit_reply_ignores_stray_message_with_no_pending_edit(vault, state):
    result = daw.handle_edit_reply("channel-with-nothing-pending", "random text", state)
    assert result is None
    assert list(vault["needs_action"].iterdir()) == []
