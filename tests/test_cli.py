"""Tests for CLI interface."""

from unittest.mock import Mock, patch

from typer.testing import CliRunner

from ai_launcher.cli import app

runner = CliRunner()


def test_version_command():
    """Test --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "claude-launcher" in result.stdout


def test_main_command_setup_needed(tmp_path):
    """Test main command when setup is needed."""
    with patch("ai_launcher.cli.ConfigManager") as mock_config:
        # Mock config that needs setup
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        mock_config_instance.load.return_value = Mock(
            scan=Mock(paths=[]),  # Empty paths triggers setup
        )

        with patch("ai_launcher.cli.typer.confirm") as mock_confirm:
            mock_confirm.return_value = False  # User declines setup

            result = runner.invoke(app, [])

            assert result.exit_code == 1
            assert "No scan paths configured" in result.stdout
