"""Tests for clawteam.spawn.adapters — CLI detection and command preparation."""

from __future__ import annotations

from clawteam.spawn.adapters import (
    NativeCliAdapter,
    command_basename,
    is_hermes_command,
    is_interactive_cli,
    is_opencode_command,
    is_qwen_command,
)


class TestCLIDetection:
    """Each detector must accept full paths, bare names, and reject others."""

    def test_is_qwen_command(self):
        assert is_qwen_command(["qwen"])
        assert is_qwen_command(["qwen-code"])
        assert is_qwen_command(["/usr/local/bin/qwen"])
        assert not is_qwen_command(["claude"])
        assert not is_qwen_command([])

    def test_is_opencode_command(self):
        assert is_opencode_command(["opencode"])
        assert is_opencode_command(["/opt/bin/opencode"])
        assert not is_opencode_command(["openai"])
        assert not is_opencode_command([])

    def test_is_hermes_command(self):
        assert is_hermes_command(["hermes"])
        assert is_hermes_command(["/usr/local/bin/hermes"])
        assert not is_hermes_command(["claude"])
        assert not is_hermes_command([])

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        for cmd in ["claude", "codex", "nanobot", "gemini", "hermes", "kimi", "qwen", "opencode"]:
            assert is_interactive_cli([cmd]), f"{cmd} should be interactive"

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        assert not is_interactive_cli(["my-custom-agent"])
        assert not is_interactive_cli([])

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        assert command_basename(["/usr/local/bin/Claude"]) == "claude"
        assert command_basename([]) == ""


class [GENERIC_SECRET_REDACTED]:
    """Verify the skip_permissions flag maps to the correct CLI flag."""

    adapter = NativeCliAdapter()

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        result = self.adapter.prepare_command(
            ["qwen"], skip_permissions=True,
        )
        assert "--dangerously-skip-permissions" in result.final_command

    def test_opencode_gets_yolo(self):
        result = self.adapter.prepare_command(
            ["opencode"], skip_permissions=True,
        )
        assert "--yolo" in result.final_command

    def test_claude_unchanged(self):
        result = self.adapter.prepare_command(
            ["claude"], skip_permissions=True,
        )
        assert "--dangerously-skip-permissions" in result.final_command


class TestPrepareCommandPrompt:
    """Prompt delivery: via command args or post_launch_prompt."""

    adapter = NativeCliAdapter()

    def test_qwen_prompt_via_flag(self):
        result = self.adapter.prepare_command(
            ["qwen"], prompt="do work",
        )
        assert "-p" in result.final_command
        assert "do work" in result.final_command
        assert result.post_launch_prompt is None

    def test_opencode_prompt_via_flag(self):
        result = self.adapter.prepare_command(
            ["opencode"], prompt="analyse this",
        )
        assert "-p" in result.final_command
        assert "analyse this" in result.final_command
        assert result.post_launch_prompt is None

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        result = self.adapter.prepare_command(
            ["claude"], prompt="hello", interactive=True,
        )
        assert result.post_launch_prompt == "hello"
        assert "-p" not in result.final_command

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        result = self.adapter.prepare_command(
            ["claude"], prompt="hello", interactive=False,
        )
        assert result.post_launch_prompt is None
        assert "-p" in result.final_command

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        result = self.adapter.prepare_command(
            ["codex"], prompt="hello", interactive=True,
        )
        assert result.post_launch_prompt == "hello"
        assert "hello" not in result.final_command

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        result = self.adapter.prepare_command(
            ["codex", "exec"], prompt="hello", interactive=True,
        )
        assert result.post_launch_prompt is None
        assert "hello" in result.final_command


class TestHermesCommandPreparation:
    """Hermes Agent: chat subcommand insertion, --source tool tag, -q prompt, --yolo."""

    adapter = NativeCliAdapter()

    def test_hermes_gets_yolo(self):
        result = self.adapter.prepare_command(
            ["hermes"], skip_permissions=True, agent_name="w1",
        )
        assert "--yolo" in result.final_command
        assert "chat" in result.final_command

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        result = self.adapter.prepare_command(["hermes"], agent_name="w1")
        assert result.final_command[1] == "chat"

    def test_hermes_no_duplicate_chat(self):
        result = self.adapter.prepare_command(["hermes", "chat"], agent_name="w1")
        assert result.final_command.count("chat") == 1

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        # If user passes hermes with global options (e.g., --profile), we must
        # NOT insert 'chat' and break the argv order. Hermes CLI shape is
        # `hermes [global-options] <command>`.
        result = self.adapter.prepare_command(
            ["hermes", "--profile", "foo"], agent_name="w1",
        )
        # chat should NOT be injected when the user passed global options
        assert "chat" not in result.final_command
        # source tag should still apply
        assert "--source" in result.final_command

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        # If user passes a non-chat subcommand (e.g., `hermes sessions`),
        # we must not rewrite it as `hermes chat sessions`.
        result = self.adapter.prepare_command(["hermes", "sessions"], agent_name="w1")
        assert result.final_command[1] == "sessions"
        assert "chat" not in result.final_command

    def test_hermes_prompt_via_q_flag(self):
        result = self.adapter.prepare_command(
            ["hermes"], prompt="do work", agent_name="w1",
        )
        assert "-q" in result.final_command
        assert "do work" in result.final_command
        assert result.post_launch_prompt is None

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        # Hermes spawns from clawteam use --source tool so they don't
        # pollute the user's session list (which defaults to cli)
        result = self.adapter.prepare_command(["hermes"], agent_name="w1")
        assert "--source" in result.final_command
        assert "tool" in result.final_command

    def test_hermes_no_continue_flag(self):
        # Hermes --continue resumes an existing session; clawteam spawns
        # are fresh, so we must not pass --continue
        result = self.adapter.prepare_command(["hermes"], agent_name="w1")
        assert "--continue" not in result.final_command

    def [SENSITIVE_TOKEN_HARD_REDACTED](self):
        result = self.adapter.prepare_command(
            ["hermes"], skip_permissions=True, agent_name="w1",
        )
        assert "--yolo" in result.final_command
        assert "chat" in result.final_command
        chat_idx = result.final_command.index("chat")
        assert chat_idx == 1  # chat at position 1
