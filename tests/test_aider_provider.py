"""Tests for Aider provider implementation.

Author: Solent Labs™
"""

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_launcher.core.models import CleanupConfig
from ai_launcher.providers.aider import AiderProvider


@pytest.fixture
def provider():
    return AiderProvider()


@pytest.fixture
def cleanup_config():
    return CleanupConfig(
        enabled=True,
        clean_provider_files=True,
        clean_system_cache=False,
        clean_npm_cache=False,
    )


class TestAiderMetadata:
    """Tests for Aider provider metadata."""

    def test_metadata_name(self, provider):
        assert provider.metadata.name == "aider"

    def test_metadata_display_name(self, provider):
        assert provider.metadata.display_name == "Aider"

    def test_metadata_command(self, provider):
        assert provider.metadata.command == "aider"

    def test_metadata_config_files(self, provider):
        assert ".aider.conf.yml" in provider.metadata.config_files
        assert "AIDER.md" in provider.metadata.config_files

    def test_metadata_requires_installation(self, provider):
        assert provider.metadata.requires_installation is True


class TestAiderIsInstalled:
    """Tests for Aider installation check."""

    def test_installed_when_found(self, provider):
        with patch("shutil.which", return_value="/usr/bin/aider"):
            assert provider.is_installed() is True

    def test_not_installed_when_missing(self, provider):
        with patch("shutil.which", return_value=None):
            assert provider.is_installed() is False


class TestAiderLaunch:
    """Tests for Aider launch."""

    def test_launch_basic(self, provider, tmp_path):
        with patch("subprocess.run") as mock_run:
            with patch("os.chdir"):
                provider.launch(tmp_path)
                mock_run.assert_called_once_with(["aider"], check=True)

    def test_launch_with_config_file(self, provider, tmp_path):
        config_file = tmp_path / ".aider.conf.yml"
        config_file.write_text("model: gpt-4")

        with patch("subprocess.run") as mock_run:
            with patch("os.chdir"):
                provider.launch(tmp_path)
                mock_run.assert_called_once_with(
                    ["aider", "--config", str(config_file)], check=True
                )

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
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "aider")):
            with patch("os.chdir"):
                with pytest.raises(SystemExit) as exc_info:
                    provider.launch(tmp_path)
                assert exc_info.value.code == 1


class TestAiderCleanup:
    """Tests for Aider cleanup."""

    def test_cleanup_no_config(self, provider, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            aider_dir = tmp_path / ".aider" / "cache"
            aider_dir.mkdir(parents=True)
            (aider_dir / "cached.txt").write_text("data")

            provider.cleanup_environment(verbose=False, cleanup_config=None)
            assert (aider_dir / "cached.txt").exists()

    def test_cleanup_disabled(self, provider, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            config = CleanupConfig(enabled=False)
            provider.cleanup_environment(verbose=False, cleanup_config=config)

    def test_cleanup_provider_files_disabled(self, provider, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            config = CleanupConfig(enabled=True, clean_provider_files=False)
            aider_cache = tmp_path / ".aider" / "cache"
            aider_cache.mkdir(parents=True)
            (aider_cache / "data.txt").write_text("data")

            provider.cleanup_environment(verbose=False, cleanup_config=config)
            assert (aider_cache / "data.txt").exists()

    def test_cleanup_removes_cache(self, provider, tmp_path, cleanup_config):
        with patch("pathlib.Path.home", return_value=tmp_path):
            aider_cache = tmp_path / ".aider" / "cache"
            aider_cache.mkdir(parents=True)
            (aider_cache / "item.txt").write_text("cached")

            provider.cleanup_environment(verbose=False, cleanup_config=cleanup_config)
            assert not aider_cache.exists()

    def test_cleanup_verbose(self, provider, tmp_path, cleanup_config, capsys):
        with patch("pathlib.Path.home", return_value=tmp_path):
            aider_cache = tmp_path / ".aider" / "cache"
            aider_cache.mkdir(parents=True)
            (aider_cache / "item.txt").write_text("cached")

            provider.cleanup_environment(verbose=True, cleanup_config=cleanup_config)
            captured = capsys.readouterr()
            assert "Cleaned Aider cache" in captured.out


class TestAiderCollectPreviewData:
    """Tests for Aider preview data collection."""

    def test_no_files(self, provider, tmp_path):
        data = provider.collect_preview_data(tmp_path)
        assert data.provider_name == "Aider"
        assert len(data.context_files) == 0

    def test_with_aider_config(self, provider, tmp_path):
        config_file = tmp_path / ".aider.conf.yml"
        config_file.write_text("model: gpt-4\napi_key: xxx\n")

        data = provider.collect_preview_data(tmp_path)
        assert len(data.context_files) == 1
        assert data.context_files[0].label == ".aider.conf.yml"
        assert data.context_files[0].exists is True
        assert data.context_files[0].line_count == 2

    def test_with_aider_md(self, provider, tmp_path):
        aider_md = tmp_path / "AIDER.md"
        aider_md.write_text("# Aider instructions\nLine 2\n")

        data = provider.collect_preview_data(tmp_path)
        assert len(data.context_files) == 1
        assert data.context_files[0].label == "AIDER.md"

    def test_with_both_files(self, provider, tmp_path):
        (tmp_path / ".aider.conf.yml").write_text("model: gpt-4\n")
        (tmp_path / "AIDER.md").write_text("# Instructions\n")

        data = provider.collect_preview_data(tmp_path)
        assert len(data.context_files) == 2
        labels = {f.label for f in data.context_files}
        assert ".aider.conf.yml" in labels
        assert "AIDER.md" in labels

    def test_global_config_paths(self, provider):
        paths = provider.get_global_context_paths()
        assert len(paths) == 1
        assert ".aider" in str(paths[0])
