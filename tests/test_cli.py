"""Tests for CLI interface."""

from typer.testing import CliRunner

from ai_launcher.cli import app

runner = CliRunner()


def test_version_command():
    """Test --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "ai-launcher" in result.stdout


def test_claude_command_no_path():
    """Test claude command without path argument shows error."""
    result = runner.invoke(app, ["claude"])
    assert result.exit_code == 1
    assert "No directory specified" in result.output
