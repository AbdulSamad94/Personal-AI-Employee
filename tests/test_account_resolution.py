"""
Tests for the multi-account Gmail resolution logic in mcp_servers/email/server.py — the
function that decides which account's credentials a reply sends from, based on the
`from_account` field on an approval-request file.
"""

from mcp_servers.email import server


def test_resolve_account_returns_default_by_name():
    creds = server._resolve_account("default")
    assert creds is server.ACCOUNTS["default"]


def test_resolve_account_falls_back_to_default_for_unknown_account():
    creds = server._resolve_account("nonexistent_account")
    assert creds is server.ACCOUNTS["default"]


def test_resolve_account_returns_work_when_configured(monkeypatch):
    fake_accounts = {
        "default": {"user": "personal@example.com", "app_password": "pw1"},
        "work": {"user": "work@example.com", "app_password": "pw2"},
    }
    monkeypatch.setattr(server, "ACCOUNTS", fake_accounts)

    assert server._resolve_account("work")["user"] == "work@example.com"
    assert server._resolve_account("default")["user"] == "personal@example.com"
    # Still falls back to default when work isn't configured at all.
    monkeypatch.setattr(server, "ACCOUNTS", {"default": fake_accounts["default"]})
    assert server._resolve_account("work")["user"] == "personal@example.com"


def test_check_credentials_reports_missing_user(monkeypatch):
    monkeypatch.setattr(
        server, "ACCOUNTS", {"default": {"user": "", "app_password": "pw"}}
    )
    err = server._check_credentials("default")
    assert err is not None
    assert "GMAIL_USER" in err


def test_check_credentials_reports_missing_app_password(monkeypatch):
    monkeypatch.setattr(
        server, "ACCOUNTS", {"default": {"user": "a@example.com", "app_password": ""}}
    )
    err = server._check_credentials("default")
    assert err is not None
    assert "GMAIL_APP_PASSWORD" in err


def test_check_credentials_passes_when_both_set(monkeypatch):
    monkeypatch.setattr(
        server,
        "ACCOUNTS",
        {"default": {"user": "a@example.com", "app_password": "pw"}},
    )
    assert server._check_credentials("default") is None
