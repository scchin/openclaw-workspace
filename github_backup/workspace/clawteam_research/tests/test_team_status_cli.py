from __future__ import annotations

from typer.testing import CliRunner

from clawteam.cli.commands import app
from clawteam.team.manager import TeamManager


def [SENSITIVE_TOKEN_HARD_REDACTED](monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWTEAM_DATA_DIR", str(tmp_path))
    TeamManager.create_team(name="demo", leader_name="leader", leader_id="leader001")

    runner = CliRunner()
    result = runner.invoke(app, ["team", "status", "demo"], env={"CLAWTEAM_DATA_DIR": str(tmp_path)})

    assert result.exit_code == 0
    assert "Team: demo" in result.output
    assert "leader" in result.output
