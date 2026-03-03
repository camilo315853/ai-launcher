"""Tests for Cursor provider implementation.

Author: Solent Labs™
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_launcher.core.models import CleanupConfig
from ai_launcher.providers.cursor import CursorProvider


@pytest.fixture
def provider():
    return CursorProvider()


@pytest.fixture
def cleanup_config():
    return CleanupConfig(
        enabled=True,
        clean_provider_files=True,
        clean_system_cache=False,
        clean_npm_cache=False,
    )


class TestCursorMetadata:
    """Tests for Cursor provider metadata."""

    def test_metadata_name(self, provider):
        assert provider.metadata.name == "cursor"

    def test_metadata_display_name(self, provider):
        assert provider.metadata.display_name == "Cursor"

    def test_metadata_command(self, provider):
        assert provider.metadata.command == "cursor"

    def test_metadata_config_files(self, provider):
        assert ".cursorrules" in provider.metadata.config_files
        assert "CURSOR.md" in provider.metadata.config_files

    def test_metadata_requires_installation(self, provider):
        assert provider.metadata.requires_installation is True


class TestCursorIsInstalled:
    """Tests for Cursor installation check."""

    def test_installed(self, provider):
        with patch("shutil.which", return_value="/usr/bin/cursor"):
            assert provider.is_installed() is True

    def test_not_installed(self, provider):
        with patch("shutil.which", return_value=None):
            assert provider.is_installed() is False


class TestCursorLaunch:
    """Tests for Cursor launch."""

    def test_launch_basic(self, provider, tmp_path):
        with patch("subprocess.run") as mock_run:
            provider.launch(tmp_path)
            mock_run.assert_called_once_with(
                ["cursor", str(tmp_path)], check=True
            )

    def test_launch_not_found(self, provider, tmp_path):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(SystemExit) as exc_info:
                provider.launch(tmp_path)
            assert exc_info.value.code == 1

    def test_launch_keyboard_interrupt(self, provider, tmp_path):
        with patch("subprocess.run", side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit) as exc_info:
                provider.launch(tmp_path)
            assert exc_info.value.code == 0

    def test_launch_called_process_error(self, provider, tmp_path):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cursor")):
            with pytest.raises(SystemExit) as exc_info:
                provider.launch(tmp_path)
            assert exc_info.value.code == 1


class TestCursorCleanup:
    """Tests for Cursor cleanup."""

    def test_cleanup_no_config(self, provider, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            provider.cleanup_environment(verbose=False, cleanup_config=None)

    def test_cleanup_disabled(self, provider, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            config = CleanupConfig(enabled=False)
            provider.cleanup_environment(verbose=False, cleanup_config=config)

    def test_cleanup_provider_files_disabled(self, provider, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            config = CleanupConfig(enabled=True, clean_provider_files=False)
            provider.cleanup_environment(verbose=False, cleanup_config=config)

    def test_cleanup_removes_cache_linux(self, provider, tmp_path, cleanup_config):
        with patch("pathlib.Path.home", return_value=tmp_path):
            cursor_dir = tmp_path / ".cursor"
            cache_dir = cursor_dir / "Cache"
            cache_dir.mkdir(parents=True)
            (cache_dir / "data.txt").write_text("cached")

            provider.cleanup_environment(verbose=False, cleanup_config=cleanup_config)
            assert not cache_dir.exists()

    def test_cleanup_verbose(self, provider, tmp_path, cleanup_config, capsys):
        with patch("pathlib.Path.home", return_value=tmp_path):
            cursor_dir = tmp_path / ".cursor"
            cache_dir = cursor_dir / "Cache"
            cache_dir.mkdir(parents=True)
            (cache_dir / "data.txt").write_text("cached")

            provider.cleanup_environment(verbose=True, cleanup_config=cleanup_config)
            captured = capsys.readouterr()
            assert "Cleaned Cursor cache" in captured.out


class TestCursorCollectPreviewData:
    """Tests for Cursor preview data collection."""

    def test_no_files(self, provider, tmp_path):
        data = provider.collect_preview_data(tmp_path)
        assert data.provider_name == "Cursor"
        assert len(data.context_files) == 0

    def test_with_cursorrules(self, provider, tmp_path):
        rules = tmp_path / ".cursorrules"
        rules.write_text("rule1\nrule2\n")

        data = provider.collect_preview_data(tmp_path)
        assert len(data.context_files) == 1
        assert data.context_files[0].label == ".cursorrules"
        assert data.context_files[0].exists is True
        assert data.context_files[0].line_count == 2

    def test_with_cursor_md(self, provider, tmp_path):
        cursor_md = tmp_path / "CURSOR.md"
        cursor_md.write_text("# Cursor\nInstructions\n")

        data = provider.collect_preview_data(tmp_path)
        assert len(data.context_files) == 1
        assert data.context_files[0].label == "CURSOR.md"

    def test_with_both_files(self, provider, tmp_path):
        (tmp_path / ".cursorrules").write_text("rules\n")
        (tmp_path / "CURSOR.md").write_text("# Cursor\n")

        data = provider.collect_preview_data(tmp_path)
        assert len(data.context_files) == 2

    def test_global_config_paths(self, provider):
        paths = provider.get_global_context_paths()
        assert len(paths) == 3
        path_strs = [str(p) for p in paths]
        assert any(".cursor" in s for s in path_strs)
