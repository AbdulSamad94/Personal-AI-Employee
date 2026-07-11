"""
Tests for the Approve/Reject/Request-Changes state transitions in
watchers/telegram_approval_watcher.py. Mirrors test_discord_state_transitions.py — same
underlying pattern, different platform. `tg_call` is mocked throughout to guarantee zero
real network calls during tests.
"""

import pytest

from watchers import telegram_approval_watcher as taw


@pytest.fixture
def vault(tmp_path, monkeypatch):
    pending = tmp_path / "Pending_Approval"
    approved = tmp_path / "Approved"
    rejected = tmp_path / "Rejected"
    needs_action = tmp_path / "Needs_Action"
    for d in (pending, approved, rejected, needs_action):
        d.mkdir()
    monkeypatch.setattr(taw, "PENDING_DIR", pending)
    monkeypatch.setattr(taw, "APPROVED_DIR", approved)
    monkeypatch.setattr(taw, "REJECTED_DIR", rejected)
    monkeypatch.setattr(taw, "NEEDS_ACTION_DIR", needs_action)
    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "needs_action": needs_action,
    }


@pytest.fixture
def state():
    return {"notified": {}, "awaiting_edit": {}, "update_offset": 0}


@pytest.fixture
def mock_tg_call(monkeypatch):
    calls = []

    def fake_tg_call(method, **params):
        calls.append({"method": method, **params})
        # Mirrors the real sendMessage response shape — send_notification() reads
        # result["result"]["message_id"], which would KeyError on an empty dict here.
        return {"ok": True, "result": {"message_id": 12345}}

    monkeypatch.setattr(taw, "tg_call", fake_tg_call)
    return calls


def test_handle_approve_moves_file_and_clears_state(vault, state):
    (vault["pending"] / "EMAIL_x.md").write_text("draft", encoding="utf-8")
    state["notified"]["abc123"] = {"file": "EMAIL_x.md"}

    taw.handle_approve("abc123", state)

    assert (vault["approved"] / "EMAIL_x.md").exists()
    assert not (vault["pending"] / "EMAIL_x.md").exists()
    assert "abc123" not in state["notified"]


def test_handle_reject_moves_file_and_clears_state(vault, state):
    (vault["pending"] / "EMAIL_x.md").write_text("draft", encoding="utf-8")
    state["notified"]["abc123"] = {"file": "EMAIL_x.md"}

    taw.handle_reject("abc123", state)

    assert (vault["rejected"] / "EMAIL_x.md").exists()
    assert "abc123" not in state["notified"]


def test_handle_approve_unknown_short_id_is_a_safe_noop(vault, state):
    # No entry in state["notified"] at all — must not raise KeyError.
    taw.handle_approve("never-notified", state)
    assert list(vault["approved"].iterdir()) == []
    assert "never-notified" not in state["notified"]


def test_handle_approve_when_file_already_moved_by_other_channel(vault, state):
    """Simulates the Discord bot having already approved the same file first."""
    state["notified"]["abc123"] = {"file": "EMAIL_x.md"}
    # File is NOT in pending — as if Discord already moved it.

    taw.handle_approve("abc123", state)

    # Still cleans up its own state even though there was nothing to move.
    assert "abc123" not in state["notified"]


def test_handle_edit_request_registers_awaiting_edit_and_notifies(state, mock_tg_call):
    state["notified"]["abc123"] = {"file": "EMAIL_x.md"}

    taw.handle_edit_request("abc123", state, chat_id="12345")

    assert state["awaiting_edit"]["12345"] == {"short_id": "abc123", "file": "EMAIL_x.md"}
    assert len(mock_tg_call) == 1
    assert mock_tg_call[0]["method"] == "sendMessage"


def test_handle_edit_request_unknown_short_id_does_not_notify(state, mock_tg_call):
    taw.handle_edit_request("never-notified", state, chat_id="12345")
    assert "12345" not in state["awaiting_edit"]
    assert len(mock_tg_call) == 0


def test_handle_edit_reply_moves_to_needs_action_with_feedback(vault, state, mock_tg_call):
    (vault["pending"] / "EMAIL_x.md").write_text(
        "---\nstatus: pending\n---\n\nOriginal draft.\n", encoding="utf-8"
    )
    state["awaiting_edit"]["12345"] = {"short_id": "abc123", "file": "EMAIL_x.md"}
    state["notified"]["abc123"] = {"file": "EMAIL_x.md"}

    taw.handle_edit_reply("12345", "Make it shorter please", state)

    assert not (vault["pending"] / "EMAIL_x.md").exists()
    moved = vault["needs_action"] / "EMAIL_x.md"
    assert moved.exists()
    content = moved.read_text(encoding="utf-8")
    assert "status: needs_revision" in content
    assert "Make it shorter please" in content
    assert "12345" not in state["awaiting_edit"]
    assert "abc123" not in state["notified"]
    assert len(mock_tg_call) == 1  # confirmation message sent


def test_handle_edit_reply_ignores_stray_message_with_no_pending_edit(vault, state, mock_tg_call):
    taw.handle_edit_reply("chat-with-nothing-pending", "random text", state)
    assert list(vault["needs_action"].iterdir()) == []
    assert len(mock_tg_call) == 0
