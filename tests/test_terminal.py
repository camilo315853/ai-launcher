"""Tests for terminal utilities."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_launcher.utils.terminal import (
    _supports_title_setting,
    format_terminal_title,
    get_terminal_info,
    set_terminal_title,
)


class TestFormatTerminalTitle:
    """Tests for format_terminal_title()."""

    def test_basic_format(self):
        """Test basic title formatting with project and provider."""
        project_path = Path("/home/user/projects/my-app")
        provider_name = "Claude Code"

        result = format_terminal_title(
            "{project} → {provider}",
            project_path,
            provider_name,
        )

        assert result == "my-app → Claude Code"

    def test_format_with_parent(self):
        """Test formatting with parent directory."""
        project_path = Path("/home/user/projects/my-app")
        provider_name = "Claude Code"

        result = format_terminal_title(
            "{parent}/{project} - {provider}",
            project_path,
            provider_name,
        )

        assert result == "projects/my-app - Claude Code"

    def test_format_with_path(self):
        """Test formatting with full path."""
        project_path = Path("/home/user/projects/my-app")
        provider_name = "Claude Code"

        result = format_terminal_title(
            "{path}",
            project_path,
            provider_name,
        )

        assert result == "/home/user/projects/my-app"

    def test_format_project_only(self):
        """Test formatting with project name only."""
        project_path = Path("/home/user/projects/my-app")
        provider_name = "Claude Code"

        result = format_terminal_title(
            "{project}",
            project_path,
            provider_name,
        )

        assert result == "my-app"

    def test_format_provider_only(self):
        """Test formatting with provider name only."""
        project_path = Path("/home/user/projects/my-app")
        provider_name = "Claude Code"

        result = format_terminal_title(
            "{provider}",
            project_path,
            provider_name,
        )

        assert result == "Claude Code"

    def test_format_with_emoji(self):
        """Test formatting with emoji characters."""
        project_path = Path("/home/user/projects/my-app")
        provider_name = "Claude Code"

        result = format_terminal_title(
            "🤖 {project} | {provider}",
            project_path,
            provider_name,
        )

        assert result == "🤖 my-app | Claude Code"

    def test_format_invalid_variable(self):
        """Test that invalid format variables raise ValueError."""
        project_path = Path("/home/user/projects/my-app")
        provider_name = "Claude Code"

        with pytest.raises(ValueError, match="Invalid format string variable"):
            format_terminal_title(
                "{unknown_variable}",
                project_path,
                provider_name,
            )

    def test_format_multiple_invalid_variables(self):
        """Test error message lists valid variables."""
        project_path = Path("/home/user/projects/my-app")
        provider_name = "Claude Code"

        with pytest.raises(ValueError, match="Valid variables"):
            format_terminal_title(
                "{foo} and {bar}",
                project_path,
                provider_name,
            )

    def test_format_strips_ansi_from_project_name(self):
        """Test that ANSI codes in project name are removed."""
        # Project path with ANSI red color codes
        project_path = Path("/home/user/\x1b[31mmy-app\x1b[0m")
        provider_name = "Claude Code"

        result = format_terminal_title(
            "{project}",
            project_path,
            provider_name,
        )

        # Should not contain ANSI escape codes
        assert "\x1b[" not in result
        assert "\x1b[31m" not in result
        assert result == "my-app"

    def test_format_strips_ansi_from_provider_name(self):
        """Test that ANSI codes in provider name are removed."""
        project_path = Path("/home/user/my-app")
        provider_name = "\x1b[32mClaude Code\x1b[0m"  # Green color

        result = format_terminal_title(
            "{provider}",
            project_path,
            provider_name,
        )

        assert "\x1b[" not in result
        assert result == "Claude Code"

    def test_format_strips_ansi_from_format_string(self):
        """Test that ANSI codes in format string are removed."""
        project_path = Path("/home/user/my-app")
        provider_name = "Claude Code"

        # Format string with screen-clearing ANSI codes
        result = format_terminal_title(
            "\x1b[H\x1b[2J{project}",  # Clear screen codes
            project_path,
            provider_name,
        )

        # Should not contain screen-clearing ANSI codes
        assert "\x1b[H" not in result
        assert "\x1b[2J" not in result
        assert "my-app" in result

    def test_format_strips_osc_sequences(self):
        """Test that OSC (Operating System Command) sequences are removed."""
        project_path = Path("/home/user/my-app")
        provider_name = "Claude Code"

        # Format with OSC sequence (like our own title-setting sequence)
        result = format_terminal_title(
            "\x1b]0;Malicious\x07{project}",
            project_path,
            provider_name,
        )

        # Should strip the OSC sequence
        assert "\x1b]" not in result
        assert "Malicious" not in result
        assert result == "my-app"

    def test_format_root_directory(self):
        """Test formatting with root directory path."""
        project_path = Path("/")
        provider_name = "Claude Code"

        result = format_terminal_title(
            "{project} → {provider}",
            project_path,
            provider_name,
        )

        # Should show "/" not empty string
        assert result != " → Claude Code"  # Not empty project
        assert "/" in result or result.startswith("/")
        assert "→ Claude Code" in result

    def test_format_current_directory(self):
        """Test formatting with current directory."""
        project_path = Path(".")
        provider_name = "Claude Code"

        result = format_terminal_title("{project}", project_path, provider_name)

        # Should show something, not empty string
        assert result != ""
        assert len(result) > 0


class TestSupportsTerminalTitle:
    """Tests for _supports_title_setting()."""

    @patch("sys.stdout.isatty")
    def test_not_tty(self, mock_isatty):
        """Test that non-tty returns False."""
        mock_isatty.return_value = False

        result = _supports_title_setting()

        assert result is False

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM": "xterm-256color"})
    def test_xterm_terminal(self, mock_isatty):
        """Test that xterm terminal is supported."""
        mock_isatty.return_value = True

        result = _supports_title_setting()

        assert result is True

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM": "screen"})
    def test_screen_terminal(self, mock_isatty):
        """Test that screen terminal is supported."""
        mock_isatty.return_value = True

        result = _supports_title_setting()

        assert result is True

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM": "tmux-256color"})
    def test_tmux_terminal(self, mock_isatty):
        """Test that tmux terminal is supported."""
        mock_isatty.return_value = True

        result = _supports_title_setting()

        assert result is True

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM": "alacritty"})
    def test_alacritty_terminal(self, mock_isatty):
        """Test that Alacritty terminal is supported."""
        mock_isatty.return_value = True

        result = _supports_title_setting()

        assert result is True

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM": "kitty"})
    def test_kitty_terminal(self, mock_isatty):
        """Test that Kitty terminal is supported."""
        mock_isatty.return_value = True

        result = _supports_title_setting()

        assert result is True

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"})
    def test_iterm_terminal(self, mock_isatty):
        """Test that iTerm is supported via TERM_PROGRAM."""
        mock_isatty.return_value = True

        result = _supports_title_setting()

        assert result is True

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM_PROGRAM": "vscode"})
    def test_vscode_terminal(self, mock_isatty):
        """Test that VS Code terminal is supported."""
        mock_isatty.return_value = True

        result = _supports_title_setting()

        assert result is True

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"WT_SESSION": "some-session-id"})
    def test_windows_terminal(self, mock_isatty):
        """Test that Windows Terminal is supported."""
        mock_isatty.return_value = True

        result = _supports_title_setting()

        assert result is True

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM": "dumb"}, clear=True)
    def test_unsupported_terminal(self, mock_isatty):
        """Test that unsupported terminal returns False."""
        mock_isatty.return_value = True

        result = _supports_title_setting()

        assert result is False


class TestSetTerminalTitle:
    """Tests for set_terminal_title()."""

    @patch("ai_launcher.utils.terminal._supports_title_setting")
    def test_unsupported_terminal(self, mock_supports):
        """Test that unsupported terminal returns False."""
        mock_supports.return_value = False

        result = set_terminal_title("Test Title")

        assert result is False

    @patch("ai_launcher.utils.terminal._supports_title_setting")
    @patch("sys.stdout")
    def test_set_title_success(self, mock_stdout, mock_supports):
        """Test successful title setting."""
        mock_supports.return_value = True

        result = set_terminal_title("Test Title")

        assert result is True
        # Check that ANSI escape sequence was written
        mock_stdout.write.assert_called_once()
        call_args = mock_stdout.write.call_args[0][0]
        assert "Test Title" in call_args
        assert "\033]0;" in call_args  # ANSI escape sequence
        assert "\007" in call_args  # BEL character

    @patch("ai_launcher.utils.terminal._supports_title_setting")
    @patch("sys.stdout")
    @patch.dict(os.environ, {"TMUX": "some-session"})
    def test_set_title_tmux(self, mock_stdout, mock_supports):
        """Test title setting in tmux uses different sequence."""
        mock_supports.return_value = True

        result = set_terminal_title("Test Title")

        assert result is True
        # Check that tmux escape sequence was written
        mock_stdout.write.assert_called_once()
        call_args = mock_stdout.write.call_args[0][0]
        assert "Test Title" in call_args
        assert "\033k" in call_args  # tmux start (ESC + k)
        assert "\033\\" in call_args  # tmux end (ESC + backslash)

    @patch("ai_launcher.utils.terminal._supports_title_setting")
    @patch("sys.stdout")
    def test_set_title_exception(self, mock_stdout, mock_supports):
        """Test that exceptions are handled gracefully."""
        mock_supports.return_value = True
        mock_stdout.write.side_effect = Exception("Test error")

        result = set_terminal_title("Test Title")

        assert result is False


class TestGetTerminalInfo:
    """Tests for get_terminal_info()."""

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM": "xterm-256color", "TERM_PROGRAM": "iTerm.app"})
    def test_get_terminal_info(self, mock_isatty):
        """Test getting terminal information."""
        mock_isatty.return_value = True

        info = get_terminal_info()

        assert "term" in info
        assert "term_program" in info
        assert "supports_title" in info
        assert "is_tty" in info
        assert "wt_session" in info
        assert "tmux" in info

        assert info["term"] == "xterm-256color"
        assert info["term_program"] == "iTerm.app"
        assert info["is_tty"] is True
        assert isinstance(info["supports_title"], bool)

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {}, clear=True)
    def test_get_terminal_info_no_env(self, mock_isatty):
        """Test terminal info with no environment variables."""
        mock_isatty.return_value = False

        info = get_terminal_info()

        assert info["term"] == "unknown"
        assert info["term_program"] == "unknown"
        assert info["is_tty"] is False
        assert info["supports_title"] is False
        assert info["wt_session"] is None
        assert info["tmux"] is False

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TMUX": "session-id", "WT_SESSION": "wt-id"})
    def test_get_terminal_info_special_terminals(self, mock_isatty):
        """Test terminal info for tmux and Windows Terminal."""
        mock_isatty.return_value = True

        info = get_terminal_info()

        assert info["tmux"] is True
        assert info["wt_session"] == "wt-id"
