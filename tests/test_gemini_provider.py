"""Tests for Gemini provider implementation.

Author: Solent Labs™
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_launcher.core.models import CleanupConfig
from ai_launcher.providers.gemini import GeminiProvider


@pytest.fixture
def provider():
    return GeminiProvider()


@pytest.fixture
def cleanup_config():
    return CleanupConfig(
        enabled=True,
        clean_provider_files=True,
        clean_system_cache=False,
        clean_npm_cache=False,
    )


class TestGeminiMetadata:
    """Tests for Gemini provider metadata."""

    def test_metadata_name(self, provider):
        assert provider.metadata.name == "gemini"

    def test_metadata_display_name(self, provider):
        assert provider.metadata.display_name == "Gemini CLI"

    def test_metadata_command(self, provider):
        assert provider.metadata.command == "gemini"

    def test_metadata_config_files(self, provider):
        assert "GEMINI.md" in provider.metadata.config_files
        assert ".geminirc" in provider.metadata.config_files

    def test_metadata_description(self, provider):
        assert "Google" in provider.metadata.description


class TestGeminiIsInstalled:
    """Tests for Gemini installation check."""

    def test_installed(self, provider):
        with patch("shutil.which", return_value="/usr/bin/gemini"):
            assert provider.is_installed() is True

    def test_not_installed(self, provider):
        with patch("shutil.which", return_value=None):
            assert provider.is_installed() is False


class TestGeminiLaunch:
    """Tests for Gemini launch."""

    def test_launch_basic(self, provider, tmp_path):
        with patch("subprocess.run") as mock_run:
            with patch("os.chdir"):
                provider.launch(tmp_path)
                mock_run.assert_called_once_with(["gemini"], check=True)

    def test_launch_not_found(self, provider, tmp_path):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with patch("os.chdir"):
                with pytest.raises(SystemExit) as exc_info:
                    provider.launch(tmp_path)
                assert exc_info.value.code == 1

    def test_launch_keyboard_interrupt(self, provider, tmp_path):
        with patch("subprocess.run", side_effect=KeyboardInterrupt):
            with patch("os.chdir"):
                with pytest.raises(SystemExit) as exc_info:
                    provider.launch(tmp_path)
                assert exc_info.value.code == 0

    def test_launch_called_process_error(self, provider, tmp_path):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "gemini")):
            with patch("os.chdir"):
                with pytest.raises(SystemExit) as exc_info:
                    provider.launch(tmp_path)
                assert exc_info.value.code == 1


class TestGeminiCleanup:
    """Tests for Gemini cleanup."""

    def test_cleanup_no_config(self, provider):
        provider.cleanup_environment(verbose=False, cleanup_config=None)

    def test_cleanup_disabled(self, provider):
        config = CleanupConfig(enabled=False)
        provider.cleanup_environment(verbose=False, cleanup_config=config)

    def test_cleanup_provider_files_disabled(self, provider):
        config = CleanupConfig(enabled=True, clean_provider_files=False)
        provider.cleanup_environment(verbose=False, cleanup_config=config)

    def test_cleanup_removes_cache(self, provider, tmp_path, cleanup_config):
        with patch("pathlib.Path.home", return_value=tmp_path):
            gemini_cache = tmp_path / ".gemini" / "cache"
            gemini_cache.mkdir(parents=True)
            (gemini_cache / "data.txt").write_text("cached")

            provider.cleanup_environment(verbose=False, cleanup_config=cleanup_config)
            assert not gemini_cache.exists()

    def test_cleanup_verbose(self, provider, tmp_path, cleanup_config, capsys):
        with patch("pathlib.Path.home", return_value=tmp_path):
            gemini_cache = tmp_path / ".gemini" / "cache"
            gemini_cache.mkdir(parents=True)
            (gemini_cache / "data.txt").write_text("cached")

            provider.cleanup_environment(verbose=True, cleanup_config=cleanup_config)
            captured = capsys.readouterr()
            assert "Cleaned Gemini cache" in captured.out


class TestGeminiCollectPreviewData:
    """Tests for Gemini preview data collection."""

    def test_no_files(self, provider, tmp_path):
        data = provider.collect_preview_data(tmp_path)
        assert data.provider_name == "Gemini CLI"
        assert len(data.context_files) == 0

    def test_with_gemini_md(self, provider, tmp_path):
        gemini_md = tmp_path / "GEMINI.md"
        gemini_md.write_text("# Gemini Instructions\nLine 2\nLine 3\n")

        data = provider.collect_preview_data(tmp_path)
        assert len(data.context_files) == 1
        assert data.context_files[0].label == "GEMINI.md"
        assert data.context_files[0].exists is True
        assert data.context_files[0].line_count == 3

    def test_global_config_paths(self, provider):
        paths = provider.get_global_context_paths()
        assert len(paths) == 2
        path_strs = [str(p) for p in paths]
        assert any(".gemini" in s for s in path_strs)
        assert any(".geminirc" in s for s in path_strs)
