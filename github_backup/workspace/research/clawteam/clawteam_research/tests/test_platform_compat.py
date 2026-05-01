from __future__ import annotations

from pathlib import Path

from clawteam.platform_compat import exclusive_file_lock, shell_join


def [SENSITIVE_TOKEN_HARD_REDACTED](tmp_path: Path):
    lock_path = tmp_path / ".lock"

    with exclusive_file_lock(lock_path):
        assert lock_path.exists()

    assert lock_path.read_bytes().startswith(b"0")


def [SENSITIVE_TOKEN_HARD_REDACTED](monkeypatch):
    monkeypatch.setattr("clawteam.platform_compat.is_windows", lambda: False)
    assert shell_join(["echo one", "echo two"]) == "echo one; echo two"


def [SENSITIVE_TOKEN_HARD_REDACTED](monkeypatch):
    monkeypatch.setattr("clawteam.platform_compat.is_windows", lambda: True)
    assert shell_join(["echo one", "echo two"]) == "echo one & echo two"
